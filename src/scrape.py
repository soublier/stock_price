import re
import os
import sys
import bs4
import json
import shutil
import logging
import datetime
import requests
import argparse
import textwrap
import functools
import multiprocessing
import pandas as pd
from time import sleep
from logging import getLogger
from dateutil import relativedelta
import config


logging.basicConfig(level=logging.INFO)
logger = getLogger(__name__)


def specify_url(code, start_date, end_date, page):
    '''
    Specify a url from stock code, scraping period, and page index.
    
    Args:
        code (str or int): a stock code.
        start_date (str): a string specifying the start date for scraping.
            its format must be 'YYYY-MM-DD'.
        end_date (str): a string specifying the end date for scraping.
            its format must be 'YYYY-MM-DD'.
        page (str or int): a page index.
    Returns:
        str: a valid url.
    '''
    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")    
    
    url = '''
    https://info.finance.yahoo.co.jp/history/?code={code}\
    &sy={start_year}&sm={start_month:0>2}&sd={start_day:0>2}\
    &ey={end_year}&em={end_month:0>2}&ed={end_day:0>2}\
    &tm=d&p={page}
    '''.strip().replace(' ', '').format(
        code=code,
        start_year=start_datetime.year,
        start_month=start_datetime.month,
        start_day=start_datetime.day,
        end_year=end_datetime.year,
        end_month=end_datetime.month,
        end_day=end_datetime.day,
        page=page)
    
    return url


def extract_soup(url):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.text, "lxml")
    
    return soup


def extract_dataframe(soup):
    
    soup_table = soup.find(name='table', attrs={"class":'boardFin'})
    soups_row = soup_table.find_all(name="tr")
    rows = []
    for soup_row in soups_row:
        soups_cell = soup_row.find_all(["td", "th"])
        row = []
        for soup_cell in soups_cell:
            row.append(soup_cell.text.replace(",", ""))
        rows.append(row)
    columns = ['date', 'start', 'end', 'low', 'high', 'volumn', 'end_adj']
    df = pd.DataFrame(rows[1:], columns=columns)
    df['date'] = pd.to_datetime(
        df['date'], format='%Y年%m月%d日').dt.strftime('%Y-%m-%d')
    
    # deal with stock division
    divs = df['start'].str.startswith('分割')
    df = df[~divs]
    df['div'] = 0
    df.loc[df.index[pd.np.where(divs)[0]], 'div'] = 1
    
    return df


def extract_company(soup):
    
    string = soup.find(name="th", attrs={"class":"symbol"}).string
    string = re.sub(r"[\(\（][\w\W]*[\)\）]", r"", string)
    string = re.sub(r",", r"", string)
    string = re.sub(r"\n", r"", string)
    string = re.sub(r"[＋+]", r"", string)
    string = re.sub(r"[－]", r"-", string)
    string = re.sub(r"\s", r"", string)
    
    return string


def scrape(code, start_date, end_date, dir_path, sleeptime):

    page = 1
    df = pd.DataFrame()
    next_found = True
    while next_found:
        logger.info("code: {}, page: {}".format(code, page))
        url = specify_url(code, start_date, end_date, page)
        soup = extract_soup(url)
        _df = extract_dataframe(soup)
        df = pd.concat([df, _df], ignore_index=True)
        next_found = soup.find(name="a", text="次へ")
        page += 1
        sleep(sleeptime)
    company = extract_company(soup)
    os.makedirs(dir_path, exist_ok=True)
    file_name = '{}_{}.csv'.format(code, company)
    file_path = os.path.join(dir_path, file_name)
    df.to_csv(file_path, index=False)
    logger.info('file saved to {}'.format(file_path))


def collect_new_data(dir_path):
    
    new_data = {}
    file_names = os.listdir(dir_path)
    for file_name in file_names:
        file_path = os.path.join(dir_path, file_name)
        code, company = file_name.strip('.csv').split('_')
        new_data[code] = {'name': company}
        df = pd.read_csv(file_path)
        data = df.set_index('date').to_dict(orient='index')
        new_data[code]['data'] = data
            
    return new_data


def main(start_date, end_date, months, sleeptime):
    
    if end_date is None:
        end_datetime = datetime.datetime.today()
    else:
        end_datetime = datetime.datetime.strptime(end, "%Y-%m-%d")
        
    if start_date is None:
        start_datetime = end_datetime - relativedelta.relativedelta(months=months)
    else:
        start_datetime = datetime.datetime.strptime(start, "%Y-%m-%d")
        
    start_date = start_datetime.strftime("%Y-%m-%d")
    end_date = end_datetime.strftime("%Y-%m-%d")
    
    data = {}
    if os.path.exists(config.json_path):
        logger.info('loading existing database from {}'.format(config.json_path))
        with open(config.json_path, "r") as f:
            data = json.load(f)
        
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        dir_path = os.path.join(os.path.dirname(config.json_path), 'tmp')
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.mkdir(dir_path)
        logger.info('scraping new data in parallel and save them in {}'.format(dir_path))
        _scrape = functools.partial(
            scrape, start_date=start_date, end_date=end_date, 
            dir_path=dir_path, sleeptime=sleeptime)
        results = p.map(_scrape, config.codes)
        
    logger.info('collecting new data from {}'.format(dir_path))
    new_data = collect_new_data(dir_path)
    data.update(new_data)

    logger.info('saving updated database to {}'.format(config.json_path))
    with open(config.json_path, "w") as f:
        json.dump(data, f, indent=1)

    logger.info('done.')


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
    parser.add_argument('-MONTH', default=1, type=int,
                        help='The number of months the start date precedes prior to the end date')
    parser.add_argument('-SLEEP', default=0.01, type=float,
                        help='The sleep time between each retrieval.')

    args = parser.parse_args()
    main(args.START, args.END, args.MONTH, args.SLEEP)
