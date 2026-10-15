import sys
import os
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from pytz import timezone
from tkinter import filedialog
import pandas as pd

#Set up the dictionary defining the contents of the pickle file
df_dict = { "Detector":"int32",
            "ID":"int64",
            "Trigger":"int16",
            "Time_sub":"int32",
            "Time_sec":"int32",
            "Time_gps":"int32",
            "Temp":"int16",
            "Ch1":"int16",
            "Ch2":"int16",
            "Ch3":"int16",
            "Ch4":"int16",
            "Ch5":"int16",
            "Ch6":"int16",
            "Ch7":"int16",
            "Ch8":"int16",
            "Ch9":"int16",
            "Ch10":"int16",
            "Ch11":"int16",
            "Ch12":"int16",
            "Ch13":"int16",
            "Ch14":"int16",
            "Ch15":"int16",
            "Ch16":"int16",
            "Argmax":"int16",
            "Summed":"int16",}

if len(sys.argv) < 2:
    print()
    print("Error! Please pass Siphra data file as argument!")
    print()
    sys.exit(1)

if not os.path.isfile(sys.argv[1]):
    print()
    print(f"ERROR! Could not find file \"{sys.argv[1]}\". Please check path!")
    print()
    sys.exit(1)

print()
print(f"Target file \"{os.path.abspath(sys.argv[1])}\" found.")
print()
print("Processing...")

#FILENAME = '6_SiPM_Ch14_Cs137_WhyIsPeakNowGone_Trigger_Ch14_Ch16.pkl'
FILENAME = sys.argv[1]
dataset = pd.read_pickle(FILENAME).astype(dtype= df_dict)
dataset.to_csv(FILENAME.replace('.pkl','.csv'), index = False)

FileBaseName, FileExtension = os.path.splitext(sys.argv[1])
print()
print(f"Done! Wrote file \"{FileBaseName}.csv\"!")
print()
