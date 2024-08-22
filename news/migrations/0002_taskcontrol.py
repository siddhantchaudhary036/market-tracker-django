# Generated by Django 5.0.7 on 2024-08-02 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskControl',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=255, unique=True)),
                ('should_run', models.BooleanField(default=False)),
            ],
        ),
    ]
