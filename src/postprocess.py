
# coding: utf-8

# In[1]:

# --- IMPORT ---
import os
import sys
import json
import datetime
import xlsxwriter
import argparse
import textwrap
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from xlsxwriter.workbook import Workbook
import config
import calc
import visualize
import extract


# In[2]:

def calculate_indicators(df, n_short=12, n_long=26, n_signal=9, n_K=5, n_D=3 ,n_D_slow=3):
    v = df["end_adj"]
    df["macd"]   = calc.calc_macd(v, n_short, n_long)
    df["signal"] = calc.calc_signal(v, n_signal, n_short, n_long)
    df["D"]      = calc.calc_D(v, n_K, n_D)
    df["D_slow"] = calc.calc_D_slow(v, n_K, n_D, n_D_slow)
    df = np.round(df)
    return df


# In[3]:

def identify_promise(df):
    data_lastday = df.iloc[-1, :]
    macd   = data_lastday["macd"]
    signal = data_lastday["signal"]
    D_slow = data_lastday["D_slow"]
    if macd >= 0 and macd > signal and D_slow <= 20:
        return "BUY"
    elif macd <= 0 and macd < signal and D_slow >= 80:
        return "SELL"
    else:
        return "STAY"


# In[4]:

def insert_df_to_xlsx(df, worksheet):    
    for c, cell in enumerate(df.reset_index().columns):
        worksheet.write(0, c, cell)
    for r, row in df.reset_index().iterrows():
        for c, cell in enumerate(row):
            if isinstance(cell, datetime.datetime):
                cell = str(cell)
            if isinstance(cell, float):
                if np.isnan(cell):
                    cell = None
            worksheet.write(r+1, c, cell)


# In[5]:

def main(start_date, end_date):

    workbook = xlsxwriter.Workbook(config.xlsx_path)
    prediction = workbook.add_worksheet("予測")
    counter = 0

    with open(config.json_path, 'r') as f:
        data = json.load(f)    
    
    for code in config.codes:
        name = data[code]['name']
        name_base = code + "_" + name
        data_focus = extract.extract_data(data, code, start_date, end_date)
        df = extract.dict2dataframe(data_focus)
        df = calculate_indicators(df)

        os.makedirs(config.c_dir_path, exist_ok=True)
        os.makedirs(config.m_dir_path, exist_ok=True)
        os.makedirs(config.s_dir_path, exist_ok=True)        
        c_path = os.path.join(config.c_dir_path, name_base + ".png")
        m_path = os.path.join(config.m_dir_path, name_base + ".png")
        s_path = os.path.join(config.s_dir_path, name_base + ".png")

        visualize.draw_candlestick(df, c_path)
        visualize.draw_indicators(df, ["macd", "signal"], m_path)
        visualize.draw_indicators(df, ["D",    "D_slow"], s_path)

        worksheet = workbook.add_worksheet(name_base[:30])

        promise = identify_promise(df)

        if  promise == "BUY":
            worksheet.set_tab_color("red")
            prediction.write(counter, 0, "BUY")
            prediction.write(counter, 1, name_base)
            counter += 1
        elif promise == "SELL":
            worksheet.set_tab_color("blue")
            prediction.write(counter, 0, "SELL")
            prediction.write(counter, 1, name_base)
            counter += 1
        insert_df_to_xlsx(df, worksheet)
        worksheet.insert_image('N1',  c_path, {'x_scale': 0.5, 'y_scale': 0.5})
        worksheet.insert_image('N21', m_path, {'x_scale': 0.5, 'y_scale': 0.5})
        worksheet.insert_image('N41', s_path, {'x_scale': 0.5, 'y_scale': 0.5})
        print("a sheet made for", code)
    workbook.close()
    print("an excel written in", config.xlsx_path)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent("""
                             Extract stock price data from a database 
                             for a specified period and make a convenient excel file.
                             If -START and -END arguments are not specified,
                             it extracts data from 6 months ago to the day of extraction.
                             """))
    parser.add_argument('-START', default=None,
                        help='The date from when to extract stock prices. Its format must be YYYY-MM-DD')
    parser.add_argument('-END', default=None,
                        help='The date until when to extract stock prices. Its format must be YYYY-MM-DD')
                        
    args = parser.parse_args()    
                        
    if args.END is None:                
        end_datetime = datetime.datetime.today()                
    else:
        end_datetime = datetime.datetime.strptime(args.END, '%Y-%m-%d')
                        
    if args.START is None:
        start_datetime = end_datetime - relativedelta(months=6)
    else:
        start_datetime = datetime.datetime.strptime(args.START, '%Y-%m-%d')
        
    end_date = end_datetime.strftime('%Y-%m-%d')
    start_date = start_datetime.strftime('%Y-%m-%d')    
    
    main(start_date, end_date)

