"""
lipidimea/lipids/annotation.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for annotating features
"""


from os import path as op
from sqlite3 import connect
from itertools import product

from mzapy.isotopes import ms_adduct_mz
from mzapy._util import _ppm_error
import yaml

from lipidimea.lipids import LMAPS, Lipid, LipidWithChains
from lipidimea.util import debug_handler
from lipidimea.lipids._fragmentation_rules import load_rules
from lipidimea.lipids._util import get_c_u_combos


class SumCompLipidDB():
    """
    creates an in-memory database with lipids at the level of sum composition for initial
    lipid identifications, using a configuration file to specify what lipids to include
    """

    def _init_db(self):
        """ initialize DB in memory and set up SumCompLipids table """
        create_qry = """
        CREATE TABLE SumCompLipids (
            lmid_prefix TEXT, 
            sum_c INT,
            sum_u INT, 
            name TEXT,
            adduct TEXT,
            mz REAL
        );
        """
        # create the database in memory
        self._con = connect(':memory:')
        self._cur = self._con.cursor()
        self._cur.execute(create_qry)

    @staticmethod
    def max_u(c):
        """
        Maximum number of unsaturations as a function of carbon count for a single carbon chain. By default up 
        to 15 C = 2 max U, 16+ C = 6 max U

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
        else:
            return 6

    def gen_sum_compositions(self, n_chains, min_c, max_c, odd_c, max_u=None):
        """ 
        yields all unique sum compositions from combinations of fatty acids that are iterated over
        using some rules:

        * specify minimum number of carbons in a FA chain
        * specify maximum number of carbons in a FA chain
        * specify whether to include odd # of carbons for FA chains
        * max number of unsaturations is determined by FA chain length (by default: up to 15 C = 2 max 
            U, 16+ C = 6 max U... override ``SumCompLipidDB.max_u()`` static method to change)

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
            sum_comp.add((c, u))
        # yield the unique sum compositions
        for comp in sum_comp:
            yield comp

    def __init__(self):
        """
        Initialize the database. Fill the database with lipids using ``SumCompLipidDB.fill_db_from_config()``
        """
        self._init_db()

    def fill_db_from_config(self, config, min_c, max_c, odd_c):
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

        where the top-level keys are lipid class names (abbreviated) which map to three lists of parameters 
        with keys "fa_mod", "n_chains" and "adducts". All permutations of defined lipid class, fatty acid modifier, 
        number of chains, and adduct are used to fill the database

        Parameters
        ----------
        config : ``str``
            YAML configuration file specifying what lipids to include
        min_c, max_c : ``int``
            min/max number of carbons in an acyl chain
        odd_c : ``bool``
            whether to include odd # C for FAs 
        """
        # load params from config file
        with open(config, 'r') as yf:
            cnf = yaml.safe_load(yf)
        # iterate over the lipid classes specified in the config and generate m/zs
        # then add to db
        insert_qry = 'INSERT INTO SumCompLipids VALUES (?,?,?,?,?,?);'
        for lmaps_prefix, adducts in cnf.items():
            # adjust min unsaturation level for sphingolipids
            max_u = 2 if lmaps_prefix[:4] == 'LMSP' else None
            n_chains = LMAPS[lmaps_prefix]['n_chains']
            for sumc, sumu in self.gen_sum_compositions(n_chains, min_c, max_c, odd_c, max_u=max_u):
                lpd = Lipid(lmaps_prefix, sumc, sumu)
                for adduct in adducts:
                    mz = ms_adduct_mz(lpd.formula, adduct)
                    qdata = (lpd.lmaps_id_prefix, sumc, sumu, str(lpd), adduct, mz)
                    self._cur.execute(insert_qry, qdata)
            
    def get_sum_comp_lipid_ids(self, mz, mz_tol):
        """
        searches the sum composition lipid ids database using a feature m/z 
        
        Returns all potential lipid annotations within search tolerance

        Parameters
        ----------
        mz : ``float``
            feature m/z
        mz_tol : ``float``
            tolerance for matching m/z

        Returns
        -------
        candidates : ``list(tuple(...))``
            list of lipid annotation candidates, each is a tuple consisting of 
            lmaps_id_prefix, name, adduct, and m/z
        """
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        qry = "SELECT lmid_prefix, name, adduct, mz FROM SumCompLipids WHERE mz>=? AND mz<=?"
        return [_ for _ in self._cur.execute(qry, (mz_min, mz_max)).fetchall()]

    def close(self):
        """
        close the database
        """
        self._con.close()


def remove_lipid_annotations(results_db):
    """
    remove all annotations from the results database

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    """
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # drop any existing annotations
    cur.execute('DELETE FROM Lipids;')
    # clean up
    con.commit()
    con.close()


def annotate_lipids_sum_composition(results_db, lipid_class_scdb_config, params,
                                    debug_flag=None, debug_cb=None):
    """
    annotate features from a DDA-DIA data analysis using a generated database of lipids
    at the level of sum composition

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    lipid_class_scdb_config : ``str``
        path to lipid class config file for generating lipid database, None to use built-in default
    params : ``dict(...)``
        parameters for lipid annotation
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    debug_handler(debug_flag, debug_cb, 'ANNOTATING LIPIDS AT SUM COMPOSITION LEVEL USING GENERATED LIPID DATABSE...')
    # unpack params
    ionization = params['misc']['ionization']
    overwrite = params['misc']['overwrite_annotations']
    params = params['annotation']['ann_sum_comp']
    # load default lipid class params if they werent specified
    dlcp_path = op.join(op.dirname(op.dirname(op.abspath(__file__))), '_include/scdb_params')
    lipid_class_scdb_config = op.join(dlcp_path, 'default_{}.yml'.format(ionization)) if lipid_class_scdb_config is None else lipid_class_scdb_config
    # params for FA length
    min_c, max_c, odd_c = params['ann_sc_min_c'], params['ann_sc_max_c'], params['ann_sc_odd_c']
    mz_tol = params['ann_sc_mz_tol']
    # create the sum composition lipid database
    scdb = SumCompLipidDB()
    scdb.fill_db_from_config(lipid_class_scdb_config, min_c, max_c, odd_c)
    # remove existing annotations if requested
    if overwrite:
        debug_handler(debug_flag, debug_cb, 'removing any existing lipid annotations')
        remove_lipid_annotations(results_db)
    else:
        debug_handler(debug_flag, debug_cb, 'appending new lipid annotations to any existing annotations')
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through DIA features and get putative annotations
    qry_sel = 'SELECT dia_feat_id, mz FROM CombinedFeatures'
    qry_ins = 'INSERT INTO Lipids VALUES (?,?,?,?,?,?,?,?)'
    n_feats, n_feats_annotated, n_anns = 0, 0, 0
    for dia_feat_id, mz, in cur.execute(qry_sel).fetchall():
        n_feats += 1
        annotated = False
        for clmidp, cname, cadduct, cmz in scdb.get_sum_comp_lipid_ids(mz, mz_tol):
            annotated = True
            qdata = (None, dia_feat_id, clmidp, cname, cadduct, _ppm_error(cmz, mz), None, None)
            cur.execute(qry_ins, qdata)
            n_anns += 1
        if annotated:
            n_feats_annotated += 1
    # report how many features were annotated
    debug_handler(debug_flag, debug_cb, 'ANNOTATED: {} / {} DIA features ({} annotations total)'.format(n_feats_annotated, n_feats, n_anns))
    # clean up
    scdb.close()
    con.commit()
    con.close()


def filter_annotations_by_rt_range(results_db, lipid_class_rt_ranges, params,
                                   debug_flag=None, debug_cb=None):
    """
    filter feature annotations based on their retention times vs. expected retention time ranges
    by lipid class for a specified chromatographic method

    Parameters
    ----------
    results_db : ``srt``
        path to DDA-DIA analysis results database
    lipid_class_rt_ranges : ``str``
        path to config file with lipid class RT ranges, None to use built-in default
    params : ``dict(...)``
        parameters for lipid annotation
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    debug_handler(debug_flag, debug_cb, 'FILTERING LIPID ANNOTATIONS BASED ON LIPID CLASS RETENTION TIME RANGES ...')
    # unpack params
    params = params['annotation']['ann_rt_range']
    # ann_rtr_only_keep_defined_classes
    # load RT ranges
    rtr_path = op.join(op.dirname(op.dirname(op.abspath(__file__))), '_include/rt_ranges/default_RP.yml')
    lipid_class_rt_ranges = rtr_path if lipid_class_rt_ranges is None else lipid_class_rt_ranges
    with open(lipid_class_rt_ranges, 'r') as yf:
        rt_ranges = yaml.safe_load(yf)
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through annotations, check if the RT is within specified range 
    anns_to_del = []  # track annotation IDs to delete
    qry_sel = 'SELECT ann_id, lmaps_id_prefix, rt FROM Lipids JOIN _DIAFeatures USING(dia_feat_id);'
    n_anns = 0
    for ann_id, lmid_prefix, rt in cur.execute(qry_sel).fetchall():
        n_anns += 1
        if lmid_prefix in rt_ranges:
            rtmin, rtmax = rt_ranges[lmid_prefix]
            if rt <= rtmin or rt >= rtmax:
                anns_to_del.append(ann_id)
        elif params['ann_rtr_only_keep_defined_classes']:
            anns_to_del.append(ann_id)
    # delete any annotations not within specified RT range
    qry_del = 'DELETE FROM Lipids WHERE ann_id=?'
    for ann_id in anns_to_del:
        cur.execute(qry_del, (ann_id,))
    # clean up
    con.commit()
    con.close()
    debug_handler(debug_flag, debug_cb, 'FILTERED: {} / {} annotations based on lipid class RT ranges'.format(len(anns_to_del), n_anns))


def update_lipid_ids_with_frag_rules(results_db,
                                     debug_flag=None, debug_cb=None):
    """
    update lipid annotations

    Parameters
    ----------
    results_db : ``srt``
        path to DDA-DIA analysis results database
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    debug_handler(debug_flag, debug_cb, 'UPDATING LIPID ANNOTATIONS USING FRAGMENTATION RULES ...')
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    n_anns = cur.execute('SELECT COUNT(*) FROM Lipids;').fetchall()[0][0]
    # iterate through annotations, see if there are annotatable fragments
    # only select out the annotations that have NULL fragments
    qry_sel1 = ('SELECT ann_id, lmaps_id_prefix, lipid, mz, dia_feat_id FROM Lipids '
                'JOIN _DIAFeatures USING(dia_feat_id) JOIN DDAFeatures USING(dda_feat_id) '
                'WHERE fragments IS NULL;')
    n_updt = 0
    qry_upd = 'UPDATE Lipids SET fragments=? WHERE ann_id=?;'
    for ann_id, lmid_prefix, lipid_name, pmz, dia_feat_id in cur.execute(qry_sel1).fetchall():
        print(ann_id, lmid_prefix, lipid_name, dia_feat_id)
        # get fragment m/zs
        qry_sel2 = 'SELECT mz FROM DIADeconFragments JOIN _DIAFeatsToDeconFrags USING(decon_frag_id) WHERE dia_feat_id=?'
        res = cur.execute(qry_sel2, (dia_feat_id,)).fetchall()
        fmzs = []
        if res is not None:
            fmzs = [_[0] for _ in res]
        for fmz in fmzs:
            print('\tfragment:', fmz)
        if fmzs != []:
            fragments_str = ''
            new_names = set()
            # load fragmentation rules
            lipid = parse_lipid_name(lipid_name)
            rules = load_rules(lipid.lipid_class_abbrev, 'POS')
            c_u_combos = [_ for _ in get_c_u_combos(lipid, 12, 24, False)]
            for rule in rules:
                if rule.static:
                    print('\trule:', rule.label(), rule.mz(pmz))
                    rmz = rule.mz(pmz)
                    for fmz in fmzs:
                        if abs(rmz - fmz) <= 0.025:
                            fragments_str += '{}->{:.4f};'.format(rule.label(), rmz)
                else:
                    for c, u in sorted(c_u_combos):
                        print('\trule:', rule.label(c, u), rule.mz(pmz, c, u))
                        rmz = rule.mz(pmz, c, u)
                        for fmz in fmzs:
                            if abs(rmz - fmz) <= 0.025:
                                fragments_str += '{}->{:.4f};'.format(rule.label(c, u), rmz)
                                # TODO (Dylan Ross): need some logic here to figure out new names
            if fragments_str != '':
                cur.execute(qry_upd, (fragments_str, ann_id))
    # clean up
    con.commit()
    con.close()
    debug_handler(debug_flag, debug_cb, 'UPDATED: {} / {} annotations using fragmentation rules'.format(n_updt, n_anns))
