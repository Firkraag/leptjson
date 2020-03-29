# leptjson

Implementation of json

Inspired by [lept-json-tutorial]

## Requirements
Python\>=3.8

## Usage
### stringify
```
>>> import leptjson
>>> leptjson.stringify([1,2,3])
'[1,2,3]'
>>> leptjson.stringify({"a":1, "b":2, "c":3})
'{"a":1,"b":2,"c":3}'
```

### parse
```
>>> import leptjson
>>> leptjson.parse('[1,2,3]')
[1.0, 2.0, 3.0]
>>> leptjson.parse('{"a": 1, "b": 2, "c": 3}')
{'a': 1.0, 'b': 2.0, 'c': 3.0}
```

[lept-json-tutorial]: https://zhuanlan.zhihu.com/json-tutorial