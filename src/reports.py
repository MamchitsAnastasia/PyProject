import json
import os
import pytest
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Callable, Any

import pandas as pd
from pandas import DataFrame

from src.utils import get_path_and_period, setup_function_logger

PATH_TO_FILE = "../data/operations.xlsx"

def report_to_file(default_filename: str = None):
    """Декоратор для сохранения результатов отчетов в файл.
    - Без параметров: сохраняет в файл с именем по умолчанию
    - С параметром filename: сохраняет в указанный файл"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Получаю результат выполнения функции
            result = func(*args, **kwargs)

            # Определяю имя файла
            filename = kwargs.get('filename', default_filename)
            if filename is None:
                # Генерирую имя файла по умолчанию, если не передано
                timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                filename = f"report_{func.__name__}_{timestamp}.json"

            # Добавляю путь к папке data
            filename = os.path.join("data", filename)

            # Сохраняю результат в файл
            if isinstance(result, (pd.DataFrame, DataFrame)):
                result.to_json(filename, orient='records', indent=4, force_ascii=False)
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            return result

        return wrapper

    return decorator


@report_to_file(default_filename="spending_by_category_report.json")
def spending_by_category(path_to_file: str, category: str, date: Optional[str] = None) -> DataFrame:
    """Функция принимает файл формата xlsx, название категории и дату, и возвращает файл с тратами по категории за последние 3 месяца"""
    logger = None
    try:
        logger = setup_function_logger('spending_by_category')
        logger.info(
            f"Начало выполнения функции с параметрами: path_to_file={path_to_file}, category={category}, date={date}")

        # Валидация входных параметров
        if not isinstance(path_to_file, str):
            raise TypeError("Параметр path_to_file должен быть строкой")
        if not isinstance(category, str):
            raise TypeError("Параметр category должен быть строкой")
        if not path_to_file.strip() or not category.strip():
            raise ValueError("Параметры path_to_file и category не могут быть пустыми строками")
        if date is not None and not isinstance(date, str):
            raise TypeError("Параметр date должен быть строкой или None")

        # Преобразую дату
        try:
            if date is None:
                end_date = datetime.now()
            else:
                end_date = datetime.strptime(date, "%Y.%m.%d %H:%M:%S")

            start_date = end_date - timedelta(days=90)
            period_date = [
                start_date.strftime("%d.%m.%Y %H:%M:%S"),
                end_date.strftime("%d.%m.%Y %H:%M:%S")
            ]
        except ValueError as e:
            logger.error(f"Ошибка формата даты: {str(e)}")
            raise ValueError(f"Некорректный формат даты. Ожидается: 'YYYY.MM.DD HH:MM:SS'") from e

        try:
            transactions_df = get_path_and_period(path_to_file, period_date)
            transactions_for_three_months = transactions_df[transactions_df["Категория"] == category]

            logger.info(f"Функция отработала успешно. Найдено транзакций: {len(transactions_for_three_months)}")
            return transactions_for_three_months
        except Exception as e:
            logger.error(f"Ошибка при обработке данных: {str(e)}")
            raise Exception(f"Ошибка при обработке данных: {str(e)}") from e
    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
            raise Exception(f"Ошибка в функции: {str(e)}") from e