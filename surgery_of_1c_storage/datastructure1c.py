from enum import Enum
from uuid import UUID
from datetime import datetime
import json
import re


class DataStructure1C:
    """Интерфейс для парсера внутренней структуры 1С и компоновщика в нее же"""
    _tree = []  # Результат разложения строки
    _text = ''  # Результат компоновки в строку

    def __init__(self, text=''):
        self._tree = []
        if text:
            self.parse_text(text)

    def parse_text(self, text=''):
        if text:
            self._text = text
        self._tree = Parser1C(self._text).get_tree()
        return self._tree

    def compose_text(self, tree=[]):
        if tree:
            self._tree = tree
        self._text = Composer1C(self._tree).get_text()
        return self._text

    def to_json(self):
        class UUIDEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, UUID):
                    return obj.hex
                return json.JSONEncoder.default(self, obj)

        return json.dumps(self._tree, cls=UUIDEncoder)

    def to_utf(self):
        return self._text


class SeparateKeys(Enum):
    OPENING_BRACE = '{'
    CLOSING_BRACE = '}'
    SPLITTER = ','
    STR_QUOTE = '"'
    BOM = b'\xef\xbb\xbf'.decode('utf-8')
    NL = '\r\n'

    def __eq__(self, other):
        return self.value == other

    def __str__(self):
        return self.value


class ValueTypes(Enum):
    STRING = 'string'
    INTEGER = 'integer'
    UUID = 'uuid'
    DATETIME = 'datetime'

    def __eq__(self, other):
        return self.value == other


class Parser1C:
    """Реализация разложения внутреннего формата 1С на вложенных списках"""

    def __init__(self, text):
        self.__tree__ = []
        self.__text_for_parsing__ = text
        self.__current_index__ = 0
        self.__current_list__ = None
        self.__current_string__ = None
        self.__current_type_of_value__ = None
        self.__previous_symbol__ = None
        self._parse_text()

    def get_tree(self):
        return self.__tree__

    def _parse_text(self):
        current_list = self.__current_list__
        while not self._the_end():
            symbol = self._pop_symbol()
            if symbol == SeparateKeys.OPENING_BRACE:
                self._dive_to_the_next_level(current_list)
            elif symbol == SeparateKeys.CLOSING_BRACE:
                # Зафиксируем текущее значение
                self._completes_current_value()
                self.__previous_symbol__ = symbol
                # Возвращаемся на уровень выше по стеку рекурсии
                return
            elif symbol == SeparateKeys.SPLITTER:
                # Предыдущее значение закончилось
                self._completes_current_value()
            elif symbol == SeparateKeys.STR_QUOTE:
                # Начинается чтение текста, выполянется в отдельном режиме до парной кавычки
                self._read_string_value()
            elif symbol.isspace() or symbol == SeparateKeys.BOM:
                # Пробельный символ просто игнорируем
                pass
            else:
                self._add_symbol_to_string(symbol)
            self.__previous_symbol__ = symbol

    def _the_end(self):
        # Текущий индекс ссылается на последний символ
        return self.__current_index__ == (len(self.__text_for_parsing__))

    def _pop_symbol(self):
        symbol = self.__text_for_parsing__[self.__current_index__]
        self.__current_index__ += 1
        return symbol

    def _dive_to_the_next_level(self, current_list):
        # Добавляем список уровнем ниже
        self._append_new_list()
        # Продолжаем парсинг
        self._parse_text()
        # Возвращаем уровень списка, который был до погружения в рекурсию
        self.__current_list__ = current_list

    def _append_new_list(self):
        if not self.__current_list__:
            # Если текущий список не определен, значит только инициализировали парсинг
            # Для продолжения берем за основу первый - корневой список
            self.__current_list__ = self.__tree__
            return

        # Получаем список текущего уровня
        current_list = self.__current_list__

        # Создаем список нового уровня
        new_list = []
        # Помещаем его в конец текущего уровня
        current_list.append(new_list)
        # Делаем текущим новый список
        self.__current_list__ = new_list

    def _read_string_value(self):
        self.__current_type_of_value__ = ValueTypes.STRING
        self.__current_string__ = ''
        symbol = self._pop_symbol()
        # Читаем символы пока не дойдем до кавычки
        while symbol != SeparateKeys.STR_QUOTE:
            self._add_symbol_to_string(symbol)
            symbol = self._pop_symbol()

    def _completes_current_value(self):
        # Текущее значение может быть не указано, если завершается вложенный блок - сочетание }}
        if self.__current_type_of_value__:
            # Выразим (приведем тип) текущего значения
            current_value = self._cast_current_value()
            # Добавим его в список текущего уровня
            self.__current_list__.append(current_value)
        elif self.__previous_symbol__ == SeparateKeys.SPLITTER:
            # Если предыдущий непробельный символ был SPLITTER, то помещаем в список пустое значение - сочетание ,,
            self.__current_list__.append(None)
        # Сборсим параметры с текущим значением
        self.__current_string__ = None
        self.__current_type_of_value__ = None

    def _cast_current_value(self):
        # Проверим неявные признаки, того что значение может быть датой
        if self._is_data_value():
            self.__current_type_of_value__ = ValueTypes.DATETIME

        # В завимисимости от вычисленного типа выполним приведение
        if self.__current_type_of_value__ == ValueTypes.STRING:
            return self.__current_string__
        elif self.__current_type_of_value__ == ValueTypes.INTEGER:
            return int(self.__current_string__)
        elif self.__current_type_of_value__ == ValueTypes.UUID:
            return UUID(self.__current_string__)
        elif self.__current_type_of_value__ == ValueTypes.DATETIME:
            # Пробуем обернуть в дату, иначе оставляем как число
            try:
                value = datetime.strptime(self.__current_string__, '%Y%m%d%H%M%S')
            except:
                value = int(self.__current_string__)
            return value
        else:
            raise Exception(f'Нераспознанный тип значения: {self.__current_type_of_value__}')

    def _add_symbol_to_string(self, symbol):
        # Тип еще может быть не определен
        if not self.__current_type_of_value__:
            # Типа STRING здесь быть не может, так как он определяется в отдельной процедуре
            if symbol.isdigit():
                # Это вероятно целочисленное значение
                self.__current_type_of_value__ = ValueTypes.INTEGER
            else:
                # Это вероятно UUID
                self.__current_type_of_value__ = ValueTypes.UUID
        elif self.__current_type_of_value__ == ValueTypes.INTEGER and not symbol.isdigit():
            # Если ранее предположили, что тип целочисленный, а сейчас встретили нечисловой символ, то значит, это UUID
            self.__current_type_of_value__ = ValueTypes.UUID

        if not self.__current_string__:
            # Только начали читать новое значение
            self.__current_string__ = ''
        self.__current_string__ += symbol

    def _is_data_value(self):
        if self.__current_type_of_value__ != ValueTypes.INTEGER:
            # Строка должна быть из цифр (целочисленный тип)
            return False
        if len(self.__current_string__) != 14:
            # Длина должна быть 14 символов - соответствует маске ггггммддЧЧММСС
            return False
        # Примитивная проверка на формат даты. Ограничения на 33 число месяца или 26 час не предусмотрены
        if re.match(r'\d{4}[01]\d[0-3]\d[0-2]\d[0-5]\d[0-5]\d', self.__current_string__):
            return True
        else:
            return False


class Composer1C:
    """Реализация мехнизма составления данных из вложенных списоков во внутренний формат 1С"""

    def __init__(self, tree):
        self.__text__ = ''
        self.__tree_for_compose__ = tree
        self.__current_list = None
        self.__current_list_has_nested_list = None
        self._compose_subtree(self.__tree_for_compose__)

    def get_text(self):
        return self.__text__

    def _compose_subtree(self, current_element):
        # Выводим открывающуюся скобку
        if self.__text__:
            # При погружении на новый уровень вложенности добавляем перенос строки
            self.__text__ += str(SeparateKeys.NL)
            the_first_level = False
        else:
            # В начале текста выводим символы BOM
            self.__text__ = str(SeparateKeys.BOM)
            the_first_level = True

        self.__text__ += str(SeparateKeys.OPENING_BRACE)
        # Углубляемся в рекурсию
        self.__current_list = current_element
        self.__current_list_has_nested_list = False
        self._process_elements()
        # Выводим закрывающую скобку
        if self.__current_list_has_nested_list and not the_first_level:
            # Строка переносится только если были вложенные списки
            self.__text__ += str(SeparateKeys.NL)
        self.__text__ += str(SeparateKeys.CLOSING_BRACE)

    def _process_elements(self):
        current_list = self.__current_list
        # Обходим все элементы текущего списка
        the_first_element_in_list = True
        for current_element in current_list:
            if not the_first_element_in_list:
                self.__text__ += str(SeparateKeys.SPLITTER)

            if type(current_element) == list:
                # Если элемент сам является списком, то рекурсивно проваливаемся в него
                self._compose_subtree(current_element)
                self.__current_list_has_nested_list = True
            else:
                # Иначе выводим элемент в итоговую строку
                self._add_element_in_text(current_element)
            the_first_element_in_list = False

    def _add_element_in_text(self, element):
        if type(element) == str:
            self.__text__ += f'{str(SeparateKeys.STR_QUOTE)}{element}{str(SeparateKeys.STR_QUOTE)}'
        elif type(element) == int:
            self.__text__ += str(element)
        elif type(element) == UUID:
            self.__text__ += str(element)
        elif type(element) == datetime:
            self.__text__ += element.strftime('%Y%m%d%H%M%S')
        elif element is None:
            # Для пустого элемент ничего не выводим
            pass
        else:
            raise Exception(
                f"Ошибка разбора элементов дерева. Не удалось идентифицировать "
                f"тип элемента ({type(element)}) {element}")
