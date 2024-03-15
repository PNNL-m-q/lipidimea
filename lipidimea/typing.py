"""
lipidimea/typing.py

Dylan Ross (dylan.ross@pnnl.gov)

    type annotations for use across this package
"""


from typing import Union, Tuple, Optional
import sqlite3

import numpy as np
import numpy.typing as npt


# TODO (Dylan Ross): add some descriptions for all of these

type ResultsDbPath = str
type ResultsDbConnection = sqlite3.Connection
type ResultsDbCursor = sqlite3.Cursor

type YamlFilePath = str

type Xic = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
type Atd = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
type Ms1 = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
type Ms2 = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
type Spec = Union[Ms1, Ms2]
type SpecStr = str

type DdaReader = Union[_MSMSReaderDDA, _MSMSReaderDDA_Cached]  # type: ignore
type DdaChromFeat = Tuple[float, float, float, float, float]
type DdaFeature = Tuple[None, str, float, float, float, float, float, int, Optional[int], Optional[str]]

type DiaDeconFragment = Tuple[float, Xic, float, Atd, float]

type ScdbLipidId = Tuple[str, str, str, float]
