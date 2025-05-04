from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
from datetime import datetime
from src.services import analyze_cashback_categories
import os


@pytest.fixture
def setup_test_file(tmp_path):
    """Функция создаёт тестовый файл Excel с правильным листом"""
    test_file_path = os.path.join(tmp_path, "test_operations.xlsx")

    data = {
        "Дата операции": ["01.01.2023 12:00:00", "15.01.2023 12:00:00", "01.02.2023 12:00:00"],
        "Сумма операции": [-1000, -2000, -3000],
        "Кэшбэк": [10, 20, 30],
        "Категория": ["Супермаркеты", "Рестораны", "Транспорт"],
        "Сумма операции с округлением": [1000, 2000, 3000]
    }

    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    with pd.ExcelWriter(test_file_path) as writer:
        df.to_excel(writer, sheet_name="Отчет по операциям", index=False)

    return test_file_path


@patch('src.services.get_path_and_period')
@patch('src.services.get_cashback_by_category')
@patch('src.services.get_data_time')
def test_analyze_cashback_categories_success(mock_get_data_time, mock_get_cashback, mock_get_path, setup_test_file):
    """Тест успешного выполнения функции analyze_cashback_categories"""
    # Настройка моков
    mock_get_data_time.return_value = ["01.01.2023 00:00:00", "31.01.2023 23:59:59"]
    mock_get_path.return_value = pd.DataFrame({
        "Дата операции": pd.to_datetime(["01.01.2023 12:00:00"]),
        "Категория": ["Тест"],
        "Кэшбэк": [100]
    })
    mock_get_cashback.return_value = {"Тест": 100}

    # Вызов тестируемой функции
    result = analyze_cashback_categories(setup_test_file, 2023, 1)

    # Проверки
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Кэшбэк" in result.columns
    assert len(result) == 1
    assert result["Кэшбэк"].sum() == 100

    # Проверка вызовов моков
    mock_get_data_time.assert_called_once()
    mock_get_path.assert_called_once()
    mock_get_cashback.assert_called_once()


def test_analyze_cashback_categories_invalid_path():
    """Тест функции analyze_cashback_categories на обработку неверного пути к файлу"""
    with patch('src.services.setup_function_logger'):
        with pytest.raises(Exception) as exc_info:
            analyze_cashback_categories("invalid_path.xlsx", 2023, 1)
        assert "Файл не найден" in str(exc_info.value)


@patch('src.services.setup_function_logger')
def test_analyze_cashback_categories_invalid_year(mock_logger, setup_test_file):
    """Тест функции analyze_cashback_categories на обработку неверного года"""
    mock_logger.return_value = MagicMock()

    with pytest.raises(Exception):
        analyze_cashback_categories(setup_test_file, 1999, 1)  # Год меньше 1957

    with pytest.raises(Exception):
        analyze_cashback_categories(setup_test_file, datetime.now().year + 1, 1)  # Год больше текущего


@patch('src.services.setup_function_logger')
def test_analyze_cashback_categories_invalid_month(mock_logger, setup_test_file):
    """Тест функции analyze_cashback_categories на обработку неверного месяца"""
    mock_logger.return_value = MagicMock()

    with pytest.raises(Exception):
        analyze_cashback_categories(setup_test_file, 2023, 0)  # Месяц меньше 1

    with pytest.raises(Exception):
        analyze_cashback_categories(setup_test_file, 2023, 13)  # Месяц больше 12


def test_analyze_cashback_categories_empty_file(tmp_path):
    """Тест функции analyze_cashback_categories на обработку пустого файла"""
    empty_file_path = os.path.join(tmp_path, "empty.xlsx")
    with pd.ExcelWriter(empty_file_path) as writer:
        pd.DataFrame().to_excel(writer, sheet_name="Отчет по операциям")

    with patch('src.services.setup_function_logger'):
        with pytest.raises(Exception) as exc_info:
            analyze_cashback_categories(empty_file_path, 2023, 1)
        assert "пуст" in str(exc_info.value).lower() or "не найден" in str(exc_info.value).lower()


def test_analyze_cashback_categories_missing_columns(tmp_path):
    """Тест функции analyze_cashback_categories на обработку файла с отсутствующими колонками"""
    invalid_file_path = os.path.join(tmp_path, "invalid.xlsx")
    with pd.ExcelWriter(invalid_file_path) as writer:
        pd.DataFrame({"Некорректная колонка": [1, 2, 3]}).to_excel(
            writer, sheet_name="Отчет по операциям"
        )

    with patch('src.services.setup_function_logger'):
        with pytest.raises(Exception) as exc_info:
            analyze_cashback_categories(invalid_file_path, 2023, 1)
        assert "ошибка при чтении файла" in str(exc_info.value).lower()


@patch('src.services.setup_function_logger')
def test_analyze_cashback_categories_logging(mock_logger, setup_test_file):
    """Тест логирования функции analyze_cashback_categories"""
    mock_logger.return_value = MagicMock()
    mock_logger.return_value.info.return_value = None
    mock_logger.return_value.error.return_value = None

    with patch('src.services.get_path_and_period'), \
            patch('src.services.get_cashback_by_category'), \
            patch('src.services.get_data_time'):
        analyze_cashback_categories(setup_test_file, 2023, 1)

    assert mock_logger.return_value.info.call_count >= 1


@patch('src.services.setup_function_logger')
def test_analyze_cashback_categories_logger_error(mock_logger, setup_test_file):
    """Тест функции analyze_cashback_categories при ошибке инициализации логгера"""
    mock_logger.side_effect = Exception("Logger error")

    with pytest.raises(Exception, match="Logger error"):
        analyze_cashback_categories(setup_test_file, 2023, 1)