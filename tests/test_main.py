import pytest
import sys

from conftest import TABLE_DATA, HEADER_DATA, CSV_FILE_PATH
from contextlib import nullcontext as does_not_raise
from pathlib import Path
# Добавляем родительскую директорию в sys.path
sys.path.append(str(Path(__file__).parent.parent))
from script import get_user_input, where_data, aggregate_data, order_by_data, main

@pytest.mark.parametrize(
    "input_args, expected_file, expected_where, expected_aggregate, expected_order_by",
    [
        (["script.py"], None, None, None, None),

        (["script.py", CSV_FILE_PATH], CSV_FILE_PATH, None, None, None),

        (["script.py", CSV_FILE_PATH, "--where", "price>500"], CSV_FILE_PATH, "price>500", None, None),

        (["script.py", CSV_FILE_PATH, "--where", "price>500", "--aggregate", "price=avg"],
         CSV_FILE_PATH, "price>500", "price=avg", None),

        (["script.py", CSV_FILE_PATH, "--where", "price>500", "--aggregate", "price=avg", "--order-by", "price=desc"],
         CSV_FILE_PATH, "price>500", "price=avg", "price=desc"),
    ],
)
def test_get_user_input(input_args, expected_file, expected_where, expected_aggregate, expected_order_by, monkeypatch):
    monkeypatch.setattr("sys.argv", input_args)
    args = get_user_input()
    assert args.file == expected_file
    assert args.where == expected_where
    assert args.aggregate == expected_aggregate
    assert args.order_by == expected_order_by

@pytest.mark.parametrize(
    "condition, res, expectation",
    [
        (
            "price>500", # условие
            [ # результат
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["galaxy s23 ultra", "samsung", "1199", "4.8"],
                ["iphone 13 mini", "apple", "599", "4.5"]
            ],
            does_not_raise()
        ),

        (
            "rating<4.5", # условие
            [ # результат
                ["galaxy a54", "samsung", "349", "4.2"],
                ["redmi 10c", "xiaomi", "149", "4.1"],
            ],
            does_not_raise()
        ),

        (
            "brand=apple", # условие
            [ # результат
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["iphone 13 mini", "apple", "599", "4.5"]
            ],
            does_not_raise()
        ),

        (
            "price<150", # условие
            [["redmi 10c", "xiaomi", "149", "4.1"]], # результат
            does_not_raise()
        ),

        ("price<0",[], does_not_raise()),

        ("price<apple",None, pytest.raises(ValueError)), # ошибка: нельзя использовать < для строки

        ("brand<1200",None, pytest.raises(ValueError) ), # ошибка: нельзя отфильтровать строку по числовому значению

        ("price$apple",None, pytest.raises(ValueError)), # ошибка: неверное условие

        ("test_header>apple", None, pytest.raises(ValueError)),  # ошибка: некорректный столбец
    ]
)
def test_where_data(condition, res, expectation):
    with expectation:
        assert where_data(TABLE_DATA, HEADER_DATA, condition) == res


@pytest.mark.parametrize(
    "target_aggregate, res, expectation",
    [
        ("price=avg", [[659.0]], does_not_raise()),# результат: среднее значение
        ("price=min", [[149.0]], does_not_raise()),# результат: минимальная цена
        ("price=max", [[1199.0]], does_not_raise()),# результат: максимальная цена

        ("unknown=avg", None, pytest.raises(ValueError)), # ошибка: колонка не найдена
        ("brand=avg", None,pytest.raises(ValueError)),# ошибка: нечисловые данные
        ("price=unknown", None, pytest.raises(ValueError)),# ошибка: неизвестная агрегатная функция
    ]
)
def test_aggregate_data(target_aggregate, res, expectation):
    with expectation:
        result, _ = aggregate_data(TABLE_DATA, HEADER_DATA, target_aggregate)
        assert result == res


@pytest.mark.parametrize(
    "order_by, expected_result, expectation",
    [
        # Сортировка по числовым значениям
        (
            "price=asc",
            [
                ["redmi 10c", "xiaomi", "149", "4.1"],
                ["galaxy a54", "samsung", "349", "4.2"],
                ["iphone 13 mini", "apple", "599", "4.5"],
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["galaxy s23 ultra", "samsung", "1199", "4.8"]
            ],
            does_not_raise()
        ),
        (
            "price=desc",
            [
                ["galaxy s23 ultra", "samsung", "1199", "4.8"],
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["iphone 13 mini", "apple", "599", "4.5"],
                ["galaxy a54", "samsung", "349", "4.2"],
                ["redmi 10c", "xiaomi", "149", "4.1"]
            ],
            does_not_raise()
        ),

        # Сортировка по строковым значениям
        (
            "brand=asc",
            [
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["iphone 13 mini", "apple", "599", "4.5"],
                ["galaxy s23 ultra", "samsung", "1199", "4.8"],
                ["galaxy a54", "samsung", "349", "4.2"],
                ["redmi 10c", "xiaomi", "149", "4.1"]
            ],
            does_not_raise()
        ),
        (
            "brand=desc",
            [
                ["redmi 10c", "xiaomi", "149", "4.1"],
                ["galaxy s23 ultra", "samsung", "1199", "4.8"],
                ["galaxy a54", "samsung", "349", "4.2"],
                ["iphone 15 pro", "apple", "999", "4.9"],
                ["iphone 13 mini", "apple", "599", "4.5"]
            ],
            does_not_raise()
        ),

        # Ошибочные случаи
        ("unknown=asc", None, pytest.raises(ValueError)),  # Несуществующий столбец
        ("price=invalid", None, pytest.raises(ValueError))  # Неправильный порядок
    ]
)
def test_order_by_data(order_by, expected_result, expectation):
    with expectation:
        result = order_by_data(TABLE_DATA, HEADER_DATA, order_by)
        if expected_result is not None:
            assert result == expected_result


@pytest.mark.parametrize(
    "input_args, expected_lines",
    [
        # Вывод всей таблицы
        (
            ["script.py", CSV_FILE_PATH],
            (
                '+------------------+---------+---------+----------+\n'
                '| name             | brand   |   price |   rating |\n'
                '|------------------+---------+---------+----------|\n'
                '| iphone 15 pro    | apple   |     999 |      4.9 |\n'
                '| galaxy s23 ultra | samsung |    1199 |      4.8 |\n'
                '| galaxy a54       | samsung |     349 |      4.2 |\n'
                '| redmi 10c        | xiaomi  |     149 |      4.1 |\n'
                '| iphone 13 mini   | apple   |     599 |      4.5 |\n'
                '+------------------+---------+---------+----------+\n'
            )
        ),

        # Фильтрация
        (
            ["script.py", CSV_FILE_PATH, "--where", "price>500"],
            (
                '+------------------+---------+---------+----------+\n'
                '| name             | brand   |   price |   rating |\n'
                '|------------------+---------+---------+----------|\n'
                '| iphone 15 pro    | apple   |     999 |      4.9 |\n'
                '| galaxy s23 ultra | samsung |    1199 |      4.8 |\n'
                '| iphone 13 mini   | apple   |     599 |      4.5 |\n'
                '+------------------+---------+---------+----------+\n'
            )
        ),

        # Агрегация
        (
            ["script.py", CSV_FILE_PATH, "--aggregate", "price=avg"],
            (
                '+---------+\n'
                '|   price |\n'
                '|---------|\n'
                '|     659 |\n'
                '+---------+\n'
            )
        ),

        # Сортировка по убыванию цены
        (
            ["script.py", CSV_FILE_PATH, "--order-by", "price=desc"],
            (
                '+------------------+---------+---------+----------+\n'
                '| name             | brand   |   price |   rating |\n'
                '|------------------+---------+---------+----------|\n'
                '| galaxy s23 ultra | samsung |    1199 |      4.8 |\n'
                '| iphone 15 pro    | apple   |     999 |      4.9 |\n'
                '| iphone 13 mini   | apple   |     599 |      4.5 |\n'
                '| galaxy a54       | samsung |     349 |      4.2 |\n'
                '| redmi 10c        | xiaomi  |     149 |      4.1 |\n'
                '+------------------+---------+---------+----------+\n'
            )
        ),

        # Фильтрация + сортировка (цена > 500, сортировка по возрастанию рейтинга)
        (
            ["script.py", CSV_FILE_PATH, "--where", "price>500", "--order-by", "rating=asc"],
            (
                '+------------------+---------+---------+----------+\n'
                '| name             | brand   |   price |   rating |\n'
                '|------------------+---------+---------+----------|\n'
                '| iphone 13 mini   | apple   |     599 |      4.5 |\n'
                '| galaxy s23 ultra | samsung |    1199 |      4.8 |\n'
                '| iphone 15 pro    | apple   |     999 |      4.9 |\n'
                '+------------------+---------+---------+----------+\n'
            )
        ),

        # Фильтрация + агрегация (бренд = apple, средняя цена)
        (
            ["script.py", CSV_FILE_PATH, "--where", "brand=apple", "--aggregate", "price=avg"],
            (
                '+---------+\n'
                '|   price |\n'
                '|---------|\n'
                '|     799 |\n'
                '+---------+\n'
            )
        ),

        # Комбинация всех условий (фильтрация + сортировка + агрегация)
        (
            ["script.py", CSV_FILE_PATH, "--where", "rating>4.1", "--order-by", "price=asc", "--aggregate",
             "price=max"],
            (
                '+---------+\n'
                '|   price |\n'
                '|---------|\n'
                '|    1199 |\n'
                '+---------+\n'
            )
        )
    ]
)
def test_main_success(input_args, expected_lines, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", input_args)
    main()
    captured = capsys.readouterr()
    assert expected_lines == captured.out


@pytest.mark.parametrize(
    "input_args, expected_message",
    [
        (["script.py", "missing.csv"], "Ошибка: По указанному пути файла нет!"),
        (["script.py", CSV_FILE_PATH, "--where", "price>9999"], "С данными условиями не найдено ни одного значения!")
    ]
)
def test_main_errors(input_args, expected_message, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", input_args)

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert expected_message in captured.out  # сравниваем ожидаемый результат и фактический вывод