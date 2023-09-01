"""
LipidIMEA/lipids/annotation.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for annotating features
"""


from sqlite3 import connect
from itertools import product

from mzapy.isotopes import ms_adduct_mz
import yaml

from LipidIMEA.lipids import Lipid


class SumCompLipidDB():
    """
    creates an in-memory database with lipids at the level of sum composition for initial
    lipid identifications, using a configuration file to specify what lipids to include
    """

    def _init_db(self):
        """ initialize DB in memory and set up SumCompLipids table """
        create_qry = """
        CREATE TABLE SumCompLipids (
            lclass TEXT,
            fa_mod TEXT,
            n_chains INT,
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
        to 16 C = 2 max U, 17-18 C = 3 max U, 19-21 C = 5 max U, 22+ C = 6 max U

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
        if c <= 16:
            return 2
        elif c <= 18:
            return 3
        elif c <= 20:
            return 5
        else:
            return 6

    def gen_sum_compositions(self, n_chains, min_c, max_c, odd_c, min_u):
        """ 
        yields all unique sum compositions from combinations of fatty acids that are iterated over
        using some rules:

        * specify minimum number of carbons in a FA chain
        * specify maximum number of carbons in a FA chain
        * specify whether to include odd # of carbons for FA chains
        * max number of unsaturations is determined by FA chain length (by default: up to 16 C = 2 max U, 17-18 C = 3 max U,
          19-21 C = 5 max U, 22+ C = 6 max U... override ``SumCompLipidDB.max_u()`` static method to change)

        Parameters
        ----------
        n_chains : ``int``
            number of FA chains
        min_c, max_c : ``int``
            min/max number of carbons in an acyl chain
        odd_c : ``bool``
            whether to include odd # C for FAs
        min_u : ``int``
            minimum number of unsaturations (in sum composition, not individual FAs)

        Yields
        ------
        sum_comp : ``tuple(int, int)``
            unique sum compoisions as (# carbons, # unsaturations)
        """
        fas = []
        for n_c in range(min_c, max_c + 1):
            if odd_c or n_c % 2 == 0:
                for n_u in range(0, self.max_u(n_c) + 1):
                    fas.append((n_c, n_u))
        # permute over acyl chains
        sum_comp = set() 
        for combo in product(fas, repeat=n_chains):
            c, u = 0, 0
            for fac, fau in combo:
                c += fac
                u += fau
            if u >= min_u:
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

            PC:
                fa_mod: [null, P-, O-]
                n_chains: [1, 2]
                adducts: ["[M+H]+", "[M+Na]+"]
            PE:
                fa_mod: [null, P-, O-]
                n_chains: [1, 2]
                adducts: ["[M+H]+", "[M+Na]+"]
            DG:
                fa_mod: [null]
                n_chains: [2]
                adducts: ["[M+Na]+", "[M+NH4]+"]

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
        insert_qry = 'INSERT INTO SumCompLipids VALUES (?,?,?,?,?,?,?,?);'
        for lclass, lcinfo in cnf.items():
            for fa_mod in lcinfo['fa_mod']:
                for n_chains in lcinfo['n_chains']:
                    # adjust min unsaturation level for sphingolipids
                    min_u = 1 if lclass in ['SM', 'Cer'] else 0
                    for sumc, sumu in self.gen_sum_compositions(n_chains, min_c, max_c, odd_c, min_u):
                        lpd = Lipid(lclass, sumc, sumu, 
                                    fa_mod=fa_mod if fa_mod is not None else '', 
                                    n_chains=n_chains)
                        for adduct in lcinfo['adducts']:
                            mz = ms_adduct_mz(lpd.formula, adduct)
                            qdata = (lclass, fa_mod, n_chains, sumc, sumu, str(lpd), adduct, mz)
                            self._cur.execute(insert_qry, qdata)

    def get_sum_comp_lipid_ids(self, include_lipid_classes, mz, mz_tol):
        """
        searches the sum composition lipid ids database using a feature m/z with search restricted
        to specified lipid class (and # chains). Returns all potential lipid annotations within search
        tolerance

        Parameters
        ----------
        include_lipid_classes : ``list(tuple(str, int))``
            tuples with (lipid_class, n_chains) to include in search
        mz : ``float``
            feature m/z
        mz_tol : ``float``
            tolerance for matching m/z

        Returns
        -------
        candidates : ``list(tuple(...))``
            list of lipid annotation candidates, each is a tuple consisting of 
            name, adduct, and m/z
        """
        candidates = []
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        qry = """SELECT name, adduct, mz FROM SumCompLipids WHERE lclass=? AND n_chains=? AND mz>=? AND mz<=?"""
        for lclass, n_chains in include_lipid_classes:
            for candidate in self._cur.execute(qry, (lclass, n_chains, mz_min, mz_max)).fetchall():
                candidates.append(candidate)
        return candidates

    def close(self):
        """
        close the database
        """
        self._con.close()
