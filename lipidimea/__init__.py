"""
lipidimea/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    lipidimea - Lipidomics Integrated Multi-Experiment Analysis tool
"""

# release.major_version.minor_version
__version__ = '0.12.16'


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
