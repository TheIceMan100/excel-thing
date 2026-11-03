from django.urls import path
from .views import index_view, upload_demand, upload_inventory

urlpatterns = [
    path('', index_view, name='index'),
    path('upload/demand/', upload_demand, name='upload_demand'),
    path('upload/inventory/', upload_inventory, name='upload_inventory'),
]