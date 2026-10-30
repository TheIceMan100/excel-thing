from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('excel_thing.urls')),  # Must be a string inside include(), NOT an imported module object
]