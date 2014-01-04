import h5py
import numpy as np
import matplotlib.pyplot as plt

def analyze(name, paths, subPaths, prob, currencies, instruments):
    result = getMeandAndStd(name, paths, subPaths, prob, currencies):    
    
    fig = plt.figure()
    fig.suptitle(name.replace("_", " "))
    num_time_steps = result.shape[2]
    num_npv = result.shape[1]
    x = np.arange(num_time_steps)
    for (i in range(num_npv))
        plt.plot(x, result["mean", i, :])
    
    plt.legend(instruments) 
    std = result["sdt", 0, :]
    mktPrice = result["mean", 0, 0]
    plt.plot(mktPrice + std, "r--")
    plt.plot(mktPrice - std, "r--")
    plt.axis([0, x[-1], min(mktPrice - std), max(mktPrice + std)])
    
    return(result)

def getMeandAndStd(name, paths, subPaths, prob, currencies):
    npv_file = h5py.File("NPV_data_" + name + ".hdf5", "r")
    scenarios_file = h5py.File("scenarios_" + name + ".hdf5", "r")
    npv = npv_file["CVANPVDATA"]
    bcc = scenarios_file["__AGG__EONIA_IR"]
    
    num_time_steps = npv.shape[1]
    num_npv = len(currencies)
    npv_mean = zeros((num_npv, num_time_steps))
    npv_std = zeros((num_npv, num_time_steps))
    for i in range(num_npv):
        cociente = npv.value[..., i]/bcc[..., 0]
        curr = currencies[i]
        if curr != "EUR":
            fx = scenarios_file[curr + "\EUR_PRICE"]
            cociente = cociente * fx[..., 0]
        
        npv_std[i, ...] = cociente.reshape(paths, subPaths, num_time_steps).mean(axis = 1).std(axis = 0) / sqrt(paths)
        npv_mean[i, ...] = cociente.mean(axis = 0)

    npv_std[..., 0] = 0
    npv_file.close()
    scenarios_file.close()
    return(np.array([mean = npv_mean, std = npv_std]))
