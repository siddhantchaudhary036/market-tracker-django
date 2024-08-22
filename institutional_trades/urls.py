from django.urls import path
from . import views

urlpatterns  = [ 
    path('recent_trades/',views.recent_trades,name = "recent_trades"),
    path('recent_trades_heatmap/',views.recent_trades_heatmap,name = "recent_trades_heatmap"),

]