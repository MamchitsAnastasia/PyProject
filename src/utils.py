import json
import pytest
from datetime import datetime

import pandas as pd
from pandas import DataFrame
import os
import logging
import requests
from dotenv import load_dotenv

os.makedirs("logs", exist_ok=True)

load_dotenv("../.env")
EXCHANGE_RATES_API_KEY = os.getenv("EXCHANGE_RATES_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
EXCHANGE_RATES_URL = "https://api.apilayer.com/exchangerates_data/convert"
STOCK_URL = "https://api.twelvedata.com/price"

CATEGORIES_WITHOUT_CASHBACK = ['Переводы', 'Наличные', 'Услуги банка']


def setup_function_logger(func_name):
    """Функция создает и настраивает логгер для конкретной функции"""
    logger = logging.getLogger(func_name)
    logger.setLevel(logging.DEBUG)
    # Настройка обработчика для записи в файл
    log_file = os.path.join("logs", f'{func_name}.log')
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    # Формат записи логов
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_time_for_greeting():
    """Функция возвращает «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи» в зависимости от текущего времени."""
    logger = None
    try:
        logger = setup_function_logger('get_time_for_greeting')
        logger.info("Начало выполнения функции")

        try:
            user_datatime_hour = datetime.now().hour
            if not isinstance(user_datatime_hour, int):
                raise RuntimeError("Невозможно определить текущий час")
            if 5 <= user_datatime_hour < 12:
                result = "Доброе утро"
            elif 12 <= user_datatime_hour < 18:
                result = "Добрый день"
            elif 18 <= user_datatime_hour < 22:
                result = "Добрый вечер"
            else:
                result = "Доброй ночи"

            logger.info(f"Функция отработала успешно. Результат выполнения: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при определении времени: {str(e)}")
            raise RuntimeError(f"Ошибка при определении времени: {str(e)}") from e

    except Exception as e:
        raise Exception (f"Ошибка инициализации логгера: {str(e)}") from e


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Функция принимает дату и возвращает диапазон от первого числа месяца до необходимой даты"""
    logger = None
    try:
        # Валидация входных параметров
        if not isinstance(date_time, str):
            raise TypeError("Параметр date_time должен быть строкой")
        if not isinstance(date_format, str):
            raise TypeError("Параметр date_format должен быть строкой")
        if not date_time.strip() or not date_format.strip():
            raise ValueError("Параметры не могут быть пустыми строками")

        logger = setup_function_logger('get_data_time')
        logger.info(f"Начало выполнения функции с параметрами: date_time={date_time}, date_format={date_format}")

        dt = datetime.strptime(date_time, date_format)
        start_of_month = dt.replace(day=1)
        result = [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]

        logger.info(f"Функция отработала успешно. Результат выполнения: {result}")
        return result

    except (ValueError, TypeError) as e:
        if logger:
            logger.error(f"Ошибка: {str(e)}")
        raise
    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_path_and_period(path_to_file: str, period_date: list) -> DataFrame:
    """Функция получает на вход файл формата xlsx и необходимый период, и возвращает таблицу в заданном периоде"""
    logger = None
    try:
        # Валидация входных параметров
        if not isinstance(path_to_file, str):
            raise TypeError("Параметр path_to_file должен быть строкой")
        if not isinstance(period_date, list) or len(period_date) != 2:
            raise ValueError("Параметр period_date должен быть списком с двумя элементами")
        if not all(isinstance(date, str) for date in period_date):
            raise TypeError("Даты в period_date должны быть строками")
        if not os.path.exists(path_to_file):
            raise FileNotFoundError(f"Файл не найден: {path_to_file}")

        logger = setup_function_logger('get_path_and_period')
        logger.info(f"Начало выполнения функции с параметрами: path_to_file={path_to_file}, period_date={period_date}")

        try:
            df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")
            if "Дата операции" not in df.columns:
                raise KeyError("В файле отсутствует колонка 'Дата операции'")

            df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True) #Перевожу в формат datetime, ранжирую по дню
            start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
            end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")

            if start_date > end_date:
                raise ValueError("Начальная дата периода не может быть больше конечной")

            filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
            sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)

            logger.info(f"Функция отработала успешно. Возвращено строк: {len(sorted_df)}")
            return sorted_df


        except pd.errors.EmptyDataError as e:
            logger.error(f"Файл пуст или поврежден: {str(e)}")
            raise ValueError(f"Файл пуст или поврежден: {str(e)}") from e

        except ValueError as e:
            logger.error(f"Ошибка формата даты: {str(e)}")
            raise ValueError(f"Ошибка формата даты: {str(e)}") from e

        except KeyError as e:
            logger.error(f"Отсутствует необходимая колонка: {str(e)}")
            raise KeyError(f"Отсутствует необходимая колонка: {str(e)}") from e

        except Exception as e:
            logger.error(f"Ошибка при обработке данных: {str(e)}")
            raise Exception(f"Ошибка при обработке данных: {str(e)}") from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_card_with_spend(sorted_df: DataFrame) -> list[dict]:
    """Функция получает срез таблицы в заданном периоде и возвращает список карт с расходами"""
    logger = None
    try:
        # Валидация входных данных
        if not isinstance(sorted_df, DataFrame):
            raise TypeError("Входные данные должны быть pandas DataFrame")
        if sorted_df.empty:
            raise ValueError("Входной DataFrame не может быть пустым")

        # Проверка наличия необходимых колонок
        required_columns = ["Номер карты", "Сумма операции", "Кэшбэк", "Сумма операции с округлением"]
        missing_columns = [col for col in required_columns if col not in sorted_df.columns]
        if missing_columns:
            raise KeyError(f"Отсутствуют необходимые колонки: {missing_columns}")

        logger = setup_function_logger('get_card_with_spend')
        logger.info("Начало выполнения функции")

        try:
            card_spend_transactions = []
            card_sorted = sorted_df[["Номер карты", "Сумма операции", "Кэшбэк", "Сумма операции с округлением"]]

            for index, row in card_sorted.iterrows():
                try:
                    if row["Сумма операции"] < 0 :
                        last_digits = str(row["Номер карты"]).replace("*", "")
                        total_spent = (row["Сумма операции с округлением"])
                        cashback = total_spent//100
                        row = {
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback
                }
                        card_spend_transactions.append(row)

                except Exception as row_error:
                    logger.warning(f"Ошибка обработки строки {index}: {str(row_error)}")
                    continue

            if not card_spend_transactions:
                logger.warning("Не найдено транзакций с расходами")

            logger.info(f"Функция отработала успешно. Транзакций найдено: {len(card_spend_transactions)}")
            return card_spend_transactions


        except Exception as processing_error:
            logger.error(f"Ошибка обработки данных: {str(processing_error)}")
            raise Exception(f"Ошибка обработки данных: {str(processing_error)}") from processing_error

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_top_transactions(sorted_df: DataFrame, get_top: int) -> list[dict]:
    """Функция получает срез таблицы в заданном периоде и возвращает топ транзакций по сумме платежа"""
    logger = None
    try:
        # Валидация входных параметров
        if not isinstance(sorted_df, DataFrame):
            raise TypeError("Входные данные должны быть pandas DataFrame")
        if not isinstance(get_top, int):
            raise TypeError("get_top должен быть целым числом")
        if get_top <= 0:
            raise ValueError("get_top должен быть положительным числом")
        if sorted_df.empty:
            raise ValueError("Входной DataFrame не может быть пустым")

        # Проверка наличия необходимых колонок
        required_columns = ["Дата платежа", "Сумма операции", "Категория", "Описание"]
        missing_columns = [col for col in required_columns if col not in sorted_df.columns]
        if missing_columns:
            raise KeyError(f"Отсутствуют необходимые колонки: {missing_columns}")

        logger = setup_function_logger('get_top_transactions')
        logger.info(f"Начало выполнения функции с параметром: get_top={get_top}")


        try:
            top_pay_transactions = []
            sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False) #Сортирую таблицу по сумме операций по убыванию
            top_transactions = sorted_pay_df.head(get_top)
            top_transactions_sorted = top_transactions[["Дата платежа", "Сумма операции", "Категория", "Описание"]]

            for index, row in top_transactions_sorted.iterrows():
                try:
                    transaction = {
                        "date": f"{row["Дата платежа"]}",
                        "amount": f"{row["Сумма операции"]}",
                        "category": f"{row["Категория"]}",
                        "description": f"{row["Описание"]}"
                    }
                    top_pay_transactions.append(transaction)
                except Exception as row_error:
                    logger.warning(f"Ошибка обработки строки {index}: {str(row_error)}")
                    continue

            logger.info(f"Функция отработала успешно. Топ транзакций возвращено: {len(top_pay_transactions)}")
            return top_pay_transactions

        except Exception as e:
            logger.error(f"Ошибка обработки данных: {str(e)}")
            raise Exception(f"Ошибка обработки данных: {str(e)}") from e
    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_currency(path_to_json: str) -> list[dict]:
    """Функция принимает на вход путь к json и возвращает курс валют"""
    logger = None
    try:
        # Валидация входных параметров
        if not isinstance(path_to_json, str):
            raise ValueError("path_to_json должен быть строкой")
        if not path_to_json.strip():
            raise ValueError("path_to_json не может быть пустой строкой")
        if not os.path.exists(path_to_json):
            raise FileNotFoundError(f"Файл не найден: {path_to_json}")

        logger = setup_function_logger('get_currency')
        logger.info(f"Начало выполнения функции с параметром: path_to_json={path_to_json}")

        currency_rates = []
        try:
            with open(path_to_json, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "user_currencies" not in data:
                    raise KeyError("Отсутствует обязательное поле 'user_currencies' в JSON")

                user_currencies = data["user_currencies"]

                if not isinstance(user_currencies, list):
                    raise ValueError("user_currencies должен быть списком")
                if not user_currencies:
                    logger.warning("Список валют пуст")
                    return currency_rates

                for currency in user_currencies:
                    try:
                        if not isinstance(currency, str):
                            raise ValueError(f"Код валюты должен быть строкой, получено: {type(currency)}")
                        params = {
                            "amount": 1,
                            "from": f"{currency}",
                            "to": "RUB"
                        }
                        headers = {"apikey": f"{EXCHANGE_RATES_API_KEY}"}
                        response = requests.request("GET", EXCHANGE_RATES_URL, headers=headers, params=params, timeout=10)

                        response.raise_for_status()

                        result = response.json()

                        if "query" not in result or "result" not in result:
                            raise ValueError("Некорректный формат ответа от API")

                        currency_code_response = result["query"]["from"]
                        currency_amount = round(result["result"], 2)

                        currency_rates.append({"currency": f"{currency_code_response}", "rate": f"{currency_amount}"})

                    except requests.RequestException as req_err:
                        logger.error(f"Ошибка запроса для валюты {currency}: {str(req_err)}")
                        continue
                    except ValueError as val_err:
                        logger.error(f"Ошибка обработки ответа для валюты {currency}: {str(val_err)}")
                        continue
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка для валюты {currency}: {str(e)}")
                        continue

            logger.info(f"Функция отработала успешно. Возвращены курсы: {currency_rates}")
            return currency_rates


        except json.JSONDecodeError as json_err:
            logger.error(f"Ошибка декодирования JSON: {str(json_err)}")
            raise json.JSONDecodeError(f"Ошибка декодирования JSON: {str(json_err)}", json_err.doc, json_err.pos) from json_err

        except KeyError as key_err:
            logger.error(f"Отсутствует обязательное поле в JSON: {str(key_err)}")
            raise KeyError(f"Отсутствует обязательное поле в JSON: {str(key_err)}") from key_err

        except Exception as e:
            logger.error(f"Ошибка обработки данных: {str(e)}")
            raise Exception(f"Ошибка обработки данных: {str(e)}") from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_stock_prices(path_to_json: str) -> list[dict]:
    """Функция принимает на вход путь к json и возвращает актуальную стоимость акций"""
    logger = None
    try:
        # Валидация входных параметров
        if not isinstance(path_to_json, str):
            raise ValueError("path_to_json должен быть строкой")
        if not path_to_json.strip():
            raise ValueError("path_to_json не может быть пустой строкой")
        if not os.path.exists(path_to_json):
            raise FileNotFoundError(f"Файл не найден: {path_to_json}")

        logger = setup_function_logger('get_stock_prices')
        logger.info(f"Начало выполнения функции с параметром: path_to_json={path_to_json}")

        stock_rates = []

        try:
            with open(path_to_json, "r", encoding="utf-8") as file:
                data = json.load(file)

                if "user_stocks" not in data:
                    raise KeyError("Отсутствует обязательное поле 'user_stocks' в JSON")

                user_stocks = data["user_stocks"]

                if not isinstance(user_stocks, list):
                    raise ValueError("user_stocks должен быть списком")
                if not user_stocks:
                    logger.warning("Список акций пуст")
                    return stock_rates

                for stock in user_stocks:
                    try:
                        if not isinstance(stock, str):
                            raise ValueError(f"Тикер акции должен быть строкой, получено: {type(stock)}")

                        params = {"symbol": f"{stock}",
                                  "apikey": f"{STOCK_API_KEY}"}
                        response = requests.request("GET", STOCK_URL, params=params, timeout=10)
                        response.raise_for_status()
                        result = response.json()

                        if "price" not in result:
                            raise ValueError("Некорректный формат ответа от API - отсутствует поле 'price'")
                        try:
                            stock_prise = round(float(result["price"]), 2)
                        except (ValueError, TypeError):
                            raise ValueError(f"Некорректное значение цены: {result['price']}")

                        stock_rates.append({"stock": f"{stock}", "price": f"{stock_prise}"})

                    except requests.RequestException as req_err:
                        logger.error(f"Ошибка запроса для акции {stock}: {str(req_err)}")
                        continue
                    except ValueError as val_err:
                        logger.error(f"Ошибка обработки ответа для акции {stock}: {str(val_err)}")
                        continue
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка для акции {stock}: {str(e)}")
                        continue

            logger.info(f"Функция отработала успешно. Возвращена стоимость акций: {stock_rates}")
            return stock_rates

        except json.JSONDecodeError as json_err:
            error_msg = f"Ошибка декодирования JSON: {str(json_err)}"
            logger.error(error_msg)
            raise json.JSONDecodeError(error_msg, json_err.doc, json_err.pos) from json_err
        except KeyError as key_err:
            error_msg = f"Отсутствует обязательное поле в JSON: {str(key_err)}"
            logger.error(error_msg)
            raise KeyError(error_msg) from key_err
        except Exception as e:
            error_msg = f"Ошибка обработки данных: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e


def get_cashback_by_category(categories_for_month: DataFrame) -> dict[str, float]:
    """Функция принимает срез таблицы за месяц и возвращает кэшбэк по категориям за данный период"""
    logger = None
    try:
        # Валидация входных данных
        if not isinstance(categories_for_month, DataFrame):
            raise TypeError("Входные данные должны быть pandas DataFrame")
        if categories_for_month.empty:
            raise ValueError("DataFrame не может быть пустым")

        # Проверка наличия необходимых колонок
        required_columns = ["Сумма операции", "Кэшбэк", "Категория", "Сумма операции с округлением"]
        missing_columns = [col for col in required_columns if col not in categories_for_month.columns]
        if missing_columns:
            raise KeyError(f"Отсутствуют необходимые колонки: {missing_columns}")

        logger = setup_function_logger('get_cashback_by_category')
        logger.info("Начало выполнения функции")

        cashback_by_category = {}

        try:
            categories_sorted = categories_for_month[["Сумма операции", "Кэшбэк", "Категория", "Сумма операции с округлением"]]

            for index, row in categories_sorted.iterrows():
                try:
                    if row["Сумма операции"] < 0 :
                        category = str(row["Категория"])
                        if not category.strip():
                            logger.warning(f"Пустое название категории в строке {index}")
                            continue
                        try:
                            total_spent = (row["Сумма операции с округлением"])
                            cashback = total_spent//100
                        except (TypeError, ValueError) as e:
                            logger.warning(f"Ошибка обработки суммы в строке {index}: {str(e)}")
                            continue

                        if category not in CATEGORIES_WITHOUT_CASHBACK and cashback > 0:
                            cashback_by_category[category] = cashback_by_category.get(category, 0) + cashback
                except Exception as row_error:
                    logger.warning(f"Ошибка обработки строки {index}: {str(row_error)}")
                    continue

            logger.info(f"Функция отработала успешно. Найдено категорий для кэшбэка: {len(cashback_by_category)}")
            return cashback_by_category

        except Exception as processing_error:
            logger.error(f"Ошибка обработки данных: {str(processing_error)}")
            raise Exception(f"Ошибка обработки данных: {str(processing_error)}") from processing_error

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception (f"Ошибка в функции: {str(e)}") from e

