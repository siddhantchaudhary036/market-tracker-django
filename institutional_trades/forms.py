from django import forms
from .models import recent_trades_db

class FilterForm(forms.Form):
    sector_name = forms.ChoiceField(
        choices=[('','All')] + 
        [(sector, sector) for sector in recent_trades_db.objects.values_list('sector', flat=True).distinct()],
        required=False
    )
    industry_name = forms.ChoiceField(
        choices = [("",'All')]+
        [(industry,industry) for industry in recent_trades_db.objects.values_list('industry', flat= True).distinct()],
        required=False
    )
    deal_type = forms.ChoiceField(
        choices = [('2','Block Deals'),("1",'Bulk Deals')]
    )
    company_name = forms.CharField(required=False,initial="")
    client_name = forms.CharField(required= False,initial="")

from datetime import datetime, timedelta
class DateRangeForm(forms.Form):

    start_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}),required=False,initial=datetime.today().date() - timedelta(days=365))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}),required=False, initial=datetime.today().date())

class TurnSectorOnlyOn(forms.Form):
    sector_only = forms.BooleanField(required=False, label='Turn X axis into Sectors',initial=True)

class QuantityCheckBoxForm(forms.Form):
    quantity_checkbox = forms.BooleanField(required=False,label='Turn heatfunction into quantity traded instead of number of deals',initial=False)

