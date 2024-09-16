from django.http import JsonResponse
from clickhouse_driver import Client

# Подключение к источнику данных (ClickHouse на порту 9000)
def get_source_client():
    return Client(
        host='clickhouse-source',  # или укажи IP контейнера
        port=9000,
        user='default',
        password='',
        database='default'
    )

# Подключение к целевой базе данных (ClickHouse на порту 9001)
def get_target_client():
    return Client(
        host='clickhouse-target',  # или укажи IP контейнера
        port=9000,
        user='default',
        password='',
        database='default'
    )

# Представление для переноса данных
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
