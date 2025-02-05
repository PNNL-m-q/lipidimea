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
from typing import Generator, Tuple, List, Optional, Callable, Dict, Iterable

from mzapy.isotopes import ms_adduct_mz
from mzapy._util import _ppm_error
import yaml
import numpy as np
import numpy.typing as npt
from scipy.optimize import curve_fit

from lipidimea.typing import (
    ScdbLipidId, ResultsDbPath, ResultsDbCursor, YamlFilePath
)
from lipidimea.util import debug_handler
from lipidimea.msms._util import tol_from_ppm
from lipidimea.params import (
    AnnotationParams, LITERATURE_CCS_TREND_PARAMS
)
from lipidimea._lipidlib.lipids import LMAPS, get_c_u_combos, Lipid, LipidWithChains
from lipidimea._lipidlib.parser import parse_lipid_name
from lipidimea._lipidlib._fragmentation_rules import load_rules


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
                             n_chains: int, 
                             min_c: int, 
                             max_c: int, 
                             odd_c: bool, 
                             max_u: Optional[int] = None
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
        path to LipidIMEA analysis results database
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
    # drop existing fragment annotations
    cur.execute("DELETE FROM LipidFragments;")
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
        path to LipidIMEA analysis results database
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
                                    params: AnnotationParams,
                                    debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                    ) -> Tuple[int, int] :
    """
    annotate features from a DDA-DIA data analysis using a generated database of lipids
    at the level of sum composition

    Parameters
    ----------
    results_db : ``str``
        path to LipidIMEA analysis results database
    params : ``AnnotationParams``
        parameters for lipid annotation
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
    scdb.fill_db_from_config(params.SumCompAnnParams.config, 
                             params.SumCompAnnParams.fa_min_c, 
                             params.SumCompAnnParams.fa_max_c, 
                             params.SumCompAnnParams.fa_odd_c)
    # connect to  results database
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through DIA features and get putative annotations
    qry_sel = """--beginsql
        SELECT dia_pre_id, mz FROM DIAPrecursors
    --endsql"""
    qry_ins = """--beginsql
        INSERT INTO Lipids VALUES (?,?,?,?,?,?,?,?,?)
    --endsql"""
    qry_ins2 = """--beginsql
        INSERT INTO LipidSumComp VALUES (?,?,?,?)
    --endsql"""
    n_feats, n_feats_annotated, n_anns = 0, 0, 0
    for dia_feat_id, mz, in cur.execute(qry_sel).fetchall():
        n_feats += 1
        annotated = False
        for clmidp, cname, csumc, csumu, cchains, cadduct, cmz in scdb.get_sum_comp_lipid_ids(mz, params.SumCompAnnParams.mz_ppm):
            annotated = True
            # special case: lipids with single chains automatically have inferred acyl chain 
            # composition instead of unknown
            chains_flag = "inferred" if cchains == 1 else None
            qdata = (
                None, dia_feat_id, clmidp, cname, cadduct, _ppm_error(cmz, mz), 
                # ccs_rel_err, ccs_lit_trend, chains 
                None, None, chains_flag
            )
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
                                   params: AnnotationParams,
                                   debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                   ) -> Tuple[int, int] :
    """
    filter lipid annotations based on their retention times vs. expected retention time ranges
    by lipid class for a specified chromatographic method

    Parameters
    ----------
    results_db : ``ResultsDbPath``
        path to LipidIMEA analysis results database
    params : ``AnnotationParams``
        parameters for lipid annotation
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_kept : ``int``
    n_filt : ``int``
        number of annotations kept or filtered based on RT ranges
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
    with open(params.rt_range_config, 'r') as yf:
        rt_ranges = yaml.safe_load(yf)
    # TODO (Dylan Ross): validate the structure of the data from the YAML config file
    con = connect(results_db) 
    cur = con.cursor()
    # iterate through annotations, check if the RT is within specified range 
    anns_to_del = []  # track annotation IDs to delete
    qry_sel = """--beginsql
        SELECT 
            lipid_id, 
            lmid_prefix, 
            rt 
        FROM 
            Lipids 
            JOIN DIAPrecursors USING(dia_pre_id)
    --endsql"""
    # track annotations kept and filtered
    n_kept, n_filt = 0, 0
    for ann_id, lmid_prefix, rt in cur.execute(qry_sel).fetchall():
        if lmid_prefix in rt_ranges:
            rtmin, rtmax = rt_ranges[lmid_prefix]
            if rt <= rtmin or rt >= rtmax:
                anns_to_del.append(ann_id)
                n_filt += 1
            else: 
                n_kept += 1
        else:
            # any annotations for which no RT bounds exist automatically get filtered out
            anns_to_del.append(ann_id)
            n_filt += 1
    # delete any annotations not within specified RT range
    qry_del = """--beginsql
        DELETE FROM Lipids WHERE lipid_id=?
    --endsql"""
    for ann_id in anns_to_del:
        cur.execute(qry_del, (ann_id,))
    # clean up
    con.commit()
    con.close()
    debug_handler(debug_flag, debug_cb, 
                  f"kept: {n_kept}, filtered: {n_filt}")
    # return the number of annotations that were kept and filtered out
    return n_kept, n_filt


def _fpow(x, a, b, c):
    """ simple power function for CCS trends """
    return a * x ** b + c


def _fit_observed_trend(mzs: npt.ArrayLike, 
                        ccss: npt.ArrayLike
                        ) -> Tuple[Optional[Tuple[float, float, float]], Optional[Exception]] :
    """
    fit a m/z vs. CCS trend using `_fpow`

    Returns the fit parameters if fitting was successful, `None` otherwise. 
    """
    try:
        opt, _ = curve_fit(_fpow, mzs, ccss, 
                           maxfev=int(1e6), 
                           p0=(10., 0.5, 0.), 
                           bounds=([0, 0, -np.inf], [np.inf, 1., np.inf])) 
        return opt, None
    except Exception as e:
        return None, e


def _point_in_trend(mz: float, 
                    ccs: float, 
                    trend_params: Tuple[float, float, float], 
                    percent: float
                    ) -> Optional[float] :
    """
    test if a point (`mz`, `ccs`) is within `percent` of a trend defined by `trend_params`

    Returns the percent error from the trend if so, otherwise `None`
    """
    trend_ccs = _fpow(mz, *trend_params)
    trend_err = 100 * (ccs - trend_ccs) / trend_ccs
    if abs(trend_err) <= percent:
        # point is within trend
        return trend_err
    else:
        # point is outside of trend
        return None


def filter_annotations_by_ccs_subclass_trend(results_db: ResultsDbPath, 
                                             params: AnnotationParams,
                                             debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                             ) -> Tuple[int, int, int, int] :
    """
    filter lipid annotations based on their CCS values vs. overall subclass trends

    Lipid annotations are grouped by LipidMAPS subclass, then a m/z vs. CCS trend (based on literature 
    CCS values) is fetched for that subclass and the annotations are filtered according to whether the 
    CCS is within `AnnotationParams.ccs_trend_percent` of the trend. If trend parameters are not 
    already present for a lipid subclass, a trend is instead constructed based only on the annotations
    themselves and outliers from this trend (using the same percent tolerance) are filtered out.

    Parameters
    ----------
    results_db : ``ResultsDbPath``
        path to LipidIMEA analysis results database
    params : ``AnnotationParams``
        parameters for lipid annotation
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_kept_lit : ``int``
    n_filt_lit : ``int``
        numbers of features kept or filtered out based on literature CCS trends
    n_kept_obs : ``int``
    n_filt_obs : ``int``
        numbers of features kept or filtered out based on observed CCS trends
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    debug_handler(debug_flag, debug_cb, 
                  "FILTERING LIPID ANNOTATIONS BASED ON LIPID CLASS CCS TRENDS ...")
    con = connect(results_db) 
    cur = con.cursor()
    # queries
    lm_sub_qry = """--beginsql
        SELECT DISTINCT
            lm_sub, adduct 
        FROM 
            LipidMapsShort 
            JOIN Lipids USING(lipid_id) 
            JOIN DIAPrecursors USING(dia_pre_id)
        WHERE 
            ccs IS NOT NULL
    --endsql"""
    ann_qry = """--beginsql
        SELECT 
            lipid_id, mz, ccs
        FROM 
            Lipids 
            JOIN LipidMapsShort USING(lipid_id) 
            JOIN DIAPrecursors USING(dia_pre_id)
        WHERE 
            lm_sub=?
            AND adduct=?
            AND ccs IS NOT NULL
    --endsql"""
    update_qry = """--beginsql
        UPDATE Lipids SET ccs_rel_err=?, ccs_lit_trend=? WHERE lipid_id=?
    --endsql"""
    # load the lipid subclass ccs trends 
    with open(LITERATURE_CCS_TREND_PARAMS, "r") as yf:
        lit_ccs_trends = yaml.safe_load(yf)
    # track lipid annotation IDs to drop
    drop_lids = []
    # track the number of annotations kept vs. filtered
    n_kept_lit, n_filt_lit, n_kept_obs, n_filt_obs = 0, 0, 0, 0
    # iterate through each lipid subclass from among the annotations
    for lm_sub, adduct in cur.execute(lm_sub_qry).fetchall():
        # fetch the lipid IDs, m/zs, and CCS values from all annotations of this subclass
        res = cur.execute(ann_qry, (lm_sub, adduct)).fetchall()
        # fetch the CCS trend parameters for this subclass (if available)
        if (sub_params := lit_ccs_trends.get(lm_sub)) is not None and (trend_params := sub_params.get(adduct)) is not None:
            debug_handler(debug_flag, debug_cb, 
                          f"literature CCS trend for subclass {lm_sub} and adduct {adduct} FOUND ({trend_params=})")
            # filter each annotation based on whether the the m/z and CCS are within
            # X % of the lipid subclass trend
            for lid, mz, ccs in res:
                if (trend_err := _point_in_trend(mz, ccs, 
                                                trend_params, 
                                                params.ccs_trend_percent)) is not None:
                    # update Lipids entry with lipids subclass CCS trend error
                    # ccs_lit_trend is 1 (True)
                    cur.execute(update_qry, (trend_err, 1, lid))
                    n_kept_lit += 1
                else:
                    # drop the Lipids entry
                    drop_lids.append(lid)
                    n_filt_lit += 1
        else:
            debug_handler(debug_flag, debug_cb, 
                          f"literature CCS trend for subclass {lm_sub} and adduct {adduct} NOT FOUND")
            # no trend parameters found for this subclass
            # try to fit a new trend
            min_points = 5
            # only proceed if there were actual annotations returned in the last query
            if len(res) < min_points:
                # move on to next subclass
                debug_handler(debug_flag, debug_cb, 
                              "\t\ttoo few values to fit observed trend")
                continue
            mzs, ccss = np.array([_[1:] for _ in res]).T
            trend_params, trend_err = _fit_observed_trend(mzs, ccss)
            if trend_params is not None:
                # success
                debug_handler(debug_flag, debug_cb, 
                              f"\t\tfit observed trend ({trend_params=})")
                for lid, mz, ccs in res:
                    if (trend_err := _point_in_trend(mz, ccs, 
                                                    trend_params, 
                                                    params.ccs_trend_percent)) is not None:
                        # update Lipids entry with lipids class CCS trend error
                        # ccs_lit_trend is 0 (False)
                        cur.execute(update_qry, (trend_err, 0, lid))
                        n_kept_obs += 1
                    else:
                        # drop the Lipids entry
                        drop_lids.append(lid)
                        n_filt_obs += 1
            else:
                # failure
                debug_handler(debug_flag, debug_cb, 
                              f"\t\tfailed to fit trend using observed values ({trend_err})")
                # drop all associated Lipid IDs
                to_drop = [_[0] for _ in res]
                drop_lids += to_drop
                n_filt_obs += len(to_drop)
        # report running total of filtering stats after each subclass
        debug_handler(debug_flag, debug_cb, 
                        f"\t\tkept:     {n_kept_lit + n_kept_obs} (lit: {n_kept_lit}, obs: {n_kept_obs})")
        debug_handler(debug_flag, debug_cb, 
                        f"\t\tfiltered: {n_filt_lit + n_filt_obs} (lit: {n_filt_lit}, obs: {n_filt_obs})")
    # drop annotations from DB
    qry_del = """--beginsql
        DELETE FROM Lipids WHERE lipid_id=?
    --endsql"""
    for lid in drop_lids:
        cur.execute(qry_del, (lid,))
    # clean up
    con.commit()
    con.close()
    return n_kept_lit, n_filt_lit, n_kept_obs, n_filt_obs


def _copy_lipid_entry_with_new_name_and_chains_flag(results_cur: ResultsDbCursor,
                                                    lipid_id: int, 
                                                    lipid_name: str,
                                                    chains: str) -> int :
    """
    make a copy of an entry from the Lipids table with a different name and chains flag
    return the lipid_id of the newly added entry
    """
    qd = list(results_cur.execute("SELECT * FROM Lipids WHERE lipid_id=?", (lipid_id,)).fetchone())
    qd[0] = None
    qd[3] = lipid_name
    qd[-1] = chains
    results_cur.execute("INSERT INTO Lipids VALUES (?,?,?,?,?,?,?,?,?)", qd)
    # lastrowid can be None, but that should not happen because we run an insert
    # query first. lastrowid should only be None if something goes wrong with the
    # insert, so go ahead and get mad if that is the case
    rowid = results_cur.lastrowid
    assert type(rowid) is int
    return rowid


def _copy_lipid_frag_entries_with_new_lipid_id(results_cur: ResultsDbCursor,
                                              dia_frag_ids: Iterable[int],
                                              lipid_id: int
                                              ) -> None :
    """
    make a copy of an entry from the LipidFragments table with a different lipid_id
    """
    # TODO: This results in a lot of duplicate entries, need to filter those down somehow
    for dia_frag_id in dia_frag_ids:
        # loop in case there are more than one?
        for qd in results_cur.execute("SELECT * FROM LipidFragments WHERE dia_frag_id=?", (dia_frag_id,)).fetchall():
            qd = list(qd)
            qd[0] = lipid_id
            results_cur.execute("INSERT INTO LipidFragments VALUES (?,?,?,?,?,?,?)", qd)


def _update_lipid_with_chain_info(results_cur: ResultsDbCursor
                                  ) -> None :
    """
    Update entries in Lipids based on annotated fragments supporting the presence
    of specified acyl chains

    Parameters
    ----------
    results_cur : ``ResultsDbCursor``
    """
    qry_sel = """--beginsql
        SELECT 
            lipid_id, 
            lipid, 
            GROUP_CONCAT(dia_frag_id),
            GROUP_CONCAT(supports_fa) 
        FROM 
            Lipids 
            JOIN LipidFragments USING(lipid_id) 
        WHERE 
            supports_fa IS NOT NULL 
        GROUP BY 
            lipid_id
    --endsql"""
    qry_updt_chains_flag = """--beginsql
        UPDATE Lipids SET chains=? WHERE lipid_id=?
    --endsql"""
    # iterate through lipid annotations that also have annotated fragments supporting specific acyl chains
    for lipid_id, lipid_name, frag_ids, supported_fas in results_cur.execute(qry_sel).fetchall():
        if (lipid := parse_lipid_name(lipid_name)) is not None:
            # unpack the FAs
            # keys: FA -> tuple(n_carbons, n_unsaturations)
            # values: fragment IDs -> set(int)
            fas = {}
            for fa, fid in zip([tuple(map(int, _.split(":"))) for _ in supported_fas.split(",")], map(int, frag_ids.split(","))):
                if fa not in fas:
                    fas[fa] = {fid}
                else:
                    fas[fa].add(fid)
            # keep track of new lipid names for this entry, as well as the chains flag and any fragment IDs 
            # that need to be remapped
            # keys: new lipid name -> str
            # values: {"chains_flag": str, "frag_ids": set(int)} 
            new_lipid_names = {}
            match lipid.n_chains:
                case 1:
                    # monoacyl
                    for (c, u) in fas.keys():
                        if c == lipid.fa_carbon and u == lipid.fa_unsat:
                            # no need for a new name
                            # update the lipid entry with "confirmed" chains flag in place
                            results_cur.execute(qry_updt_chains_flag, ("confirmed", lipid_id))
                            # no need to check more fragments
                            # just move on to the next lipid annotation
                            continue
                case 2:
                    # diacyl 
                    for (c1, u1), fids in fas.items():
                        # calculate the remaining sum composition
                        c2_exp, u2_exp = lipid.fa_carbon - c1, lipid.fa_unsat - u1
                        if c2_exp > 0 and u2_exp >= 0:
                            # we have found 1 valid chain, chains flag is "inferred"
                            flag = "inferred"
                            # see if we can match another chain
                            for (c2, u2), fids2 in fas.items():
                                if c2 == c2_exp and u2 == u2_exp:
                                    flag = "confirmed"
                                    fids |= fids2
                            # generate the new lipid name 
                            new_lipid_name = str(LipidWithChains(lipid.lmaps_id_prefix, [c1, c2_exp], [u1, u2_exp]))
                            if new_lipid_name not in new_lipid_names:
                                new_lipid_names[new_lipid_name] = {"chains_flag": flag, "frag_ids": fids}
                            else:
                                new_lipid_names[new_lipid_name]["chains_flag"] = flag
                                new_lipid_names[new_lipid_name]["frag_ids"] |= fids
                case 3:
                    # triacyl
                    for (c1, u1), fids in fas.items():
                        # calculate the remaining sum composition
                        c2_exp, u2_exp = lipid.fa_carbon - c1, lipid.fa_unsat - u1
                        if c2_exp > 0 and u2_exp >= 0:
                            # we have found 1 valid chain, chains flag is "partial"
                            flag = "partial"
                            # see if we can match another chain
                            for (c2, u2), fids2 in fas.items():
                                # calculate the remaining sum composition
                                c3_exp, u3_exp = c2_exp - c2, u2_exp - u2
                                if c3_exp > 0 and u3_exp >= 0:
                                    # see if we can match the last chain
                                    for (c3, u3), fids3 in fas.items():
                                        if c3 == c3_exp and u3 == u3_exp:
                                            flag = "confirmed"
                                            # generate the new lipid name
                                            new_lipid_name = str(LipidWithChains(lipid.lmaps_id_prefix, [c1, c2, c3], [u1, u2, u3]))
                                            if new_lipid_name not in new_lipid_names:
                                                new_lipid_names[new_lipid_name] = {"chains_flag": flag, "frag_ids": fids | fids2 | fids3}
                                            else:
                                                new_lipid_names[new_lipid_name]["chains_flag"] = flag
                                                new_lipid_names[new_lipid_name]["frag_ids"] |= fids | fids2 | fids3
                            # if flag is still partial go ahead an update the lipid annotation in place
                            if flag == "partial":
                                results_cur.execute(qry_updt_chains_flag, (flag, lipid_id))
                case 4:
                    # 4-acyl
                    assert False, "updating acyl chains for 4-acyl lipids not implemented yet"
            # if there were new names generated, update the database with them
            if len(new_lipid_names) > 0:
                # deal with all of the new lipid names
                for new_lipid_name, v in new_lipid_names.items():
                    chains_flag = v["chains_flag"]
                    frag_ids = v["frag_ids"]
                    # first make a copy of the Lipids entry
                    new_lipid_id = _copy_lipid_entry_with_new_name_and_chains_flag(results_cur, lipid_id, new_lipid_name, chains_flag)
                    # then make copies of the fragment annotations
                    _copy_lipid_frag_entries_with_new_lipid_id(results_cur, frag_ids, new_lipid_id)
                # delete the old lipid annotation
                results_cur.execute("DELETE FROM Lipids WHERE lipid_id=?", (lipid_id,))


def update_lipid_ids_with_frag_rules(results_db: ResultsDbPath,
                                     params: AnnotationParams,
                                     debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                     ) -> int :
    """
    update lipid annotations based on MS/MS spectra and fragmentation rules

    Parameters
    ----------
    results_db : ``ResultsDbPath``
        path to LipidIMEA analysis results database
    params : ``AnnotationParams``
        parameters for lipid annotation
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
            carbon,
            unsat,
            n_chains, 
            mz, 
            GROUP_CONCAT(dia_frag_id) AS frag_ids,
            GROUP_CONCAT(fmz)
        FROM 
            Lipids 
            JOIN LipidSumComp USING(lipid_id)
            JOIN DIAPrecursors USING(dia_pre_id) 
            LEFT JOIN DIAFragments USING(dia_pre_id)
        GROUP BY 
            lipid_id
        HAVING
            frag_ids IS NOT NULL
    --endsql"""
    # track number of lipids that are updated
    n_diagnostic = 0
    n_update_chains = 0
    qry_add_frag = """--beginsql
        INSERT INTO LipidFragments VALUES (?,?,?,?,?,?,?)
    --endsql"""
    for lipid_id, lmid_prefix, sum_c, sum_u, n_chains, pmz, fids, fmzs in cur.execute(qry_sel1).fetchall():
        update = False
        if fmzs is not None:
            # load fragmentation rules
            c_u_combos = list(get_c_u_combos(n_chains, 
                                             sum_c, 
                                             sum_u, 
                                             params.FragRuleAnnParams.fa_min_c, 
                                             params.FragRuleAnnParams.fa_max_c, 
                                             params.FragRuleAnnParams.fa_odd_c,
                                             max_u=SumCompLipidDB.max_u))
            ffmzs = list(map(float, fmzs.split(",")))
            ifids = list(map(int, fids.split(",")))
            _, rules = load_rules(lmid_prefix, params.ionization)
            diag_flag = 0
            # go through each rule and see if it matches any fragments
            for rule in rules:
                diag_flag = int(rule.diagnostic)
                if rule.static:
                    rmz = rule.mz(pmz)  # type: ignore
                    for ffmz, ifid in zip(ffmzs, ifids):
                        ppm = _ppm_error(rmz, ffmz)
                        if abs(ppm) <= params.FragRuleAnnParams.mz_ppm:
                            cur.execute(qry_add_frag, (lipid_id, ifid, rule.label(), rmz, ppm, diag_flag, None))  # type: ignore
                else:
                    for c, u in sorted(c_u_combos):
                        rmz = rule.mz(pmz, c, u) # type: ignore
                        for ffmz, ifid in zip(ffmzs, ifids):
                            ppm = _ppm_error(rmz, ffmz)
                            if abs(ppm) <= params.FragRuleAnnParams.mz_ppm:
                                cur.execute(qry_add_frag, (lipid_id, ifid, rule.label(c, u), rmz, ppm, diag_flag, f"{c}:{u}"))  # type: ignore
                                update = True
            # update counters
            if update:
                n_update_chains += 1
            n_diagnostic += diag_flag
    # go through annotated fragments and update lipid annotations if there is evidence for 
    # presence of specific acyl chains
    _update_lipid_with_chain_info(cur)
    # clean up
    con.commit()
    con.close()
    debug_handler(debug_flag, debug_cb, f"UPDATED: {n_update_chains} / {n_anns} annotations using fragmentation rules")
    return n_update_chains


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
    results_db : ``ResultsDbPath``
        path to LipidIMEA analysis results database
    params : ``AnnotationParams``
        parameters for lipid annotation
    scdb_config_yml
    """
    remove_lipid_annotations(results_db)
    add_lmaps_ont(results_db)
    sum_comp_results = annotate_lipids_sum_composition(results_db,
                                                       params, 
                                                       debug_flag=debug_flag, debug_cb=debug_cb)
    rt_filter_results = filter_annotations_by_rt_range(results_db, 
                                                       params, 
                                                       debug_flag=debug_flag, debug_cb=debug_cb)
    ccs_filter_results = filter_annotations_by_ccs_subclass_trend(results_db,
                                                                  params,
                                                                  debug_flag=debug_flag, debug_cb=debug_cb)
    frag_rule_results = update_lipid_ids_with_frag_rules(results_db, 
                                                         params,
                                                         debug_flag=debug_flag, debug_cb=debug_cb)