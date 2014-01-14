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
        cociente.reshape(paths, subPaths, num_time_steps)
        curr = currencies[i]
        if curr != "EUR":
            fx_key = curr + "\\EUR_PRICE"
            invfx_key = "EUR\\" + curr + "_PRICE"
            if scenarios_file.has_key(fx_key):
                fx = scenarios_file[fx_key]
                cociente = cociente * fx[..., 0]    
            elif scenarios_file.has_key(invfx_key):
                fx = scenarios_file[invfx_key]                
                cociente = cociente / fx[..., 0]
            else:
                raise Exception("FX data for currency " + curr + " not found")

        npv_std[i, ...] = cociente.reshape(paths, subPaths, num_time_steps)\
            .mean(axis = 1).std(axis = 0) / sqrt(paths) * scipy.stats.norm.ppf((1+prob)/2.0)
        npv_mean[i, ...] = cociente.mean(axis = 0)

    npv_std[..., 0] = 0
    npv_file.close()
    scenarios_file.close()
    return({"mean" : npv_mean, "std" : npv_std})
    
def analyzeFX():
    instruments = ("EUR_FixedFlow", "Forward_GBP_EUR", "Forward_GBP_EUR_K_2", 
                  "Forward_GBP_OIS_K_2", "Forward_USD_EUR", "Forward_USD_EUR_K_2", 
                  "Forward_USD_GBP_K_2", "USD_FixedFlow", "GBP_FixedFlow", "callEUR_GBP", 
                  "callEUR_USD", "callGBP_USD", "callGBP_EUR", "callUSD_EUR", "callUSD_GBP", 
                  "putEUR_GBP", "putEUR_USD", "putGBP_EUR", "putGBP_USD", "putUSD_EUR", "putUSD_GBP")
    currencies = ("EUR", "EUR", "EUR", "EUR", "EUR", "EUR", "EUR", "USD", "GBP", "GBP", 
                  "USD", "USD", "EUR", "EUR", "GBP", "GBP", "USD", "EUR", "USD", "EUR", "GBP")
    
    result = getMeanAndStd("fx_eurusd", 5000, 1, 0.95, currencies)
    
    d_mean = dict(zip(instruments, [result['mean'][i] for i in range(len(instruments)) ] ))
    analyzeInstruments(d_mean, "EUR", "GBP")
    analyzeInstruments(d_mean, "EUR", "USD")
    analyzeInstruments(d_mean, "GBP", "USD")
    
    return(d_mean)

def analyzeInstruments(d_mean, dom, fgn):
    
    # Call(dom/fgn) strike K = K-Put(dom/fgn) strike 1/k
    fgn_dom = fgn + "_" +  dom
    dom_fgn = dom + "_" + fgn
    fgndom = fgn + "/" +  dom
    domfgn = dom + "/" + fgn
    
    insCall = "call" + fgn_dom
    insPut = "put" + dom_fgn
    max_diff = max(abs(d_mean[insCall] - d_mean[insPut]))
    print "Call("+ fgndom +") strike K = K-Put(" + domfgn + ") strike 1/K: " + str(max_diff)
    
    insCall = "call" + dom_fgn
    insPut = "put" + fgn_dom
    max_diff = max(abs(d_mean[insCall] - d_mean[insPut]))
    print "Call("+ domfgn +") strike K = K-Put(" + fgndom + ") strike 1/K: " + str(max_diff)

    # Forward K = 0
    if dom == "EUR":
        insFixedFlow = fgn + "_FixedFlow"
        insForward = "Forward_" + fgn_dom
        max_diff = max(abs(d_mean[insFixedFlow] - d_mean[insForward]))
        print "Fixed Flow " + fgn + " = Forward " + fgndom + ": " + str(max_diff)
    
    # Forward K = 2
    insForward = "Forward_" + fgn_dom + "_K_2"
    insCall = "call" + fgn_dom
    insPut = "put" + fgn_dom
    fwdPrice = d_mean[insForward]
    callPutPrice = d_mean[insCall] - d_mean[insPut]
    max_CallPut_Forward_diff = max(abs(fwdPrice - callPutPrice))
    print "Forward strike 2: Call("+ fgndom +") - Put(" + fgndom + ") = Forward " + fgndom + ": " + str(max_CallPut_Forward_diff)
    insDomFixedFlow = dom + "_FixedFlow"
    insFgnFixedFlow = fgn + "_FixedFlow"
    swapPrice = d_mean[insFgnFixedFlow] - 2*d_mean[insDomFixedFlow]
    max_CallPut_FixedFlow_diff = max(abs(swapPrice - callPutPrice))
    print "Forward strike 2: Call("+ fgndom +") - Put(" + domfgn + ") = Receive a fixed flow in " \
        + fgn + " and give a fixed flow in " + dom + ": " + str(max_CallPut_FixedFlow_diff)
    max_Forward_FixedFlow_diff = max(abs(swapPrice - fwdPrice))
    print "Receive a fixed flow in " + fgn + " and give a fixed flow in " + dom + \
        " = Forward " + fgndom + ": " + str(max_Forward_FixedFlow_diff)
    
    # Forward K = 0.5
    insCall = "call" + dom_fgn
    insPut = "put" + dom_fgn
    callPutPrice = d_mean[insCall] - d_mean[insPut]
    insDomFixedFlow = dom + "_FixedFlow"
    insFgnFixedFlow = fgn + "_FixedFlow"
    swapPrice = 2*(d_mean[insDomFixedFlow] - 0.5*d_mean[insFgnFixedFlow])
    max_CallPut_FixedFlow_diff = max(abs(swapPrice - callPutPrice))
    print "Forward strike 0.5: Call("+ domfgn +") - Put(" + domfgn + ") = Receive a fixed flow in " \
        + dom + " and give a fixed flow in " + fgn + ": " + str(max_CallPut_FixedFlow_diff)
    
    
    
    
    
    
    
    
    
    
    
    
    
