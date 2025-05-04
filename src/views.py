import json
from datetime import datetime

import pytest
from typing import Any

from src.utils import (
    get_time_for_greeting,
    get_data_time,
    get_path_and_period,
    get_card_with_spend,
    get_top_transactions,
    get_currency,
    get_stock_prices, setup_function_logger
)


def main_info(date_time: str) -> dict[str, Any]:
    """Функция принимает строку с датой в формате YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ """
    logger = None
    try:
        logger = setup_function_logger('main_info')
        logger.info("Начало выполнения функции")

        # Валидация формата даты
        try:
            datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logger.error(f"Ошибка формата даты: {str(e)}")
            raise

        time_period = get_data_time(date_time)
        sorted_df = get_path_and_period("../data/operations.xlsx", time_period)

        greeting = get_time_for_greeting() #Приветствие
        cards = get_card_with_spend(sorted_df)  #Операции по дате
        top_transactions = get_top_transactions(sorted_df, 5) #Топ-5 транзакций по сумме платежа
        currency_rates = get_currency("../data/user_settings.json") # Курс валют
        stock_prices = get_stock_prices("../data/user_settings.json") # Стоимость акций из S&P500

        data = {
      "greeting": greeting,
      "cards": cards,
      "top_transactions": top_transactions,
      "currency_rates": currency_rates,
      "stock_prices": stock_prices
    }
        json_data = json.dumps(data, ensure_ascii=False, indent=4)

        logger.info(f"Функция отработала успешно.")
        return json_data

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {str(e)}")
        raise

    except ValueError as e:
        logger.error(f"Ошибка значения: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        raise