from django.urls import path
from . import views

urlpatterns = [
    path('migrate/', views.migrate_data, name='migrate_data'),  # URL для миграции данных
]
