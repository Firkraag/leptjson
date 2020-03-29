#!/usr/local/bin/env python3.8
# encoding: utf-8
"""
Implementation of json
JSON Standard: https://tools.ietf.org/html/rfc7159.html
Inspired by https://zhuanlan.zhihu.com/json-tutorial
"""
from typing import Union, Optional, Tuple, List, Dict
from string import hexdigits

JsonBasicType = Union[str, float, Dict, List, None, bool]
POSITIVE_INTEGERS_SET = set('123456789')
NONNEGATIVE_INTEGERS_SET = set('0123456789')
JSON_SPACE_CHARACTERS_SET = set(' \t\n\r')
ESCAPE_CHARACTER_MAPPING = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n',
                            'r': '\r', 't': '\t'}


class LeptJsonParseError(Exception):
    """
    Raised when encountering json string parsing error
    """

    def __init__(self, msg):
        super(LeptJsonParseError, self).__init__(msg)
        self.msg = msg


class LeptJsonStringifyError(Exception):
    """
    Raised when encountering python object stringify error
    """

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class _String:
    def __init__(self, string: str):
        self._string = string

    def __getitem__(self, item):
        try:
            return self._string[item]
        except IndexError:
            return ''


def parse(json_string: str) -> JsonBasicType:
    """
    deserialize a json string into python object
    :param json_string:
    :return:
    """
    json_string = _String(json_string)
    current_index = _parse_whitespace(json_string, 0)
    result, current_index = _parse_value(json_string, current_index)
    current_index = _parse_whitespace(json_string, current_index)
    if json_string[current_index] == '':
        return result
    raise LeptJsonParseError("lept parse root not singular")


def stringify(obj: Union[None, bool, int, float, str, List, Tuple, Dict]) -> str:
    """
    serialize a python object into json string
    :param obj:
    :return:
    """
    if obj is None:
        return "null"
    if obj is False:
        return "false"
    if obj is True:
        return "true"
    if isinstance(obj, (int, float)):
        return '{0:.17g}'.format(obj)
    if isinstance(obj, str):
        return _stringify_str(obj)
    if isinstance(obj, (list, tuple)):
        return _stringify_sequence(obj)
    if isinstance(obj, dict):
        return _stringify_dict(obj)
    # Can only stringify limited number of class
    raise LeptJsonStringifyError(f"Cannot stringify instance of {type(obj)}")


def _stringify_sequence(sequence: Union[List, Tuple]) -> str:
    if len(sequence) == 0:
        return '[]'
    buffer = ['[']
    for element in sequence:
        buffer.append(stringify(element))
        buffer.append(',')
    # According to the json standard,
    # there shall not be ',' after the last element,
    # and we change it to ']'
    buffer[-1] = ']'
    return ''.join(buffer)


def _stringify_dict(obj: Dict) -> str:
    if len(obj) == 0:
        return '{}'
    buffer = ['{']
    for key, value in obj.items():
        buffer.append(stringify(key))
        buffer.append(':')
        buffer.append(stringify(value))
        buffer.append(',')
    # According to the json standard,
    # there shall not be ',' after the last element,
    # and we change it to '}'
    buffer[-1] = '}'
    return ''.join(buffer)


# definition of json string

# string = quotation-mark *char quotation-mark
#
#      char = unescaped /
#          escape (
#              %x22 /          ; "    quotation mark  U+0022
#              %x5C /          ; \    reverse solidus U+005C
#              %x2F /          ; /    solidus         U+002F
#              %x62 /          ; b    backspace       U+0008
#              %x66 /          ; f    form feed       U+000C
#              %x6E /          ; n    line feed       U+000A
#              %x72 /          ; r    carriage return U+000D
#              %x74 /          ; t    tab             U+0009
#              %x75 4HEXDIG )  ; uXXXX                U+XXXX
#
#      escape = %x5C              ; \
#
#      quotation-mark = %x22      ; "
#
#      unescaped = %x20-21 / %x23-5B / %x5D-10FFFF

def _stringify_str(obj: str) -> str:
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
        # these unicode can be directly put into json string
        elif (0x20 <= char_ord <= 0x21) or (0x23 <= char_ord <= 0x5b) or (
                0x5d <= char_ord <= 0x10ffff):
            buffer.append(char)
        # No control characters allowed in json string, must be escaped.
        elif char_ord < 0x20:
            buffer.append('\\u{0:04x}'.format(char_ord))
    buffer.append('"')
    return ''.join(buffer)


def _parse_whitespace(json_string: _String, current_index: int) -> int:
    """
    :param json_string:
    :param current_index:
    :return: the position after whitespace
    """
    while json_string[current_index] in JSON_SPACE_CHARACTERS_SET:
        current_index += 1
    return current_index


def _parse_value(json_string: _String, current_index: int) -> Tuple[JsonBasicType, int]:
    """

    :param json_string:
    :param current_index:
    :return: tuple of a json value and the position after the json value
    """
    element = json_string[current_index]
    if element == '':
        raise LeptJsonParseError("lept parse expect value")
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


def _parse_object(json_string: _String, current_index: int) \
        -> Tuple[Dict[str, JsonBasicType], int]:
    result: Dict[str, JsonBasicType] = {}
    current_index += 1
    current_index = _parse_whitespace(json_string, current_index)
    if json_string[current_index] == '':
        raise LeptJsonParseError("lept parse miss key")
    if json_string[current_index] == '}':
        return result, current_index + 1
    while json_string[current_index] != '':
        if json_string[current_index] != '"':
            raise LeptJsonParseError("lept parse miss key")
        try:
            key, current_index = _parse_string(json_string, current_index)
        except LeptJsonParseError:
            raise LeptJsonParseError("lept parse miss key")
        current_index = _parse_whitespace(json_string, current_index)
        if json_string[current_index] != ':':
            raise LeptJsonParseError("lept parse miss colon")
        current_index = _parse_whitespace(json_string, current_index + 1)
        value, current_index = _parse_value(json_string, current_index)
        result[key] = value
        current_index = _parse_whitespace(json_string, current_index)
        if json_string[current_index] != ',' and json_string[current_index] != '}':
            raise LeptJsonParseError("lept parse miss comma or curly bracket")
        if json_string[current_index] == '}':
            return result, current_index + 1
        current_index = _parse_whitespace(json_string, current_index + 1)
    raise LeptJsonParseError("lept parse miss key")


def _parse_array(json_string: _String, current_index: int) \
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
            raise LeptJsonParseError("lept parse miss comma or square bracket")
        if json_string[current_index] == ']':
            return array, current_index + 1
        if json_string[current_index] == ',':
            current_index = _parse_whitespace(json_string, current_index + 1)
        else:
            raise LeptJsonParseError("lept parse miss comma or square bracket")
    raise LeptJsonParseError("lept parse miss comma or square bracket")


def _parse_string(json_string: _String, current_index: int) -> Tuple[str, int]:
    current_index += 1
    buffer: List[str] = []
    while (current_element := json_string[current_index]) != '"':
        if current_element == '':
            raise LeptJsonParseError("lept parse miss quotation mark")
        if ord(current_element) < 0x20:
            raise LeptJsonParseError("lept parse invalid string char")
        if current_element == '\\':
            escape_character, current_index = \
                _parse_escape_character(json_string, current_index)
            buffer.append(escape_character)
        else:
            buffer.append(current_element)
            current_index += 1
    return ''.join(buffer), current_index + 1


def _parse_escape_character(json_string: _String, current_index: int) -> Tuple[str, int]:
    current_index += 1
    current_element = json_string[current_index]
    if current_element == '':
        raise LeptJsonParseError("lept parse invalid string escape")
    if current_element == 'u':
        code_point = _str2hex(json_string, current_index + 1, 4)
        current_index += 5
        # unicode bigger than 0xFFFF is represented as "\uxxxx\uyyyy",
        # where 0xdbff >= 0xxxxx >= 0xd800 and 0xdfff >= 0xyyyy >= 0xdc00
        if 0xdbff >= code_point >= 0xd800:
            code_point, current_index = \
                _parse_surrogate_pair(json_string, current_index, code_point)
        return chr(code_point), current_index
    if current_element in ESCAPE_CHARACTER_MAPPING:
        return ESCAPE_CHARACTER_MAPPING[current_element], current_index + 1
    raise LeptJsonParseError("lept parse invalid string escape")


def _parse_surrogate_pair(json_string: _String, current_index: int, high_surrogate: int) \
        -> Tuple[int, int]:
    """

    :param json_string:
    :param current_index:
    :param high_surrogate:
    :return:
    """
    if json_string[current_index] != '\\' or json_string[current_index + 1] != 'u':
        raise LeptJsonParseError("lept parse invalid unicode surrogate")
    current_index += 2
    low_surrogate = _str2hex(json_string, current_index, 4)
    if 0xdfff >= low_surrogate >= 0xdc00:
        # the formulae to compute unicode from surrogate pair
        return 0x10000 + (high_surrogate - 0xd800) * 0x400 + (low_surrogate - 0xdc00), \
               current_index + 4
    raise LeptJsonParseError("lept parse invalid unicode surrogate")


def _str2hex(json_string: _String, current_index: int, hex_length: int) -> int:
    """
    convert hexadecimal string to decimal
    :param json_string:
    :param current_index: start position of hexadecimal string
    :param hex_length: length of hexadecimal string
    :return:
    """
    assert hex_length >= 0
    if json_string[current_index + hex_length - 1] == '':
        raise LeptJsonParseError("lept parse invalid unicode hex")
    hexadecimal_string = json_string[current_index:current_index + hex_length]
    if all(character in hexdigits for character in hexadecimal_string):
        return int(hexadecimal_string, 16)
    raise LeptJsonParseError("lept parse invalid unicode hex")


def _parse_literal(json_string: _String, current_index: int, literal: str,
                   return_value: Optional[bool]) -> Tuple[Optional[bool], int]:
    if json_string[current_index:current_index + len(literal)] == literal:
        return return_value, current_index + len(literal)
    raise LeptJsonParseError("lept parse invalid value")


def _parse_number(json_string: _String, current_index: int) -> Tuple[float, int]:
    end_index = _parse_number_aux(json_string, current_index)
    result = float(json_string[current_index:end_index])
    if result == float("Inf") or result == float("-Inf"):
        raise LeptJsonParseError("lept parse number too big")
    return result, end_index


def _parse_number_aux(json_string: _String, current_index: int) -> int:
    current_index = _parse_negative(json_string, current_index)
    current_index = _parse_int(json_string, current_index)
    current_index = _parse_fraction(json_string, current_index)
    return _parse_exp(json_string, current_index)


def _parse_negative(json_string: _String, current_index: int) -> int:
    if json_string[current_index] == '-':
        return current_index + 1
    return current_index


def _parse_int(json_string: _String, current_index: int) -> int:
    if json_string[current_index] == '':
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '0':
        return current_index + 1
    if json_string[current_index] in POSITIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_fraction(json_string: _String, current_index: int) -> int:
    if json_string[current_index] == '' or json_string[current_index] != '.':
        return current_index
    current_index += 1
    if json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_exp(json_string: _String, current_index: int) -> int:
    if json_string[current_index] == '' or (
            json_string[current_index] != 'e' and json_string[current_index] != 'E'):
        return current_index
    current_index += 1
    if json_string[current_index] == '':
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '-' or json_string[current_index] == '+':
        current_index += 1
    if json_string[current_index] == '':
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
        while json_string[current_index] in NONNEGATIVE_INTEGERS_SET:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


if __name__ == '__main__':
    with open('data/twitter.json', encoding='utf-8') as f:
        large_obj_data = f.read()
        for _ in range(10):
            parse(large_obj_data)
