import os
import sys
import json
import datetime
from dateutil.relativedelta import relativedelta
import argparse
import textwrap
import pandas as pd
import config

def extract_data(data, code, date_start, date_end):
    d1 = datetime.datetime.strptime(date_start, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date_end,   "%Y-%m-%d")
    dates = {(d1 + datetime.timedelta(i)).strftime("%Y-%m-%d") for i in range((d2-d1).days + 1)}
    data_focus = {k: data[code]['data'][k] for k in data[code]['data'].keys() & dates}
    return data_focus

def dict2dataframe(data):
    df = pd.DataFrame(data).T
    df.index = pd.to_datetime(df.index)
    df = df.dropna().apply(pd.to_numeric) # deal with stock division
    df = df.sort_index()
    return df

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent("""
                             Extract stock price data from the database.
                             Specification of stock code is mandatory but period is optional.
                             """))
    parser.add_argument('CODE', 
                        help='The stock code of which you want to extract the stock price data')
    parser.add_argument('-START', default=None,
                        help='The date from when to extract stock prices. Its format must be YYYY-MM-DD')
    parser.add_argument('-END', default=None,
                        help='The date until when to extract stock prices. Its format must be YYYY-MM-DD')
                        
    args = parser.parse_args()    
                        
    if args.END is None:                
        datetime_end = datetime.datetime.today()                
    else:
        datetime_end = datetime.datetime.strptime(args.END, '%Y-%m-%d')
                        
    if args.START is None:
        datetime_start = datetime_end - relativedelta(months=6)
    else:
        datetime_start = datetime.datetime.strptime(args.START, '%Y-%m-%d')
        
    date_end = datetime_end.strftime('%Y-%m-%d')
    date_start = datetime_start.strftime('%Y-%m-%d')
    
    with open(config.json_path, "r") as f:
        data = json.load(f)    
        
    data_focus = extract_data(data, args.CODE, date_start, date_end)
    df = dict2dataframe(data_focus)
    
    print(df)