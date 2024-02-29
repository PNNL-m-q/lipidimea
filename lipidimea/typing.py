"""
lipidimea/typing.py

Dylan Ross (dylan.ross@pnnl.gov)

    type annotations for use across this package
"""


from typing import Union, Tuple, Optional
import sqlite3

import numpy as np
import numpy.typing as npt


type ResultsDBPath = str
type ResultsDBConnection = sqlite3.Connection
type ResultsDBCursor = sqlite3.Cursor

type Xic = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
type Atd = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]

type DdaReader = Union[_MSMSReaderDDA, _MSMSReaderDDA_Cached]  # type: ignore
type DdaChromFeat = Tuple[float, float, float, float, float]
type DdaFeature = Tuple[None, str, float, float, float, float, float, int, Optional[int], Optional[str]]

type DiaDeconFragment = Tuple[float, Xic, float, Atd, float]
