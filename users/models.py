from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Profiles(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True,null=True)
    email = models.EmailField(max_length=500, blank=True,null=True)
    phone = models.CharField(max_length=100, blank=True,null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


    def __str__(self):
        return self.email
    