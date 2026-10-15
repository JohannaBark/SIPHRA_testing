import numpy as np
import pandas as pd
import os
import sys
sys.path.append("/home/mk/ComCube/Operations/DataConversion")
from d2a_decoder_old import D2a
import gc
import wx
#import ROOT
from kaitaistruct import KaitaiStream, ValidationNotEqualError

pt100_calib = [(2132.45, 0.029005),
                (2342.96,  0.029048),
                (2069.69,  0.028884),
                (2171.65,  0.029113)]

crystal_id = ['A', 'B', 'C', 'D']

pt100_calib = np.asarray(pt100_calib).T

def temp(x,a,b):
    res = 100 + (x-b)*a 
    return -245 + 2.3519*res+ 0.00103*(res*res)

def process_events(f, crystal_code):
    p,n = os.path.split(f)
    b,e = os.path.splitext(n)
    #newpath = f'{p}/ROOT_FILES' 
    #if not os.filepath.exists(newpath):
    #    os.makedirs(newpath)

    i = 0
    with open(f, 'rb') as test_file:
        while test_file.read(4) != b"\xC2\x10\x00\x00":
            i+=4
            test_file.seek(i)
            if i >128:
                raise Exception('File is corrupted or format is invalid')
    size = os.path.getsize(f)
    num_events = int(size/64)

    io = KaitaiStream(open(f, 'rb' )) # Open data file in streaming mode
    io.seek(i)

    data = np.empty((num_events,23), dtype = np.uint32)
    j = 0
    while io is not None:        
        try:
            data[j] =  D2a.Event(io).ret
            j+=1
        except ValidationNotEqualError:
            print('seeking')
            print(io.pos())
        except EOFError:
            break
            


    i = crystal_code

    det_a_events = data[data[:,0] == 5+i]
    det_a_external = det_a_events[det_a_events[:,2] < 25]
    det_a_internal = det_a_events[det_a_events[:,2] > 25]
    det_a_baselines = np.mean(det_a_internal[:,6:], axis = 0)
    det_a_master_external = np.zeros((np.shape(det_a_external)[0],(np.shape(det_a_external)[1]+2)))
    det_a_master_external[:,:-2] = det_a_external   
    #det_a_master_external[:,6:-2] -= det_a_baselines
    det_a_master_external[:,-2] = np.argmax(det_a_master_external[:,7:-2], axis = 1)+1
    det_a_master_external[:,-1] = np.sum(det_a_master_external[:,7:-2], axis = 1)
    det_a_T = det_a_master_external.T


    dataset = pd.DataFrame({'Detector': det_a_T[0],
                            'ID': det_a_T[1],
                            'Trigger': det_a_T[2],
                            'Time_sub': det_a_T[3],
                            'Time_sec': det_a_T[4],
                            'Time_gps': det_a_T[5],
                            'Temp': temp(det_a_T[6], pt100_calib[1,i], pt100_calib[0,i]),
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
                            'Summed': det_a_T[24]}, dtype = np.float64)


    

    #dataset.to_pickle(f'{newpath}/{n}.CRYSTAL{crystal_id[i]}.pkl')
    #dataset.to_pickle(f'{n}.CRYSTAL{crystal_id[i]}.pkl')
    #dataset.to_pickle(f'{n}.pkl')
    dataset.to_pickle(f'{b}.pkl')
    
    det_a_master_internal = np.zeros((np.shape(det_a_internal)[0],(np.shape(det_a_internal)[1]+2)))
    det_a_master_internal[:,:-2] = det_a_internal   
    det_a_master_internal[:,6:-2] -=0
    det_a_master_internal[:,-2] = np.argmax(det_a_master_internal[:,7:-2], axis = 1)+1
    det_a_master_internal[:,-1] = np.sum(det_a_master_internal[:,7:-2], axis = 1)
    det_a_internal_T = det_a_master_internal.T

    dataset = pd.DataFrame({'Detector': det_a_internal_T[0],
                    'ID': det_a_internal_T[1],
                    'Trigger': det_a_internal_T[2],
                    'Time_sub': det_a_internal_T[3],
                    'Time_sec': det_a_internal_T[4],
                    'Time_gps': det_a_internal_T[5],
                    'Temp': temp(det_a_internal_T[6], pt100_calib[0,i], pt100_calib[1,i]),
                    'Ch1': det_a_internal_T[7],
                    'Ch2': det_a_internal_T[8],
                    'Ch3': det_a_internal_T[9],
                    'Ch4': det_a_internal_T[10],
                    'Ch5': det_a_internal_T[11],
                    'Ch6': det_a_internal_T[12],
                    'Ch7': det_a_internal_T[13],
                    'Ch8': det_a_internal_T[14],
                    'Ch9': det_a_internal_T[15],
                    'Ch10': det_a_internal_T[16],
                    'Ch11': det_a_internal_T[17],
                    'Ch12': det_a_internal_T[18],
                    'Ch13': det_a_internal_T[19],
                    'Ch14': det_a_internal_T[20],
                    'Ch15': det_a_internal_T[21],
                    'Ch16': det_a_internal_T[22],
                    'Argmax':det_a_internal_T[23],
                    'Summed':det_a_internal_T[24]}, dtype = np.float64)       

    #dataset.to_pickle(f'{newpath}/{n}.CRYSTAL{crystal_id[i]}_Internal.pkl')

def main():

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

    FileWithPath=os.path.abspath(sys.argv[1])
    FilePathOnly, FileName = os.path.split(FileWithPath)
    FileBaseName, FileExtension = os.path.splitext(FileName)
    print()
    print(f"Target file \"{FileWithPath}\" found.")
    print()
    print("Processing...")
    
    app = wx.App()
    frame = wx.Frame(None, -1, 'win.py')
    frame.SetSize(0,0,200,50)

    # Creating the open file dialog
    #file_dialogue = wx.FileDialog(frame, "Open", "", "",
    #    "Event files (*.0*)|*.0*", 
    #    wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
    #file_dialogue.ShowModal()
    #f = file_dialogue.GetPath()
    #file_dialogue.Destroy()
    #for i in range(0,4):
    #   process_events(f, i)
    #process_events(f, 0)
    process_events(FileWithPath, 0)
    print()
    print(f"Done! Wrote file \"{FileBaseName}.pkl\"!")
    print()

if __name__ == '__main__':
    main()

