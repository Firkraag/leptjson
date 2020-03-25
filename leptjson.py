#!/usr/local/bin/python3
# encoding: utf-8

POSITIVE_INTEGERS_LIST = '123456789'
NONNEGATIVE_INTEGERS_LIST = '0123456789'
JSON_SPACE_CHARACTERS_LIST = ' \t\n\r'
mapping = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}


class LeptJsonParseError(Exception):
    def __init__(self, msg):
        super(LeptJsonParseError, self).__init__(msg)
        self.msg = msg


def lept_parse(json_string):
    current_index = 0
    string_length = len(json_string)
    current_index = _lept_parse_whitespace(json_string, current_index, string_length)
    result, current_index = _lept_parse_value(json_string, current_index, string_length)
    current_index = _lept_parse_whitespace(json_string, current_index, string_length)
    if current_index < string_length:
        raise LeptJsonParseError("lept parse root not singular")
    else:
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


def _lept_parse_whitespace(json_string:str, current_index:int, string_length):
    while current_index < string_length and json_string[
        current_index] in JSON_SPACE_CHARACTERS_LIST:
        current_index += 1
    return current_index


def _lept_parse_value(json_string, current_index, string_length):
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse expect value")
    element = json_string[current_index]
    if element == 'n':
        return _lept_parse_literal(json_string, current_index, string_length, "null", None)
    elif element == 't':
        return _lept_parse_literal(json_string, current_index, string_length, "true", True)
    elif element == 'f':
        return _lept_parse_literal(json_string, current_index, string_length, "false", False)
    elif element == '"':
        return _lept_parse_string(json_string, current_index, string_length)
    elif element == '[':
        return _lept_parse_array(json_string, current_index, string_length)
    elif element == '{':
        return _lept_parse_object(json_string, current_index, string_length)
    else:
        return _lept_parse_number(json_string, current_index, string_length)


def _lept_parse_object(json_string, current_index, string_length):
    result = {}
    current_index += 1
    current_index = _lept_parse_whitespace(json_string, current_index, string_length)
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse miss key")
    if json_string[current_index] == '}':
        return result, current_index + 1
    while current_index < string_length:
        if json_string[current_index] != '"':
            raise LeptJsonParseError("lept parse miss key")
        try:
            key, current_index = _lept_parse_string(json_string, current_index, string_length)
        except:
            raise LeptJsonParseError("lept parse miss key")
        current_index = _lept_parse_whitespace(json_string, current_index, string_length)
        if current_index >= string_length or json_string[current_index] != ':':
            raise LeptJsonParseError("lept parse miss colon")
        current_index += 1
        current_index = _lept_parse_whitespace(json_string, current_index, string_length)
        value, current_index = _lept_parse_value(json_string, current_index, string_length)
        result[key] = value
        current_index = _lept_parse_whitespace(json_string, current_index, string_length)
        if current_index >= string_length or (
                json_string[current_index] != ',' and json_string[current_index] != '}'):
            raise LeptJsonParseError("lept parse miss comma or curly bracket")
        if json_string[current_index] == '}':
            return result, current_index + 1
        current_index += 1
        current_index = _lept_parse_whitespace(json_string, current_index, string_length)
    raise LeptJsonParseError("lept parse miss key")


def _lept_parse_array(json_string, current_index, string_length):
    result = []
    current_index += 1
    current_index = _lept_parse_whitespace(json_string, current_index, string_length)
    if json_string[current_index] == ']':
        return result, current_index + 1
    while current_index < string_length:
        value, current_index = _lept_parse_value(json_string, current_index, string_length)
        result.append(value)
        current_index = _lept_parse_whitespace(json_string, current_index, string_length)
        if current_index >= string_length:
            raise LeptJsonParseError("lept parse miss comma or square bracket")
        elif json_string[current_index] == ']':
            return result, current_index + 1
        elif json_string[current_index] == ',':
            current_index = _lept_parse_whitespace(json_string, current_index + 1, string_length)
        else:
            raise LeptJsonParseError("lept parse miss comma or square bracket")
    raise LeptJsonParseError("lept parse miss comma or square bracket")


# @profile
def _lept_parse_string(json_string, current_index, string_length):
    current_index += 1
    l = []
    while True:
        try:
            current_element = json_string[current_index]
        except IndexError:
            raise LeptJsonParseError("lept parse miss quotation mark")
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
                raise LeptJsonParseError("lept parse invalid string escape")

            # if current_element in mapping:
            #     l.append(mapping[current_element])
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
                code_point, current_index = _lept_parse_hex4(json_string, current_index + 1,
                                                             string_length)
                if 0xdbff >= code_point >= 0xd800:
                    if current_index + 1 >= string_length or (
                            json_string[current_index] != '\\' or json_string[
                        current_index + 1] != 'u'):
                        raise LeptJsonParseError("lept parse invalid unicode surrogate")
                    current_index += 2
                    low_surrogate, current_index = _lept_parse_hex4(json_string, current_index,
                                                                    string_length)
                    if 0xdfff >= low_surrogate >= 0xdc00:
                        code_point = 0x10000 + (code_point - 0xd800) * 0x400 + (
                                low_surrogate - 0xdc00)
                    else:
                        raise LeptJsonParseError("lept parse invalid unicode surrogate")
                l.append(chr(code_point))
                continue
            else:
                raise LeptJsonParseError("lept parse invalid string escape")
            current_index += 1
        elif ord(current_element) < 32:
            raise LeptJsonParseError("lept parse invalid string char")


def _lept_parse_hex4(json_string, current_index, string_length):
    return _str2hex(json_string, current_index, string_length, 4)


def _str2hex(json_string, current_index, string_length, hex_length):
    assert hex_length >= 0
    if current_index + hex_length - 1 >= string_length:
        raise LeptJsonParseError("lept parse invalid unicode hex")
    sum = 0
    power = 1
    for i in range(hex_length - 1, -1, -1):
        current_element = json_string[current_index + i]
        current_element_ord = ord(current_element)
        if ord('F') >= current_element_ord >= ord('A'):
            sum += (current_element_ord - ord('A') + 10) * power
        elif ord('9') >= current_element_ord >= ord('0'):
            sum += (current_element_ord - ord('0')) * power
        elif ord('f') >= current_element_ord >= ord('a'):
            sum += (current_element_ord - ord('a') + 10) * power
        else:
            raise LeptJsonParseError("lept parse invalid unicode hex")
        power *= 16
    return sum, current_index + hex_length


def _lept_parse_literal(json_string, current_index, string_length, literal, return_value):
    n = len(literal)
    if json_string[current_index:current_index + n] == literal:
        return return_value, current_index + n
    raise LeptJsonParseError("lept parse invalid value")


def _lept_parse_number(json_string, current_index, string_length):
    end_index = _parse_number(json_string, current_index, string_length)
    result = float(json_string[current_index:end_index])
    if result == float("Inf") or result == float("-Inf"):
        raise LeptJsonParseError("lept parse number too big")
    return result, end_index


def _parse_number(json_string, current_index, string_length):
    current_index = _parse_negative(json_string, current_index, string_length)
    current_index = _parse_int(json_string, current_index, string_length)
    current_index = _parse_frac(json_string, current_index, string_length)
    return _parse_exp(json_string, current_index, string_length)


def _parse_negative(json_string, current_index, string_length):
    if json_string[current_index] == '-':
        return current_index + 1
    else:
        return current_index


def _parse_int(json_string, current_index, string_length):
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '0':
        return current_index + 1
    if json_string[current_index] in POSITIVE_INTEGERS_LIST:
        while current_index < string_length and json_string[
            current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_frac(json_string, current_index, string_length):
    if current_index >= string_length or json_string[current_index] != '.':
        return current_index
    current_index += 1
    if current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
        while current_index < string_length and json_string[
            current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_exp(json_string, current_index, string_length):
    if current_index >= string_length or (
            json_string[current_index] != 'e' and json_string[current_index] != 'E'):
        return current_index
    current_index += 1
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '-' or json_string[current_index] == '+':
        current_index += 1
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse invalid value")
    if current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
        while current_index < string_length and json_string[
            current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


loads = lept_parse
dumps = lept_stringify
if __name__ == '__main__':
    with open('data/twitter.json', encoding='utf-8') as f:
        large_obj_data = f.read()
        for _ in range(10):
            lept_parse(large_obj_data)
