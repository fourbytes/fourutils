## fourUtils
##### There's actually more than four.

#### fourutils.FilterParser
```python
from fourutils import FilterParser

fp = FilterParser()

query_text = 'user:orainford email:oscar@fourbytes.me good:"sometimes you can\'t help needing need spaces"'

for key, value in fp.match_all(query_text):
    print(f'{key}: {value}')

""" stdout
user: orainford
email: oscar@fourbytes.me
good: sometimes you can\'t help needing need spaces
"""
```