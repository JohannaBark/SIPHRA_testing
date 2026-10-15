# *****************************************************************************
#   Description: Definition of the :class:`SiphraAcquisition` to handle SIPHRA
#   data efficiently.
#   Written by: Oscar Rosero (KTH)
#....
#   Date: 02/2026

import pandas as pd
from typing import TypeVar
from pathlib import Path
from .metadata import Metadata, MetadataLoader

PathLike = TypeVar("PathLike", str, Path, None)

class SiphraAcquisition:
    '''
    Class to handle SIPHRA data from acquisitions efficiently using on-demand (lazy) loading.

    This class provides an interface to access data from large .csv or .pkl files without loading the entire dataset
    into memory. It also allows to store information about the active channels, exposure time and SiPM channels used,
    and allows for flexible data retrieval via dictionary-like indexing or direct methods.
    '''

    ch_strs = [f"Ch{_}" for _ in range(17)] # Names of the channels in the dataframe.

    def __init__(self, filepath: PathLike,
                 active_chs:int | list[int] = [],
                 exposure_sec:float = 1,
                 sipm_chs:str | None = None,
                 n_events:int = 100_000,
                 name: str | None = None,):

        self.filepath = self._resolve_path(filepath)
        self.metadataFile = self._resolve_metadata_file(self.filepath)
        if self.metadataFile.is_file():
            # print(f"Metadata file found {self.metadataFile}")
            metadata = MetadataLoader.load(self.metadataFile)
            exposure_sec = metadata.exposure_sec
            active_chs = metadata.active_chs
            sipm_chs = metadata.sipm_chs
            n_events = metadata.n_events
        else:
            self.metadataFile = None
        self.active_chs = self._resolve_active_chs(active_chs)
        self.exposure = exposure_sec
        self.sipm_chs = sipm_chs
        self.n_events = n_events
        self.name = name

    def _resolve_path(self, f):
        try:
            f = Path(f).resolve()
            if not f.exists():
                raise FileNotFoundError(f"File {f} does not exist")
            if not f.suffix in ['.csv', '.pkl']:
                raise NotImplementedError("Path does not point to a .csv or a .pkl file")
            return f
        except Exception as e:
            raise ValueError(f"Invalid filepath argument: {e}")

    def _resolve_metadata_file(self, filepath):
        '''
        Assume the metadata file is named the same as the raw file and that
        the name starts with an integer. This function strips away any
        prefix that may habe been added to the file name during conversion.
        '''
        for idx, c in enumerate(filepath.stem):
            try:
                int(c)
                return (filepath.parent/filepath.stem[idx:]).with_suffix(".json")
            except:
                pass
        return None

    def _resolve_active_chs(self, chs) -> list[int]:
        channels = [chs] if isinstance(chs, int) else chs
        if all(isinstance(_, int) and 1 <= _ <= 16 for _ in channels):
            return channels
        else:
            raise ValueError("Channels outside the allowed range (1 - 16)")

    def _read_column(self, col_name: str) -> numpy.ndarray:
        try:
            if self.filepath.suffix == '.csv':
                return pd.read_csv(self.filepath, usecols=[col_name])[col_name].to_numpy()

            elif self.filepath.suffix == '.pkl':
                df = pd.read_pickle(self.filepath)
                data = df[col_name].to_numpy()
                del df
                return data
        except Exception as e:
            raise ValueError(f"Cannot retrieve data from field {col_name} in file {self.filepath.name}: {e}")

    # def _get_ch_data(self, ch: int) -> np.ndarray:
    #     return self._read_column(self.ch_strs[ch])

    def _get_active_chs_data(self):
        '''
        Returns a dict whose keys are the channel numbers and whose values are
        numpy.ndarrays containig the corresponding acquisition data of that channel.
        '''
        # if len(self.active_chs) == 1:
        #     return self._read_column(self.ch_strs(self.active_chs[0]))
        active_chs_data = {}
        for ch in self.active_chs:
             active_chs_data[ch] = self._read_column(self.ch_strs[ch])
        return active_chs_data

    def __getitem__(self, items):
        '''
        Retrieve channel data using flexible indexing syntax.

        This method enables dictionary.like access to the acquisition data. It interprets the input 'items' to determine
        whether to return a single channel, a specific subset, a list of mixed identifiers, or special aggregates like
        the active-channels set or the summed spectrum.

        Parameters
        ----------
        items: int, str, list, or tuple-like
            The identifier(s) for the data to be retrieved. Accepted formats include:
            * **int**: Channel number (e.g., ``5`` for ``Ch5``),
            * **str**: Actual name of the register in the original file (e.g., ``'Ch2'``, ``'Trigger'``, ``'Temp'``)
            or special key (see table below).
            * **list[int]**: List of channel numbers (e.g., ``[1, 5, 10]``).
            * **list[str] or list[int/str]**: Mixed list of register names and channel numbers (e.g., ``['Argmax', 5,
            10, 'Trigger']``).

        Returns
        -------
        numpy.ndarray or dict
            * If a single channel is requested (int or str), returns a :class:`numpy.ndarray` containing the data.
            * If a list of channels is requested via a list of integers, returns a ``dict`` where keys are the number
            of the channel and values are :class:`numpy.ndarray` containing the data.
            * If a list of registers is requested via a mixed list or a list of strings, returns a ``dict`` where keys
            are the name of the register and values are :class:`numpy.ndarray` containing the data.

        Notes
        -----
        ** Special Keys **
        The following string keys trigger specific retrieval modes:

        +------------------+-----------------------------------------------------------------+
        | Key              | Description                                                     |
        +==================+=================================================================+
        | ``'active'``     | Retrieves all channels defined in ``self.active_chs``. Returns  |
        | ``'a'``          | a dictionary whose keys are the (int) channel numbers.          |
        | ``'A'``          |                                                                 |
        +------------------+-----------------------------------------------------------------+
        | ``'s'``          | Retrieves the 'Summed' register from the original file. Returns |
        | ``'+'``          | a numpy array.                                                  |
        | ``'S'``          |                                                                 |
        +------------------+-----------------------------------------------------------------+
        '''
        if any(items == _ for _ in ('active', 'a', 'A')):
            return self._get_active_chs_data()

        elif any(items == _ for _ in ('s', '+', 'S')):
            return self._read_column('Summed')

        elif isinstance(items, (int, str)):
            col_name = self.ch_strs[items] if isinstance(items, int) else items
            return self._read_column(col_name)

        elif isinstance(items, list) and all(isinstance(item, int) for item in items):
            data = {}
            for ch in items:
                data[ch] = self._read_column(self.ch_strs[ch])
            return data

        elif isinstance(items, list) and all(isinstance(item, (int, str)) for item in items):
            data = {}
            for item in items:
                col_name = self.ch_strs[item] if isinstance(item, int) else item
                data[col_name] = self._read_column(col_name)
            return data

    def as_dataset(self):
        file_type = self.filepath.suffix
        if file_type == ".csv":
            return pd.read_csv(self.filepath)
        elif file_type == ".pkl":
            return pd.read_pickle(self.filepath)

    def __repr__(self):
        return f"SIPHRAAcquisition(File: \'{self.filepath.stem}\')"



