from unittest.mock import patch

import pandas as pd
import pytest

from src.main import (get_user_date_choice, handle_cashback_report,
                      handle_category_report, is_valid_date, main,
                      print_main_info)


# Фикстуры для тестов
@pytest.fixture
def valid_date():
    return "2021-12-23 23:59:59"


@pytest.fixture
def mock_main_data():
    return {
        "greeting": "Добрый вечер",
        "cards": [{"last_digits": "1234", "total_spent": 1000, "cashback": 10}],
        "top_transactions": [
            {
                "date": "2021-12-15",
                "amount": 500,
                "category": "Магазины",
                "description": "Покупки",
            }
        ],
        "currency_rates": [{"currency": "USD", "rate": "75.50"}],
        "stock_prices": [{"stock": "AAPL", "price": "175.50"}],
    }


def test_is_valid_date_valid():
    """Тест функции is_valid_date c корректной датой"""
    assert is_valid_date("2021", "12", "31") is True


def test_is_valid_date_invalid():
    """Тест функции is_valid_date с некорректной датой"""
    assert is_valid_date("2021", "13", "32") is False


def test_is_valid_date_non_numeric():
    """Тест функции is_valid_date с нечисловыми значениями"""
    assert is_valid_date("year", "month", "day") is False


@patch("builtins.input", side_effect=["1"])
def test_get_user_date_choice_default_date(mock_input, valid_date):
    """Тест функции get_user_date_choice для выбора текущей даты"""
    result = get_user_date_choice(valid_date)
    assert result == "2021.12.23 23:59:59"


@patch("builtins.input", side_effect=["2", "2021", "12", "31"])
def test_get_user_date_choice_custom_date_valid(mock_input, valid_date):
    """Тест функции get_user_date_choice для выбора пользовательской даты (корректный ввод)"""
    result = get_user_date_choice(valid_date)
    assert result == "2021.12.31 23:59:59"


@patch("builtins.input", side_effect=["2", "2021", "13", "31", "2021", "12", "31"])
def test_get_user_date_choice_custom_date_invalid_then_valid(mock_input, valid_date):
    """Тест функции get_user_date_choice для выбора пользовательской даты с исправлением ошибки"""
    result = get_user_date_choice(valid_date)
    assert result == "2021.12.31 23:59:59"


@patch("builtins.input", side_effect=["3", "1"])
def test_get_user_date_choice_invalid_then_valid_option(mock_input, valid_date):
    """Тест функции get_user_date_choice для неверного выбора опции с последующим исправлением"""
    result = get_user_date_choice(valid_date)
    assert result == "2021.12.23 23:59:59"


@patch("src.main.get_user_date_choice", return_value="2021.12.31 23:59:59")
@patch("src.main.spending_by_category")
@patch("builtins.input", return_value="Еда")
def test_handle_category_report_success(
    mock_input, mock_spending, mock_date, valid_date, capsys
):
    """Тест успешного выполнения функции handle_category_report"""
    mock_spending.return_value = pd.DataFrame(
        {"Дата операции": ["2021-12-15"], "Сумма операции": [500], "Категория": ["Еда"]}
    )

    handle_category_report(valid_date)
    captured = capsys.readouterr()
    assert "Расходы по категории 'Еда':" in captured.out


@patch("src.main.get_user_date_choice", return_value="2021.12.31 23:59:59")
@patch("src.main.spending_by_category")
@patch("builtins.input", return_value="Еда")
def test_handle_category_report_empty_result(
    mock_input, mock_spending, mock_date, valid_date, capsys
):
    """Тест функции handle_category_report с пустым результатом"""
    mock_spending.return_value = pd.DataFrame()

    handle_category_report(valid_date)
    captured = capsys.readouterr()
    assert (
        "За данный период операций по этой категории не производилось" in captured.out
    )


@patch("src.main.get_user_date_choice", return_value="2021.12.31 23:59:59")
@patch("src.main.spending_by_category", side_effect=Exception("Test error"))
@patch("builtins.input", return_value="Еда")
def test_handle_category_report_error(
    mock_input, mock_spending, mock_date, valid_date, capsys
):
    """Тест функции handle_category_report с ошибкой"""
    handle_category_report(valid_date)
    captured = capsys.readouterr()
    assert "Ошибка: Test error" in captured.out


@patch("src.main.analyze_cashback_categories")
@patch("builtins.input", side_effect=["2021", "12"])
def test_handle_cashback_report_success(mock_input, mock_analyze, capsys):
    """Тест успешного выполнения функции handle_cashback_report"""
    mock_analyze.return_value = pd.DataFrame({"Категория": ["Еда"], "Кэшбэк": [100]})

    handle_cashback_report()
    captured = capsys.readouterr()
    assert "Наиболее выгодные категории кэшбэка за 12/2021:" in captured.out


@patch("builtins.input", side_effect=["invalid", "invalid", "2021", "13", "2021", "12"])
def test_handle_cashback_report_invalid_input(mock_input, capsys):
    """Тест функции handle_cashback_report с некорректным вводом"""
    handle_cashback_report()
    captured = capsys.readouterr()
    assert "Некорректный год или месяц." in captured.out
    assert "Год и месяц должны быть числами." in captured.out


@patch("src.main.analyze_cashback_categories", side_effect=Exception("Test error"))
@patch("builtins.input", side_effect=["2021", "12"])
def test_handle_cashback_report_error(mock_input, mock_analyze, capsys):
    """Тест функции handle_cashback_report с ошибкой"""
    handle_cashback_report()
    captured = capsys.readouterr()
    assert "Ошибка: Test error" in captured.out


@patch("src.main.get_time_for_greeting", return_value="Добрый вечер")
def test_print_main_info(mock_greeting, mock_main_data, capsys):
    """Тест функции print_main_info"""
    print_main_info(mock_main_data)
    captured = capsys.readouterr()

    assert "Добрый вечер" in captured.out
    assert "Карта ****1234: потрачено 1000, кэшбэк 10" in captured.out
    assert "1. 2021-12-15 - 500 (Магазины/Покупки)" in captured.out
    assert "USD: 75.50 RUB" in captured.out
    assert "AAPL: 175.50 USD" in captured.out


@patch(
    "src.main.main_info",
    return_value='{"greeting": "Добрый день", '
    '"cards": [], '
    '"top_transactions": [], '
    '"currency_rates": [], '
    '"stock_prices": []}',
)
@patch("builtins.input", side_effect=["0"])
def test_main_success_exit(mock_input, mock_main_info, capsys):
    """Тест успешного выполнения функции main с выходом"""
    main()
    captured = capsys.readouterr()
    assert "Выход из программы." in captured.out


@patch("src.main.main_info", side_effect=Exception("Test error"))
def test_main_error(mock_main_info, capsys):
    """Тест функции main с ошибкой"""
    main()
    captured = capsys.readouterr()
    assert "Произошла ошибка: Test error" in captured.out


@patch(
    "src.main.main_info",
    return_value='{"greeting": "Добрый день", '
    '"cards": [], '
    '"top_transactions": [], '
    '"currency_rates": [], '
    '"stock_prices": []}',
)
@patch("builtins.input", side_effect=["3", "0"])
def test_main_invalid_choice(mock_input, mock_main_info, capsys):
    """Тест функции main с неверным выбором опции"""
    main()
    captured = capsys.readouterr()
    assert "Некорректный выбор. Пожалуйста, введите 0, 1 или 2." in captured.out
