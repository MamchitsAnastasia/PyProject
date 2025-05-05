from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas import DataFrame, Timestamp

from src.reports import spending_by_category


@pytest.fixture
def sample_transactions() -> DataFrame:
    """Фикстура с тестовыми данными транзакций"""
    return pd.DataFrame(
        {
            "Дата операции": [
                Timestamp("2023-05-01 10:00:00"),
                Timestamp("2023-05-15 14:30:00"),
                Timestamp("2023-05-31 23:59:59"),
            ],
            "Категория": ["Другое", "Еда", "Другое"],
            "Сумма операции": [100, 200, 300],
        }
    )


def test_spending_by_category_success(sample_transactions: DataFrame) -> None:
    """Тест успешного выполнения функции spending_by_category"""
    result = spending_by_category(sample_transactions, "Другое", "2023.05.31 23:59:59")
    assert len(result) == 2
    assert all(result["Категория"] == "Другое")


def test_spending_by_category_empty_result(sample_transactions: DataFrame) -> None:
    """Тест функции spending_by_category без результатов"""
    result = spending_by_category(sample_transactions, "Несуществующая", "2023.05.31 23:59:59")
    assert len(result) == 0


@patch("src.utils.setup_function_logger")
def test_spending_by_category_invalid_date_format(mock_logger: MagicMock, sample_transactions: DataFrame) -> None:
    """Тест функции spending_by_category с некорректным форматом даты"""
    mock_logger.return_value = MagicMock()

    with pytest.raises(
        Exception, match="Ошибка в функции: Некорректный формат даты. Ожидается: 'YYYY.MM.DD HH:MM:SS'"
    ):
        spending_by_category(sample_transactions, "Другое", "2023-05-31")


@patch("src.utils.setup_function_logger")
def test_spending_by_category_empty_category(mock_logger: MagicMock, sample_transactions: DataFrame) -> None:
    """Тест функции spending_by_category с пустой категорией"""
    mock_logger.return_value = MagicMock()

    with pytest.raises(Exception, match="Ошибка в функции: Параметр category не может быть пустой строкой"):
        spending_by_category(sample_transactions, "", "2023.05.31 23:59:59")


@patch("src.utils.setup_function_logger")
def test_spending_by_category_wrong_input_types(mock_logger: MagicMock, sample_transactions: DataFrame) -> None:
    """Тест функции spending_by_category с неправильными типами параметров"""
    mock_logger.return_value = MagicMock()

    with pytest.raises(Exception, match="Ошибка в функции: Параметр transactions_df должен быть pandas DataFrame"):
        spending_by_category("not_a_dataframe", "Другое", "2023.05.31 23:59:59")

    with pytest.raises(Exception, match="Ошибка в функции: Параметр category должен быть строкой"):
        spending_by_category(sample_transactions, 123, "2023.05.31 23:59:59")

    with pytest.raises(Exception, match="Ошибка в функции: Параметр date должен быть строкой или None"):
        spending_by_category(sample_transactions, "Другое", 123)


@patch("src.reports.setup_function_logger")  # Изменяем target на модуль, где применяется декоратор
def test_spending_by_category_logging(mock_logger: MagicMock, sample_transactions: DataFrame) -> None:
    """Тест логирования функции spending_by_category"""
    mock_log = MagicMock()
    mock_logger.return_value = mock_log

    # Вызываем тестируемую функцию
    spending_by_category(sample_transactions, "Другое", "2023.05.31 23:59:59")

    # Проверяем вызовы логгера
    mock_log.info.assert_any_call("Начало выполнения функции с параметрами: category=Другое, date=2023.05.31 23:59:59")
    mock_log.info.assert_any_call("Функция отработала успешно. Найдено транзакций: 2")
