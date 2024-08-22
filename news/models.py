from django.db import models
import uuid
from django.db import models
import uuid
# Create your models here.

    
class live_news_db(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    report_time = models.DateTimeField()
    company_name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=200, default='Not Available')
    news_id = models.CharField(max_length=200)
    subject = models.CharField(max_length=2000)
    body = models.CharField(max_length=200)
    pdf_url = models.CharField(max_length=500, default='Not Available')
    bse_page_url = models.CharField(max_length=500, default='Not Available')
    full_text = models.TextField(default='')
    sentiment_score = models.FloatField(default=0.0)
    sentiment_label = models.CharField(max_length=50, default='')

    def __str__(self):
        return f"{self.company_name} - {self.news_id} on {self.report_time} {self.pdf_url}"
    



class TaskControl(models.Model):
    ticker = models.CharField(max_length=255, unique=True)
    should_run = models.BooleanField(default=False)


class watchlist_db(models.Model):
    tickers = models.CharField(max_length=20000, default = '')
    user_email = models.CharField(max_length=500, default='')

    def __str__(self):
        return f"{self.tickers} - {self.user_email}"