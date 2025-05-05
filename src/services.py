from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame

from src.utils import (get_cashback_by_category, get_data_time,
                       get_path_and_period, setup_function_logger)

PATH_TO_FILE = "../data/operations.xlsx"


def analyze_cashback_categories(path_to_file: str, year: int, month: int) -> DataFrame:
    """Функция принимает файл формата xlsx, год и месяц,
    и возвращает наиболее выгодные категории кешбэка за выбранный период"""
    logger = None
    try:
        logger = setup_function_logger("analyze_cashback_categories")
        logger.info(
            f"Начало выполнения функции с параметрами: path_to_file={path_to_file}, year={year}, month={month}"
        )
        # Валидация входных параметров
        if not isinstance(path_to_file, str):
            raise TypeError("Параметр path_to_file должен быть строкой")
        if not isinstance(year, int) or year < 1957 or year > datetime.now().year:
            raise ValueError(
                "Некорректный год. Должен быть целым числом между 1957 и текущим годом"
            )
        if not isinstance(month, int) or month < 1 or month > 12:
            raise ValueError("Некорректный месяц. Должен быть целым числом от 1 до 12")

        try:
            pd.read_excel(path_to_file, sheet_name="Отчет по операциям")

            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            last_day_time = datetime(next_year, next_month, 1) - timedelta(seconds=1)
            date_time = last_day_time.strftime("%Y-%m-%d %H:%M:%S")

            time_period = get_data_time(
                date_time
            )  # Получаю необходимый период (выбранный месяц, год)

            try:
                categories_for_month = get_path_and_period(
                    PATH_TO_FILE, time_period
                )  # Делаю срез таблицы по этому периоду
                try:
                    cashback_by_category = get_cashback_by_category(
                        categories_for_month
                    )  # Получаю необходимый период (выбранный месяц, год)
                    result_df = pd.DataFrame.from_dict(
                        cashback_by_category, orient="index", columns=["Кэшбэк"]
                    )
                    result_df = result_df.sort_values(by="Кэшбэк", ascending=False)

                    logger.info(
                        f"Функция отработала успешно. Найдено {len(result_df)} категорий с кэшбэком"
                    )
                    return result_df

                except Exception as e:
                    logger.error(f"Ошибка при расчете кэшбэка по категориям: {str(e)}")
                    raise Exception(
                        f"Ошибка при расчете кэшбэка по категориям: {str(e)}"
                    ) from e

            except Exception as e:
                logger.error(f"Ошибка при фильтрации данных по периоду: {str(e)}")
                raise Exception(
                    f"Ошибка при фильтрации данных по периоду: {str(e)}"
                ) from e

        except FileNotFoundError as e:
            logger.error(f"Файл не найден: {str(e)}")
            raise FileNotFoundError(f"Файл не найден: {str(e)}") from e
        except pd.errors.EmptyDataError as e:
            logger.error(f"Файл пуст или поврежден: {str(e)}")
            raise ValueError(f"Файл пуст или поврежден: {str(e)}") from e
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {str(e)}")
            raise Exception(f"Ошибка при чтении файла: {str(e)}") from e

    except Exception as e:
        if logger:
            logger.error(f"Ошибка в функции: {str(e)}")
        raise Exception(f"Ошибка в функции: {str(e)}") from e
