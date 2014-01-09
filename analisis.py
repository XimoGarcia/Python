import h5py
import numpy as np
import matplotlib.pyplot as plt



def analyze(name, paths, subPaths, prob, currencies, instruments, plots = dict()):
    if len(plots) == 0:
        plots = dict(zip(instruments, [[x] for x in range(len(instruments))]))
    
    result = getMeanAndStd(name, paths, subPaths, prob, currencies)
    x = np.arange(len(result['mean'][0, :]))
    for plotKey in plots.keys():
        fig = plt.figure()
        fig.suptitle(plotKey)
        plot_colors = []
        for i in plots[plotKey]:
            npv_mean = result["mean"][i, :]
            base_line, = plt.plot(x, npv_mean, "o-")
            plot_colors.append(base_line.get_color())

        plt.legend([instruments[i] for i in plots[plotKey]])        
        plot_colors.reverse()
        for i in plots[plotKey]:
            std = result["std"][i, :]
            mktPrice = result["mean"][i, 0]
            plot_color = plot_colors.pop()
            plt.plot(mktPrice + std, "--", color = plot_color)
            plt.plot(mktPrice - std, "--", color = plot_color)
            min_y = min(np.concatenate([mktPrice - std, npv_mean]))
            max_y = max(np.concatenate([mktPrice + std, npv_mean]))
            plt.axis([0, x[-1], min_y, max_y])

    return(result)

def getMeanAndStd(name, paths, subPaths, prob, currencies):
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
        
        npv_std[i, ...] = cociente.reshape(paths, subPaths, num_time_steps)\
            .mean(axis = 1).std(axis = 0) / sqrt(paths) * scipy.stats.norm.ppf((1+prob)/2.0)
        npv_mean[i, ...] = cociente.mean(axis = 0)

    npv_std[..., 0] = 0
    npv_file.close()
    scenarios_file.close()
    return({"mean" : npv_mean, "std" : npv_std})
