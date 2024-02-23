"""
lipidimea/typing.py

Dylan Ross (dylan.ross@pnnl.gov)

    type annotations for use across this package
"""


from typing import Union, Tuple, Optional
import sqlite3


type ResultsDBPath = str
type ResultsDBConnection = sqlite3.Connection
type ResultsDBCursor = sqlite3.Cursor
type DdaReader = Union[_MSMSReaderDDA, _MSMSReaderDDA_Cached]  # type: ignore
type DdaChromFeat = Tuple[float, float, float, float, float]
type DdaQdata = Tuple[None, str, float, float, float, float, float, int, Optional[int], Optional[str]]


