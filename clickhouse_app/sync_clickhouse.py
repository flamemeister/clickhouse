from django.core.management.base import BaseCommand
from clickhouse_driver import Client

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

class Command(BaseCommand):
    help = 'Transfer data from source ClickHouse to target ClickHouse'

    def handle(self, *args, **kwargs):
        source_client = get_source_client()
        target_client = get_target_client()

        # Извлекаем данные из источника за последние 7 дней
        query = "SELECT * FROM test_table WHERE event_time >= now() - interval 7 day"
        data = source_client.execute(query)

        # Если данные есть, вставляем их в целевую базу
        if data:
            insert_query = "INSERT INTO test_table (id, event_time) VALUES"
            values = ','.join([f"({row[0]}, '{row[1]}')" for row in data])
            target_client.execute(insert_query + values)

            self.stdout.write(self.style.SUCCESS(f'Successfully transferred {len(data)} rows from source to target.'))
        else:
            self.stdout.write(self.style.WARNING('No data to transfer.'))
