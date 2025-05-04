import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.views import main_info
from src.utils import get_time_for_greeting, get_data_time, get_path_and_period, get_card_with_spend, \
    get_top_transactions, get_currency, get_stock_prices


# Фикстуры для тестов
@pytest.fixture
def valid_date():
    return "2023-10-15 12:00:00"


@pytest.fixture
def invalid_date():
    return "2023-13-15 12:00:00"


@pytest.fixture
def mock_data():
    return {
        "greeting": "Добрый день",
        "cards": [{"last_digits": "1234", "total_spent": -1000, "cashback": 10}],
        "top_transactions": [
            {"date": "2023-10-15", "amount": "-5000", "category": "Магазины", "description": "Покупка"}
        ],
        "currency_rates": [{"currency": "USD", "rate": "90.50"}],
        "stock_prices": [{"stock": "AAPL", "price": "175.50"}]
    }


def test_main_info_success(valid_date, mock_data):
    """Тест успешного выполнения функции main_info с корректными входными данными"""

    with patch('src.views.get_time_for_greeting', return_value=mock_data["greeting"]), \
            patch('src.views.get_data_time', return_value=["01.10.2023 00:00:00", "15.10.2023 12:00:00"]), \
            patch('src.views.get_path_and_period', return_value=MagicMock()), \
            patch('src.views.get_card_with_spend', return_value=mock_data["cards"]), \
            patch('src.views.get_top_transactions', return_value=mock_data["top_transactions"]), \
            patch('src.views.get_currency', return_value=mock_data["currency_rates"]), \
            patch('src.views.get_stock_prices', return_value=mock_data["stock_prices"]):
        result = main_info(valid_date)
        result_data = json.loads(result)

        assert isinstance(result, str)
        assert result_data["greeting"] == mock_data["greeting"]
        assert len(result_data["cards"]) == len(mock_data["cards"])
        assert len(result_data["top_transactions"]) == len(mock_data["top_transactions"])
        assert len(result_data["currency_rates"]) == len(mock_data["currency_rates"])
        assert len(result_data["stock_prices"]) == len(mock_data["stock_prices"])


def test_main_info_invalid_date_format():
    """Тест функции main_info на обработку неверного формата даты"""
    invalid_dates = [
        "2023-13-15 12:00:00",  # Несуществующий месяц
        "2023-10-32 12:00:00",  # Несуществующий день
        "2023/10/15 12:00:00",  # Неправильный разделитель
        "15-10-2023 12:00:00",  # Неправильный порядок
        "12:00:00",  # Нет даты
        "",  # Пустая строка
        "invalid-date",  # Полностью неверный формат
    ]

    for invalid_date in invalid_dates:
        with pytest.raises(ValueError):
            main_info(invalid_date)


def test_main_info_file_not_found(valid_date):
    """Тест функции main_info на обработку отсутствия файла"""
    with patch('src.views.get_time_for_greeting', return_value="Добрый день"), \
            patch('src.views.get_data_time', return_value=["01.10.2023 00:00:00", "15.10.2023 12:00:00"]), \
            patch('src.views.get_path_and_period', side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            main_info(valid_date)


def test_main_info_empty_data(valid_date):
    """Тест обработки пустых данных"""
    with patch('src.views.get_time_for_greeting', return_value="Добрый день"), \
            patch('src.views.get_data_time', return_value=["01.10.2023 00:00:00", "15.10.2023 12:00:00"]), \
            patch('src.views.get_path_and_period', return_value=MagicMock()), \
            patch('src.views.get_card_with_spend', return_value=[]), \
            patch('src.views.get_top_transactions', return_value=[]), \
            patch('src.views.get_currency', return_value=[]), \
            patch('src.views.get_stock_prices', return_value=[]):
        result = main_info(valid_date)
        result_data = json.loads(result)

        assert isinstance(result, str)
        assert result_data["cards"] == []
        assert result_data["top_transactions"] == []
        assert result_data["currency_rates"] == []
        assert result_data["stock_prices"] == []


def test_main_info_partial_data(valid_date, mock_data):
    """Тест обработки частичных данных (когда некоторые данные отсутствуют)"""
    partial_mock_data = {
        "greeting": mock_data["greeting"],
        "cards": [],
        "top_transactions": mock_data["top_transactions"],
        "currency_rates": [],
        "stock_prices": mock_data["stock_prices"]
    }

    with patch('src.views.get_time_for_greeting', return_value=partial_mock_data["greeting"]), \
            patch('src.views.get_data_time', return_value=["01.10.2023 00:00:00", "15.10.2023 12:00:00"]), \
            patch('src.views.get_path_and_period', return_value=MagicMock()), \
            patch('src.views.get_card_with_spend', return_value=partial_mock_data["cards"]), \
            patch('src.views.get_top_transactions', return_value=partial_mock_data["top_transactions"]), \
            patch('src.views.get_currency', return_value=partial_mock_data["currency_rates"]), \
            patch('src.views.get_stock_prices', return_value=partial_mock_data["stock_prices"]):
        result = main_info(valid_date)
        result_data = json.loads(result)

        assert isinstance(result, str)
        assert result_data["greeting"] == partial_mock_data["greeting"]
        assert result_data["cards"] == partial_mock_data["cards"]
        assert result_data["top_transactions"] == partial_mock_data["top_transactions"]
        assert result_data["currency_rates"] == partial_mock_data["currency_rates"]
        assert result_data["stock_prices"] == partial_mock_data["stock_prices"]