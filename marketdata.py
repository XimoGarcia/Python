import win32clipboard
import datetime as dt
import pandas as pd
from xlwings import Workbook, Range

def getIndex(workbook, index_header, indexes, shifters):
    vol_header = "<volatility surface_type=\"FIXED\" type=\"PARAMS_INTERPOLATED\" " + \
        "value=\"VOL_PARAM_SABR\" vol_nature=\"NORMAL\">\n" + \
        "<interpolation extrapolate=\"true\" flat_extrapolation=\"true\" " + \
        "left_side_derivatives=\"false\" magnitude=\"VOL\" method=\"LINEAR\"/>\n" + \
        "<maturities_defaults type=\"SABR_NORMAL\"/>\n<maturities>\n"
    
    item_sep = "<maturity value=\"{date}\">\n<parameters>\n"
    
    item = "<parameter name=\"{param_name}\" value=\"{param_value}\" />\n"
    
    item_padding = "</parameters>\n</maturity>\n"
    
    index_padding = "</maturities>\n</volatility>\n</marketdata_index>\n"
    
    lowerK = 0.0
    upperK = 10
    
    result = ""
    wb = Workbook(workbook)
    wb.set_current()
    for index, shifter in zip(indexes, shifters):
        result += index_header.format(index_name=index, tenor_shifter=shifter)
        result += vol_header
        rawFrame = Range(index, "CalibratedModelParams").value
        for line in filter(lambda x: any(x), rawFrame[1:]):
            date = line[0]
            if isinstance(date, dt.datetime):
                date = datetime_to_xldate(date)
                
            result += item_sep.format(date = int(date))
            result += item.format(param_name = "alpha", param_value=line[1])
            result += item.format(param_name = "beta", param_value=line[2])
            result += item.format(param_name = "rho", param_value=line[3])
            result += item.format(param_name = "nu", param_value=line[4])
            result += item.format(param_name = "lower_k", param_value=lowerK)
            result += item.format(param_name = "upper_k", param_value=upperK)
            result += item.format(param_name = "displacement", param_value=line[5])
            result += item_padding
        result += index_padding
    
    wb.close()
    return result

def getIndexesFromCube(cube, maturities, index_header, indexes, shifters):
    vol_header = "<volatility surface_type=\"FIXED\" type=\"PARAMS_INTERPOLATED\" " + \
        "value=\"VOL_PARAM_SABR\" vol_nature=\"NORMAL\">\n" + \
        "<interpolation extrapolate=\"true\" flat_extrapolation=\"true\" " + \
        "left_side_derivatives=\"false\" magnitude=\"VOL\" method=\"LINEAR\"/>\n" + \
        "<maturities_defaults type=\"SABR_NORMAL\"/>\n<maturities>\n"
    
    item_sep = "<maturity value=\"{date}\">\n<parameters>\n"
    
    item = "<parameter name=\"{param_name}\" value=\"{param_value}\" />\n"
    
    item_padding = "</parameters>\n</maturity>\n"
    
    index_padding = "</maturities>\n</volatility>\n</marketdata_index>\n"
    
    lowerK = 0.0
    upperK = 10
    
    result = ""
    for index, shifter in zip(indexes, shifters):
        result += index_header.format(index_name=index, tenor_shifter=shifter)
        result += vol_header
        params = cube[index] + [maturities]
        for alpha, beta, rho, nu, shift, date in zip(*params):

            result += item_sep.format(date = int(date))
            result += item.format(param_name = "alpha", param_value=alpha)
            result += item.format(param_name = "beta", param_value=beta)
            result += item.format(param_name = "rho", param_value=rho)
            result += item.format(param_name = "nu", param_value=nu)
            result += item.format(param_name = "lower_k", param_value=lowerK)
            result += item.format(param_name = "upper_k", param_value=upperK)
            result += item.format(param_name = "displacement", param_value=shift)
            result += item_padding
        result += index_padding
        
    return result


def xldate_to_datetime(xldate):
    temp = dt.datetime(1899, 12, 30)
    delta = dt.timedelta(days=xldate)
    return temp+delta

def datetime_to_xldate(date):
    temp = dt.datetime(1899, 12, 30)
    delta = date - temp
    return float(delta.days) + (float(delta.seconds) / 86400)
    
def getDateShifters(amounts, shifter_types, names):
    result = "<date_shifter>\n"
    item = "<date_shifter_item amount=\"{amount:.0f}\" stay_in_month=\"false\" " + \
      "type=\"{shifter_type}\" value=\"{name}\"/>\n"
      
    for amount, shifter_type, name in zip(amounts, shifter_types, names):
        result += item.format(amount = amount, shifter_type = shifter_type, name = name)
      
    return result + "</date_shifter>\n"

def getHolidays():
    return "<holidays>\n " + \
        "<holidays_item value=\"NoHols\">\n " + \
        "<hols_curve>\n<curve/>\n</hols_curve>\n " + \
        "</holidays_item>\n</holidays>\n"

def getVolatilitySwaption(name, indexes):
    result = "<volatility_swaption value=\"{name}\">\n".format(name = name)
    for index in indexes:
        result += "<tenor value=\"{index}\"/>\n".format(index = index)

    return result + "</volatility_swaption>\n"


def getCaccran():
    filename = "C:\Users\e022434\Desktop\Range Accrual\Cuadre\Libor\RangeAccrual.xls"
    wb = Workbook(filename)
    wb.set_current()
    rawFrame = Range("LGMRangeAccrual", "rangeaccrual.fixings").value
               
    columns = ("payment_date", "upper_bound", "in_rate", "out_rate",
               "reference_tenor", "spread_date", "spread",  "option_date", 
               "amort_date", "amort", "add_flow_date", "add_flow")
               
    df = pd.DataFrame(rawFrame, columns = columns).dropna(how = 'all')

    # Option
    option_dates = df["option_date"].dropna().apply(datetime_to_xldate)
    df["option_date"] = option_dates
    df["notice_date"] = option_dates
    df["option_idx"] = pd.Series(range(len(option_dates)), option_dates.index)
    
    # Funding Leg
    initial_date = 42207
    spread_nominal = 1E6
    spread_end_dates = df["spread_date"].dropna().apply(datetime_to_xldate)
    spread_start_dates = ([initial_date] + spread_end_dates.values.tolist())[:-1]
    df["spread_end_date"] = spread_end_dates    
    df["spread_start_date"] = pd.Series(spread_start_dates, spread_end_dates.index)    
    df["spread_nominal"] = pd.Series([spread_nominal] * len(spread_end_dates), spread_end_dates.index)
    df["spread_idx"] = pd.Series(range(len(spread_end_dates)), spread_end_dates.index)
    
    # Exotic leg
    exotic_nominal = 1E6
    reference_tenor = "USD_3M"
    payment_dates = df["payment_date"].dropna().apply(datetime_to_xldate)
    start_dates = ([initial_date] + payment_dates.values.tolist())[:-1]
    df["payment_date"] = payment_dates
    df["end_date"] = payment_dates
    df["start_date"] = pd.Series(start_dates, payment_dates.index)
    df["reference_tenor"] = pd.Series([reference_tenor]*len(start_dates), payment_dates.index)
    df["nominal"] = pd.Series([exotic_nominal] * len(start_dates), payment_dates.index)
    df["idx"] = pd.Series(range(len(start_dates)), payment_dates.index)
    
    columns += ("notice_date",  "option_idx", "spread_end_date",
                "spread_start_date", "spread_nominal", "spread_idx",  
                "end_date", "start_date", "nominal", "idx")
              
    df.columns = columns
    
    result = "<deal>\n"
    result += getOptions(df.dropna(subset = ("option_date",)))    
    result += getSwap()    
    result += getExoticLeg(df)    
    result += getFundingLeg(df)    
    result += "</deal>\n"
    
    return result

def getExoticLeg(dataFrame):
    header = "<range_accrual id=\"exoticLeg\" basis=\"{basis}\" >\n"
    item =  "<range_accrual start_date=\"{start_date:.0f}\" " + \
        "end_date=\"{end_date:.0f}\" upper_bound=\"{upper_bound}\" " + \
        "observed_market_data_id=\"{reference_tenor}\" in_rate=\"{in_rate}\" " + \
        "out_rate=\"{out_rate}\" nominal=\"{nominal}\" "+ \
        "id=\"range_accrual_{idx}\"/>\n"
    foot = "</range_accrual>\n"
    
    header = header.format(basis = "30/360")
    return getXml(header, item, foot, dataFrame)


def getFundingLeg(dataFrame):
    header = "<deposit basis=\"{basis}\" market_data_id=\"{index}\" " + \
                "capital_exchange=\"false\" id=\"legFloating\" " + \
                "frequency=\"SIMPLE\" multiplier=\"1.0\">\n"
    item = "<deposit fixing_date=\"{spread_start_date:.0f}\" start_date=\"{spread_start_date:.0f}\" " + \
            "end_date=\"{spread_end_date:.0f}\" payment_date=\"{payment_date:.0f}\" " + \
            "spread=\"{spread}\" nominal=\"{spread_nominal}\" id=\"floating_flow_{spread_idx}\"/>\n"
            
    foot = "</deposit>\n"
    
    header = header.format(basis = "Act/360", index="USD_3M")
    return getXml(header, item, foot, dataFrame)

def getOptions(dataFrame):
    header = "<option value='myOption'>\n<option_payoff>\n"    
    foot = "</option_payoff>\n</option>\n"
    item = "<payoff_item strike=\"0\" call_put=\"CALL\" " + \
        "pmt_date=\"{option_date:.0f}\" date=\"{notice_date:.0f}\" " + \
        "underlying=\"mySwap\" pay_libor=\"false\" exercise_type=\"EUROPEAN\" " + \
        "id=\"STD\" option_factor=\"1\" uid=\"test_{option_idx:.0f}\"/>\n"
    
    return getXml(header, item, foot, dataFrame)


def getXml(header, item, foot, dataFrame):
    result = header
    for index, row in dataFrame.iterrows():
        result += item.format(**row)
        
    return result + foot

def getSwap():
    return "<swap id=\"mySwap\">\n<legs>\n " + \
        "<legs_item value=\"exoticLeg\" quantity=\"1\"/>\n " + \
        "<legs_item value=\"legFloating\" quantity='-1'/>\n " + \
        "</legs>\n</swap>"


def getMarketData():
    
    cms_index_header = "<marketdata_index basis=\"30/360\" " + \
        "cms_floating_leg=\"{floating_index}\" " + \
        "date_shifter=\"0 OPEN DAYS\" estimation_ccy_curve=\"OIS\" " + \
        "holidays=\"NoHols\" schedule_shifter=\"6M MODFOL\" " + \
        "tenor_shifter=\"{{tenor_shifter}}\" value=\"{{index_name}}\">\n"
        
    libor_index_header = "<marketdata_index basis=\"Act/360\" " + \
        "date_shifter=\"0 OPEN DAYS\" estimation_ccy_curve=\"USD3M\" " + \
        "holidays=\"NoHols\" tenor_shifter=\"{tenor_shifter}\" value=\"{index_name}\">"
        
    
    cms_indexes = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30)
    cms_names = map(lambda x: "CMS_USD_{years}y".format(years=x), cms_indexes)
    cms_shifters = map(lambda x: "{years}Y MODFOL".format(years=x), cms_indexes)
    
    libor_indexes = (3,)
    libor_names = map(lambda x: "USD_{months}M".format(months=x), libor_indexes)
    libor_shifters = map(lambda x: "{months}m_index".format(months=x), libor_indexes)
    
    fileName = r"C:\Users\e022434\Desktop\Range Accrual\Cuadre\Libor\CopulaDataNormDisplacedUSD.xls"
    index_template = cms_index_header.format(floating_index = libor_names[0])
    cms_xml = getIndex(fileName, index_template, cms_names, cms_shifters)
    
    libor_xml = getIndex(fileName, libor_index_header, libor_names, libor_shifters)
    
    shifter_types = ["YEARS"] * len(cms_indexes) + ["MONTHS"] * len(libor_indexes)
    shifters_xml = getDateShifters(cms_indexes + libor_indexes, shifter_types, cms_shifters + libor_shifters)
    
    holidays_xml = getHolidays()
    
    cms_swaption_vol_xml = getVolatilitySwaption("cms_vol_cube", cms_names)
    libor_swaption_vol_xml = getVolatilitySwaption("libor_vol_cube", libor_names)
    
    return cms_swaption_vol_xml + libor_swaption_vol_xml + libor_xml + cms_xml + shifters_xml + holidays_xml

def getTable():
    return pd.read_clipboard(header = None, sep=r"\t")


def getSABRCube(items):
    cube = {}
    for alpha, beta, rho, nu, shift, index in zip(*items):
        cube[index] = [alpha, beta, rho, nu, shift]
        
        
    return cube

def getIndexes():
    
    cms_index_header = "<marketdata_index basis=\"30/360\" " + \
        "cms_floating_leg=\"{floating_index}\" " + \
        "date_shifter=\"0 OPEN DAYS\" estimation_ccy_curve=\"OIS\" " + \
        "holidays=\"NoHols\" schedule_shifter=\"6M MODFOL\" " + \
        "tenor_shifter=\"{{tenor_shifter}}\" value=\"{{index_name}}\">\n"
        
    libor_index_header = "<marketdata_index basis=\"Act/360\" " + \
        "date_shifter=\"0 OPEN DAYS\" estimation_ccy_curve=\"USD3M\" " + \
        "holidays=\"NoHols\" tenor_shifter=\"{tenor_shifter}\" value=\"{index_name}\">"
        
    
    cms_indexes = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30)
    cms_names = map(lambda x: "CMS_USD_{years}y".format(years=x), cms_indexes)
    cms_shifters = map(lambda x: "{years}Y MODFOL".format(years=x), cms_indexes)
    
    libor_indexes = (3,)
    libor_names = map(lambda x: "USD_{months}M".format(months=x), libor_indexes)
    libor_shifters = map(lambda x: "{months}m_index".format(months=x), libor_indexes)
    
    index_template = cms_index_header.format(floating_index = libor_names[0])
    cube = getSABRCube([alphas, betas, rhos, nus, shifts, libor_names + cms_names])
    cms_xml = getIndexesFromCube(cube, maturities, index_template, cms_names, cms_shifters)
    
    libor_xml = getIndexesFromCube(cube, maturities, libor_index_header, libor_names, libor_shifters)
    
    
    return libor_xml + cms_xml



#result = getCaccran()
#result = getMarketData()
indexes = getIndexes()

win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.SetClipboardText(indexes)
win32clipboard.CloseClipboard()
