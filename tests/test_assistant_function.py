import pytest
import sys

from conftest import TABLE_DATA, HEADER_DATA, CSV_FILE_PATH
from contextlib import nullcontext as does_not_raise
from pathlib import Path
# Добавляем родительскую директорию в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from script import get_csv_data, get_column_index, parse_condition



@pytest.mark.parametrize(
    'path, expectation',
    [
        (CSV_FILE_PATH, does_not_raise()),
        ('incorrect_path', pytest.raises(ValueError))
    ]
)
def test_get_csv_data(path, expectation):
    with expectation:
        result = get_csv_data(path)
        if path == CSV_FILE_PATH:
            assert isinstance(result, list)  # Проверяем, что возвращается список
            assert len(result) > 0  # Проверяем, что список не пустой
            assert result[0] == HEADER_DATA
            assert result[1:] == TABLE_DATA

@pytest.mark.parametrize(
    'data_header, expectation',
    (
        ['price', does_not_raise()],
        ['incorrect_column', pytest.raises(ValueError)]
    )
)
def test_get_column_index(data_header, expectation):
    with expectation:
        result = get_column_index(data_header, HEADER_DATA)
        if data_header in HEADER_DATA:
            assert result == HEADER_DATA.index(data_header)


@pytest.mark.parametrize(
    "condition, expected_result, expectation",
    [
        # Успешные случаи
        ("price>500", ("price", ">", "500"), does_not_raise()),
        ("rating<=4.5", ("rating", "<=", "4.5"), does_not_raise()),
        ("brand=apple", ("brand", "=", "apple"), does_not_raise()),
        ("name_1<test", ("name_1", "<", "test"), does_not_raise()),
        ("col123>=value", ("col123", ">=", "value"), does_not_raise()),

        # Ошибочные случаи
        ("price$500", None, pytest.raises(ValueError)),  # неверный оператор
        ("123>test", None, pytest.raises(ValueError)),  # название колонки начинается с цифры
        ("price>", None, pytest.raises(ValueError)),  # нет значения
        (">500", None, pytest.raises(ValueError)),  # нет названия колонки
        ("", None, pytest.raises(ValueError)),  # пустая строка
        ("test", None, pytest.raises(ValueError)),  # только название колонки
    ]
)
def test_parse_condition(condition, expected_result, expectation):
    with expectation:
        result = parse_condition(condition)
        if expected_result is not None:
            assert result == expected_result