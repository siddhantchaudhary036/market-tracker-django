import requests
from PyPDF2 import PdfReader 
from io import BytesIO
import brotli
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from .models import live_news_db
from huey import crontab
import yfinance as yf
import pandas as pd
from django.conf import settings
from django_huey import db_periodic_task, db_task
from transformers import pipeline
import yfinance as yf
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from .models import TaskControl

classifier = pipeline('sentiment-analysis')

import asyncio

async def fetch_ltp(ticker):
    channel_layer = get_channel_layer()
    while True:
        task_control = await sync_to_async(TaskControl.objects.get)(ticker=ticker)
        if not task_control.should_run:
            break
        print(task_control.should_run)
        data = yf.download(ticker, period='1d', interval='1m')
        ltp = data['Close'].iloc[-1]

        await channel_layer.group_send(f"news_{ticker}", {
            "type": "ltp_update",
            "ltp_value": ltp,
        })
        print('value sent', ltp)
        await asyncio.sleep(5)

    print(f"Task for {ticker} has been stopped.")


def get_live_news():

    print('CHECKING FOR NEW NEWS!!!')
    url = "https://www.bsealerts.in/subscription.php"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "PHPSESSID=aa52436f18246cb46765316bc64bde51",
        "Origin": "https://www.bsealerts.in",
        "Referer": "https://www.bsealerts.in/index.php",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    data = {
        "operId": 9,
        "exchange": "undefined"
    }

    response = requests.post(url, headers=headers, data=data)
    #print(f'response status {response.status_code}')
    #print(f"ENCODING: {response.headers.get('Content-Encoding')}")
    #print(f"LAST UPDATED FROM SERVER: {response.headers['Date']}")
    print(response.status_code)
    if response.headers.get('Content-Encoding') == 'br':

        try:
            decompressed_content = response.content #brotli.decompress(response.content)
        except:
            decompressed_content = brotli.decompress(response.content)

    else:
        print('incorrect decoding setup of ZIPPED data')


    try: 
        decompressed_text = decompressed_content#.decode('utf-8')
        import json
        data = json.loads(decompressed_text)
        return data['data']  # Return the 'data' key if it exists
    
    # Sometimes the Cookie PHPSESSID expires, so we need to update it. Ill email myself when the time comes :))
    except:
        print('ERROR IN DECODING JSON')
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail('ERROR IN DECODING JSON', 'ERROR IN DECODING JSON for get_live_news function, please update the cookie ssid', settings.EMAIL_HOST_USER, ['siddhantchaudhary036@gmail.com'])
        return []
  
      



'''Function gets the full text of the pdf news id, the pdf url and the url to the BSE website where the PDF is listed'''
def get_full_text(news_id):
  print('Fetching News URLS')
  url = "https://www.bseindia.com/corporates/anndet_new.aspx"
  params = {
      "newsid": str(news_id)
  }
  headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"}

  # Make the GET request
  response = requests.get(url, params=params, headers=headers)

  # Parse the HTML content using BeautifulSoup
  soup = BeautifulSoup(response.text, 'html.parser')

  # Find the <a> tag that contains the PDF link
  pdf_link_tag = soup.find('a', href=lambda href: href and href.endswith('.pdf'))

  # Extract the PDF URL
  if pdf_link_tag:
      pdf_url = pdf_link_tag['href']
      response = requests.get(pdf_url, headers=headers)
  else:
      print("PDF URL not found")



  # Check if the request was successful
  if response and response.status_code == 200:

    pdf_text = ''
    pdf_file = BytesIO(response.content)
    pdf_reader = PdfReader(pdf_file) # Use PdfReader here
    for page_num in range(len(pdf_reader.pages)): # Use pdf_reader.pages to get the pages
        page = pdf_reader.pages[page_num]
        pdf_text += page.extract_text()


    url = f'{url}?newsid={news_id}'
    return pdf_text,pdf_url,url
  else:
    return response.status_code

def convert_company_name_to_ticker(company_name):
    with open ('news/sectors.csv') as f:
        convertor_df = pd.read_csv(f)
    
    for i in range(len(convertor_df)):
        if convertor_df['Security Name'][i] == company_name:
            ticker = convertor_df['Security Id'][i]
            return ticker+".BO"
    print('TICKER NOT FOUND!!')
    return ''

from transformers import AutoTokenizer

max_length = 500
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
def truncate_input(text):
    tokens = tokenizer.encode(text, add_special_tokens=True, max_length=max_length, truncation=True)
    return tokenizer.decode(tokens)

from django.db.models import Q
from .models import live_news_db, watchlist_db
from django.contrib import messages
from django.core.mail import send_mail

@db_periodic_task(crontab(minute='*/1'),queue='updater')
def update_live_news():
    live_news_data = get_live_news()

    existing_records = set(live_news_db.objects.values_list('report_time', 'company_name', 'news_id'))
    records_to_insert = []

# Parse the date string

    for i in range(len(live_news_data)):

        report_time = datetime.strptime(live_news_data[i]['report_date'], '%b %d, %H:%M').replace(year = datetime.now().year)
        company_name = live_news_data[i]['company_name']
        news_id = live_news_data[i]['news_id']
        subject =live_news_data[i]['subject']
        body = live_news_data[i]['body']
        '''Only check for news affecting live price if the news type was press release'''

        key = (report_time,company_name,news_id)
        if key not in existing_records:
            print('UPDATING DATABASE WITH NEW TRADES -- TRADES:')
            print(key)

            try:
                pdf_text,pdf_url,bse_page_url = get_full_text(news_id)
                ticker = convert_company_name_to_ticker(company_name)
            except:
                print('PDF URL or Base_Page_Url not found')
                pdf_url = 'Not Available'
                bse_page_url = 'Not Available'
                pdf_text = ''
            

            truncated_pdf_text = truncate_input(pdf_text)
            classifier_response = classifier(truncated_pdf_text)


            # Get the user's watchlist and all the emails that have this stock in their watchlist
            queryset = watchlist_db.objects.filter(Q(tickers__iexact=ticker[:-3]))
            emails = queryset.values_list('user_email', flat=True)


            # Send emails to all the users who have this stock in their watchlist
            send_mail(
                'There is a new press release for ' + company_name,
                subject + '\n\n' + pdf_url,
                settings.EMAIL_HOST_USER,
                emails,
                fail_silently=False,
            )

            # Prepare to bulk insert into the database (to reduce the number of queries)
            records_to_insert.append(
                live_news_db(
                    report_time=report_time,
                    company_name = company_name,
                    ticker = ticker,
                    news_id = news_id,
                    subject = subject,
                    body = body,
                    pdf_url = pdf_url,
                    bse_page_url = bse_page_url,
                    full_text = pdf_text,
                    sentiment_score = classifier_response[0]['score'],
                    sentiment_label = classifier_response[0]['label']

                )
            )

    if records_to_insert:
        live_news_db.objects.bulk_create(records_to_insert)
