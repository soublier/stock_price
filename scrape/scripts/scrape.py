
# coding: utf-8

# In[1]:

# --- IMPORT ---
import re
import os
import sys
import bs4
import time
import json
import datetime
import requests
import argparse
import textwrap
from dateutil import relativedelta
from utils.config import codes, path_json


# In[121]:

def specify_url(code, date_stt, date_end, idx_page):
    '''
    specify a url from stock code, scraping period, and page index.
    Args:
        code (str or int): a stock code.
        date_stt (str): a string specifying the start date for scraping.
            its format must be 'YYYY-MM-DD'.
        date_end (str): a string specifying the end date for scraping.
            its format must be 'YYYY-MM-DD'.
        idx_page (str or int): a page index.
    Returns:
        str: a valid url.
    '''
    # base url
    url_base = "https://info.finance.yahoo.co.jp/history/"
    # code attribute
    attr_code = "?code={}".format(code)
    # start and end date
    datetime_stt = datetime.datetime.strptime(date_stt, "%Y-%m-%d")
    datetime_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")
    attr_date_stt = datetime_stt.strftime("&sy=%Y&sm=%m&sd=%d")
    attr_date_end = datetime_end.strftime("&ey=%Y&em=%m&ed=%d")
    attr_date = attr_date_stt + attr_date_end + "&tm=d"
    # page attribute
    attr_page = "&p={}".format(idx_page)
    # full url
    url = url_base + attr_code + attr_date + attr_page
    return url


# In[122]:

def extract_soup(url):
    dict_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)                     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=dict_headers)
    soup = bs4.BeautifulSoup(response.text, "lxml")
    return soup


# In[123]:

def extract_data(soup):
    soup_table = soup.find(name='table', attrs={"class":'boardFin'})
    soups_row = soup_table.find_all(name="tr")
    data_rows = []
    for soup_row in soups_row:
        soups_cell = soup_row.find_all(["td", "th"])
        data_row = []
        for soup_cell in soups_cell:
            data_row.append(soup_cell.text.replace(",", ""))
        data_rows.append(data_row)
    return data_rows


# In[168]:

def convert_format(data_rows):

    dict_corres = {"始値": "start",
                   "終値": "end",
                   "安値": "low",
                   "高値": "high",
                   "調整後終値*":"end_adj",
                   "出来高": "volumn"}
    
    keys = data_rows[0][1:]    
    keys = [dict_corres[k] for k in keys]
    dict_data = {}
    for data_row in data_rows[1:]:
        date = data_row[0]
        date = datetime.datetime.strptime(date, "%Y年%m月%d日")
        date = date.strftime("%Y-%m-%d")
        dict_data[date] = {}
        for k, v in zip(keys, data_row[1:]):
            dict_data[date][k] = v
    return dict_data


# In[169]:

def extract_company(soup):
    string = soup.find(name="th", attrs={"class":"symbol"}).string
    string = re.sub(r"[\(\（][\w\W]*[\)\）]", r"", string)
    string = re.sub(r",", r"", string)
    string = re.sub(r"\n", r"", string)
    string = re.sub(r"[＋+]", r"", string)
    string = re.sub(r"[－]", r"-", string)
    string = re.sub(r"\s", r"", string)
    return string


# In[170]:

def insert_data(str_code, data_old, date_stt, date_end, sleeptime):
    print("code: {}".format(str_code))
    if str_code not in data_old:
        data_old[str_code] = {"data":{}}
    idx_page = 1
    while True:
        print("scraping from page: {}".format(idx_page))
        url = specify_url(str_code, date_stt, date_end, idx_page)
        soup = extract_soup(url)
        data = extract_data(soup)
        data_new = convert_format(data)
        data_old[str_code]["data"].update(data_new)
        idx_page += 1
        time.sleep(sleeptime)
        if soup.find(name="a", text="次へ") is None:
            break
    data_old[str_code]["name"] = extract_company(soup)
    return data_old


# In[ ]:

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent("""
                             Retrieve stock prices of specified companies for a specified period. 
                             The retrieved data will be merged with the existing database.
                             For specification of companies, modify stock_prices/scripts/config.py.
                             """))
    parser.add_argument('-START', default=None,
                        help='The date from when to retrieve stock prices. Its format must be YYYY-MM-DD')
    parser.add_argument('-END', default=None, 
                        help='The date until when to retrieve stock prices. Its format must be YYYY-MM-DD')
    parser.add_argument('-SLEEP', default=0.01, type=float,
                        help='The sleep time between each retrieval.')

    args = parser.parse_args()
    
    # scraping period
    if args.END is None:
        datetime_end = datetime.datetime.today()
    else:
        datetime_end = datetime.datetime.strptime(args.END, "%Y-%m-%d")
    if args.START is None:
        datetime_start = datetime_end - relativedelta.relativedelta(months=12)
    else:
        datetime_start = datetime.datetime.strptime(args.START, "%Y-%m-%d")
    date_start = datetime_start.strftime("%Y-%m-%d")
    date_end   = datetime_end.strftime("%Y-%m-%d")
    
if os.path.exists(path_json):
    with open(path_json, "r") as f:
        data = json.load(f)
else:
    data = {}
    
for code in codes:
    data = insert_data(code, data, date_start, date_end, args.SLEEP)

with open(path_json, "w") as f:
    json.dump(data, f, indent=1)

