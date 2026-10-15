from pathlib import Path
import argparse
from tqdm import tqdm
import sys
import os
import numpy as np
import pandas as pd
from d2a_decoder_old import D2a
from kaitaistruct import KaitaiStream, ValidationNotEqualError

pt100_calib = [(2132.45, 0.029005),
               (2342.96, 0.029048),
               (2069.69, 0.028884),
               (2171.65, 0.029113)]

crystal_id = ['A', 'B', 'C', 'D']

pt100_calib = np.asarray(pt100_calib).T


def temp(x, a, b):
    res = 100 + (x - b) * a
    return -245 + 2.3519 * res + 0.00103 * (res * res)


def process_events(f, crystal_code):
    p, n = os.path.split(f)
    b, e = os.path.splitext(n)
    filepath = f
    # newpath = f'{p}/ROOT_FILES'
    # if not os.filepath.exists(newpath):
    #    os.makedirs(newpath)

    i = 0
    with open(f, 'rb') as test_file:
        while test_file.read(4) != b"\xC2\x10\x00\x00":
            i += 4
            test_file.seek(i)
            if i > 128:
                raise Exception('File is corrupted or format is invalid')
    size = os.path.getsize(f)
    num_events = int(size / 64)

    io = KaitaiStream(open(f, 'rb'))  # Open data file in streaming mode
    io.seek(i)

    data = np.empty((num_events, 23), dtype=np.uint32)
    j = 0
    while io is not None:
        try:
            data[j] = D2a.Event(io).ret
            j += 1
        except ValidationNotEqualError:
            print('seeking')
            print(io.pos())
        except EOFError:
            break

    i = crystal_code

    det_a_events = data[data[:, 0] == 5 + i]
    det_a_external = det_a_events[det_a_events[:, 2] < 25]
    det_a_internal = det_a_events[det_a_events[:, 2] > 25]
    det_a_baselines = np.mean(det_a_internal[:, 6:], axis=0)
    det_a_master_external = np.zeros((np.shape(det_a_external)[0], (np.shape(det_a_external)[1] + 2)))
    det_a_master_external[:, :-2] = det_a_external
    # det_a_master_external[:,6:-2] -= det_a_baselines
    det_a_master_external[:, -2] = np.argmax(det_a_master_external[:, 7:-2], axis=1) + 1
    det_a_master_external[:, -1] = np.sum(det_a_master_external[:, 7:-2], axis=1)
    det_a_T = det_a_master_external.T

    dataset = pd.DataFrame({'Detector': det_a_T[0],
                            'ID': det_a_T[1],
                            'Trigger': det_a_T[2],
                            'Time_sub': det_a_T[3],
                            'Time_sec': det_a_T[4],
                            'Time_gps': det_a_T[5],
                            'Temp': temp(det_a_T[6], pt100_calib[1, i], pt100_calib[0, i]),
                            'Ch1': det_a_T[7],
                            'Ch2': det_a_T[8],
                            'Ch3': det_a_T[9],
                            'Ch4': det_a_T[10],
                            'Ch5': det_a_T[11],
                            'Ch6': det_a_T[12],
                            'Ch7': det_a_T[13],
                            'Ch8': det_a_T[14],
                            'Ch9': det_a_T[15],
                            'Ch10': det_a_T[16],
                            'Ch11': det_a_T[17],
                            'Ch12': det_a_T[18],
                            'Ch13': det_a_T[19],
                            'Ch14': det_a_T[20],
                            'Ch15': det_a_T[21],
                            'Ch16': det_a_T[22],
                            'Argmax': det_a_T[23],
                            'Summed': det_a_T[24]}, dtype=np.float64)

    # dataset.to_pickle(f'{newpath}/{n}.CRYSTAL{crystal_id[i]}.pkl')
    # dataset.to_pickle(f'{n}.CRYSTAL{crystal_id[i]}.pkl')
    # dataset.to_pickle(f'{n}.pkl')
    output = filepath.with_suffix('.csv')
    dataset.to_csv(output)

def build_parser():
    parser = argparse.ArgumentParser(
        prog='ODR_DatToCSV',
        description='Converts .dat files obtained from SIPHRA to .csv',
        usage='%(prog)s PATH',
    )
    parser.add_argument("filepath",
                        help="Path to .dat file or directory containing multiple .dat files")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="only available for folder processing. Print information about every individual file")
    parser.add_argument("--process_all",
                        action="store_true",
                        help="convert all .dat files in the directory, even if they already have a matching .csv file", )
    return parser

def process_file(file, log_fn):
    log_fn("")
    log_fn(f"Target file \"{file.name}\" found.")
    log_fn("Processing...")
    process_events(file, 0)
    log_fn(f"Wrote file \"{file.stem}.csv\"!")
    log_fn("")


def find_lonely_dat_files(directory):
    '''
    Returns a list with the paths of .dat files that have no matching .csv
    file in the specified directory.
    '''
    files = []
    for file in directory.glob('*.dat'):
        if not file.with_suffix('.csv').is_file():
            files.append(file)
    return sorted(files)


if __name__ == "__main__":
    args = build_parser().parse_args()

    def vprint(msg):
        if args.verbose:
            print(msg)

    path = Path(args.filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path {path} not found!")

    if path.is_file():
        process_file(path, print)
        print("Done! 1 file converted to CSV.")

    if path.is_dir():
        if not args.process_all:
            files = find_lonely_dat_files(path)
            if len(files) == 0:
                sys.exit("All .dat files contain a matching .csv file. If you want to convert all files again execute with flag --process_all")
        else:
            files = sorted(path.glob('*.dat'))
        qty = len(files)
        print()
        print(f"Found {qty} suitable files in directory \"{path.name}\".")
        print("Starting conversion...")
        for file in tqdm(files):
            process_file(file, vprint)
        print(f"Done! {qty} files converted to CSV.")
    print()









