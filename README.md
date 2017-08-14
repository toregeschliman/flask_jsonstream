# Flask_JSONStream

Provides a wrapper for Mappings and Iterables to convert to JSON and stream using flask

## Sample usage
```python
import flask
from flask_jsonstream import jsonify_stream

app = flask.Flask(__name__)
@app.route('/', methods=['GET'])
def big_list_route():
  return jsonify_stream({'numbers': range(1000000)})
```

## Test & Install


After setting up a virtual environment (requires Python 3.4 or up), run `pip install .` to install the module and dependencies using `wheel` (required for testing) then `python setup.py test` to run two basic tests.