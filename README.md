# fourUtils
##### There's actually more than four.
As this library is focused on my own private projects, it will be pretty opinionated, however anybody is welcome to use it and/or pull parts of the package for their own use.

## Contributing
* Contributions are more than welcome.
* Any contributions should loosely follow PEP8 style guides.

### Some quick docs.
## fourutils.webnotifications.PushPackageBuilder
I was unable to find a good way of building Apple .pushpackages dynamically in python. This module resizes and caches the required app icon sizes, builds and signs the manifest, then zips the result completely in-memory with no temporary files.

For help on building your certs into a .pem, [take a look here](https://gist.github.com/fahied/f1dffbbea3333c7045f7).

```python
from fourutils import make_logger
from fourutils.webnotifications import PushPackageBuilder

log = make_logger(__name__)

log.info('Generating pushpackage...')
outfile = os.path.abspath('app.pushpackage')
with open(outfile, 'wb') as f:
    app_icon_path = os.path.abspath('app_icon_1024x1024.png')
    ppb = PushPackageBuilder(
        key_path=system_uploads.path('./apn_key.pem'),
        icon_path=app_icon_path, website_dict={
            "websiteName": "Flaskdesk",
            "websitePushID": "me.fourbytes.flaskdesk",
            "allowedDomains": ['https://127.0.0.1'],
            "urlFormatString": 'https://127.0.0.1/%@/%@',
            "webServiceURL": 'https://127.0.0.1/api/apn'
        })
    ppb.build_pushpackage(f, merge_website_dict={
        'authenticationToken': '123456789'
    })
log.info('Finished generating pushpackage in %s', outfile)
```

## fourutils.FilterParser
```python
from fourutils import FilterParser

fp = FilterParser()

query_text = 'user:orainford email:oscar@fourbytes.me good:"sometimes you can\'t help needing need spaces"'

for key, value in fp.match_all(query_text):
    print(f'{key}: {value}')

""" stdout
user: orainford
email: oscar@fourbytes.me
good: sometimes you can't help needing need spaces
"""

query_text = 'user:42 a friendly man'
value = fp.match('user', query_text)
print(value)

excess = fp.clear_filters(query_text)
print(excess)

""" stdout
user: 42
a friendly man
"""
```