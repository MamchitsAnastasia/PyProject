import json
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from pandas import DataFrame

from src.utils import setup_function_logger


def report_to_file(default_filename: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор для сохранения результатов отчетов в файл.
    - Без параметров: сохраняет в файл с именем по умолчанию
    - С параметром filename: сохраняет в указанный файл"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Получаю результат выполнения функции
            result = func(*args, **kwargs)

            # Определяю имя файла
            filename = kwargs.get("filename", default_filename)
            if filename is None:
                # Генерирую имя файла по умолчанию, если не передано
                timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                filename = f"report_{func.__name__}_{timestamp}.json"

            # Добавляю путь к папке data
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join(data_dir, filename)

            # Сохраняю результат в файл
            if isinstance(result, (pd.DataFrame, DataFrame)):
                result.to_json(filepath, orient="records", indent=4, force_ascii=False)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            return result

        return wrapper

    return decorator


@report_to_file(default_filename="spending_by_category_report.json")
def spending_by_category(transactions_df: DataFrame, category: str, date: Optional[str] = None) -> DataFrame:
    """Функция принимает DataFrame транзакций, название категории и дату,
    и возвращает операции по категории за последние 3 месяца"""
    logger = None
    try:
        logger = setup_function_logger("spending_by_category")
        logger.info(f"Начало выполнения функции с параметрами: category={category}, date={date}")

        # Валидация входных параметров
        if not isinstance(transactions_df, DataFrame):
            logger.error("Параметр transactions_df должен быть pandas DataFrame")
            raise TypeError("Параметр transactions_df должен быть pandas DataFrame")
        if not isinstance(category, str):
            logger.error("Параметр category должен быть строкой")
            raise TypeError("Параметр category должен быть строкой")
        if not category.strip():
            logger.error("Параметр category не может быть пустой строкой")
            raise ValueError("Параметр category не может быть пустой строкой")
        if date is not None and not isinstance(date, str):
            logger.error("Параметр date должен быть строкой или None")
            raise TypeError("Параметр date должен быть строкой или None")

        # Проверяем наличие необходимых колонок
        required_columns = ["Категория", "Дата операции"]
        missing_columns = [col for col in required_columns if col not in transactions_df.columns]
        if missing_columns:
            logger.error(f"Отсутствуют необходимые колонки: {missing_columns}")
            raise KeyError(f"Отсутствуют необходимые колонки: {missing_columns}")

        # Преобразуем дату
        try:
            if date is None:
                end_date = datetime.now()
            else:
                end_date = datetime.strptime(date, "%Y.%m.%d %H:%M:%S")

            start_date = end_date - timedelta(days=90)
            filtered_df = transactions_df[
                (transactions_df["Дата операции"] >= start_date)
                & (transactions_df["Дата операции"] <= end_date)
                & (transactions_df["Категория"] == category)
            ]

            if filtered_df.empty:
                logger.info(f"Не найдено транзакций по категории '{category}' за указанный период")
                return pd.DataFrame()

            logger.info(f"Функция отработала успешно. Найдено транзакций: {len(filtered_df)}")
            return filtered_df

        except ValueError as e:
            logger.error(f"Ошибка формата даты: {str(e)}")
            raise ValueError("Некорректный формат даты. Ожидается: 'YYYY.MM.DD HH:MM:SS'") from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception(f"Ошибка в функции: {str(e)}") from e
