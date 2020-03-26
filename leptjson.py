#!/usr/local/bin/python3
# encoding: utf-8
from typing import Union, Optional, Tuple, List, Dict

JsonBasicType = Union[str, float, Dict, List, None, bool]
POSITIVE_INTEGERS_SET = set('123456789')
NONNEGATIVE_INTEGERS_SET = set('0123456789')
JSON_SPACE_CHARACTERS_SET = set(' \t\n\r')
ESCAPE_CHARACTER_MAPPING = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n',
                            'r': '\r', 't': '\t'}


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
            return ''


def parse(json_string: str) -> JsonBasicType:
    json_string = String(json_string)
    current_index = _parse_whitespace(json_string, 0)
    result, current_index = _parse_value(json_string, current_index)
    current_index = _parse_whitespace(json_string, current_index)
    if json_string[current_index] == '':
        return result
    raise _LeptJsonParseError("lept parse root not singular")


def stringify(obj: JsonBasicType) -> str:
    if obj is None:
        return "null"
    if obj is False:
        return "false"
    if obj is True:
        return "true"
    if isinstance(obj, (int, float)):
        # return f'{obj:.17f}'
        return '{0:.17g}'.format(obj)
    if isinstance(obj, str):
        buffer = ['"']
        for char in obj:
            char_ord = ord(char)
            if char_ord == 0x22:
                buffer.append('\\"')
            elif char_ord == 0x5c:
                buffer.append('\\\\')
            elif char_ord == 0x08:
                buffer.append('\\b')
            elif char_ord == 0x0c:
                buffer.append('\\f')
            elif char_ord == 0x0a:
                buffer.append('\\n')
            elif char_ord == 0x0d:
                buffer.append('\\r')
            elif char_ord == 0x09:
                buffer.append('\\t')
            elif (0x20 <= char_ord <= 0x21) or (0x23 <= char_ord <= 0x5b) or (
                    0x5d <= char_ord <= 0x10ffff):
                buffer.append(char)
            elif char_ord < 0x20:
                buffer.append('\\u{0:04x}'.format(char_ord))
        buffer.append('"')
        return ''.join(buffer)
    if isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            return '[]'
        buffer = ['[']
        for element in obj:
            buffer.append(stringify(element))
            buffer.append(',')
        buffer[-1] = ']'
        return ''.join(buffer)
    if isinstance(obj, dict):
        if len(obj) == 0:
            return '{}'
        buffer = ['{']
        for key, value in obj.items():
            buffer.append(stringify(key))
            buffer.append(':')
            buffer.append(stringify(value))
            buffer.append(',')
        buffer[-1] = '}'
        return ''.join(buffer)


def _parse_whitespace(json_string: String, current_index: int) -> int:
    while json_string[current_index] in JSON_SPACE_CHARACTERS_SET:
        current_index += 1
    return current_index


def _parse_value(json_string: String, current_index: int) -> Tuple[JsonBasicType, int]:
    element = json_string[current_index]
    if element == '':
        raise _LeptJsonParseError("lept parse expect value")
    if element == 'n':
        return _parse_literal(json_string, current_index, "null", None)
    if element == 't':
        return _parse_literal(json_string, current_index, "true", True)
    if element == 'f':
        return _parse_literal(json_string, current_index, "false", False)
    if element == '"':
        return _parse_string(json_string, current_index)
    if element == '[':
        return _parse_array(json_string, current_index)
    if element == '{':
        return _parse_object(json_string, current_index)
    return _parse_number(json_string, current_index)


def _parse_object(json_string: String, current_index: int) \
        -> Tuple[Dict[str, JsonBasicType], int]:
    result: Dict[str, JsonBasicType] = {}
    current_index += 1
    current_index = _parse_whitespace(json_string, current_index)
    if json_string[current_index] == '':
        raise _LeptJsonParseError("lept parse miss key")
    if json_string[current_index] == '}':
        return result, current_index + 1
    while json_string[current_index] != '':
        if json_string[current_index] != '"':
            raise _LeptJsonParseError("lept parse miss key")
        try:
            key, current_index = _parse_string(json_string, current_index)
        except _LeptJsonParseError:
            raise _LeptJsonParseError("lept parse miss key")
        current_index = _parse_whitespace(json_string, current_index)
        if json_string[current_index] != ':':
            raise _LeptJsonParseError("lept parse miss colon")
        current_index = _parse_whitespace(json_string, current_index + 1)
        value, current_index = _parse_value(json_string, current_index)
        result[key] = value
        current_index = _parse_whitespace(json_string, current_index)
        if json_string[current_index] != ',' and json_string[current_index] != '}':
            raise _LeptJsonParseError("lept parse miss comma or curly bracket")
        if json_string[current_index] == '}':
            return result, current_index + 1
        current_index = _parse_whitespace(json_string, current_index + 1)
    raise _LeptJsonParseError("lept parse miss key")


def _parse_array(json_string: String, current_index: int) \
        -> Tuple[List[JsonBasicType], int]:
    array: List[JsonBasicType] = []
    current_index += 1
    current_index = _parse_whitespace(json_string, current_index)
    if json_string[current_index] == ']':
        return array, current_index + 1
    while json_string[current_index] != '':
        value, current_index = _parse_value(json_string, current_index)
        array.append(value)
        current_index = _parse_whitespace(json_string, current_index)
        if json_string[current_index] == '':
            raise _LeptJsonParseError("lept parse miss comma or square bracket")
        if json_string[current_index] == ']':
            return array, current_index + 1
        if json_string[current_index] == ',':
            current_index = _parse_whitespace(json_string, current_index + 1)
        else:
            raise _LeptJsonParseError("lept parse miss comma or square bracket")
    raise _LeptJsonParseError("lept parse miss comma or square bracket")


# @profile
def _parse_surrogate_pair(json_string: String, current_index: int, high_surrogate: int) \
        -> Tuple[int, int]:
    if json_string[current_index] != '\\' or json_string[current_index + 1] != 'u':
        raise _LeptJsonParseError("lept parse invalid unicode surrogate")
    current_index += 2
    low_surrogate = _parse_hex4(json_string, current_index)

    if 0xdfff >= low_surrogate >= 0xdc00:
        return 0x10000 + (high_surrogate - 0xd800) * 0x400 + (low_surrogate - 0xdc00), \
               current_index + 4
    raise _LeptJsonParseError("lept parse invalid unicode surrogate")


def _parse_escape_character(json_string: String, current_index: int) -> Tuple[str, int]:
    current_index += 1
    current_element = json_string[current_index]
    if current_element == '':
        raise _LeptJsonParseError("lept parse invalid string escape")
    if current_element == 'u':
        code_point = _parse_hex4(json_string, current_index + 1)
        current_index += 5
        if 0xdbff >= code_point >= 0xd800:
            code_point, current_index = \
                _parse_surrogate_pair(json_string, current_index, code_point)
        return chr(code_point), current_index
    if current_element in ESCAPE_CHARACTER_MAPPING:
        return ESCAPE_CHARACTER_MAPPING[current_element], current_index + 1
    raise _LeptJsonParseError("lept parse invalid string escape")


def _parse_string(json_string: String, current_index: int) -> Tuple[str, int]:
    current_index += 1
    buffer: List[str] = []
    while (current_element := json_string[current_index]) != '"':
        if current_element == '':
            raise _LeptJsonParseError("lept parse miss quotation mark")
        if ord(current_element) >= 32 and current_element != '\\':
            buffer.append(current_element)
            current_index += 1
        elif current_element == '\\':
            escape_character, current_index = \
                _parse_escape_character(json_string, current_index)
            buffer.append(escape_character)
        elif ord(current_element) < 32:
            raise _LeptJsonParseError("lept parse invalid string char")
    return ''.join(buffer), current_index + 1


def _parse_hex4(json_string: String, current_index: int) -> int:
    return _str2hex(json_string, current_index, 4)


def _str2hex(json_string: String, current_index: int, hex_length: int) -> int:
    assert hex_length >= 0
    if json_string[current_index + hex_length - 1] == '':
        raise _LeptJsonParseError("lept parse invalid unicode hex")
    summation = 0
    power = 1
    for current_element in reversed(json_string[current_index:current_index + hex_length]):
        current_element_ord = ord(current_element)
        if ord('F') >= current_element_ord >= ord('A'):
            summation += (current_element_ord - ord('A') + 10) * power
        elif ord('9') >= current_element_ord >= ord('0'):
            summation += (current_element_ord - ord('0')) * power
        elif ord('f') >= current_element_ord >= ord('a'):
            summation += (current_element_ord - ord('a') + 10) * power
        else:
            raise _LeptJsonParseError("lept parse invalid unicode hex")
        power *= 16
    return summation


def _parse_literal(json_string: String, current_index: int, literal: str,
                   return_value: Optional[bool]) -> Tuple[Optional[bool], int]:
    if json_string[current_index:current_index + (length := len(literal))] == literal:
        return return_value, current_index + length
    raise _LeptJsonParseError("lept parse invalid value")


def _parse_number(json_string: String, current_index: int) -> Tuple[float, int]:
    end_index = _parse_number_aux(json_string, current_index)
    result = float(json_string[current_index:end_index])
    if result == float("Inf") or result == float("-Inf"):
        raise _LeptJsonParseError("lept parse number too big")
    return result, end_index


def _parse_number_aux(json_string: String, current_index: int) -> int:
    current_index = _parse_negative(json_string, current_index)
    current_index = _parse_int(json_string, current_index)
    current_index = _parse_frac(json_string, current_index)
    return _parse_exp(json_string, current_index)


def _parse_negative(json_string: String, current_index: int) -> int:
    if json_string[current_index] == '-':
        return current_index + 1
    return current_index


def _parse_int(json_string: String, current_index: int) -> int:
    if json_string[current_index] == '':
        raise _LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '0':
        return current_index + 1
    if json_string[current_index] in POSITIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


def _parse_frac(json_string: String, current_index: int) -> int:
    if json_string[current_index] == '' or json_string[current_index] != '.':
        return current_index
    current_index += 1
    if json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


def _parse_exp(json_string: String, current_index: int) -> int:
    if json_string[current_index] == '' or (
            json_string[current_index] != 'e' and json_string[current_index] != 'E'):
        return current_index
    current_index += 1
    if json_string[current_index] == '':
        raise _LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '-' or json_string[current_index] == '+':
        current_index += 1
    if json_string[current_index] == '':
        raise _LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise _LeptJsonParseError("lept parse invalid value")


if __name__ == '__main__':
    with open('data/twitter.json', encoding='utf-8') as f:
        large_obj_data = f.read()
        for _ in range(10):
            parse(large_obj_data)
