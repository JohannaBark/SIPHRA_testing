import sys
import os
from d2a_lib import D2a
import time
import numpy as np

if len(sys.argv) < 2:
    
    print()
    print("ERROR! Please pass the binary configuration file as argument!")
    print()
    sys.exit(1)
    
if not os.path.isfile(sys.argv[1]):
    
    print()
    print(f"ERROR! Could not find file \"{sys.argv[1]}\". Please check path!")
    print()
    sys.exit(1)

ucd_det = D2a()
ucd_det.sysclk(6)
ucd_det.reset('All')
ucd_det.writeSIPHRAfromFile(sys.argv[1], 'A')
time.sleep(1)
ucd_det.hold1Hz()
print()
print("Configuration",sys.argv[1],"written!")
print()

