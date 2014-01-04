import h5py
import numpy as np

def CreateFile():
    f = h5py.File("mytestfile2.hdf5", "w-")
    dset = f.create_dataset("mydataset", (100,), dtype='i')
    dset[...]  = np.arange(100)
    f.close()
    
def ReadFile():
    f = h5py.File("mytestfile2.hdf5", "r")
    dset = f["mydataset"]
    print dset[...]
    f.close()

#CreateFile()
ReadFile()