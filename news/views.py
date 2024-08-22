from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import live_news_db, watchlist_db 
from .forms import FilterNewsForm, ManageWatchlistForm
import ast
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend because other wise matplotlib uses tkinter as a backend and it crashes the server since it does not work well with django.
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, time , timedelta, timezone
import pandas as pd
import yfinance as yf
from django.http import JsonResponse
from . tasks import fetch_ltp
from django.contrib.auth.decorators import login_required

'''live_news_db.objects.all().delete()
print('delteing all news')'''


def create_line_chart(data,index_of_news,timeseries):
    plt.figure(figsize=(10, 5))
    plt.plot(timeseries,data, marker='o', linestyle='-', label='Data')

    # Highlight the specific point
    if index_of_news != 0:
        plt.plot(timeseries[index_of_news], data[index_of_news], marker='o', color='red', label='News Release')
    plt.title('Line Chart')
    plt.ylabel('Close Price/ Traded Volume')
    plt.xlabel('Time')
    plt.legend()

    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Convert the BytesIO object to a base64 string
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return image_base64


def get_live_price(ticker, news_time):

    try:
        start_date = (news_time).strftime('%Y-%m-%d')
        end_date = (news_time+timedelta(days=1)).strftime('%Y-%m-%d')
        ohlcv_data = yf.download(ticker, start=start_date, end=end_date, interval='1m')
        close_values_list = ohlcv_data['Close'].tolist()
        volume_values_list = ohlcv_data['Volume'].tolist()
        timeseries = ohlcv_data.index.tolist()
        for i in timeseries:
            i = str(i)
    except:
        print('Ticker not found in Yahoo Finance API')
        return [0],[0],[0],0
  
    start_time = datetime.replace(news_time, hour=9, minute=15, second=0, microsecond=0)
    end_time = datetime.replace(news_time, hour=15, minute=30, second=0, microsecond=0)
    if news_time>start_time and news_time<end_time and news_time.weekday()<5 and news_time.weekday()>=0:

        try:
            timestamp = (news_time + timedelta(minutes=1)).replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            index_of_value = ohlcv_data.index.get_loc(pd.to_datetime(timestamp))-1
            return timeseries,volume_values_list, close_values_list, index_of_value
        
        except:
            print('News time not found in the data, DATA GAP IN YF API')
            return timeseries,volume_values_list,close_values_list,0
        
    else:
        print('News time not within market hours')
        return [0],[0],[0],0
    

    
@login_required(login_url='login')
def live_news_analyse(request, id):

    news = live_news_db.objects.get(id=id)
    timeseries,volume_values_list, close_values_list, index_of_news = get_live_price(news.ticker, news.report_time)
    close_line_chart = create_line_chart(close_values_list,index_of_news,timeseries)
    volume_line_chart = create_line_chart(volume_values_list,index_of_news,timeseries)


    if close_values_list[index_of_news] == 0:
        price_upon_news_release = yf.download(news.ticker, period='1d', interval='1m')['Close'][-1]
    else:
        price_upon_news_release = close_values_list[index_of_news]
    room_name = news.ticker  # Assuming you want to use the ticker as the room name
    return render(request, 'live_news_analyse.html', {'news': news,
                                                      'close_line_chart':close_line_chart,
                                                      'volume_line_chart':volume_line_chart,
                                                      'close_values': close_values_list,
                                                      'volume_values': volume_values_list,
                                                      'index_of_news': index_of_news,
                                                      'price_upon_news_release':price_upon_news_release,
                                                      'room_name': room_name

                                                      })


@login_required(login_url='login')
def live_news(request):
    form  = FilterNewsForm(request.GET or None)
    if form.is_valid():
        subject_filter = form.cleaned_data.get('subject_filter')
        company_name = form.cleaned_data.get('company_name')
        time_filter = form.cleaned_data.get('time_filter')
        news_list = live_news_db.objects.filter(subject__icontains = subject_filter, company_name__icontains = company_name).order_by('-report_time')
        if time_filter == 'market_hours':
            news_list = news_list.filter(
                    report_time__time__gte=time(9, 15),
                    report_time__time__lt=time(15, 30),
                    report_time__week_day__gte=2,  # Monday
                    report_time__week_day__lte=6   # Friday
                )

    else:
        news_list = live_news_db.objects.all().order_by('-report_time')
    
    

    paginator = Paginator(news_list, 25)  # Show 25 trades per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'live_news.html',{'added_entries':page_obj,'filter_news_form':form})

from django.http import HttpResponse


from django.contrib.auth.models import User
import pandas as pd
@login_required(login_url='login')
def manage_watchlist(request):
    user_email = request.user.email

    # Load valid tickers from a CSV file and create a dictionary with ticker as the key
    with open('C:\\Users\\abhap\\Downloads\\bsenews\\news\\sectors.csv', 'r') as f:
        df = pd.read_csv(f)
    valid_tickers = dict(zip(df['Security Id'].str.upper(), df['Security Name']))

    # Get or create the user's watchlist
    watchlist, created = watchlist_db.objects.get_or_create(user_email=user_email)
    if created:
        watchlist.tickers = ''
        watchlist.save()

    # Initialize the form
    form = ManageWatchlistForm(request.GET or None)

    # Update the watchlist if the form is valid
    if form.is_valid():
        ticker_filter = form.cleaned_data.get('ticker_filter').upper()  # Convert to uppercase for consistency
        if ticker_filter in valid_tickers:
            # Append the new ticker to the existing list of tickers
            tickers_list = watchlist.tickers.split() if watchlist.tickers else []
            if ticker_filter not in tickers_list:
                tickers_list.append(ticker_filter)
                watchlist.tickers = ' '.join(tickers_list)
                watchlist.save()
        else:
            form.add_error('ticker_filter', 'Invalid ticker symbol.')

    # Prepare the current watchlist for rendering
    current_watchlist = [
        {'ticker': ticker, 'company_name': valid_tickers.get(ticker, 'Unknown')}
        for ticker in watchlist.tickers.split()
    ]

    return render(request, 'manage_watchlist.html', {
        'manage_watchlist_form': form,
        'current_watchlist': current_watchlist,
        'user_email': user_email
    })

        