import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Callable, Any

import pandas as pd
from pandas import DataFrame

from src.utils import get_path_and_period


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

    # Преобразую дату
    if date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(date, "%Y.%m.%d %H:%M:%S")
    start_date = end_date - timedelta(days=90)
    period_date = [
        start_date.strftime("%d.%m.%Y %H:%M:%S"),
        end_date.strftime("%d.%m.%Y %H:%M:%S")
    ]

    transactions_df = get_path_and_period("../data/operations.xlsx", period_date)
    transactions_for_three_months = transactions_df[transactions_df["Категория"] == category]

    return transactions_for_three_months

print(spending_by_category("../data/operations.xlsx", "Другое", "2020.04.22 12:00:00"))