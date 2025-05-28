from datetime import datetime

import pandas as pd
from pandas import DataFrame

from src.utils import get_cashback_by_category, setup_function_logger


def analyze_cashback_categories(transactions: list[dict], year: int, month: int) -> DataFrame:
    """Функция принимает список транзакций, год и месяц,
    и возвращает наиболее выгодные категории кешбэка за выбранный период"""
    logger = None
    try:
        logger = setup_function_logger("analyze_cashback_categories")
        logger.info(f"Начало выполнения функции с параметрами: year={year}, month={month}")

        # Валидация входных параметров
        if not isinstance(transactions, list) or not all(isinstance(t, dict) for t in transactions):
            logger.error("Параметр transactions должен быть списком словарей")
            raise TypeError("Параметр transactions должен быть списком словарей")
        if not isinstance(year, int) or year < 1957 or year > datetime.now().year:
            raise ValueError("Некорректный год. Должен быть целым числом между 1957 и текущим годом")
        if not isinstance(month, int) or month < 1 or month > 12:
            raise ValueError("Некорректный месяц. Должен быть целым числом от 1 до 12")

        try:
            # Преобразуем список словарей в DataFrame
            categories_for_month = pd.DataFrame(transactions)

            # Проверяем наличие необходимых колонок
            required_columns = [
                "Сумма операции",
                "Кэшбэк",
                "Категория",
                "Сумма операции с округлением",
            ]
            missing_columns = [col for col in required_columns if col not in categories_for_month.columns]
            if missing_columns:
                logger.error(f"Отсутствуют необходимые колонки: {missing_columns}")
                raise KeyError(f"Отсутствуют необходимые колонки: {missing_columns}")

            # Фильтруем данные по году и месяцу
            categories_for_month["Дата операции"] = pd.to_datetime(categories_for_month["Дата операции"])
            filtered_df = categories_for_month[
                (categories_for_month["Дата операции"].dt.year == year)
                & (categories_for_month["Дата операции"].dt.month == month)
            ]

            # Получаем кэшбэк по категориям
            cashback_by_category = get_cashback_by_category(filtered_df)
            result_df = pd.DataFrame.from_dict(cashback_by_category, orient="index", columns=["Кэшбэк"])
            result_df = result_df.sort_values(by="Кэшбэк", ascending=False)

            logger.info(f"Функция отработала успешно. Найдено {len(result_df)} категорий с кэшбэком")
            return result_df

        except Exception as e:
            logger.error(f"Ошибка при обработке данных: {str(e)}")
            raise Exception(f"Ошибка при обработке данных: {str(e)}") from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception(f"Ошибка в функции: {str(e)}") from e
