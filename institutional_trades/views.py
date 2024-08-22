#Importing Django stuff
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import recent_trades_db
import pandas as pd
import plotly.express as px
from .forms import FilterForm, TurnSectorOnlyOn, DateRangeForm , QuantityCheckBoxForm
from .models import recent_trades_db
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def recent_trades(request):

    # Retrieve data from the database as required by the filtering setup
    form = FilterForm(request.GET or None)
    trades = recent_trades_db.objects.all().order_by('-deal_date')
    formd = DateRangeForm(request.GET or None)

    if formd.is_valid():
        start_date = formd.cleaned_data.get('start_date')
        end_date = formd.cleaned_data.get('end_date')
        
        if start_date and end_date:
            trades = trades.filter(deal_date__range=[start_date, end_date])

    if form.is_valid():
        sector_name = form.cleaned_data.get('sector_name')
        company_name = form.cleaned_data.get('company_name')
        client_name = form.cleaned_data.get('client_name')
        industry_name = form.cleaned_data.get('industry_name')
        deal_type = form.cleaned_data.get('deal_type')

        if deal_type:
            if deal_type == '1':
                print(f'Deal Type = {deal_type}')
                trades = trades.filter(dtype_db=int(deal_type))
            if deal_type == '2':
                print(f'Deal Type = {deal_type}')
                trades = trades.filter(dtype_db=int(deal_type))
  
        if sector_name:
            trades = trades.filter(sector=sector_name)
        if company_name:
            trades = trades.filter(company__icontains=company_name)
        if client_name:
            trades = trades.filter(client_name__icontains=client_name)
        if industry_name:
            trades = trades.filter(industry=industry_name)
    

    paginator = Paginator(trades, 25)  # Show 25 trades per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request, 'institutional_trades/recent_trades.html', {'sector_dropdown_form':form,'added_entries': page_obj,'form_date':formd})


from datetime import datetime, timedelta

@login_required(login_url='login')
def recent_trades_heatmap(request):
    today = datetime.today().date()
    one_year_ago = today - timedelta(days=365)

    # Set initial data for the forms
    initial_data = {
        'start_date': one_year_ago,
        'end_date': today,
        'deal_type': '2',
        'sector_only':True
        # Add other fields with initial values if necessary
    }


    form = DateRangeForm(request.GET or initial_data)
    formf = FilterForm(request.GET or None)
    form_sector_checkbox = TurnSectorOnlyOn(request.GET or initial_data)
    form_quantity_checkbox = QuantityCheckBoxForm(request.GET or None)

    # Default to all trades if no valid dates are provided
    trades = recent_trades_db.objects.all().order_by('-deal_date')

    # Filter by date range if provided
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        if start_date and end_date:
            trades = trades.filter(deal_date__range=[start_date, end_date])

    # Check if sector-only checkbox is selected
    sector_checkbox = form_sector_checkbox.is_valid() and form_sector_checkbox.cleaned_data.get('sector_only')

    
    # Apply other filters only if the form is valid and sector-only is not selected
    if formf.is_valid() and not sector_checkbox:
        sector_name = formf.cleaned_data.get('sector_name')
        company_name = formf.cleaned_data.get('company_name')
        client_name = formf.cleaned_data.get('client_name')
        industry_name = formf.cleaned_data.get('industry_name')
        deal_type = formf.cleaned_data.get('deal_type')

        if deal_type:
            trades = trades.filter(dtype_db=int(deal_type))
        if sector_name:
            trades = trades.filter(sector=sector_name)
        if company_name:
            trades = trades.filter(company__icontains=company_name)
        if client_name:
            trades = trades.filter(client_name__icontains=client_name)
        if industry_name:
            trades = trades.filter(industry=industry_name)

    if form_quantity_checkbox.is_valid():
        quantity_checkbox = form_quantity_checkbox.cleaned_data.get('quantity_checkbox')
    else:
        quantity_checkbox = False
    # Create the data dictionary based on sector checkbox
    data = {
        'Deal Date': [trade.deal_date for trade in trades],
        'Company/Sector': [trade.sector if sector_checkbox else trade.company for trade in trades]
    }

    # Convert to DataFrame and create the heatmap
    if quantity_checkbox:
        data['Value'] = [trade.quantity for trade in trades]
    else:
        data['Value'] = [(trade.price * trade.quantity) for trade in trades]

    df = pd.DataFrame(data)

    if quantity_checkbox:
        heatmap_data = df.groupby(['Deal Date', 'Company/Sector'])['Value'].sum().reset_index(name='Quantity')
        heatmap_pivot = heatmap_data.pivot(index='Deal Date', columns='Company/Sector', values='Quantity').fillna(0)
    else:
        heatmap_data = df.groupby(['Deal Date', 'Company/Sector']).size().reset_index(name='Count')
        heatmap_pivot = heatmap_data.pivot(index='Deal Date', columns='Company/Sector', values='Count').fillna(0)

    fig = px.imshow(
        heatmap_pivot, 
        labels=dict(x="Company/Sector", y="Deal Date", color="Quantity" if quantity_checkbox else "Count"),
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        width=1200,
        height=600
    )
    heatmap_html = fig.to_html(full_html=False)

    return render(request, 'institutional_trades/recent_trades_heatmap.html', {
        'heatmap_html': heatmap_html, 
        'form': form, 
        'formf': formf,
        'sector_checkbox': form_sector_checkbox,
        'form_quantity_checkbox': form_quantity_checkbox,
    })
















































'''INTITAL DB CREATION

from datetime import datetime
import pandas as pd
from .tasks import update_database
import requests
from datetime import timedelta
from io import BytesIO
from django.http import HttpResponse

yesterday = '01/01/2010'
for i in range(8):
    for dtype in [1,2]:
    
        today = (datetime.strptime(yesterday, "%d/%m/%Y")+timedelta(days=365*2)).strftime('%d/%m/%Y')
        print(f'range search: {yesterday}-{today}')

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
        update_database(df, dtype)

    yesterday = today
    if datetime.strptime(yesterday, "%d/%m/%Y")>datetime.today():
        break
    
'''


