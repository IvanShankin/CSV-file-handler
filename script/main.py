import os
import argparse
import sys

from pathlib import Path
# Добавляем родительскую директорию в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from script.assistant_function import get_csv_data, get_column_index, parse_condition

from typing import Tuple
from tabulate import tabulate

tablefmt="psql"

def get_user_input()-> argparse.Namespace:
    """Принимает данные которые ввёл пользователь"""
    parser = argparse.ArgumentParser(description='Обработка CSV-файла')
    parser.add_argument('file', nargs='?', help='Путь к CSV-файлу')
    parser.add_argument('--where', help='Условие фильтрации (например, "price>500")')
    parser.add_argument('--aggregate', help='Агрегация (например, "price=avg")')
    parser.add_argument('--order-by', help='Сортировка (например, "price=desc")')

    try:
        return parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"Ошибка аргументов: {e}")
        return None

def where_data(table: list, headers: list, condition: str)->list[list[str]]:
    """
    Фильтрует данные по условию.
    :param table: Таблица данных (без заголовков)
    :param headers: Список заголовков таблицы
    :param condition: Строка условия в формате "column=значение" (например, "price=500")
    :return отфильтрованный список
    :raise ValueError: некорректная операция над данными
    """
    col, op, val = parse_condition(condition)

    col_index = get_column_index(col, headers) # индекс колонки по которой происходит фильтрация

    # Определяем, является ли значение условия числом
    try:
        # используется replace т.к. пользователь мог использовать запятую для указания нецелого числа
        val_num = float(val.replace(',', '.'))
        is_num = True
    except ValueError:
        is_num = False

    # для строки разрешаем только оператор сравнения
    if not is_num and op != '=':
        raise ValueError(f"Невозможно применить фильтрацию '{op}' к строковому значению")

    search_result = []
    for row in table:
        cell = row[col_index]

        if not cell:# Пропускаем пустые ячейки
            continue

        if is_num:# Для числового сравнения
            try:
                cell_num = float(cell)
            except ValueError: # Если в столбце строка, а в условии число - ошибка
                if op != '=':
                    raise ValueError(f"Невозможно применить оператор '{op}' для строкового значения в колонке '{col}'")
                continue  # Для оператора '=' просто пропускаем несоответствие

            if op == '=' and cell_num == val_num:
                search_result.append(row)
            elif op == '>' and cell_num > val_num:
                search_result.append(row)
            elif op == '>=' and cell_num >= val_num:
                search_result.append(row)
            elif op == '<' and cell_num < val_num:
                search_result.append(row)
            elif op == '<=' and cell_num <= val_num:
                search_result.append(row)
        else: # Для строкового сравнения
            if op == '=' and cell == val:
                search_result.append(row)

    return search_result

def aggregate_data(table: list, headers: list, target_aggregate: str)->Tuple[list[list[float]], list[str]]:
    """
    Вычисляет агрегатное значение по указанной колонке. Все возможные операции: avg, min, max
    :param table: Таблица данных (без заголовков)
    :param headers: Список заголовков таблицы
    :param target_aggregate: Строка условия в формате "column=func" (например, "price=avg")
    :return Кортеж из (название_колонки, результат_вычислений)
    :raise ValueError: Если колонка не найдена, данные нечисловые или неизвестная функция
    """
    try:
        col, func = target_aggregate.split("=")
    except ValueError:
        raise ValueError(f"Условие '{target_aggregate}' написанно некорректно")

    col_index = get_column_index(col, headers)  # индекс колонки по которой происходит агрегация
    list_to_calculate = []

    try:
        for row in table:
            if row[col_index]:  # Пропускаем пустые значения
                list_to_calculate.append(float(row[col_index]))
    except ValueError:
        raise ValueError(f"Колонка '{col}' содержит нечисловые данные")

    if not list_to_calculate:
        raise ValueError(f"Нет данных для вычисления в колонке '{col}'")

    if func == "avg":
        result = sum(list_to_calculate) / len(list_to_calculate)
    elif func == "min":
        result = min(list_to_calculate)
    elif func == "max":
        result = max(list_to_calculate)
    else:
        raise ValueError(f"Неизвестная агрегатная функция: {func}")

    return ([[result]], [col])

def order_by_data(table: list, headers: list, order_by: str)->list[list[str]]:
    """
        Сортирует данные по указанной колонке
        :param table: Данные (без заголовков)
        :param headers: Заголовки таблицы
        :param order_by: Условие сортировки в формате "column=order" (asc/desc)
        :return Отсортированный список строк
        """
    try:
        col, order = order_by.split("=")
    except ValueError:
        raise ValueError(f"Условие '{order_by}' написанно некорректно")

    col_index = get_column_index(col, headers)  # индекс колонки по которой происходит сортировка

    if order.lower() != 'desc' and order.lower() != 'asc':
        raise ValueError(f"Условия {order} для сортировки не существует")

    reverse = (order.lower() == 'desc') # Будет True если пользователь указал 'desc'

    try: # пробуем отсортировать как число
        return sorted(table,
                      key=lambda x: float(x[col_index]),
                      reverse=reverse)
    except ValueError: # если не получилось, значит работаем как со строкой
        return sorted(table,
                      key=lambda x: x[col_index],
                      reverse=reverse)

def main()->None:
    try:
        user_input = get_user_input()

        if not user_input.file or not os.path.isfile(user_input.file):
            raise ValueError('По указанному пути файла нет!')

        scv_data = get_csv_data(user_input.file)
        headers = scv_data[0]
        table = scv_data[1:]

        if not scv_data or len(scv_data) < 2:
            raise ValueError('В файле нет ни одной записи!')

        if user_input.where:
            table = where_data(table, headers, user_input.where)
        if user_input.aggregate:
            table, headers = aggregate_data(table, headers, user_input.aggregate)
        if user_input.order_by:
            try:
                col = user_input.order_by.split("=")[0]
            except ValueError:
                raise ValueError(f"Условие '{user_input.order_by}' написанно некорректно")

            if not col in headers and user_input.aggregate:
                print(f"Сортировка не будет применена т.к. после агрегации не осталось колонки {col}")
            else:
                table = order_by_data(table, headers, user_input.order_by)

        if table:
            print(tabulate(table, headers=headers, tablefmt=tablefmt)) # если нет условий, то выведется вся таблица
        else:
            print('С данными условиями не найдено ни одного значения!')
            sys.exit(1)

    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()