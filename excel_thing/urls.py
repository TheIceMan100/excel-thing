from django.urls import path
from .views import index_view  # Or whatever your view name is

urlpatterns = [
    path('', index_view, name='index'),  # Must be a list of paths
]