from django.db import models
import uuid
# Create your models here.

    
class recent_trades_db(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    deal_date = models.DateTimeField()
    security_code = models.IntegerField()
    company = models.CharField(max_length=500)
    client_name = models.CharField(max_length=500)
    deal_type = models.CharField(max_length=10)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    industry = models.CharField(max_length=500,null=True,blank=True)
    sector = models.CharField(max_length=500,null=True,blank=True)
    dtype_db = models.IntegerField(default = 2)
 

    def __str__(self):
        return f"{self.client_name} - {self.company} on {self.deal_date}"