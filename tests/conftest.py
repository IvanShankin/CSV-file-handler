import pytest
import sys

from pathlib import Path
# Добавляем родительскую директорию в sys.path
sys.path.append(str(Path(__file__).parent.parent))



HEADER_DATA = ["name", "brand", "price", "rating"]
TABLE_DATA = [
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["galaxy s23 ultra", "samsung", "1199", "4.8"],
                ["galaxy a54", "samsung", "349", "4.2"],
                ["redmi 10c", "xiaomi", "149", "4.1"],
                ["iphone 13 mini", "apple", "599", "4.5"]
             ]

CSV_FILE_PATH = 'products.csv'


@pytest.fixture(scope="function", autouse=True)
def create_csv_file():
    with open(CSV_FILE_PATH, 'w', newline='') as file:
        # Записываем заголовки
        file.write(','.join(HEADER_DATA) + '\n')

        # Записываем данные
        for row in TABLE_DATA:
            file.write(','.join(row) + '\n')
