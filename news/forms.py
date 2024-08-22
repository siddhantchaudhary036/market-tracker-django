from django import forms


class FilterNewsForm(forms.Form):
    subject_filter = forms.ChoiceField(
        choices=[('','All')] + 
        [(subject, subject) for subject in ['Press Release','Financial Results']],
        required=False
    )

    company_name = forms.CharField(required=False,initial="")
    time_filter = forms.ChoiceField(
        choices=[('','All'), ('market_hours', 'During Market Hours')],
        required=False
    )

from django import forms

class ManageWatchlistForm(forms.Form):
    ticker_filter = forms.CharField(
        required=False,
        initial="",
        max_length=1000,
        label="Ticker Symbol",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter ticker symbol',
            'class': 'form-control',
        })
    )
