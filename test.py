#!/usr/local/bin/python3
# coding=utf-8

import unittest
from leptjson import parse, _LeptJsonParseError, stringify


class LeptJsonTest(unittest.TestCase):
    def test_null(self):
        self.assertTrue(parse("null") is None)

    def test_parse_true(self):
        self.assertTrue(parse("true"))

    def test_parse_false(self):
        self.assertFalse(parse("false"))

    def test_parse_expect_value(self):
        self.exception("", "lept parse expect value")
        self.exception(" ", "lept parse expect value")

    def test_parse_invalid_value(self):
        self.exception("nul", "lept parse invalid value")
        self.exception("?", "lept parse invalid value")
        self.exception("+0", "lept parse invalid value")
        self.exception("+1", "lept parse invalid value")
        self.exception(".123", "lept parse invalid value")
        self.exception("1.", "lept parse invalid value")
        self.exception("INF", "lept parse invalid value")
        self.exception("inf", "lept parse invalid value")
        self.exception("NAN", "lept parse invalid value")
        self.exception("nan", "lept parse invalid value")

    def test_parse_root_not_singular(self):
        self.exception("null x", "lept parse root not singular")
        self.exception("0123", "lept parse root not singular")
        self.exception("0x0", "lept parse root not singular")
        self.exception("0x123", "lept parse root not singular")

    def test_parse_number(self):
        self.assertEqual(0, parse("0"))
        self.assertEqual(0.0, parse("0"))
        self.assertEqual(0.0, parse("-0"))
        self.assertEqual(0.0, parse("-0.0"))
        self.assertEqual(1.0, parse("1"))
        self.assertEqual(-1.0, parse("-1"))
        self.assertEqual(1.5, parse("1.5"))
        self.assertEqual(-1.5, parse("-1.5"))
        self.assertEqual(3.1416, parse("3.1416"))
        self.assertEqual(1E10, parse("1E10"))
        self.assertEqual(1e10, parse("1e10"))
        self.assertEqual(1E+10, parse("1E+10"))
        self.assertEqual(1E-10, parse("1E-10"))
        self.assertEqual(-1E10, parse("-1E10"))
        self.assertEqual(-1e10, parse("-1e10"))
        self.assertEqual(-1E+10, parse("-1E+10"))
        self.assertEqual(-1E-10, parse("-1E-10"))
        self.assertEqual(1.234E+10, parse("1.234E+10"))
        self.assertEqual(1.234E-10, parse("1.234E-10"))
        self.assertEqual(0.0, parse("1e-10000"))
        self.assertEqual(1.0000000000000002, parse("1.0000000000000002"))
        self.assertEqual(4.9406564584124654e-324, parse("4.9406564584124654e-324"))
        self.assertEqual(-4.9406564584124654e-324, parse("-4.9406564584124654e-324"))
        self.assertEqual(2.2250738585072009e-308, parse("2.2250738585072009e-308"))
        self.assertEqual(-2.2250738585072009e-308, parse("-2.2250738585072009e-308"))
        self.assertEqual(2.2250738585072014e-308, parse("2.2250738585072014e-308"))
        self.assertEqual(-2.2250738585072014e-308, parse("-2.2250738585072014e-308"))
        self.assertEqual(1.7976931348623157e+308, parse("1.7976931348623157e+308"))
        self.assertEqual(-1.7976931348623157e+308, parse("-1.7976931348623157e+308"))

    def test_parse_number_too_big(self):
        self.exception("1e309", "lept parse number too big")
        self.exception("-1e309", "lept parse number too big")

    def test_parse_string(self):
        self.assertEqual("", parse("\"\""))
        self.assertEqual("Hello", parse("\"Hello\""))
        self.assertEqual("Hello\nWorld", parse("\"Hello\\nWorld\""))
        self.assertEqual("\" \\ / \b \f \n \r \t", parse("\"\\\" \\\\ \\/ \\b \\f \\n \\r \\t\""))
        self.assertEqual("\\\\", parse("\"\\\\\\\\\""))
        self.assertEqual("Hello\0World", parse("\"Hello\\u0000World\""))
        self.assertEqual("\x24", parse("\"\\u0024\""))
        self.assertEqual('\u00a2', parse("\"\\u00A2\""))
        self.assertEqual("\u20ac", parse("\"\\u20AC\""))
        self.assertEqual(b"\xF0\x9D\x84\x9E".decode('utf8'), parse("\"\\uD834\\uDD1E\""))

    def test_parse_invalid_string_char(self):
        self.exception("\"\x01\"", "lept parse invalid string char")
        self.exception("\"\x1F\"", "lept parse invalid string char")

    def test_parse_missing_quotation_mark(self):
        self.exception("\"", "lept parse miss quotation mark")
        self.exception("\"abc", "lept parse miss quotation mark")
        self.exception("\"\\\\\\\"", "lept parse miss quotation mark")

    def test_parse_invalid_string_escape(self):
        self.exception("\"\\v\"", "lept parse invalid string escape")
        self.exception("\"\\'\"", "lept parse invalid string escape")
        self.exception("\"\\0\"", "lept parse invalid string escape")
        self.exception("\"\\x12\"", "lept parse invalid string escape")
        self.exception("\"\\t\\v", "lept parse invalid string escape")
        self.exception("\"a\\", "lept parse invalid string escape")

    def test_parse_invalid_unicode_hex(self):
        self.exception("\"\\u\"", "lept parse invalid unicode hex")
        self.exception("\"\\u0\"", "lept parse invalid unicode hex")
        self.exception("\"\\u01\"", "lept parse invalid unicode hex")
        self.exception("\"\\u012\"", "lept parse invalid unicode hex")
        self.exception("\"\\u/000\"", "lept parse invalid unicode hex")
        self.exception("\"\\uG000\"", "lept parse invalid unicode hex")
        self.exception("\"\\u0/00\"", "lept parse invalid unicode hex")
        self.exception("\"\\u0G00\"", "lept parse invalid unicode hex")
        self.exception("\"\\u0/00\"", "lept parse invalid unicode hex")
        self.exception("\"\\u00G0\"", "lept parse invalid unicode hex")
        self.exception("\"\\u000/\"", "lept parse invalid unicode hex")
        self.exception("\"\\u000G\"", "lept parse invalid unicode hex")
        self.exception("\"\\u 123\"", "lept parse invalid unicode hex")

    def test_parse_invalid_unicode_surrogate(self):
        self.exception("\"\\uD800\"", "lept parse invalid unicode surrogate")
        self.exception("\"\\uDBFF\"", "lept parse invalid unicode surrogate")
        self.exception("\"\\uD800\\\\\"", "lept parse invalid unicode surrogate")
        self.exception("\"\\uD800\\uDBFF\"", "lept parse invalid unicode surrogate")
        self.exception("\"\\uD800\\uE000\"", "lept parse invalid unicode surrogate")

    def test_parse_array(self):
        self.assertEqual([], parse("[ ]"))
        self.assertEqual([None, False, True, 123.0, 'abc'], parse("[ null , false , true, 123, \"abc\"]"))
        self.assertEqual([[], [0], [0, 1], [0, 1, 2]], parse("[ [ ] , [ 0 ] , [ 0 , 1 ] , [ 0 , 1 , 2 ] ] "))

    def test_parse_miss_comma_or_square_bracket(self):
        self.exception("[1", "lept parse miss comma or square bracket")
        self.exception("[1}", "lept parse miss comma or square bracket")
        self.exception("[1 2", "lept parse miss comma or square bracket")
        self.exception("[[]", "lept parse miss comma or square bracket")
        self.exception("[[1]", "lept parse miss comma or square bracket")
        self.exception("[\"\"", "lept parse miss comma or square bracket")

    def test_parse_object(self):
        self.assertEqual(
            {"n": None, "f": False, "t": True, "i": 123.0, "s": "abc", "a": [1, 2, 3], "o": {"1": 1, "2": 2, "3": 3}},
            parse(
                # self.assertEqual({'n': None}, lept_parse(
                " { "
                "\"n\" : null, "
                "\"f\" : false , "
                "\"t\" : true , "
                "\"i\" : 123 , "
                "\"s\" : \"abc\", "
                "\"a\" : [ 1, 2, 3 ],"
                "\"o\" : { \"1\" : 1, \"2\" : 2, \"3\" : 3 }"
                " } "
            ))

    def test_parse_miss_key(self):
        self.exception("{:1,", "lept parse miss key")
        self.exception("{1:1,", "lept parse miss key")
        self.exception("{true:1,", "lept parse miss key")
        self.exception("{false:1,", "lept parse miss key")
        self.exception("{null:1,", "lept parse miss key")
        self.exception("{[]:1,", "lept parse miss key")
        self.exception("{{}:1,", "lept parse miss key")
        self.exception("{\"a\":1,", "lept parse miss key")

    def test_parse_miss_colon(self):
        self.exception("{\"a\"}", "lept parse miss colon")
        self.exception("{\"a\",\"b\"}", "lept parse miss colon")

    def test_parse_miss_comma_or_curly_bracket(self):
        self.exception("{\"a\":1", "lept parse miss comma or curly bracket")
        self.exception("{\"a\":1]", "lept parse miss comma or curly bracket")
        self.exception("{\"a\":1 \"b\"", "lept parse miss comma or curly bracket")
        self.exception("{\"a\":{}", "lept parse miss comma or curly bracket")

    def test_stringify_number(self):
        self.roundtrip("0")
        self.roundtrip("-0")
        self.roundtrip("1")
        self.roundtrip("-1")
        self.roundtrip("1.5")
        self.roundtrip("-1.5")
        self.roundtrip("3.25")
        self.roundtrip("1e+17")
        self.roundtrip("1.234e+20")
        self.roundtrip("1.234e-20")
        self.roundtrip("1.0000000000000002")  # the smallest number > 1
        self.roundtrip("4.9406564584124654e-324")  # minimum denormal
        self.roundtrip("-4.9406564584124654e-324")
        self.roundtrip("2.2250738585072009e-308")  # Max subnormal double
        self.roundtrip("-2.2250738585072009e-308")
        self.roundtrip("2.2250738585072014e-308")  # Min normal positive double
        self.roundtrip("-2.2250738585072014e-308")
        self.roundtrip("1.7976931348623157e+308")  # Max double
        self.roundtrip("-1.7976931348623157e+308")

    def test_stringify_string(self):
        self.roundtrip("\"\"")
        self.roundtrip("\"Hello\"")
        self.roundtrip("\"Hello\\nWorld\"")
        self.roundtrip("\"\\\" \\\\ / \\b \\f \\n \\r \\t\"")
        self.roundtrip("\"Hello\\u000f\\u0000World\"")

    def test_stringify_array(self):
        self.roundtrip("[]")
        self.roundtrip("[null,false,true,123,\"abc\",[1,2,3]]")

    def test_stringify_object(self):
        self.roundtrip("{}")
        self.roundtrip(
            "{\"n\":null,\"f\":false,\"t\":true,\"i\":123,\"s\":\"abc\",\"a\":[1,2,3],\"o\":{\"1\":1,\"2\":2,\"3\":3}}")

    def test_stringify_literal(self):
        self.roundtrip("null")
        self.roundtrip("false")
        self.roundtrip("true")

    def exception(self, json_string, msg):
        with self.assertRaises(_LeptJsonParseError) as context:
            parse(json_string)
        self.assertEqual(context.exception.msg, msg)

    def roundtrip(self, json_string):
        self.assertEqual(stringify(parse(json_string)), json_string)
