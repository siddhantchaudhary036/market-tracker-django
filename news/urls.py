from django.urls import path
from . import views

urlpatterns  = [ 

    path('live_news/',views.live_news,name = "live_news"),
    path('live_news/analyse/<id>/',views.live_news_analyse,name='live_news_analyse'),
    path('manage_watchlist/',views.manage_watchlist, name = 'manage_watchlist')
]