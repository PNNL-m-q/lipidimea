"""
lipidimea/annotation.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for annotating features
"""


from os import path as op
import os
import errno
from sqlite3 import connect
from itertools import product
from typing import Generator, Tuple, List, Optional, Callable

from mzapy.isotopes import ms_adduct_mz
from mzapy._util import _ppm_error
import yaml

from lipidlib.lipids import LMAPS, get_c_u_combos, Lipid
from lipidlib.parser import parse_lipid_name
from lipidlib._fragmentation_rules import load_rules

from lipidimea.typing import (
    ScdbLipidId, ResultsDbPath, YamlFilePath
)
from lipidimea.util import debug_handler
from lipidimea.msms._util import tol_from_ppm, str_to_ms2
from lipidimea.params import (
    SumCompAnnotationParams, FragRuleAnnParams, AnnotationParams
)


# define paths to default sum composition lipid DB config files
DEFAULT_POS_SCDB_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), '_include/scdb/pos.yml')
DEFAULT_NEG_SCDB_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), '_include/scdb/neg.yml')

# define path to default RT ranges config
DEFAULT_RP_RT_RANGE_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), '_include/rt_ranges/RP.yml')


class SumCompLipidDB():
    """
    creates an in-memory database with lipids at the level of sum composition for initial
    lipid identifications, using a configuration file to specify what lipids to include
    """

    def _init_db(self
                 ) -> None :
        """ initialize DB in memory and set up SumCompLipids table """
        create_qry = """--beginsql
        CREATE TABLE SumCompLipids (
            lmid_prefix TEXT NOT NULL, 
            sum_c INT NOT NULL,
            sum_u INT NOT NULL, 
            n_chains INT NOT NULL,
            name TEXT NOT NULL,
            adduct TEXT NOT NULL,
            mz REAL NOT NULL
        ) STRICT
        --endsql"""
        # create the database in memory
        self._con = connect(':memory:')
        self._cur = self._con.cursor()
        self._cur.execute(create_qry)

    @staticmethod
    def max_u(c: int
              ) -> int :
        """
        Maximum number of unsaturations as a function of carbon count for a single carbon chain. By default up 
        to 15 C = 2 max U, 16-19 C = 4 max U, 20+ C = 6 max U

        override this static method to change how this is calculated (input: ``int`` number of carbons in chain, 
        output: ``int`` max number of unsaturations)

        Parameters
        ----------
        c : ``int``
            number of carbons in chain

        Returns
        -------
        u : ``int``
            max number of unsaturations in chain
        """
        if c < 16:
            return 2
        elif c <= 20:
            return 4
        else:
            return 6

    def gen_sum_compositions(self, 
                             n_chains, 
                             min_c, 
                             max_c, 
                             odd_c, 
                             max_u=None
                             ) -> Generator[Tuple[int, int], None, None] :
        """ 
        yields all unique sum compositions from combinations of fatty acids that are iterated over
        using some rules:

        * specify minimum number of carbons in a FA chain
        * specify maximum number of carbons in a FA chain
        * specify whether to include odd # of carbons for FA chains
        * max number of unsaturations is determined by FA chain length,
          override ``SumCompLipidDB.max_u()`` static method to change)

        Parameters
        ----------
        n_chains : ``int``
            number of FA chains
        min_c, max_c : ``int``
            min/max number of carbons in an acyl chain
        odd_c : ``bool``
            whether to include odd # C for FAs
        max_u : ``int``, optional
            restrict maximum number of unsaturations (in sum composition, not individual FAs)

        Yields
        ------
        sum_comp : ``tuple(int, int)``
            unique sum compoisions as (# carbons, # unsaturations)
        """
        fas = []
        for n_c in range(min_c, max_c + 1):
            if odd_c or n_c % 2 == 0:
                max_u = self.max_u(n_c) if max_u is None else min(max_u, self.max_u(n_c))
                for n_u in range(0, self.max_u(n_c) + 1):
                    fas.append((n_c, n_u))
        # permute over acyl chains
        sum_comp = set()
        for combo in product(fas, repeat=n_chains):
            c, u = 0, 0
            for fac, fau in combo:
                c += fac
                u += fau
            comp = (c, u)
            if comp not in sum_comp:
                sum_comp.add(comp)
                yield comp

    def __init__(self
                 ) -> None :
        """
        Initialize the database. 
        
        Fill the database with lipids using ``SumCompLipidDB.fill_db_from_config()``
        """
        self._init_db()

    def fill_db_from_config(self, 
                            config_yml: str,
                            min_c: int, 
                            max_c: int, 
                            odd_c: bool
                            ) -> None :
        """ 
        fill the DB with lipids using parameters from a YAML config file
        
        Config file should have a structure as in the following example:

        .. code-block:: yaml

            LMFA0707: ['[M+H]+']
            LMGP0101: ['[M+H]+']
            LMGP0102: ['[M+H]+']
            LMGP0103: ['[M+H]+']
            LMGP0105: ['[M+H]+']
            LMGP0106: ['[M+H]+']
            LMGP0107: ['[M+H]+']

        Parameters
        ----------
        config_yml : ``str``
            YAML configuration file specifying what lipids to include
        min_c, max_c : ``int``
            min/max number of carbons in an acyl chain
        odd_c : ``bool``
            whether to include odd # C for FAs 
        """
        # load params from config file
        with open(config_yml, 'r') as yf:
            cnf = yaml.safe_load(yf)
        # TODO (Dylan Ross): validate the structure of the data from the YAML config file
        # iterate over the lipid classes specified in the config and generate m/zs
        # then add to db
        insert_qry = """--beginsql
            INSERT INTO SumCompLipids VALUES (?,?,?,?,?,?,?)
        --endsql"""
        for lmaps_prefix, adducts in cnf.items():
            # adjust min unsaturation level for sphingolipids
            max_u = 2 if lmaps_prefix[:4] == 'LMSP' else None
            n_chains = LMAPS[lmaps_prefix]['n_chains']
            for sumc, sumu in self.gen_sum_compositions(n_chains, min_c, max_c, odd_c, max_u=max_u):
                lpd = Lipid(lmaps_prefix, sumc, sumu)
                for adduct in adducts:
                    mz = ms_adduct_mz(lpd.formula, adduct)
                    qdata = (lpd.lmaps_id_prefix, sumc, sumu, n_chains, str(lpd), adduct, mz)
                    self._cur.execute(insert_qry, qdata)
            
    def get_sum_comp_lipid_ids(self, 
                               mz: float, 
                               ppm: float
                               ) -> List[ScdbLipidId] :
        """
        searches the sum composition lipid ids database using a feature m/z 
        
        Returns all potential lipid annotations within search tolerance

        Parameters
        ----------
        mz : ``float``
            feature m/z
        ppm : ``float``
            tolerance for matching m/z (in ppm)

        Returns
        -------
        candidates : ``list(tuple(...))``
            list of lipid annotation candidates, each is a tuple consisting of 
            lmaps_id_prefix, name, adduct, and m/z
        """
        mz_tol = tol_from_ppm(mz, ppm)
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        qry = """--beginsql
            SELECT lmid_prefix, name, sum_c, sum_u, n_chains, adduct, mz FROM SumCompLipids WHERE mz>=? AND mz<=?
        --endsql"""
        return [_ for _ in self._cur.execute(qry, (mz_min, mz_max)).fetchall()]

    def close(self
              ) -> None :
        """
        close the database
        """
        self._con.close()


def remove_lipid_annotations(results_db: ResultsDbPath
                             ) -> None :
    """
    remove all annotations from the results database

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # drop any existing annotations
    cur.execute("DELETE FROM Lipids;")
    # drop existing sum composition entries for annotations
    cur.execute("DELETE FROM LipidSumComp;")
    # clean up
    con.commit()
    con.close()


def add_lmaps_ont(results_db: ResultsDbPath,
                  ) -> None :
    """
    Add category/class/subclass from LipidMAPS ontology (as defined in lipidlib)
    
    .. note:: 

        This is necessary for the `LipidMapsLong` view to be populated

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    """
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # drop any existing entries
    cur.execute("DELETE FROM _LipidMapsPrefixToLong;")
    qry = """--beginsql
        INSERT INTO _LipidMapsPrefixToLong VALUES (?,?,?,?)
    --endsql"""
    for k, v in LMAPS.items():
        cur.execute(qry, (k,) + tuple(v["classification"]))
    # clean up
    con.commit()
    con.close()


def annotate_lipids_sum_composition(results_db: ResultsDbPath, 
                                    scdb_config_yml: YamlFilePath, 
                                    params: SumCompAnnotationParams,
                                    debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                    ) -> Tuple[int, int] :
    """
    annotate features from a DDA-DIA data analysis using a generated database of lipids
    at the level of sum composition

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    scdb_config_yml : ``str``
        path to lipid class config file for generating lipid database
        use DEFAULT_POS_SCDB_CONFIG or DEFAULT_NEG_SCDB_CONFIG for built in default config files
    params : ``SumCompAnnotationParams``
        parameters for lipid annotation by sum composition
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_feats_annotated : ``int``
        number of features annotated
    n_anns : ``int``
        number of total annotations
    """
    # ensure results database file exists
    if not op.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    debug_handler(debug_flag, debug_cb, 
                  "ANNOTATING LIPIDS AT SUM COMPOSITION LEVEL USING GENERATED LIPID DATABASE...")
    # create the sum composition lipid database
    scdb = SumCompLipidDB()
    scdb.fill_db_from_config(scdb_config_yml, params.fa_min_c, params.fa_max_c, params.fa_odd_c)
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through DIA features and get putative annotations
    qry_sel = """--beginsql
        SELECT dia_pre_id, mz FROM DIAPrecursors
    --endsql"""
    qry_ins = """--beginsql
        INSERT INTO Lipids VALUES (?,?,?,?,?,?,?)
    --endsql"""
    qry_ins2 = """--beginsql
        INSERT INTO LipidSumComp VALUES (?,?,?,?)
    --endsql"""
    n_feats, n_feats_annotated, n_anns = 0, 0, 0
    for dia_feat_id, mz, in cur.execute(qry_sel).fetchall():
        n_feats += 1
        annotated = False
        for clmidp, cname, csumc, csumu, cchains, cadduct, cmz in scdb.get_sum_comp_lipid_ids(mz, params.mz_ppm):
            annotated = True
            qdata = (None, dia_feat_id, clmidp, cname, cadduct, _ppm_error(cmz, mz), None)
            # add the Lipids entry
            cur.execute(qry_ins, qdata)
            # add the LipidSumComp entry
            cur.execute(qry_ins2, (cur.lastrowid, csumc, csumu, cchains))
            n_anns += 1
        if annotated:
            n_feats_annotated += 1
    # report how many features were annotated
    debug_handler(debug_flag, debug_cb, 
                  f"ANNOTATED: {n_feats_annotated} / {n_feats} DIA features ({n_anns} annotations total)")
    # clean up
    scdb.close()
    con.commit()
    con.close()
    # return the number of features annotated
    return n_feats_annotated, n_anns


def filter_annotations_by_rt_range(results_db: ResultsDbPath, 
                                   rt_range_config_yml: YamlFilePath,
                                   debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                   ) -> int :
    """
    filter feature annotations based on their retention times vs. expected retention time ranges
    by lipid class for a specified chromatographic method

    Parameters
    ----------
    results_db : ``ResultsDbPath``
        path to DDA-DIA analysis results database
    rt_ranges_config : ``str``
        path to YAML config file with lipid class RT ranges, None to use built-in default
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_anns_filtered : ``int``
        number of annotations filtered based on RT ranges
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    debug_handler(debug_flag, debug_cb, 
                  "FILTERING LIPID ANNOTATIONS BASED ON LIPID CLASS RETENTION TIME RANGES ...")
    # ann_rtr_only_keep_defined_classes
    # load RT ranges
    rtr_path = op.join(op.dirname(op.dirname(op.abspath(__file__))), "_include/rt_ranges/default_RP.yml")
    rt_range_config_yml = rtr_path if rt_range_config_yml is None else rt_range_config_yml
    with open(rt_range_config_yml, 'r') as yf:
        rt_ranges = yaml.safe_load(yf)
    # TODO (Dylan Ross): validate the structure of the data from the YAML config file
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through annotations, check if the RT is within specified range 
    anns_to_del = []  # track annotation IDs to delete
    qry_sel = """--beginsql
        SELECT lipid_id, lmid_prefix, rt FROM Lipids JOIN DIAPrecursors USING(dia_pre_id)
    --endsql"""
    n_anns = 0
    for ann_id, lmid_prefix, rt in cur.execute(qry_sel).fetchall():
        n_anns += 1
        if lmid_prefix in rt_ranges:
            rtmin, rtmax = rt_ranges[lmid_prefix]
            if rt <= rtmin or rt >= rtmax:
                anns_to_del.append(ann_id)
        else:
            anns_to_del.append(ann_id)
    # delete any annotations not within specified RT range
    qry_del = """--beginsql
        DELETE FROM Lipids WHERE lipid_id=?
    --endsql"""
    for ann_id in anns_to_del:
        cur.execute(qry_del, (ann_id,))
    # clean up
    con.commit()
    con.close()
    n_anns_filtered = len(anns_to_del)
    debug_handler(debug_flag, debug_cb, 
                  f"FILTERED: {n_anns_filtered} / {n_anns} annotations based on lipid class RT ranges")
    # return the number of annotations that were filtered out
    return n_anns_filtered 


def update_lipid_ids_with_frag_rules(results_db: ResultsDbPath,
                                     params: FragRuleAnnParams,
                                     debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                     ) -> None :
    """
    update lipid annotations based on MS/MS spectra and fragmentation rules

    Parameters
    ----------
    results_db : ``ResultsDbPath``
        path to DDA-DIA analysis results database
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    
    Returns 
    -------
    n_anns_updated : ``int``
        number of feature annotations updated using frag rules
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    debug_handler(debug_flag, debug_cb, 'UPDATING LIPID ANNOTATIONS USING FRAGMENTATION RULES ...')
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    n_anns = cur.execute('SELECT COUNT(*) FROM Lipids;').fetchall()[0][0]
    # iterate through annotations, see if there are annotatable fragments
    # only select out the annotations that have NULL fragments
    qry_sel1 = """--beginsql
        SELECT 
            lipid_id, 
            lmid_prefix, 
            lipid, 
            mz, 
            dia_pre_id,
            GROUP_CONCAT(dia_frag_id),
            GROUP_CONCAT(fmz)
        FROM 
            Lipids 
            JOIN DIAPrecursors USING(dia_pre_id) 
            LEFT JOIN DIAFragments USING(dia_pre_id)
        GROUP BY 
            dia_pre_id
    --endsql"""
    n_updt = 0
    qry_add_frag = """--beginsql
        INSERT INTO LipidFragments VALUES (?,?,?,?,?,?)
    --endsql"""
    for lipid_id, lmid_prefix, lipid_name, pmz, dia_pre_id, fids, fmzs in cur.execute(qry_sel1).fetchall():
        updt = False
        #print(lipid_id, lmid_prefix, lipid_name, dia_pre_id)
        if fmzs is not None:
            new_names = set()
            # load fragmentation rules
            lipid = parse_lipid_name(lipid_name)
            found, rules = load_rules(lipid.lmaps_id_prefix, 'POS')
            c_u_combos = [_ for _ in get_c_u_combos(lipid, params.fa_min_c, params.fa_max_c, params.fa_odd_c,
                                                    max_u=SumCompLipidDB.max_u)]
            for ffmz, ffid in zip(map(float, fmzs.split(",")), map(int, fids.split(","))):
                for rule in rules:
                    if rule.static:
                        rmz = rule.mz(pmz)
                        ppm = _ppm_error(rmz, ffmz)
                        if abs(ppm) <= params.mz_ppm:
                            cur.execute(qry_add_frag, (lipid_id, ffid, rule.label(), rmz, ppm, None))
                    else:
                        for c, u in sorted(c_u_combos):
                            rmz = rule.mz(pmz, c, u)
                            ppm = _ppm_error(rmz, ffmz)
                            if abs(ppm) <= params.mz_ppm:
                                cur.execute(qry_add_frag, (lipid_id, ffid, rule.label(c, u), rmz, ppm, f"{c}:{u}"))
                                updt = True
                                #print('\trule:', rule.label(c, u), rmz)
                                #print("\t\tmatches fragment:", ffmz)
                                # TODO (Dylan Ross): need some logic here to figure out new names
            if updt:
                n_updt += 1
    # clean up
    con.commit()
    con.close()
    debug_handler(debug_flag, debug_cb, f"UPDATED: {n_updt} / {n_anns} annotations using fragmentation rules")
    return n_updt


def annotate_lipids(results_db: ResultsDbPath,
                    params: AnnotationParams,
                    scdb_config_yml: YamlFilePath,
                    rt_range_config_yml: YamlFilePath,
                    debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                    ) -> None :
    """
    Perform the full lipid annotation workflow:
    
    - remove existing lipid annotations
    - populate the LipidMAPS ontology info (from lipidlib)
    - generate initial lipid annotation at the level of sum composition
    - filter annotations based on retention time ranges
    - update lipid annotations using fragmentation rules
    
    Parameters
    ----------

    """
    remove_lipid_annotations(results_db)
    add_lmaps_ont(results_db)
    n_feats_annotated, n_anns = annotate_lipids_sum_composition(results_db, scdb_config_yml, 
                                                                 params.sum_comp_annotation_params, 
                                                                 debug_flag=debug_flag, debug_cb=debug_cb)
    n_feats_filtered = filter_annotations_by_rt_range(results_db, rt_range_config_yml, 
                                                      debug_flag=debug_flag, debug_cb=debug_cb)
    n_anns_updated = update_lipid_ids_with_frag_rules(results_db, params.frag_rule_ann_params,
                                                      debug_flag=debug_flag, debug_cb=debug_cb)
    pass