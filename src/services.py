from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame

from src.utils import get_path_and_period, get_data_time, get_cashback_by_category


def analyze_cashback_categories(path_to_file: str, year: int, month: int) -> DataFrame:
    """Функция принимает файл формата xlsx, год и месяц, и возвращает наиболее выгодные категории кешбэка за выбранный период"""
    df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")

    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    last_day_time = datetime(next_year, next_month, 1) - timedelta(seconds=1)

    date_time = last_day_time.strftime("%Y-%m-%d %H:%M:%S")

    time_period = (get_data_time(date_time)) # Получаю необходимый период (выбранный месяц, год)

    categories_for_month = get_path_and_period("../data/operations.xlsx", time_period) # Делаю срез таблицы по этому периоду

    cashback_by_category = get_cashback_by_category(categories_for_month) # Получаю необходимый период (выбранный месяц, год)

    return cashback_by_category

print(analyze_cashback_categories("../data/operations.xlsx", 2020, 6))

