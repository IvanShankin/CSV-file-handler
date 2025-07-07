import os.path
import re
import csv

def get_csv_data(path: str)->list[list[str]]:
    """
    Получает данные из файла .csv
    :param path: путь к файлу
    :return: список данных из этого файла (под индексом 0 хранится заголовок)
    """
    if os.path.isfile(path):
        with open(path, newline='') as csvfile:
            scv_data = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
        return scv_data
    else:
        raise ValueError(f"По пути {path} файл не найден!")

def get_column_index(column: str, headers: list)->int:
    """
    Ищет index колонки по указанному значению
    :param column: необходимая колонка
    :param headers: заголовок по которому будет происходить поиск
    :return: индекс переданной колонки
    :raise ValueError: Если колонка не найдена
    """
    if column not in headers:
        raise ValueError(f"Колонка '{column}' не найдена")
    return headers.index(column) # индекс колонки

def parse_condition(condition: str)->tuple[str, str,str]:
    """Разбирает условие вида 'price>500' на колонку, оператор и значение.
    :param condition: Строка с условием
    :raise ValueError: Если неверный формат условия"""
    match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)([<>=]+)(.+)", condition)
    if not match:
        raise ValueError(f"Неверный формат условия: {condition}")
    return match.groups()
