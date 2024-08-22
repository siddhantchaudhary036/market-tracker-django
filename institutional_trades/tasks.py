# tasks.py or a utility module
import requests
import pandas as pd
from datetime import timedelta

from .models import recent_trades_db
from datetime import datetime
import uuid
from io import BytesIO
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django_huey import db_periodic_task, db_task

with open('institutional_trades/sectors.csv') as f:
    df_sectors = pd.read_csv(f)



@db_periodic_task(crontab(minute='*/1'),queue='updater')
def get_bnb_trades():
    
    print('CHECKING FOR NEW INSTITUTIONAL TRADES!!!')
    for dtype in [1,2]:
        today = (datetime.today()).strftime('%d/%m/%Y')
        yesterday = (datetime.today()-timedelta(days=10)).strftime('%d/%m/%Y')

        data_type = dtype  # or 2 depending on what you need
        scrip = ""  # leave blank for all trades # Write the BSE scrip code for particular stock
        start_date = yesterday
        end_date = today
        url = "https://www.bseindia.com/markets/equity/EQReports/BulknBlockDeals.aspx?flag=2"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        with open('institutional_trades/request_validation_codes/viewstate.txt', 'r') as f:
            viewstate = f.read()
        with open('institutional_trades/request_validation_codes/eventvalidation.txt', 'r') as f:
            eventvalidation = f.read()

        data = {'flag': '2',
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$btndownload1',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': '43DF1E00',
                '__VIEWSTATEENCRYPTED': '',
                '__EVENTVALIDATION': eventvalidation,
                'ctl00$ContentPlaceHolder1$hf_scripcode': scrip,
                'ctl00$ContentPlaceHolder1$rblDT': str(data_type),
                'ctl00$ContentPlaceHolder1$chkAllMarket': 'on',
                'ctl00$ContentPlaceHolder1$txtDate': start_date,
                'ctl00$ContentPlaceHolder1$txtToDate': end_date
                }

        response = requests.post(url, headers=headers, data=data)
        print(response.status_code)

        df = pd.read_csv(BytesIO(response.content), usecols=[0, 1, 2, 3, 4, 5, 6], encoding='latin1')
        
        update_database(df,dtype)


def update_database(df,dtype):


    # Merge df with sector information
    df_merged = df.merge(df_sectors[['Security Code','Industry', 'Sector Name']], on='Security Code', how='left')


    # Convert DataFrame to a list of dictionaries
    new_records = df_merged.to_dict('records')

    # Get existing records from the database
    existing_records = set(recent_trades_db.objects.values_list('deal_date', 'security_code', 'client_name', 'deal_type', 'quantity'))

    # Filter out records that already exist in the database
    records_to_insert = []
    for record in new_records:
        try: 
            key = (datetime.strptime(record['Deal Date'], '%d/%m/%Y'), int(record['Security Code']), record['Client Name'], record['Deal Type'], int(record['Quantity']))
            if key not in existing_records:
                
                print('UPDATING DATABASE WITH NEW TRADES -- TRADES:')
                print(key)

                records_to_insert.append(
                    recent_trades_db(
                        deal_date=datetime.strptime(record['Deal Date'], '%d/%m/%Y'),
                        security_code=record['Security Code'],
                        company=record['Company'],
                        client_name=record['Client Name'],
                        deal_type=record['Deal Type'],
                        quantity=record['Quantity'],
                        price=record['Price'],
                        sector=record['Sector Name'],
                        industry = record['Industry'],
                        dtype_db = dtype
                    )
                )
        except:
            continue

    # Bulk create new records
    if records_to_insert:
        recent_trades_db.objects.bulk_create(records_to_insert)
