import json
import logging
import os
from logging import Handler
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.utils import (
    get_card_with_spend,
    get_cashback_by_category,
    get_currency,
    get_data_time,
    get_path_and_period,
    get_stock_prices,
    get_time_for_greeting,
    get_top_transactions,
    setup_function_logger,
)


def test_setup_function_logger_success(tmpdir: Any) -> None:
    """Тест функции setup_function_logger для успешного создания логгера"""
    with patch("os.makedirs"), patch("logging.FileHandler"):
        logger = setup_function_logger("test_function")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_function"
        assert logger.level == logging.DEBUG


def test_setup_function_logger_directory_creation(tmpdir: Any) -> None:
    """Тест функции setup_function_logger для создания директории для логов"""
    test_dir = tmpdir.mkdir("test_logs")
    with patch("os.path.join", return_value=str(test_dir)):
        with patch("logging.FileHandler"):
            setup_function_logger("test_function")
            assert os.path.exists(str(test_dir))


def test_setup_function_logger_mocked() -> None:
    """Тест функции setup_function_logger для создания файла лога (без проверки файла)"""
    with (
        patch("logging.getLogger") as mock_get_logger,
        patch("logging.FileHandler") as mock_file_handler,
        patch("logging.Formatter") as mock_formatter,
    ):
        # Настраиваю мок-логгер
        mock_logger = MagicMock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        # Настраиваю мок-обработчик
        mock_handler_instance = MagicMock(spec=Handler)
        mock_file_handler.return_value = mock_handler_instance

        # Настраиваю мок-форматтер
        mock_formatter_instance = MagicMock()
        mock_formatter.return_value = mock_formatter_instance

        # Вызываю тестируемую функцию
        setup_function_logger("test_function")

        # Проверяю вызовы ПОСЛЕ выполнения функции
        mock_file_handler.assert_called_once()
        mock_formatter.assert_called_once_with("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        mock_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)
        mock_logger.addHandler.assert_called_once_with(mock_handler_instance)
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)


def test_setup_function_logger_existing_logger() -> None:
    """Тест функции setup_function_logger для получения существующего логгера"""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = logging.getLogger("existing_function")
        mock_get_logger.return_value = mock_logger

        logger = setup_function_logger("existing_function")
        assert logger is mock_logger


def test_get_time_for_greeting_morning() -> None:
    """Тест функции get_time_for_greeting для утреннего приветствия"""
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 8
        assert get_time_for_greeting() == "Доброе утро"


def test_get_time_for_greeting_afternoon() -> None:
    """Тест функции get_time_for_greeting для дневного приветствия"""
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 14
        assert get_time_for_greeting() == "Добрый день"


def test_get_time_for_greeting_evening() -> None:
    """Тест функции get_time_for_greeting для вечернего приветствия"""
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 19
        assert get_time_for_greeting() == "Добрый вечер"


def test_get_time_for_greeting_night() -> None:
    """Тест функции get_time_for_greeting для ночного приветствия"""
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 23
        assert get_time_for_greeting() == "Доброй ночи"


def test_get_time_for_greeting_edge_cases() -> None:
    """Тест функции get_time_for_greeting для граничных значений"""
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 5
        assert get_time_for_greeting() == "Доброе утро"

        mock_datetime.now.return_value.hour = 12
        assert get_time_for_greeting() == "Добрый день"

        mock_datetime.now.return_value.hour = 18
        assert get_time_for_greeting() == "Добрый вечер"

        mock_datetime.now.return_value.hour = 22
        assert get_time_for_greeting() == "Доброй ночи"


def test_get_time_for_greeting_logger_error() -> None:
    """Тест функции get_time_for_greeting при ошибке инициализации логгера"""
    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception, match="Ошибка инициализации логгера: Logger error"):
            get_time_for_greeting()


def test_get_time_for_greeting_time_error() -> None:
    """Тест функции get_time_for_greeting при ошибке при определении времени"""
    with patch("src.utils.setup_function_logger") as mock_logger:
        mock_logger.return_value.info.return_value = None
        mock_logger.return_value.error.return_value = None

        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = "invalid"

        with patch("src.utils.datetime", mock_datetime):
            with pytest.raises(
                Exception,
                match="Ошибка инициализации логгера: "
                "Ошибка при определении времени: "
                "Невозможно определить текущий час",
            ):
                get_time_for_greeting()


def test_get_time_for_greeting_logging(tmpdir: Any) -> None:
    """Тест функции get_time_for_greeting для записи в лог"""
    logger_mock = MagicMock()
    logger_mock.info.return_value = None

    with (
        patch("src.utils.setup_function_logger", return_value=logger_mock),
        patch("src.utils.datetime") as mock_datetime,
    ):
        mock_datetime.now.return_value.hour = 10  # Утро (чтобы функция отработала)
        get_time_for_greeting()
        assert logger_mock.info.call_count >= 2


def test_get_data_time_success() -> None:
    """Тест функции get_data_time для успешного выполнения функции"""
    test_date = "2023-05-15 14:30:00"
    result = get_data_time(test_date)
    assert len(result) == 2
    assert result[0] == "01.05.2023 14:30:00"
    assert result[1] == "15.05.2023 14:30:00"


def test_get_data_time_invalid_date() -> None:
    """Тест функции get_data_time с некорректной датой"""
    with pytest.raises(ValueError, match="day is out of range for month"):
        get_data_time("2023-02-30 00:00:00")  # Несуществующая дата


def test_get_data_time_invalid_format() -> None:
    """Тест функции get_data_time с некорректным форматом"""
    with pytest.raises(ValueError, match="unconverted data remains"):
        get_data_time("2023-05-15", "%Y-%m")  # Неполный формат


def test_get_data_time_empty_string() -> None:
    """Тест функции get_data_time с пустой строкой"""
    with pytest.raises(ValueError, match="Параметры не могут быть пустыми строками"):
        get_data_time("", "%Y-%m-%d")


def test_get_data_time_wrong_types() -> None:
    """Тест функции get_data_time с неправильными типами параметров"""
    with pytest.raises(TypeError, match="Параметр date_time должен быть строкой"):
        get_data_time(12345)  # type: ignore[arg-type]
        # Число вместо строки
    with pytest.raises(TypeError, match="Параметр date_format должен быть строкой"):
        get_data_time("2023-05-15", 123)  # type: ignore[arg-type]
        # Число вместо формата


def test_get_data_time_edge_cases() -> None:
    """Тест функции get_data_time для граничных случаев"""
    # Первое число месяца
    assert get_data_time("2023-05-01 00:00:00")[0] == "01.05.2023 00:00:00"
    # Последний день месяца
    assert get_data_time("2023-04-30 23:59:59")[1] == "30.04.2023 23:59:59"
    # Високосный год
    assert get_data_time("2020-02-29 12:00:00")[1] == "29.02.2020 12:00:00"


@patch("src.utils.setup_function_logger")
def test_get_data_time_logging(mock_logger: MagicMock) -> None:
    """Тест функции get_data_time для логирования"""
    mock_logger.return_value = logging.getLogger("test")
    with patch.object(mock_logger.return_value, "info") as mock_info:
        get_data_time("2023-05-15 14:30:00")
        assert mock_info.call_count == 2


def test_get_data_time_logger_error() -> None:
    """Тест функции get_data_time при ошибке инициализации логгера"""
    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception, match="Ошибка в функции: Logger error"):
            get_data_time("2023-05-15 14:30:00")


def test_get_path_and_period_success(tmpdir: Any) -> None:
    """Тест успешного выполнения функции get_path_and_period"""
    # Создаем тестовый файл
    test_file = tmpdir.join("test.xlsx")
    df = pd.DataFrame(
        {
            "Дата операции": [
                "01.05.2023 10:00:00",
                "15.05.2023 14:30:00",
                "31.05.2023 23:59:59",
            ],
            "Сумма": [100, 200, 300],
        }
    )
    df.to_excel(test_file, sheet_name="Отчет по операциям", index=False)

    result = get_path_and_period(str(test_file), ["01.05.2023 00:00:00", "31.05.2023 23:59:59"])
    assert len(result) == 3
    assert result["Дата операции"].iloc[0].strftime("%d.%m.%Y %H:%M:%S") == "01.05.2023 10:00:00"


def test_get_path_and_period_filtered(tmpdir: Any) -> None:
    """Тест функции get_path_and_period для фильтрации по периоду"""
    test_file = tmpdir.join("test.xlsx")
    df = pd.DataFrame(
        {
            "Дата операции": ["01.05.2023", "15.05.2023", "31.05.2023"],
            "Сумма": [100, 200, 300],
        }
    )
    df.to_excel(test_file, sheet_name="Отчет по операциям", index=False)

    result = get_path_and_period(str(test_file), ["10.05.2023 00:00:00", "20.05.2023 23:59:59"])
    assert len(result) == 1
    assert result["Дата операции"].iloc[0].strftime("%d.%m.%Y") == "15.05.2023"


def test_get_path_and_period_file_not_found() -> None:
    """Тест функции get_path_and_period с несуществующим файлом"""
    with pytest.raises(Exception):
        get_path_and_period("nonexistent_file.xlsx", ["01.01.2023 00:00:00", "31.12.2023 23:59:59"])


def test_get_path_and_period_invalid_period(tmpdir: Any) -> None:
    """Тест функции get_path_and_period с некорректным периодом"""
    test_file = tmpdir.join("test.xlsx")
    pd.DataFrame().to_excel(test_file)

    with pytest.raises(Exception):
        # Неправильный формат даты
        get_path_and_period(str(test_file), ["01-01-2023", "31-12-2023"])

    with pytest.raises(Exception):
        # Начальная дата больше конечной
        get_path_and_period(str(test_file), ["31.12.2023 23:59:59", "01.01.2023 00:00:00"])


def test_get_path_and_period_missing_column(tmpdir: Any) -> None:
    """Тест функции get_path_and_period с отсутствующей колонкой"""
    test_file = tmpdir.join("test.xlsx")
    pd.DataFrame({"Неправильная колонка": [1, 2, 3]}).to_excel(test_file)

    with pytest.raises(Exception):
        get_path_and_period(str(test_file), ["01.01.2023 00:00:00", "31.12.2023 23:59:59"])


def test_get_path_and_period_empty_file(tmpdir: Any) -> None:
    """Тест функции get_path_and_period с пустым файлом"""
    test_file = tmpdir.join("test.xlsx")
    pd.DataFrame().to_excel(test_file)

    with pytest.raises(Exception):
        get_path_and_period(str(test_file), ["01.01.2023 00:00:00", "31.12.2023 23:59:59"])


def test_get_path_and_period_wrong_types() -> None:
    """Тест функции get_path_and_period с неправильными типами параметров"""
    with pytest.raises(Exception):
        get_path_and_period(123, ["01.01.2023", "31.12.2023"])  # type: ignore[arg-type]
        # Число вместо строки
    with pytest.raises(Exception):
        get_path_and_period("test.xlsx", "not_a_list")  # type: ignore[arg-type]
        # Строка вместо списка
    with pytest.raises(Exception):
        get_path_and_period("test.xlsx", [123, 456])  # type: ignore[arg-type]
        # Числа вместо дат


@patch("os.path.exists")
@patch("pandas.read_excel")
def test_get_path_and_period_logging(mock_read: MagicMock, mock_exists: MagicMock, tmpdir: Any) -> None:
    """Тест логирования функции get_path_and_period"""
    test_file = tmpdir.join("test.xlsx")

    mock_exists.return_value = True
    mock_read.return_value = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["01.05.2023"]),
            "Сумма операции": [100],
            "Кэшбэк": [1],
            "Сумма операции с округлением": [100],
        }
    )

    with patch("src.utils.setup_function_logger") as mock_logger:
        mock_logger.return_value = logging.getLogger("test")
        with patch.object(mock_logger.return_value, "info") as mock_info:
            result = get_path_and_period(str(test_file), ["01.05.2023 00:00:00", "01.05.2023 23:59:59"])
            assert isinstance(result, pd.DataFrame)
            assert mock_info.call_count == 2


def test_get_path_and_period_logger_error(tmpdir: Any) -> None:
    """Тест функции get_path_and_period при ошибке инициализации логгера"""
    test_file = tmpdir.join("test.xlsx")
    pd.DataFrame().to_excel(test_file)

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_path_and_period(str(test_file), ["01.01.2023 00:00:00", "31.12.2023 23:59:59"])


def test_get_card_with_spend_success() -> None:
    """Тест успешного выполнения функции get_card_with_spend"""
    test_data = {
        "Номер карты": ["*5678", "*4321"],
        "Сумма операции": [-100.0, -200.0],
        "Кэшбэк": [1.0, 2.0],
        "Сумма операции с округлением": [100.0, 200.0],
    }
    df = pd.DataFrame(test_data)

    result = get_card_with_spend(df)
    assert len(result) == 2
    assert result[0]["last_digits"] == "5678"
    assert result[0]["total_spent"] == 100.0
    assert result[0]["cashback"] == 1.0


def test_get_card_with_spend_no_spend_transactions() -> None:
    """Тест функции get_card_with_spend без расходных транзакций"""
    test_data = {
        "Номер карты": ["*5678"],
        "Сумма операции": [100.0],
        "Кэшбэк": [1.0],
        "Сумма операции с округлением": [100.0],
    }
    df = pd.DataFrame(test_data)

    result = get_card_with_spend(df)
    assert len(result) == 0


def test_get_card_with_spend_empty_dataframe() -> None:
    """Тест функции get_card_with_spend с пустым DataFrame"""
    df = pd.DataFrame()
    with pytest.raises(Exception, match="Входной DataFrame не может быть пустым"):
        get_card_with_spend(df)


def test_get_card_with_spend_missing_columns() -> None:
    """Тест функции get_card_with_spend с отсутствующими колонками"""
    test_data = {"Номер карты": ["*5678"], "Сумма операции": [-100.0]}
    df = pd.DataFrame(test_data)
    with pytest.raises(Exception):
        get_card_with_spend(df)


def test_get_card_with_spend_wrong_input_type() -> None:
    """Тест функции get_card_with_spend с неправильным типом входных данных"""
    with pytest.raises(Exception):
        get_card_with_spend("not a dataframe")  # type: ignore[arg-type]
        # Передаем строку вместо DataFrame


def test_get_card_with_spend_cashback_calculation() -> None:
    """Тест функции get_card_with_spend на правильность расчета кэшбэка"""
    test_data = {
        "Номер карты": ["*5678"],
        "Сумма операции": [-150.0],
        "Кэшбэк": [1.5],
        "Сумма операции с округлением": [150.0],
    }
    df = pd.DataFrame(test_data)

    result = get_card_with_spend(df)
    assert result[0]["cashback"] == 1  # 150 // 100 = 1


def test_get_card_with_spend_row_error_handling() -> None:
    """Тест функции get_card_with_spend для обработки ошибок в отдельных строках"""
    test_data = {
        "Номер карты": ["*5678", "invalid"],
        "Сумма операции": [
            -100.0,
            "not a number",
        ],  # Некорректные данные во второй строке
        "Кэшбэк": [1.0, 2.0],
        "Сумма операции с округлением": [100.0, 200.0],
    }
    df = pd.DataFrame(test_data)

    with patch("logging.Logger.warning") as mock_warning:
        result = get_card_with_spend(df)
        assert len(result) == 1  # Только одна корректная транзакция
        assert mock_warning.call_count >= 1  # Должно быть предупреждение об ошибке


@patch("src.utils.setup_function_logger")
def test_get_card_with_spend_logging(mock_logger: MagicMock) -> None:
    """Тест логирования функции get_card_with_spend"""
    test_data = {
        "Номер карты": ["*5678"],
        "Сумма операции": [-100.0],
        "Кэшбэк": [1.0],
        "Сумма операции с округлением": [100.0],
    }
    df = pd.DataFrame(test_data)

    mock_logger.return_value = logging.getLogger("test")
    with patch.object(mock_logger.return_value, "info") as mock_info:
        get_card_with_spend(df)
        assert mock_info.call_count == 2


def test_get_card_with_spend_logger_error() -> None:
    """Тест функции get_card_with_spend при ошибке инициализации логгера"""
    test_data = {
        "Номер карты": ["*5678"],
        "Сумма операции": [-100.0],
        "Кэшбэк": [1.0],
        "Сумма операции с округлением": [100.0],
    }
    df = pd.DataFrame(test_data)

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_card_with_spend(df)


def test_get_top_transactions_success() -> None:
    """Тест успешного выполнения функции get_top_transactions"""
    test_data = {
        "Дата платежа": ["31.12.2021", "28.12.2021", "23.12.2021"],
        "Сумма операции": [1000.0, 500.0, 1500.0],
        "Категория": ["Супермаркеты", "Переводы", "Ж/д билеты"],
        "Описание": ["Магнит", "Константин Л.", "РЖД"],
    }
    df = pd.DataFrame(test_data)

    result = get_top_transactions(df, 2)
    assert len(result) == 2
    assert float(result[0]["amount"]) == 1500.0  # Проверяю сортировку по убыванию
    assert result[0]["category"] == "Ж/д билеты"


def test_get_top_transactions_empty_dataframe() -> None:
    """Тест функции get_top_transactions с пустым DataFrame"""
    df = pd.DataFrame()
    with pytest.raises(Exception, match="Входной DataFrame не может быть пустым"):
        get_top_transactions(df, 5)


def test_get_top_transactions_missing_columns() -> None:
    """Тест функции get_top_transactions с отсутствующими колонками"""
    test_data = {
        "Дата платежа": ["31.12.2021"],
        "Сумма операции": [1000.0],
        # Нет других необходимых колонок
    }
    df = pd.DataFrame(test_data)
    with pytest.raises(Exception):
        get_top_transactions(df, 5)


def test_get_top_transactions_invalid_top() -> None:
    """Тест функции get_top_transactions с некорректным значением get_top"""
    test_data = {
        "Дата платежа": ["31.12.2021"],
        "Сумма операции": [1000.0],
        "Категория": ["Супермаркеты"],
        "Описание": ["Колхоз"],
    }
    df = pd.DataFrame(test_data)

    with pytest.raises(Exception):
        get_top_transactions(df, 0)  # Ноль

    with pytest.raises(Exception):
        get_top_transactions(df, -1)  # Отрицательное число

    with pytest.raises(Exception):
        get_top_transactions(df, "5")  # type: ignore[arg-type]
        # Строка вместо числа


def test_get_top_transactions_wrong_input_type() -> None:
    """Тест функции get_top_transactions с неправильным типом входных данных"""
    with pytest.raises(Exception):
        get_top_transactions("not a dataframe", 5)  # type: ignore[arg-type]
        # Передаем строку вместо DataFrame


@patch("src.utils.setup_function_logger")
def test_get_top_transactions_logging(mock_logger: MagicMock) -> None:
    """Тест логирования функции get_top_transactions"""
    test_data = {
        "Дата платежа": ["31.12.2021"],
        "Сумма операции": [1000.0],
        "Категория": ["Еда"],
        "Описание": ["Ресторан"],
    }
    df = pd.DataFrame(test_data)

    mock_logger.return_value = logging.getLogger("test")
    with patch.object(mock_logger.return_value, "info") as mock_info:
        get_top_transactions(df, 1)
        assert mock_info.call_count == 2


def test_get_top_transactions_logger_error() -> None:
    """Тест функции get_top_transactions при ошибке инициализации логгера"""
    test_data = {
        "Дата платежа": ["31.12.2021"],
        "Сумма операции": [1000.0],
        "Категория": ["Супермаркеты"],
        "Описание": ["Колхоз"],
    }
    df = pd.DataFrame(test_data)

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_top_transactions(df, 1)


def test_get_currency_success(tmpdir: Any) -> None:
    """Тест успешного выполнения функции get_currency"""
    # Создаю тестовый JSON файл
    test_json = tmpdir.join("test_currency.json")
    test_json.write(json.dumps({"user_currencies": ["USD"]}))

    # Мокирую запрос к API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.1234}

    with patch("requests.request", return_value=mock_response):
        result = get_currency(str(test_json))
        assert len(result) == 1
        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == "75.12"


def test_get_currency_file_not_found() -> None:
    """Тест функции get_currency с несуществующим файлом"""
    with pytest.raises(Exception, match="Файл не найден"):
        get_currency("nonexistent_file.json")


def test_get_currency_invalid_json(tmpdir: Any) -> None:
    """Тест функции get_currency с невалидным JSON"""
    test_json = tmpdir.join("invalid.json")
    test_json.write("{invalid json}")

    with pytest.raises(Exception, match="Ошибка декодирования JSON"):
        get_currency(str(test_json))


def test_get_currency_missing_key(tmpdir: Any) -> None:
    """Тест функции get_currency с отсутствующим обязательным полем"""
    test_json = tmpdir.join("missing_key.json")
    test_json.write(json.dumps({"wrong_key": ["USD"]}))

    with pytest.raises(Exception):
        get_currency(str(test_json))


def test_get_currency_empty_currencies(tmpdir: Any) -> None:
    """Тест функции get_currency с пустым списком валют"""
    test_json = tmpdir.join("empty_currencies.json")
    test_json.write(json.dumps({"user_currencies": []}))

    with patch("requests.request"):
        result = get_currency(str(test_json))
        assert len(result) == 0


def test_get_currency_api_error(tmpdir: Any) -> None:
    """Тест функции get_currency с ошибкой API"""
    test_json = tmpdir.join("test_api_error.json")
    test_json.write(json.dumps({"user_currencies": ["USD"]}))

    with patch(
        "requests.request",
        side_effect=requests.exceptions.RequestException("API error"),
    ):
        result = get_currency(str(test_json))
        assert len(result) == 0


def test_get_currency_invalid_response(tmpdir: Any) -> None:
    """Тест функции get_currency с некорректным ответом API"""
    test_json = tmpdir.join("test_invalid_response.json")
    test_json.write(json.dumps({"user_currencies": ["USD"]}))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"wrong_format": True}

    with patch("requests.request", return_value=mock_response):
        result = get_currency(str(test_json))
        assert len(result) == 0


def test_get_currency_wrong_input_type() -> None:
    """Тест функции get_currency с некорректным типом входных данных"""
    with pytest.raises(Exception):
        get_currency(123)  # type: ignore[arg-type]
        # Число вместо строки

    with pytest.raises(Exception):
        get_currency("")  # Пустая строка


@patch("src.utils.setup_function_logger")
def test_get_currency_logging(mock_logger: MagicMock, tmpdir: Any) -> None:
    """Тест логирования функции get_currency"""
    test_json = tmpdir.join("test_logging.json")
    test_json.write(json.dumps({"user_currencies": ["USD"]}))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.12}

    mock_logger.return_value = logging.getLogger("test")
    with patch("requests.request", return_value=mock_response):
        with patch.object(mock_logger.return_value, "info") as mock_info:
            get_currency(str(test_json))
            assert mock_info.call_count == 2


def test_get_currency_logger_error(tmpdir: Any) -> None:
    """Тест функции get_currency при ошибке инициализации логгера"""
    test_json = tmpdir.join("test_logger_error.json")
    test_json.write(json.dumps({"user_currencies": ["USD"]}))

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_currency(str(test_json))


def test_get_stock_prices_success(tmpdir: Any) -> None:
    """Тест успешного выполнения функции get_stock_prices"""
    # Создаем тестовый JSON файл
    test_json = tmpdir.join("test_stocks.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL", "GOOGL"]}))

    # Мокируем запрос к API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": 150.1234}

    with patch("requests.request", return_value=mock_response):
        result = get_stock_prices(str(test_json))
        assert len(result) == 2
        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == "150.12"


def test_get_stock_prices_file_not_found() -> None:
    """Тест функции get_stock_prices с несуществующим файлом"""
    with pytest.raises(Exception, match="Ошибка в функции: Файл не найден: nonexistent_file.json"):
        get_stock_prices("nonexistent_file.json")


def test_get_stock_prices_invalid_json(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с невалидным JSON"""
    test_json = tmpdir.join("invalid.json")
    test_json.write("{invalid json}")

    with pytest.raises(Exception):
        get_stock_prices(str(test_json))


def test_get_stock_prices_missing_key(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с отсутствующим обязательным полем"""
    test_json = tmpdir.join("missing_key.json")
    test_json.write(json.dumps({"wrong_key": ["AAPL"]}))

    with pytest.raises(Exception):
        get_stock_prices(str(test_json))


def test_get_stock_prices_empty_stocks(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с пустым списком акций"""
    test_json = tmpdir.join("empty_stocks.json")
    test_json.write(json.dumps({"user_stocks": []}))

    with patch("requests.request"):
        result = get_stock_prices(str(test_json))
        assert len(result) == 0


def test_get_stock_prices_api_error(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с ошибкой API"""
    test_json = tmpdir.join("test_api_error.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL"]}))

    with patch(
        "requests.request",
        side_effect=requests.exceptions.RequestException("API error"),
    ):
        result = get_stock_prices(str(test_json))
        assert len(result) == 0


def test_get_stock_prices_invalid_response(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с некорректным ответом API"""
    test_json = tmpdir.join("test_invalid_response.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL"]}))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"wrong_format": True}

    with patch("requests.request", return_value=mock_response):
        result = get_stock_prices(str(test_json))
        assert len(result) == 0


def test_get_stock_prices_invalid_price_format(tmpdir: Any) -> None:
    """Тест функции get_stock_prices с некорректным форматом цены"""
    test_json = tmpdir.join("test_invalid_price.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL"]}))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": "not_a_number"}

    with patch("requests.request", return_value=mock_response):
        result = get_stock_prices(str(test_json))
        assert len(result) == 0


def test_get_stock_prices_wrong_input_type() -> None:
    """Тест функции get_stock_prices с некорректным типом входных данных"""
    with pytest.raises(Exception):
        get_stock_prices(123)  # type: ignore[arg-type]
        # Число вместо строки

    with pytest.raises(Exception):
        get_stock_prices("")  # Пустая строка


@patch("src.utils.setup_function_logger")
def test_get_stock_prices_logging(mock_logger: MagicMock, tmpdir: Any) -> None:
    """Тест логирования функции get_stock_prices"""
    test_json = tmpdir.join("test_logging.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL"]}))

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": 150.12}

    mock_logger.return_value = logging.getLogger("test")
    with patch("requests.request", return_value=mock_response):
        with patch.object(mock_logger.return_value, "info") as mock_info:
            get_stock_prices(str(test_json))
            assert mock_info.call_count == 2


def test_get_stock_prices_logger_error(tmpdir: Any) -> None:
    """Тест функции get_stock_prices при ошибке инициализации логгера"""
    test_json = tmpdir.join("test_logger_error.json")
    test_json.write(json.dumps({"user_stocks": ["AAPL"]}))

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_stock_prices(str(test_json))


def test_get_cashback_by_category_success() -> None:
    """Тест успешного выполнения функции get_cashback_by_category"""
    test_data = {
        "Сумма операции": [-100.0, -200.0, -50.0, 100.0],
        "Кэшбэк": [1.0, 2.0, 0.5, 0.0],
        "Категория": ["Супермаркеты", "Рестораны", "Наличные", "Зарплата"],
        "Сумма операции с округлением": [100.0, 200.0, 50.0, 100.0],
    }
    df = pd.DataFrame(test_data)

    result = get_cashback_by_category(df)
    assert len(result) == 2
    assert result["Супермаркеты"] == 1
    assert result["Рестораны"] == 2
    assert "Наличные" not in result  # Должна быть исключена


def test_get_cashback_by_category_empty_df() -> None:
    """Тест функции get_cashback_by_category с пустым DataFrame"""
    df = pd.DataFrame()
    with pytest.raises(Exception, match="Ошибка в функции: DataFrame не может быть пустым"):
        get_cashback_by_category(df)


def test_get_cashback_by_category_wrong_input_type() -> None:
    """Тест функции get_cashback_by_category с неправильным типом входных данных"""
    with pytest.raises(Exception, match="Ошибка в функции: Входные данные должны быть pandas DataFrame"):
        get_cashback_by_category("not a dataframe")  # type: ignore[arg-type]
        # Строка вместо DataFrame


def test_get_cashback_by_category_missing_columns() -> None:
    """Тест функции get_cashback_by_category с отсутствующими колонками"""
    test_data = {
        "Сумма операции": [-100.0],
        "Категория": ["Супермаркеты"],
        # Нет других необходимых колонок
    }
    df = pd.DataFrame(test_data)
    with pytest.raises(Exception):
        get_cashback_by_category(df)


def test_get_cashback_by_category_excluded_categories() -> None:
    """Тест функции get_cashback_by_category с категориями без кэшбэка"""
    test_data = {
        "Сумма операции": [-100.0, -200.0],
        "Кэшбэк": [1.0, 2.0],
        "Категория": ["Переводы", "Наличные"],  # Обе категории в списке исключений
        "Сумма операции с округлением": [100.0, 200.0],
    }
    df = pd.DataFrame(test_data)

    result = get_cashback_by_category(df)
    assert len(result) == 0  # Не должно быть категорий с кэшбэком


def test_get_cashback_by_category_invalid_values() -> None:
    """Тест функции get_cashback_by_category с некорректными значениями"""
    test_data = {
        "Сумма операции": [-100.0, "invalid"],
        "Кэшбэк": [1.0, 2.0],
        "Категория": ["Супермаркеты", "Рестораны"],
        "Сумма операции с округлением": [100.0, "not_a_number"],
    }
    df = pd.DataFrame(test_data)

    with patch("logging.Logger.warning") as mock_warning:
        result = get_cashback_by_category(df)
        assert len(result) == 1  # Только одна корректная строка
        assert mock_warning.call_count >= 1  # Должно быть предупреждение


def test_get_cashback_by_category_empty_category_name() -> None:
    """Тест функции get_cashback_by_category с пустым названием категории"""
    test_data = {
        "Сумма операции": [-100.0],
        "Кэшбэк": [1.0],
        "Категория": [""],  # Пустое название
        "Сумма операции с округлением": [-100.0],
    }
    df = pd.DataFrame(test_data)

    with patch("logging.Logger.warning") as mock_warning:
        result = get_cashback_by_category(df)
        assert len(result) == 0
        mock_warning.assert_called()


@patch("src.utils.setup_function_logger")
def test_get_cashback_by_category_logging(mock_logger: MagicMock) -> None:
    """Тест логирования функции get_cashback_by_category"""
    test_data = {
        "Сумма операции": [-100.0],
        "Кэшбэк": [1.0],
        "Категория": ["Супермаркеты"],
        "Сумма операции с округлением": [-100.0],
    }
    df = pd.DataFrame(test_data)

    mock_logger.return_value = logging.getLogger("test")
    with patch.object(mock_logger.return_value, "info") as mock_info:
        get_cashback_by_category(df)
        assert mock_info.call_count == 2


def test_get_cashback_by_category_logger_error() -> None:
    """Тест функции get_cashback_by_category при ошибке инициализации логгера"""
    test_data = {
        "Сумма операции": [-100.0],
        "Кэшбэк": [1.0],
        "Категория": ["Супермаркеты"],
        "Сумма операции с округлением": [-100.0],
    }
    df = pd.DataFrame(test_data)

    with patch("src.utils.setup_function_logger", side_effect=Exception("Logger error")):
        with pytest.raises(Exception):
            get_cashback_by_category(df)
