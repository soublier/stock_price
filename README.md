### stock price scraper

0. Download this repository by 

    * clicking on **Clone or download**
    
    * and clicking on **Download ZIP**

1. Place it to your favorite location and unzip.

2. In the command prompt, move to the `scripts` directory.

    * `cd PATH/TO/src` 

3. Enter following commands in the command prompt:
   
    * If you run the script for the first time

         * `python scrape.py -MONTH 12`

         * The above command retrieves stock price data 

           from 12 months ago to the day of retrieval

           and make a database inside the `result` directory.

    * If you have already run the script once

         * `python scrape.py`

         * The above commands retrieves stock price data

           from 1 month ago to the day of retrieval

           and updates the database inside the `result` directory.

5. Enter following commands:

    * `python postprocess.py`

    * The above command extracts data from the database

      and makes an excel file.

6. If you want to see the help message, enter following commands.

    * `python scrape.py -h`

    * `python postprocess.py -h`
