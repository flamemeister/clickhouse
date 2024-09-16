import os
import json
from django.http import JsonResponse
from django.core.files.storage import default_storage
from clickhouse_driver import Client
from django.views.decorators.csrf import csrf_exempt


# Папка для сохранения дампов
DUMP_DIR = 'dumps/'

# Подключение к источнику данных (ClickHouse на порту 9000)
def get_source_client():
    return Client(
        host='clickhouse-source',  
        port=9000,
        user='default',
        password='',
        database='default'
    )

# Подключение к целевой базе данных (ClickHouse на порту 9001)
def get_target_client():
    return Client(
        host='clickhouse-target', 
        port=9000,
        user='default',
        password='',
        database='default'
    )

# Функция для загрузки данных с учётом дельты
from datetime import datetime

def load_data_with_delta(dump_file):
    client = get_target_client()

    # Читаем последнюю дату синхронизации
    last_sync = read_last_sync()

    # Выполняем проверку наличия данных перед вставкой
    command = f"""
    clickhouse-client --query="INSERT INTO test_table
    SELECT * FROM input('id UInt32, event_time DateTime')
    WHERE id NOT IN (SELECT id FROM test_table)
    FORMAT Native" < {dump_file}
    """
    
    # Выполняем команду
    os.system(command)

    # Обновляем последнюю дату синхронизации на текущую
    current_sync = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    write_last_sync(current_sync)

    print(f"Данные из {dump_file} загружены в базу данных.")



# Чтение последней синхронизированной даты из файла
def read_last_sync():
    try:
        with open('last_sync.json', 'r') as f:
            data = json.load(f)
            return data['last_sync']
    except FileNotFoundError:
        return None

# Запись последней синхронизированной даты в файл
def write_last_sync(sync_date):
    with open('last_sync.json', 'w') as f:
        json.dump({'last_sync': sync_date}, f)

# Представление для загрузки дампа через POST-запрос
def upload_dump_view(request):
    if request.method == 'POST' and 'dump_file' in request.FILES:
        dump_file = request.FILES['dump_file']
        
        # Сохраняем загруженный дамп в папку
        file_path = default_storage.save(os.path.join(DUMP_DIR, dump_file.name), dump_file)
        
        # Восстанавливаем данные из дампа в базу
        load_data_with_delta(file_path)

        return JsonResponse({'status': 'success', 'message': 'Дамп успешно загружен и данные восстановлены'})
    
    return JsonResponse({'error': 'Необходимо предоставить файл дампа'}, status=400)

# Представление для создания дампа
def create_dump_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Укажите период: start_date и end_date'}, status=400)

    # Убедимся, что папка существует
    if not os.path.exists(DUMP_DIR):
        os.makedirs(DUMP_DIR)

    dump_file = f"{DUMP_DIR}dump_{start_date}_to_{end_date}.native"
    create_dump(start_date, end_date, dump_file)

    return JsonResponse({'status': 'success', 'dump_file': dump_file})

# Функция для создания дампа данных за указанный период
def create_dump(start_date, end_date, dump_file):
    client = get_source_client()

    # SQL-запрос для извлечения данных за указанный период
    query = f"SELECT * FROM test_table WHERE event_time BETWEEN '{start_date}' AND '{end_date}'"
    
    # Формируем команду для создания дампа в формате Native
    command = f"clickhouse-client --query=\"{query}\" --format Native > {dump_file}"
    os.system(command)

    print(f"Дамп данных за период с {start_date} по {end_date} создан: {dump_file}")

# Представление для загрузки данных с учётом дельты
@csrf_exempt
def load_data_view(request):
    if request.method == 'POST' and 'dump_file' in request.FILES:
        dump_file = request.FILES['dump_file']
        
        # Сохраняем загруженный дамп в папку
        file_path = default_storage.save(os.path.join(DUMP_DIR, dump_file.name), dump_file)
        
        # Восстанавливаем данные из дампа в базу
        load_data_with_delta(file_path)

        return JsonResponse({'status': 'success', 'message': 'Дамп успешно загружен и данные восстановлены'})
    
    return JsonResponse({'error': 'Необходимо предоставить файл дампа'}, status=400)

# Представление для миграции данных за последние 7 дней
def migrate_data(request):
    source_client = get_source_client()
    target_client = get_target_client()

    # Извлекаем данные из источника за последние 7 дней
    query = "SELECT * FROM test_table WHERE event_time >= now() - interval 7 day"
    data = source_client.execute(query)

    if data:
        # Переносим данные в целевую базу данных
        insert_query = "INSERT INTO test_table (id, event_time) VALUES"
        values = ','.join([f"({row[0]}, '{row[1]}')" for row in data])
        target_client.execute(insert_query + values)

        return JsonResponse({'status': 'success', 'transferred_rows': len(data)})
    else:
        return JsonResponse({'status': 'no_data', 'message': 'No data to transfer.'})
