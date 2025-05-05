from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.services import analyze_cashback_categories


@pytest.fixture
def sample_transactions() -> list[dict[str, object]]:
    """Фикстура с тестовыми данными транзакций"""
    return [
        {
            "Дата операции": "2023-01-01 12:00:00",  # Изменен формат даты
            "Сумма операции": -1000,
            "Кэшбэк": 10,
            "Категория": "Супермаркеты",
            "Сумма операции с округлением": 1000,
        },
        {
            "Дата операции": "2023-01-15 12:00:00",  # Изменен формат даты
            "Сумма операции": -2000,
            "Кэшбэк": 20,
            "Категория": "Рестораны",
            "Сумма операции с округлением": 2000,
        },
    ]


@patch("src.services.get_cashback_by_category")
def test_analyze_cashback_categories_success(
    mock_get_cashback: MagicMock, sample_transactions: list[dict[Any, Any]]
) -> None:
    """Тест успешного выполнения функции analyze_cashback_categories"""
    mock_get_cashback.return_value = {"Супермаркеты": 10, "Рестораны": 20}

    result = analyze_cashback_categories(sample_transactions, 2023, 1)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Кэшбэк" in result.columns
    assert len(result) == 2


def test_analyze_cashback_categories_invalid_input() -> None:
    """Тест функции с неверными входными данными"""
    with patch("src.services.setup_function_logger"):
        with pytest.raises(Exception, match="Ошибка в функции: Параметр transactions должен быть списком словарей"):
            analyze_cashback_categories("not_a_list", 2023, 1)  # type: ignore

        with pytest.raises(Exception, match="Ошибка в функции: Некорректный год"):
            analyze_cashback_categories([{"key": "value"}], "not_an_int", 1)  # type: ignore

        with pytest.raises(Exception, match="Ошибка в функции: Некорректный месяц"):
            analyze_cashback_categories([{"key": "value"}], 2023, "not_an_int")  # type: ignore


@patch("src.services.setup_function_logger")
@patch("src.services.get_cashback_by_category")
def test_analyze_cashback_categories_invalid_year(
    mock_get_cashback: MagicMock, mock_logger: MagicMock, sample_transactions: list[dict[Any, Any]]
) -> None:
    """Тест функции с неверным годом"""
    mock_logger.return_value = MagicMock()
    mock_get_cashback.return_value = {}

    current_year = datetime.now().year

    # Проверяем год меньше 1957
    with pytest.raises(Exception) as exc_info:
        analyze_cashback_categories(sample_transactions, 1956, 1)
    assert "Некорректный год. Должен быть целым числом между 1957 и текущим годом" in str(exc_info.value)

    # Проверяем год больше текущего
    with pytest.raises(Exception) as exc_info:
        analyze_cashback_categories(sample_transactions, current_year + 1, 1)
    assert "Некорректный год. Должен быть целым числом между 1957 и текущим годом" in str(exc_info.value)


@patch("src.services.setup_function_logger")
@patch("src.services.get_cashback_by_category")
def test_analyze_cashback_categories_invalid_month(
    mock_get_cashback: MagicMock, mock_logger: MagicMock, sample_transactions: list[dict[Any, Any]]
) -> None:
    """Тест функции с неверным месяцем"""
    mock_logger.return_value = MagicMock()
    mock_get_cashback.return_value = {}  # Добавляем мок для get_cashback_by_category

    with pytest.raises(Exception, match="Ошибка в функции: Некорректный месяц. Должен быть целым числом от 1 до 12"):
        analyze_cashback_categories(sample_transactions, 2023, 0)

    with pytest.raises(Exception, match="Ошибка в функции: Некорректный месяц. Должен быть целым числом от 1 до 12"):
        analyze_cashback_categories(sample_transactions, 2023, 13)


@patch("src.services.setup_function_logger")
def test_analyze_cashback_categories_missing_columns(mock_logger: MagicMock) -> None:
    """Тест функции с отсутствующими колонками"""
    mock_logger.return_value = MagicMock()
    invalid_transactions = [{"Некорректная_колонка": "значение"}]

    with pytest.raises(Exception):
        analyze_cashback_categories(invalid_transactions, 2023, 1)


@patch("src.services.setup_function_logger")
def test_analyze_cashback_categories_logging(
    mock_logger: MagicMock, sample_transactions: list[dict[Any, Any]]
) -> None:
    """Тест логирования функции"""
    mock_logger.return_value = MagicMock()
    mock_logger.return_value.info = MagicMock()

    with patch("src.services.get_cashback_by_category"):
        analyze_cashback_categories(sample_transactions, 2023, 1)

    mock_logger.return_value.info.assert_called()
