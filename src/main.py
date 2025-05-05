import json
from datetime import datetime

from src.reports import spending_by_category
from src.services import analyze_cashback_categories
from src.utils import get_time_for_greeting
from src.views import main_info

DATE_NOW = "2021-12-23 23:59:59"


def is_valid_date(year: str, month: str, day: str) -> bool:
    """Функция проверяет корректность введения даты"""
    try:
        year_int = int(year)
        month_int = int(month)
        day_int = int(day)
        datetime(year=year_int, month=month_int, day=day_int)
        return True
    except ValueError:
        return False


def get_user_date_choice(default_date: str) -> str:
    """Функция получает от пользователя выбор даты для отчета"""
    print(
        "\nХотите получить отчёт по категории за последние 3 месяца с текущей даты, или ввести другую дату?"
    )
    print("1 - С текущей даты")
    print("2 - Ввести дату")

    while True:
        choice = input("Ваш выбор (1-2): ")

        if choice == "1":
            return datetime.strptime(default_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%Y.%m.%d %H:%M:%S"
            )

        if choice == "2":
            while True:
                year = input("Введите год (например, 2021): ")
                month = input("Введите месяц (1-12): ")
                day = input("Введите число: ")

                if is_valid_date(year, month, day):
                    return datetime(
                        year=int(year),
                        month=int(month),
                        day=int(day),
                        hour=23,
                        minute=59,
                        second=59,
                    ).strftime("%Y.%m.%d %H:%M:%S")

                print("Ошибка: такой даты не существует!")

        print("Некорректный выбор. Пожалуйста, введите 1 или 2.")


def handle_category_report(default_date: str) -> None:
    """Функция обрабатывает запрос отчета по категории"""
    while True:
        category = input("Введите название категории: ").strip()
        if not category:
            print("Название категории не может быть пустым.")
            continue

        date = get_user_date_choice(default_date)

        try:
            result = spending_by_category("../data/operations.xlsx", category, date)
            if result.empty:
                print("За данный период операций по этой категории не производилось")
            else:
                print(f"\nРасходы по категории '{category}':")
                print(result.to_string(index=False))
            break
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            break


def handle_cashback_report() -> None:
    """Функция обрабатывает запрос отчета по кэшбэку"""
    while True:
        year = input("Введите год (например, 2021): ")
        month = input("Введите месяц (1-12): ")

        if not (year.isdigit() and month.isdigit()):
            print("Год и месяц должны быть числами.")
            continue

        year_int = int(year)
        month_int = int(month)

        if not (1 <= month_int <= 12 and 1957 <= year_int <= datetime.now().year):
            print("Некорректный год или месяц.")
            continue

        print("\nАнализируем категории кэшбэка...")
        try:
            result = analyze_cashback_categories(
                "../data/operations.xlsx", year_int, month_int
            )
            print(f"\nНаиболее выгодные категории кэшбэка за {month_int}/{year_int}:")
            print(result.to_string())
            break
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            break


def print_main_info(main_data: dict) -> None:
    """Функция выводит основную информацию"""
    print(f"{get_time_for_greeting()}")

    print("\nСписок трат за текущий месяц:")
    for card in main_data["cards"]:
        print(
            f"Карта ****{card['last_digits']}: потрачено {card['total_spent']}, кэшбэк {card['cashback']}"
        )

    print("\nТоп-5 транзакций за текущий месяц:")
    for i, transaction in enumerate(main_data["top_transactions"], 1):
        print(
            f"{i}. {transaction['date']} - {transaction['amount']} "
            f"({transaction['category']}/{transaction['description']})"
        )

    print("\nКурсы валют:")
    for rate in main_data["currency_rates"]:
        print(f"{rate['currency']}: {rate['rate']} RUB")

    print("\nЦены акций:")
    for stock in main_data["stock_prices"]:
        print(f"{stock['stock']}: {stock['price']} USD")


def main() -> None:
    """Основная функция для вывода функционала"""
    try:
        main_result = main_info(DATE_NOW)
        main_data = json.loads(main_result)
        print_main_info(main_data)

        while True:
            print("\nХотите получить дополнительный отчет?")
            print("1 - Операции по категории за последние 3 месяца с необходимой даты")
            print("2 - Наиболее выгодные категории кэшбэка за месяц")
            print("0 - Выход")

            choice = input("Ваш выбор (0-2): ").strip()

            if choice == "0":
                print("Выход из программы.")
                break
            elif choice == "1":
                handle_category_report(DATE_NOW)
            elif choice == "2":
                handle_cashback_report()
            else:
                print("Некорректный выбор. Пожалуйста, введите 0, 1 или 2.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    main()
