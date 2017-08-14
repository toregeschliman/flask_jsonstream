import unittest
import json
import collections

import flask

from flask_jsonstream import stream_big_object_as_json

# build some test data, a big generator-based list and a big generator-based map
huge_list = {'numbers': range(1000000)}

class HugeDict(collections.UserDict):
    def items(self):
        for x, y in zip(range(1000000), range(1000000, 2000000)):
            yield x, y

huge_dict = HugeDict()


# build a sample Flask app to try it out
app = flask.Flask(__name__)


@app.route('/list', methods=['GET'])
def list_route():
    res = stream_big_object_as_json(huge_list)
    return res


@app.route('/dict', methods=['GET'])
def dict_route():
    res = stream_big_object_as_json(huge_dict)
    return res


class TestBasicStreams(unittest.TestCase):
    def test_stream_list(self):
        with app.test_client() as c:
            list_resp = c.get('/list')
            thing = json.loads(list_resp.data)
            assert 'numbers' in thing
            assert 20 in thing['numbers']

    def test_stream_dict(self):
        with app.test_client() as c:
            dict_resp = c.get('/dict')
            thing = json.loads(dict_resp.data)
            assert '10' in thing  # JSON doesn't allow number keys, so these are converted to strings
            assert thing['10'] == 1000010  # but it does allow number values, so this is the same