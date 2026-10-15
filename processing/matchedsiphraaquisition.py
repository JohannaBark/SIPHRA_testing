import pandas as pd
import numpy as np
from typing import TypeVar
from pathlib import Path

from .metadata import MetadataLoader

PathLike = TypeVar("PathLike", str, Path, None)


class MatchedSiphraAcquisition:
    """
    Class for handling matched/coincident SIPHRA acquisition datasets.

    This class behaves similarly to SiphraAcquisition, but operates on
    CSV/PKL files generated from matched detector events.

    Expected column naming convention:

        A_<column_name>
        B_<column_name>

    Example:
        A_Time_sec
        B_Time_sec
        A_Ch1
        B_Ch1

    The class supports:
    - lazy loading of columns
    - dictionary-like indexing
    - retrieval of detector A/B channels
    - retrieval of matched timing information
    """

    ch_strs_A = [f"A_Ch{_}" for _ in range(17)]
    ch_strs_B = [f"B_Ch{_}" for _ in range(17)]

    def __init__(self,
                 filepath: PathLike,
                 active_chs: int | list[int] = [],
                 exposure_sec: float = 1,
                 sipm_chs: str | None = None,
                 n_events: int = 100_000,
                 name: str | None = None):

        self.filepath = self._resolve_path(filepath)

        self.metadataFile = self._resolve_metadata_file(self.filepath)

        if self.metadataFile and self.metadataFile.is_file():

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

    # ==========================================================
    # PATH HANDLING
    # ==========================================================

    def _resolve_path(self, f):

        try:

            f = Path(f).resolve()

            if not f.exists():
                raise FileNotFoundError(f"File {f} does not exist")

            if f.suffix not in ['.csv', '.pkl']:
                raise NotImplementedError(
                    "Path does not point to a .csv or .pkl file"
                )

            return f

        except Exception as e:
            raise ValueError(f"Invalid filepath argument: {e}")

    def _resolve_metadata_file(self, filepath):

        for idx, c in enumerate(filepath.stem):

            try:
                int(c)

                return (
                    filepath.parent /
                    filepath.stem[idx:]
                ).with_suffix(".json")

            except:
                pass

        return None

    def _resolve_active_chs(self, chs) -> list[int]:

        channels = [chs] if isinstance(chs, int) else chs

        if all(isinstance(_, int) and 1 <= _ <= 16 for _ in channels):
            return channels

        else:
            raise ValueError(
                "Channels outside the allowed range (1 - 16)"
            )

    # ==========================================================
    # COLUMN READING
    # ==========================================================

    def _read_column(self, col_name: str) -> np.ndarray:

        try:

            if self.filepath.suffix == '.csv':

                return pd.read_csv(
                    self.filepath,
                    usecols=[col_name]
                )[col_name].to_numpy()

            elif self.filepath.suffix == '.pkl':

                df = pd.read_pickle(self.filepath)

                data = df[col_name].to_numpy()

                del df

                return data

        except Exception as e:

            raise ValueError(
                f"Cannot retrieve data from field "
                f"{col_name} in file "
                f"{self.filepath.name}: {e}"
            )

    # ==========================================================
    # ACTIVE CHANNEL DATA
    # ==========================================================

    def _get_active_chs_data(self, detector='A'):

        active_chs_data = {}

        ch_strs = (
            self.ch_strs_A
            if detector.upper() == 'A'
            else self.ch_strs_B
        )

        for ch in self.active_chs:

            active_chs_data[ch] = self._read_column(
                ch_strs[ch]
            )

        return active_chs_data

    # ==========================================================
    # DATA ACCESS
    # ==========================================================

    def __getitem__(self, items):

        # ----------------------------------------------
        # Active channels
        # ----------------------------------------------

        if items in ('activeA', 'aA', 'AA'):
            return self._get_active_chs_data('A')

        elif items in ('activeB', 'aB', 'AB'):
            return self._get_active_chs_data('B')

        # ----------------------------------------------
        # Summed spectra
        # ----------------------------------------------

        elif items in ('sumA', '+A', 'SA'):
            return self._read_column('A_Summed')

        elif items in ('sumB', '+B', 'SB'):
            return self._read_column('B_Summed')

        # ----------------------------------------------
        # Single column
        # ----------------------------------------------

        elif isinstance(items, str):

            return self._read_column(items)

        # ----------------------------------------------
        # Single integer channel
        # Defaults to detector A
        # ----------------------------------------------

        elif isinstance(items, int):

            return self._read_column(
                self.ch_strs_A[items]
            )

        # ----------------------------------------------
        # List of channels
        # ----------------------------------------------

        elif isinstance(items, list):

            data = {}

            for item in items:

                if isinstance(item, int):

                    col_name = self.ch_strs_A[item]

                else:

                    col_name = item

                data[col_name] = self._read_column(col_name)

            return data

    # ==========================================================
    # FULL DATASET
    # ==========================================================

    def as_dataset(self):

        file_type = self.filepath.suffix

        if file_type == ".csv":
            return pd.read_csv(self.filepath)

        elif file_type == ".pkl":
            return pd.read_pickle(self.filepath)

    # ==========================================================
    # MATCHED EVENT HELPERS
    # ==========================================================

    def timing_difference(self):

        return self._read_column("subsec_difference")

    def detector_A_times(self):

        sec = self._read_column("A_Time_sec")
        sub = self._read_column("A_Time_sub")

        return sec + sub / 100000

    def detector_B_times(self):

        sec = self._read_column("B_Time_sec")
        sub = self._read_column("B_Time_sub")

        return sec + sub / 100000

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self):

        return (
            f"MatchedSiphraAcquisition("
            f"File='{self.filepath.stem}')"
        )