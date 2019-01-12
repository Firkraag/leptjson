#!/usr/local/bin/python3
# encoding: utf-8
import string

POSITIVE_INTEGERS_LIST = '123456789'
NONNEGATIVE_INTEGERS_LIST = '0123456789'
JSON_SPACE_CHARACTERS_LIST = ' \t\n\r'
mapping = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}


class InputStream(object):
    def __init__(self, input: str):
        if not input:
            raise LeptJsonParseError("lept parse expect value")
        self._pos = 0
        self._line = 1
        self._col = 0
        self._input = input

    def next(self) -> str:
        try:
            ch = self._input[self._pos]
        except IndexError:
            ch = ""
        finally:
            self._pos += 1
            if ch == "\n":
                self._line += 1
                self._col = 0
            else:
                self._col += 1
            return ch

    def peek(self) -> str:
        try:
            return self._input[self._pos]
        except IndexError:
            return ""

    def eof(self) -> bool:
        return self.peek() == ""

    def croak(self, msg: str):
        raise Exception(msg + " (" + str(self._line) + ":" + str(self._col) + ")")


class JsonTokenStream(object):
    KEYWORDS = set("true false null".split())
    ID_START = set(string.ascii_letters)
    ID = set(string.ascii_letters + string.digits + 'λ_?!-<>=')
    OP = set("+-*/%=&|<>!")
    PUNC = set(",;:{}[]")
    WHITESPACE = set(" \t\n")

    def __init__(self, input_stream: InputStream):
        self._input_stream = input_stream
        self.current = None

    def is_keyword(self, word: str) -> bool:
        return word in self.KEYWORDS

    def is_digit(self, ch: str) -> bool:
        return ch.isdigit()

    def is_id_start(self, ch: str) -> bool:
        return ch in self.ID_START

    def is_id(self, ch: str) -> bool:
        return ch in self.ID

    def is_whitespace(self, ch: str) -> bool:
        return ch in JSON_SPACE_CHARACTERS_LIST

    def is_punc(self, ch: str) -> bool:
        return ch in self.PUNC

    def is_positive_integer(self, ch: str) -> bool:
        return ch in POSITIVE_INTEGERS_LIST

    def is_nonnegative_integer(self, ch: str) -> bool:
        return ch in NONNEGATIVE_INTEGERS_LIST

    def read_ident(self) -> dict:
        id = self.read_while(self.is_id)
        if id == 'null':
            return {
                'type': 'null',
                'value': None,
            }
        if id == 'true':
            return {
                'type': 'bool',
                'value': True,
            }
        if id =='false':
            return {
                'type': 'bool',
                'value': False,
            }
        else:
            return {
                'type': 'invalid',
                'value': id,
            }
        # raise LeptJsonParseError("lept parse invalid value")
    def parse_hex4(self):
        return self.str2hex(4)

    def str2hex(self, hex_length):
        assert hex_length >= 0
        result = 0
        power = 16
        for i in range(hex_length):
            if self._input_stream.eof():
                raise LeptJsonParseError("lept parse invalid unicode hex")
            ch = self._input_stream.next()
            ch_ord = ord(ch)
            if ord('F') >= ch_ord >= ord('A'):
                result = result * power + (ch_ord - ord('A') + 10)
            elif ord('9') >= ch_ord >= ord('0'):
                result = result * power + (ch_ord - ord('0'))
            elif ord('f') >= ch_ord >= ord('a'):
                result = result * power + (ch_ord - ord('a') + 10)
            else:
                raise LeptJsonParseError("lept parse invalid unicode hex")
        return result

    def read_string(self) -> dict:
        self._input_stream.next()
        l = []
        while True:
            if self._input_stream.eof():
                raise LeptJsonParseError("lept parse miss quotation mark")
            ch = self._input_stream.next()
            if ord(ch) >= 32 and ch != '"' and ch != '\\':
                l.append(ch)
            elif ch == '"':
                return {'type': 'str', 'value': ''.join(l)}

            elif ch == '\\':
                if self._input_stream.eof():
                    raise LeptJsonParseError("lept parse invalid string escape")
                ch = self._input_stream.next()
                if ch == '"':
                    l.append('"')
                elif ch == '\\':
                    l.append('\\')
                elif ch == '/':
                    l.append('/')
                elif ch == 'b':
                    l.append('\b')
                elif ch == 'f':
                    l.append('\f')
                elif ch == 'n':
                    l.append('\n')
                elif ch == 'r':
                    l.append('\r')
                elif ch == 't':
                    l.append('\t')
                elif ch == 'u':
                    code_point = self.parse_hex4()
                    if 0xdbff >= code_point >= 0xd800:
                        ch1 = self._input_stream.next()
                        ch2 = self._input_stream.next()
                        if ch1 != '\\' or ch2 != 'u':
                            raise LeptJsonParseError("lept parse invalid unicode surrogate")
                        low_surrogate = self.parse_hex4()
                        if 0xdfff >= low_surrogate >= 0xdc00:
                            code_point = 0x10000 + (code_point - 0xd800) * 0x400 + (low_surrogate - 0xdc00)
                        else:
                            raise LeptJsonParseError("lept parse invalid unicode surrogate")
                    l.append(chr(code_point))
                    continue
                else:
                    raise LeptJsonParseError("lept parse invalid string escape")
            elif ord(ch) < 32:
                raise LeptJsonParseError("lept parse invalid string char")

    def read_number(self) -> dict:
        negative = self.read_number_negative()
        integer = self.read_number_int()
        frac = self.read_number_frac()
        exp = self.read_number_exp()
        number_string = negative + integer + frac + exp
        result = float(number_string)
        if result == float("Inf") or result == float("-Inf"):
            raise LeptJsonParseError("lept parse number too big")
        return {
            'type': 'num',
            'value': result,
        }

    def read_number_negative(self):
        ch = self._input_stream.peek()
        if ch == '-':
            return self._input_stream.next()
        else:
            return ''

    def read_number_int(self):
        if self._input_stream.eof():
            raise LeptJsonParseError("lept parse invalid value")
        ch = self._input_stream.peek()
        if ch == '0':
            return self._input_stream.next()
        if self.is_positive_integer(ch):
            l = self.read_while(self.is_nonnegative_integer)
            return ''.join(l)
        raise LeptJsonParseError("lept parse invalid value")

    def read_number_frac(self):
        if self._input_stream.eof() or self._input_stream.peek() != '.':
            return ''
        self._input_stream.next()
        ch = self._input_stream.peek()
        if (not self._input_stream.eof()) and self.is_nonnegative_integer(ch):
            result = self.read_while(self.is_nonnegative_integer)
            return '.' + ''.join(result)
        raise LeptJsonParseError("lept parse invalid value")

    def read_number_exp(self):
        ch = self._input_stream.peek()
        if self._input_stream.eof() or (ch != 'e' and ch != 'E'):
            return ''
        result = 'e'
        self._input_stream.next()
        if self._input_stream.eof():
            raise LeptJsonParseError("lept parse invalid value")
        ch = self._input_stream.peek()
        if ch == '-' or ch == '+':
            result = 'e' + self._input_stream.next()

        if self._input_stream.eof():
            raise LeptJsonParseError("lept parse invalid value")
        if self.is_nonnegative_integer(self._input_stream.peek()):
            return result + ''.join(self.read_while(self.is_nonnegative_integer))
        raise LeptJsonParseError("lept parse invalid value")

    def read_while(self, predicate) -> str:
        l = []
        while (not self._input_stream.eof()) and predicate(self._input_stream.peek()):
            l.append(self._input_stream.next())
        return ''.join(l)

    def read_next(self) -> dict:
        self.read_while(self.is_whitespace)
        if self._input_stream.eof():
            return {}
        ch = self._input_stream.peek()
        if self.is_id_start(ch):
            return self.read_ident()
        if ch == '"':
            return self.read_string()
        if self.is_punc(ch):
            return {
                'type': 'punc',
                'value': self._input_stream.next()
            }
        # if self.is_digit(ch):
        return self.read_number()
        # self._input_stream.croak("Can't handle character: {}".format(ch))

    def peek(self):
        if self.current:
            return self.current
        self.current = self.read_next()
        return self.current

    def next(self):
        token = self.current
        self.current = None
        if token:
            return token
        return self.read_next()

    def __iter__(self):
        while True:
            token = self.read_next()
            if token is not None:
                yield token
            else:
                break

    def eof(self) -> bool:
        return not self.peek()

    def croak(self, msg):
        self._input_stream.croak(msg)


class LeptJsonParseError(Exception):
    def __init__(self, msg):
        super(LeptJsonParseError, self).__init__(msg)
        self.msg = msg


class JsonParser(object):
    PRECEDENCE = {
        "=": 1,
        "||": 2,
        "&&": 3,
        "<": 7, ">": 7, "<=": 7, ">=": 7, "==": 7, "!=": 7,
        "+": 10, "-": 10,
        "*": 20, "/": 20, "%": 20,
    }

    def __init__(self, json_token_stream: JsonTokenStream):
        self.json_token_stream = json_token_stream

    def skip_punc(self, ch: str, msg: str = '') -> None:
        if self.is_punc(ch):
            self.json_token_stream.next()
        else:
            raise LeptJsonParseError(msg)

    def is_bool(self) -> bool:
        return self.judge_type('bool')

    def is_null(self) -> bool:
        return self.judge_type('null')

    def is_punc(self, ch: str) -> bool:
        return self.judge_type_and_value('punc', ch)

    def is_num(self) -> bool:
        return self.judge_type('num')

    def is_str(self) -> bool:
        return self.judge_type('str')

    def judge_type(self, type: str) -> bool:
        token = self.json_token_stream.peek()
        return token and token['type'] == type

    def judge_type_and_value(self, type: str, value: str) -> bool:
        token = self.json_token_stream.peek()
        return token and token['type'] == type and token['value'] == value

    def delimited(self, start: str, stop: str, separator: str, parser, skip_msg:str='', item_msg:str='') -> list:
        a = []
        first = True
        self.skip_punc(start)
        while not self.json_token_stream.eof():
            if self.is_punc(stop):
                break
            if first:
                first = False
            else:
                self.skip_punc(separator, skip_msg)
            if self.is_punc(stop):
                break
            a.append(parser(item_msg))
        self.skip_punc(stop, skip_msg)
        return a

    def parse_toplevel(self) -> object:
        result = self.parse_token()
        if self.json_token_stream.eof():
            return result
        raise LeptJsonParseError("lept parse root not singular")

    def parse_token(self, msg:str='') -> object:
        if self.json_token_stream.eof():
            raise LeptJsonParseError("lept parse expect value")
        if self.is_bool():
            return self.parse_bool()
        if self.is_null():
            return self.parse_null()
        if self.is_num():
            return self.parse_num()
        if self.is_str():
            return self.parse_str()
        if self.is_punc('['):
            return self.parse_array()
        if self.is_punc('{'):
            return self.parse_map()
        raise LeptJsonParseError("lept parse invalid value")

    def parse_bool(self) -> bool:
        return self.extract_next_token_value()

    def parse_null(self) -> None:
        return self.extract_next_token_value()

    def parse_num(self) -> float:
        return self.extract_next_token_value()

    def parse_str(self) -> str:
        return self.extract_next_token_value()

    def extract_next_token_value(self) -> object:
        return self.json_token_stream.next()['value']

    def parse_array(self):
        return self.delimited('[', ']', ',', self.parse_token, skip_msg='lept parse miss comma or square bracket')

    def parse_map(self):
        def parser(msg:str):
            if self.is_str():
                key = self.json_token_stream.next()['value']
            else:
                raise LeptJsonParseError("lept parse miss key")
            self.skip_punc(':', 'lept parse miss colon')
            value = self.parse_token()
            return key, value

        return dict(self.delimited('{', '}', ',', parser, 'lept parse miss comma or curly bracket'
, "lept parse miss key"))

    def unexpected(self):
        self.json_token_stream.croak('Unexpected token: ' + str(self.json_token_stream.peek()))


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
            elif (0x20 <= char_ord <= 0x21) or (0x23 <= char_ord <= 0x5b) or (0x5d <= char_ord <= 0x10ffff):
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


#
#
# def _hex2str(hex):
#     result = []
#     for _ in range(4):
#         result.append(str(hex % 16))
#         hex = hex // 16
#     return ''.join(reversed(result))
#

def _lept_parse_whitespace(json_string, current_index, string_length):
    while current_index < string_length and json_string[current_index] in JSON_SPACE_CHARACTERS_LIST:
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
        if current_index >= string_length or (json_string[current_index] != ',' and json_string[current_index] != '}'):
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
                code_point, current_index = _lept_parse_hex4(json_string, current_index + 1, string_length)
                if 0xdbff >= code_point >= 0xd800:
                    if current_index + 1 >= string_length or (
                                    json_string[current_index] != '\\' or json_string[current_index + 1] != 'u'):
                        raise LeptJsonParseError("lept parse invalid unicode surrogate")
                    current_index += 2
                    low_surrogate, current_index = _lept_parse_hex4(json_string, current_index, string_length)
                    if 0xdfff >= low_surrogate >= 0xdc00:
                        code_point = 0x10000 + (code_point - 0xd800) * 0x400 + (low_surrogate - 0xdc00)
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
        while current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_frac(json_string, current_index, string_length):
    if current_index >= string_length or json_string[current_index] != '.':
        return current_index
    current_index += 1
    if current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
        while current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


def _parse_exp(json_string, current_index, string_length):
    if current_index >= string_length or (json_string[current_index] != 'e' and json_string[current_index] != 'E'):
        return current_index
    current_index += 1
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse invalid value")
    if json_string[current_index] == '-' or json_string[current_index] == '+':
        current_index += 1
    if current_index >= string_length:
        raise LeptJsonParseError("lept parse invalid value")
    if current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
        while current_index < string_length and json_string[current_index] in NONNEGATIVE_INTEGERS_LIST:
            current_index += 1
        return current_index
    raise LeptJsonParseError("lept parse invalid value")


lept_parse = lambda json_string: JsonParser(JsonTokenStream(InputStream(json_string))).parse_toplevel()
loads = lept_parse
dumps = lept_stringify
if __name__ == '__main__':
    with open('data/twitter.json', encoding='utf-8') as f:
        large_obj_data = f.read()
        for _ in range(10):
            lept_parse(large_obj_data)
