from django.urls import path
from . import views

urlpatterns = [
    # Эндпоинт для создания дампа
    path('create_dump/', views.create_dump_view, name='create_dump'),

    # Эндпоинт для загрузки данных с учётом дельты
    path('load_data/', views.load_data_view, name='load_data'),

    # Эндпоинт для загрузки дампа через POST-запрос
    path('upload_dump/', views.upload_dump_view, name='upload_dump'),

    # Эндпоинт для миграции данных за последние 7 дней
    path('migrate/', views.migrate_data, name='migrate_data'),
]
