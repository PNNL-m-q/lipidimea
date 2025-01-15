"""
lipidimea/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    lipidimea - Lipidomics Integrated Multi-Experiment Analysis tool
"""


# release.major_version.minor_version
__version__ = '0.12.26'


# TODO (Dylan Ross): When migrating to GitHub, convert TODOs across the package into issues.


# TODO (Dylan Ross): Move all query string literals into their own module in the package and
#                    import them as constants? There is a chance a couple queries get re-used 
#                    in more than one place, so it makes sense to centralize them. It also
#                    could make it easier to accomodate DB schema changes because then there 
#                    is only one place to look for where to modify the queries. Then you can
#                    search by reference to constants with any modified queries to find places 
#                    in the code that use them and make whatever appropriate changes there.


# TODO (Dylan Ross): Might be nice to put interactions with the results database behind some
#                    sort of database interface class. This would hide away any SQL queries
#                    which would probably be a nicer and less complex way to deal with getting
#                    info out of and putting info into the results database. This would also make
#                    changing implementation details for the database easier and breaks less stuff 
#                    throughout the codebase as a result.


# TODO: Use named bindings in queries (especially INSERTs) so that the query data can
#       be specified using dictionaries. This would make it easier to understand what
#       information is going into what columns of the database tables without having
#       to refer to the database schema to determine the order, as is the case now with
#       the default tuple syntax for doing bindings.


# TODO: Clean up all the Parameters sections of docstrings for functions with type 
#       annotated parameters. Favor specifying type annotations for the parameters and
#       keeping the docstring Parameters section cleaner. The signature should define the
#       types and the docstring should provide explanation. See example below:
#
#       def export_results_table(results_db: ResultsDbPath,
#                                out_csv: str,
#                                tolerances: Tuple[float, float, float],
#                                select_data_files: Optional[Union[List[int], List[str]]],
#                                include_unknowns: bool = False,
#                                data_file_aliases: Optional[Dict[Union[int, str], str]] = None,
#                                ) -> None :
#           """
#            Aggregate the results (DIA) from the database and output in a tabular format (.csv). 
#    
#            Aligns features across samples (data files) based on m/z, RT, and arrival time using specified
#           tolerances. If more than one feature from a single data file falls within the specified tolerances, 
#            the features are combined (summed). Annotations for the features from the different DIA data files 
#           are aggregated by taking the intersection. The feature intensities will be output in separate columns
#           for each data file. The column names will be the data file names by default, but this can be
#           overridden using the optional data_file_aliases parameter, which maps either data file name (str) or 
#           data file ID (int) to an alias (str).
# 
#           Parameters
#           ----------
#           results_db
#               results database with annotated DIA features
#           out_csv
#               output results file (.csv)
#           tolerances
#               tuple of tolerances (m/z, RT, arrival time) for combining DIA precursors
#           select_data_files, optional
#               If provided, restrict the results to only include the specified list of data files, by data file
#               name if list of str or by data file ID if list of int
#           include_unknowns : default=False
#               flag indicating whether to include DIA features that do not have any associated annotations
#           data_file_aliases : optional
#               If provided, map data file names to specified aliases. The mapping may be defined as data
#           file name (str) to alias (str) or data file ID (int) to alias (str)f
#           """
