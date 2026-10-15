from dataclasses import dataclass
from typing import TypeVar
import json
from pathlib import Path

PathLike = TypeVar("PathLike", str, Path, None)

@dataclass
class Metadata:
    exposure_sec: float
    active_chs: list[int]
    sipm_chs: str | list[str]
    n_events: int
    source: str | None

class MetadataLoader:

    @staticmethod
    def load(path: PathLike) -> Metadata:
        with open(path, "r") as f:
            raw = json.load(f)

        version = raw.get("schema_version", "1.0")

        if version == "1.0":
            return MetadataLoader._parse_v1(raw)
        else:
            raise ValueError(f"Unsupported schema version: {version}")

    @staticmethod
    def _parse_v1(raw: dict) -> Metadata:
        acq = raw["acquisition"]
        source = raw["source"]["type"]

        return Metadata(
            exposure_sec=acq["exposure_sec"],
            active_chs=[int(ch) for ch in acq["active_chs"]],
            sipm_chs=acq["sipm_chs"],
            n_events=acq["counts"],
            source=source,
        )