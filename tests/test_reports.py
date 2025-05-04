import logging
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import spending_by_category


def test_spending_by_category_success(tmpdir):
    """Тест успешного выполнения функции spending_by_category"""
    # Создаем тестовый файл
    test_file = tmpdir.join("test_operations.xlsx")
    test_data = {
        "Дата операции": ["01.05.2023 10:00:00", "15.05.2023 14:30:00", "31.05.2023 23:59:59"],
        "Категория": ["Другое", "Еда", "Другое"],
        "Сумма операции": [100, 200, 300]
    }
    df = pd.DataFrame(test_data)
    df.to_excel(test_file, sheet_name="Отчет по операциям", index=False)

    result = spending_by_category(str(test_file), "Другое", "2023.05.31 23:59:59")
    assert len(result) == 2
    assert all(result["Категория"] == "Другое")

def test_spending_by_category_empty_result(tmpdir):
    """Тест функции spending_by_category без результатов"""
    test_file = tmpdir.join("test_operations.xlsx")
    test_data = {
        "Дата операции": ["01.05.2023"],
        "Категория": ["Еда"],
        "Сумма операции": [100]
    }
    df = pd.DataFrame(test_data)
    df.to_excel(test_file, sheet_name="Отчет по операциям", index=False)

    result = spending_by_category(str(test_file), "Другое", "2023.05.31 23:59:59")
    assert len(result) == 0

def test_spending_by_category_file_not_found():
    """Тест функции spending_by_category с несуществующим файлом"""
    with pytest.raises(Exception, match="Ошибка в функции: Ошибка при обработке данных"):
        spending_by_category("nonexistent_file.xlsx", "Другое", "2023.05.31 23:59:59")

def test_spending_by_category_invalid_date_format(tmpdir):
    """Тест функции spending_by_category с некорректным форматом даты"""
    test_file = tmpdir.join("test_operations.xlsx")
    pd.DataFrame().to_excel(test_file)

    with pytest.raises(Exception, match="Некорректный формат даты"):
        spending_by_category(str(test_file), "Другое", "2023-05-31")

def test_spending_by_category_empty_category(tmpdir):
    """Тест функции spending_by_category с пустой категорией"""
    test_file = tmpdir.join("test_operations.xlsx")
    pd.DataFrame().to_excel(test_file)

    with pytest.raises(Exception, match="Параметры path_to_file и category не могут быть пустыми строками"):
        spending_by_category(str(test_file), "", "2023.05.31 23:59:59")

def test_spending_by_category_wrong_input_types(tmpdir):
    """Тест функции spending_by_category с неправильными типами параметров"""
    test_file = tmpdir.join("test_operations.xlsx")
    pd.DataFrame().to_excel(test_file)

    with pytest.raises(Exception, match="Параметр path_to_file должен быть строкой"):
        spending_by_category(123, "Другое", "2023.05.31 23:59:59")

    with pytest.raises(Exception, match="Параметр category должен быть строкой"):
        spending_by_category(str(test_file), 123, "2023.05.31 23:59:59")

    with pytest.raises(Exception, match="Параметр date должен быть строкой или None"):
        spending_by_category(str(test_file), "Другое", 123)

@patch('src.utils.setup_function_logger')
def test_spending_by_category_logging(mock_logger, tmpdir):
    """Тест логирования функции spending_by_category"""
    test_file = tmpdir.join("test_operations.xlsx")
    test_data = {
        "Дата операции": ["01.05.2023"],
        "Категория": ["Другое"],
        "Сумма операции": [100]
    }
    df = pd.DataFrame(test_data)
    df.to_excel(test_file, sheet_name="Отчет по операциям", index=False)

    mock_logger.return_value = logging.getLogger('test')
    with patch.object(mock_logger.return_value, 'info') as mock_info:
        spending_by_category(str(test_file), "Другое", "2023.05.31 23:59:59")
        assert mock_info.call_count == 2

def test_spending_by_category_logger_error(tmpdir):
    """Тест функции spending_by_category при ошибке инициализации логгера"""
    test_file = tmpdir.join("test_operations.xlsx")
    pd.DataFrame().to_excel(test_file)

    with patch('src.utils.setup_function_logger', side_effect=Exception("Logger error")):
        with pytest.raises(Exception, match="Ошибка в функции: Logger error"):
            spending_by_category(str(test_file), "Другое", "2023.05.31 23:59:59")