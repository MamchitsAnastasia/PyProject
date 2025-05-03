import json
from datetime import datetime
from http.client import responses

import pandas as pd
from pandas import DataFrame
import os
import requests
from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv("../.env")
EXCHANGE_RATES_API_KEY = os.getenv("EXCHANGE_RATES_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
EXCHANGE_RATES_URL = "https://api.apilayer.com/exchangerates_data/convert"
STOCK_URL = "https://api.twelvedata.com/price"

CATEGORIES_WITHOUT_CASHBACK = ['Переводы', 'Наличные', 'Услуги банка']

def get_time_for_greeting():
    """Функция возвращает «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи» в зависимости от текущего времени."""

    user_datatime_hour = datetime.now().hour
    if 5 <= user_datatime_hour < 12:
        return "Доброе утро"
    elif 12 <= user_datatime_hour < 18:
        return "Добрый день"
    elif 18 <= user_datatime_hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"

def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Функция принимает дату и возвращает диапазон от первого числа месяца до необходимой даты"""
    dt = datetime.strptime(date_time, date_format)
    start_of_month = dt.replace(day=1)

    return [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]

def get_path_and_period(path_to_file: str, period_date: list) -> DataFrame:
    """Функция получает на вход файл формата xlsx и необходимый период, и возвращает таблицу в заданном периоде"""
    df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True) #Перевожу в формат datetime, ранжирую по дню
    start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
    end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")

    filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
    sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)

    return sorted_df


def get_card_with_spend(sorted_df: DataFrame) -> list[dict]:
    """Функция получает срез таблицы в заданном периоде и возвращает список карт с расходами"""
    card_spend_transactions = []
    card_sorted = sorted_df[["Номер карты", "Сумма операции", "Кэшбэк", "Сумма операции с округлением"]]

    for index, row in card_sorted.iterrows():
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

    return card_spend_transactions


def get_top_transactions(sorted_df: DataFrame, get_top: int) -> list[dict]:
    """Функция получает срез таблицы в заданном периоде и возвращает топ транзакций по сумме платежа"""
    top_pay_transactions = []
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False) #Сортирую таблицу по сумме операций по убыванию
    top_transactions = sorted_pay_df.head(get_top)
    top_transactions_sorted = top_transactions[["Дата платежа", "Сумма операции", "Категория", "Описание"]]

    for index, row in top_transactions_sorted.iterrows():
        transaction = {
            "date": f"{row["Дата платежа"]}",
            "amount": f"{row["Сумма операции"]}",
            "category": f"{row["Категория"]}",
            "description": f"{row["Описание"]}"
        }
        top_pay_transactions.append(transaction)
    return  top_pay_transactions

def get_currency(path_to_json: str) -> list[dict]:
    """Функция принимает на вход путь к json и возвращает курс валют"""
    currency_rates = []
    with open(path_to_json, "r", encoding="utf-8") as file:
        data = json.load(file)
        user_currencies = data["user_currencies"]

        for currency in user_currencies:
            params = {
                "amount": 1,
                "from": f"{currency}",
                "to": "RUB"
            }
            headers = {"apikey": f"{EXCHANGE_RATES_API_KEY}"}
            response = requests.request("GET", EXCHANGE_RATES_URL, headers=headers, params=params, timeout=10)

            status_code = response.status_code
            if status_code == 200:
                result = response.json()
                currency_code_response = result["query"]["from"]
                currency_amount = round(result["result"], 2)
                currency_rates.append({"currency": f"{currency_code_response}", "rate": f"{currency_amount}"})
        return currency_rates

def get_stock_prices(path_to_json: str) -> list[dict]:
    """Функция принимает на вход путь к json и возвращает актуальную стоимость акций"""
    stock_rates = []
    with open(path_to_json, "r", encoding="utf-8") as file:
        data = json.load(file)
        stocks = data["user_stocks"]

        for stock in stocks:
            params = {"symbol": f"{stock}",
                      "apikey": f"{STOCK_API_KEY}"}
            response = requests.request("GET", STOCK_URL, params=params, timeout=10)

            status_code = response.status_code
            if status_code == 200:
                result = response.json()
                stock_prise = round(float(result["price"]), 2)
                stock_rates.append({"stock": f"{stock}", "price": f"{stock_prise}"})
    return stock_rates

def get_cashback_by_category(categories_for_month: DataFrame) -> dict[str, float]:
    """Функция принимает срез таблицы за период и возвращает кэшбэк по категориям за месяц"""
    cashback_by_category = {}
    categories_sorted = categories_for_month[["Сумма операции", "Кэшбэк", "Категория", "Сумма операции с округлением"]]

    for index, row in categories_sorted.iterrows():
        if row["Сумма операции"] < 0 :
            category = str(row["Категория"])
            total_spent = (row["Сумма операции с округлением"])
            cashback = total_spent//100
            if category not in CATEGORIES_WITHOUT_CASHBACK and cashback > 0:
                if category in cashback_by_category:
                    cashback_by_category[category] += int(cashback)
                elif category not in cashback_by_category:
                    cashback_by_category[category] = int(cashback)

    return cashback_by_category
