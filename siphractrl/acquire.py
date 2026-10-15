# *****************************************************************************
# Description: CLI to perform an acquisition executing the dma_to_raw_file
# script. Automatically stores a json file with the relevant metadata.
# Written by: Oscar Rosero (KTH)
# ....
#   Date: 02/2026

import argparse
import subprocess
import json
from pathlib import Path
import time
from datetime import datetime, timezone

def parse_args():
    parser = argparse.ArgumentParser(
        description="Acquire data from SIPHRA ASIC using dma_to_raw_file and store metadata."
    )

    parser.add_argument("-o", "--output",
                        required=True,
                        help="Base name for output files (without extension).")
    parser.add_argument("-c", "--counts", type=int, default=100_000,
                        help="Total number of events to acquire.")
    parser.add_argument("--active-chs", nargs="*", type=int, default=[],
                        help="SIPHRA active channels. Receives all active channel numbers (1 -16) separated by a space.")
    parser.add_argument("--sipm-chs", nargs="*", default='',
                        help="Configuration of SIPM channels. One or more strings explaining this configuration.")
    parser.add_argument("--source", type=str, default='[NOT SPECIFIED]',
                        help="A single string containing \'Background\' or any radioactive source present")
    parser.add_argument("--source-description", type=str, default='[NOT SPECIFIED]',
                        help="A single string.")
    parser.add_argument("--notes", type=str, default='[NONE]',
                        help="A single string.")
    parser.add_argument("--siphra-config-file", type=str, default='D2a/Ongoing.txt',
                        help="By default, it takes the \'Ongoing.txt\' file in the \'D2a\' directory and writes its contents to the metadata file. If any other configuration is used, the path to the text file containing it must be specified here.")
    parser.add_argument("-s", "--size", type=int, default=4095,
                        help="[DO NOT CHANGE UNLESS CHANGING dma_to_raw_file SETTINGS]. Block size. Default is 4095.")
    parser.add_argument("--device", default="/dev/D2A_DMA",
                        help = "[DO NOT CHANGE UNLESS CHANGING dma_to_raw_file SETTINGS].")


    return parser.parse_args()

def run_acquisition(args):
    output_base = Path(args.output).resolve()
    dat_file = output_base.with_suffix(".dat")

    cmd = [
        "./dma_to_raw_file",
        "-i", args.device,
        "-o", str(dat_file),
        "-s", str(args.size),
        "-v",
        "-c", str(args.counts),
        "-b"
    ]

    start = time.time()
    subprocess.run(cmd, check=True)
    end = time.time()

    exposure = end - start
    return exposure, output_base

def write_metadata(output_base, exposure, args):
    with open(args.siphra_config_file) as f:
        siphra_config = f.readline().strip()
    metadata = {
        "schema-version": "1.0",

        "acquisition": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "exposure_sec": exposure,
            "counts": args.counts,
            "active_chs": args.active_chs,
            "sipm_chs": args.sipm_chs,
        },

        "source": {
            "type": args.source,
            "description": args.source_description,
        },

        "SIPHRA_config":{
            "cmd_string": siphra_config,
        },

        "additional_info": {
            "data_file": str(output_base.with_suffix(".dat")),
            "notes": args.notes,
        }
    }

    json_file = output_base.with_suffix(".json")
    with open(json_file, "w") as f:
        json.dump(metadata, f, indent=4)

def main():
    args = parse_args()
    exposure, output_base = run_acquisition(args)
    write_metadata(output_base, exposure, args)
    print(f"\n\nAcquisition complete.\n\tWritten to: {output_base}\n\tTotal exposure: {exposure:,.2f} seconds.")

if __name__ == "__main__":
    main()

