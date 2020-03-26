#!/usr/local/bin/python3
# encoding: utf-8
from itertools import islice
from typing import Union, Optional, Tuple, List, Dict

_JSON_BASIC_TYPE = Union[str, float, Dict, List, None, bool]
_POSITIVE_INTEGERS_LIST = '123456789'
_NONNEGATIVE_INTEGERS_LIST = '0123456789'
_JSON_SPACE_CHARACTERS_LIST = ' \t\n\r'


# mapping = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}


class _LeptJsonParseError(Exception):
    def __init__(self, msg):
        super(_LeptJsonParseError, self).__init__(msg)
        self.msg = msg


class String:
    def __init__(self, string: str):
        self._string = string

    def __getitem__(self, item):
        try:
            return self._string[item]
        except IndexError:
            return None


def lept_parse(json_string: str) -> _JSON_BASIC_TYPE:
    current_index = 0
    string_length = len(json_string)
    current_index = _lept_parse_whitespace(json_string, current_index)
    result, current_index = _lept_parse_value(json_string, current_index)
    current_index = _lept_parse_whitespace(json_string, current_index)
    if current_index < string_length:
        raise _LeptJsonParseError("lept parse root not singular")
    return result


def lept_stringify(obj):
    if obj is None:
        return "null"
    elif obj is False:
        return "false"
    elif obj is True:
        return "true"
    elif isinstance(obj, (int, float)):
        # return f'{obj:.17f}'
        return '{0:.17g}'.format(obj)
    elif isinstance(obj, str):
        l = ['"']
        for char in obj:
            char_ord = ord(char)
            if char_ord == 0x22:
                l.append('\\"')
            elif char_ord == 0x5c:
                l.append('\\\\')
            elif char_ord == 0x08:
                l.append('\\b')
            elif char_ord == 0x0c:
                l.append('\\f')
            elif char_ord == 0x0a:
                l.append('\\n')
            elif char_ord == 0x0d:
                l.append('\\r')
            elif char_ord == 0x09:
                l.append('\\t')
            elif (0x20 <= char_ord <= 0x21) or (0x23 <= char_ord <= 0x5b) or (
                    0x5d <= char_ord <= 0x10ffff):
                l.append(char)
            elif char_ord < 0x20:
                l.append('\\u{0:04x}'.format(char_ord))
        l.append('"')
        return ''.join(l)
    elif isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            return '[]'
        l = ['[']
        for element in obj:
            l.append(lept_stringify(element))
            l.append(',')
        l[-1] = ']'
        return ''.join(l)
    elif isinstance(obj, dict):
        if len(obj) == 0:
            return '{}'
        l = ['{']
        for key, value in obj.items():
            l.append(lept_stringify(key))
            l.append(':')
            l.append(lept_stringify(value))
            l.append(',')
        l[-1] = '}'
        return ''.join(l)


def _lept_parse_whitespace(json_string: str, current_index: int):
    while current_index < len(json_string) and \
            json_string[current_index] in _JSON_SPACE_CHARACTERS_LIST:
        current_index += 1
    return current_index


def _lept_parse_value(json_string: str, current_index: int) -> Tuple[_JSON_BASIC_TYPE, int]:
    if current_index >= len(json_string):
        raise _LeptJsonParseError("lept parse expect value")
    element = json_string[current_index]
    if element == 'n':
        return _lept_parse_literal(json_string, current_index, "null", None)
    elif element == 't':
        return _lept_parse_literal(json_string, current_index, "true", True)
    elif element == 'f':
        return _lept_parse_literal(json_string, current_index, "false", False)
    elif element == '"':
        return _lept_parse_string(json_string, current_index)
    elif element == '[':
        return _lept_parse_array(json_string, current_index)
    elif element == '{':
        return _lept_parse_object(json_string, current_index)
    else:
        return _lept_parse_number(json_string, current_index)


def _lept_parse_object(json_string: str, current_index: int) -> Tuple[
    Dict[str, _JSON_BASIC_TYPE], int]:
    result: Dict[str, _JSON_BASIC_TYPE] = {}
    current_index += 1
    current_index = _lept_parse_whitespace(json_string, current_index)
    if current_index >= len(json_string):
        raise _LeptJsonParseError("lept parse miss key")
    if json_string[current_index] == '}':
        return result, current_index + 1
    while current_index < len(json_string):
        if json_string[current_index] != '"':
            raise _LeptJsonParseError("lept parse miss key")
        try:
            key, current_index = _lept_parse_string(json_string, current_index)
        except:
            raise _LeptJsonParseError("lept parse miss key")
        current_index = _lept_parse_whitespace(json_string, current_index)
        if current_index >= len(json_string) or json_string[current_index] != ':':
            raise _LeptJsonParseError("lept parse miss colon")
        current_index += 1
        current_index = _lept_parse_whitespace(json_string, current_index)
        value, current_index = _lept_parse_value(json_string, current_index)
        result[key] = value
        current_index = _lept_parse_whitespace(json_string, current_index)
        if current_index >= len(json_string) or (
                json_string[current_index] != ',' and json_string[current_index] != '}'):
            raise _LeptJsonParseError("lept parse miss comma or curly bracket")
        if json_string[current_index] == '}':
            return result, current_index + 1
        current_index += 1
        current_index = _lept_parse_whitespace(json_string, current_index)
    raise _LeptJsonParseError("lept parse miss key")


def _lept_parse_array(json_string: str, current_index: int) -> Tuple[List[_JSON_BASIC_TYPE], int]:
    result: List[_JSON_BASIC_TYPE] = []
    current_index += 1
    current_index = _lept_parse_whitespace(json_string, current_index)
    if json_string[current_index] == ']':
        return result, current_index + 1
    while current_index < len(json_string):
        value, current_index = _lept_parse_value(json_string, current_index)
        result.append(value)
        current_index = _lept_parse_whitespace(json_string, current_index)
        if current_index >= len(json_string):
            raise _LeptJsonParseError("lept parse miss comma or square bracket")
        elif json_string[current_index] == ']':
            return result, current_index + 1
        elif json_string[current_index] == ',':
            current_index = _lept_parse_whitespace(json_string, current_index + 1)
        else:
            raise _LeptJsonParseError("lept parse miss comma or square bracket")
    raise _LeptJsonParseError("lept parse miss comma or square bracket")


# @profile
def _lept_parse_string(json_string: str, current_index: int) -> Tuple[str, int]:
    current_index += 1
    l: List[_JSON_BASIC_TYPE] = []
    while True:
        try:
            current_element = json_string[current_index]
        except IndexError:
            raise _LeptJsonParseError("lept parse miss quotation mark")
        if ord(current_element) >= 32 and current_element != '"' and current_element != '\\':
            l.append(current_element)
            current_index += 1
        elif current_element == '"':
            return ''.join(l), current_index + 1
        elif current_element == '\\':
            current_index += 1
            try:
                current_element = json_string[current_index]
            except IndexError:
                raise _LeptJsonParseError("lept parse invalid string escape")

            if current_element == '"':
                l.append('"')
            elif current_element == '\\':
                l.append('\\')
            elif current_element == '/':
                l.append('/')
            elif current_element == 'b':
                l.append('\b')
            elif current_element == 'f':
                l.append('\f')
            elif current_element == 'n':
                l.append('\n')
            elif current_element == 'r':
                l.append('\r')
            elif current_element == 't':
                l.append('\t')
            elif current_element == 'u':
                code_point, current_index = _lept_parse_hex4(json_string, current_index + 1)
                if 0xdbff >= code_point >= 0xd800:
                    if current_index + 1 >= len(json_string) or \
                            (json_string[current_index] != '\\' or json_string[
                                current_index + 1] != 'u'):
                        raise _LeptJsonParseError("lept parse invalid unicode surrogate")
                    current_index += 2
                    low_surrogate, current_index = _lept_parse_hex4(json_string, current_index)
                    if 0xdfff >= low_surrogate >= 0xdc00:
                        code_point = 0x10000 + (code_point - 0xd800) * 0x400 + (
                                low_surrogate - 0xdc00)
                    else:
                        raise _LeptJsonParseError("lept parse invalid unicode surrogate")
                l.append(chr(code_point))
                continue
            else:
                raise _LeptJsonParseError("lept parse invalid string escape")
            current_index += 1
        elif ord(current_element) < 32:
            raise _LeptJsonParseError("lept parse invalid string char")


def _lept_parse_hex4(json_string: str, current_index: int) -> Tuple[int, int]:
    return _str2hex(json_string, current_index, 4)


def _str2hex(json_string: str, current_index: int, hex_length: int) -> Tuple[int, int]:
    assert hex_length >= 0
    if current_index + hex_length - 1 >= len(json_string):
        raise _LeptJsonParseError("lept parse invalid unicode hex")
    sum = 0
    power = 1
    for current_element in reversed(json_string[current_index:current_index + hex_length]):
        current_element_ord = ord(current_element)
        if ord('F') >= current_element_ord >= ord('A'):
            sum += (current_element_ord - ord('A') + 10) * power
        elif ord('9') >= current_element_ord >= ord('0'):
            sum += (current_element_ord - ord('0')) * power
        elif ord('f') >= current_element_ord >= ord('a'):
            sum += (current_element_ord - ord('a') + 10) * power
        else:
            raise _LeptJsonParseError("lept parse invalid unicode hex")
        power *= 16
    return sum, current_index + hex_length


def _lept_parse_literal(json_string: str, current_index: int, literal: str,
                        return_value: Optional[bool]) -> Tuple[Optional[bool], int]:
    # n = len(literal)
    if json_string[current_index:current_index + (n := len(literal))] == literal:
        return return_value, current_index + n
    raise _LeptJsonParseError("lept parse invalid value")


def _lept_parse_number(json_string: str, current_index: int) -> Tuple[float, int]:
    end_index = _parse_number(json_string, current_index)
    result = float(json_string[current_index:end_index])
    if result == float("Inf") or result == float("-Inf"):
        raise _LeptJsonParseError("lept parse number too big")
    return result, end_index


def _parse_number(json_string: str, current_index: int) -> int:
    current_index = _parse_negative(json_string, current_index)
    current_index = _parse_int(json_string, current_index)
    current_index = _parse_frac(json_string, current_index)
    return _parse_exp(json_string, current_index)


def _parse_negative(json_string: str, current_index: int) -> int:
    if json_string[current_index] == '-':
        return current_index + 1
    else:
        return current_index


def _parse_int(json_string: str, current_index: int) -> int:
    if current_index >= len(json_string):
        raise _LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '0':
        return current_index + 1
    if json_string[current_index] in _POSITIVE_INTEGERS_LIST:
        while current_index < len(json_string) and json_string[
            current_index] in _NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


def _parse_frac(json_string: str, current_index: int) -> int:
    if current_index >= len(json_string) or json_string[current_index] != '.':
        return current_index
    current_index += 1
    if current_index < len(json_string) and json_string[
        current_index] in _NONNEGATIVE_INTEGERS_LIST:
        while current_index < len(json_string) and json_string[
            current_index] in _NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


def _parse_exp(json_string: str, current_index: int) -> int:
    if current_index >= len(json_string) or (
            json_string[current_index] != 'e' and json_string[current_index] != 'E'):
        return current_index
    current_index += 1
    if current_index >= len(json_string):
        raise _LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '-' or json_string[current_index] == '+':
        current_index += 1
    if current_index >= len(json_string):
        raise _LeptJsonParseError("lept parse invalid value")
    if current_index < len(json_string) and json_string[
        current_index] in _NONNEGATIVE_INTEGERS_LIST:
        while current_index < len(json_string) and json_string[
            current_index] in _NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


loads = lept_parse
dumps = lept_stringify
if __name__ == '__main__':
    with open('data/twitter.json', encoding='utf-8') as f:
        large_obj_data = f.read()
        for _ in range(10):
            lept_parse(large_obj_data)
