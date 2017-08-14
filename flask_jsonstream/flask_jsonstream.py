import json
import collections.abc
from functools import lru_cache
from io import BytesIO

from flask import stream_with_context, Response


class StreamableList(list):
    '''The json.JSONEncoder.iterencode method only handles built-in lists, but will iterate over any iterable. This class will fool it into parsing other iterables.'''
    def __init__(self, source_iterable):
        self._stream = source_iterable

    def __bool__(self):
        # This is necessary because JSONEncoder checks for empty lists as a shortcut
        return True

    def __iter__(self):
        return iter(self._stream)


class StreamableMapping(dict):
    '''The json.JSONEncoder.iterencode method only handles built-in dicts, but will iterate over any object with .items() yielding key, value pairs. This class will fool it into parsing other Mappings.'''
    def __init__(self, source_iterable):
        self._stream = source_iterable

    def __bool__(self):
        # This is necessary because JSONEncoder checks for empty dicts as a shortcut
        return True

    def items(self):
        return iter(self._stream.items())


@lru_cache(typed=True)  # gonna get a lot of calls with the same parameters
def wrap_default(default):
    'Return a wrapped function for a provided default function that will try to trick JSONENcoder.iterencode into dealing with dynamic generators and mappings'
    def streaming_default(o):
        try:
            o = default(o)
        except TypeError:  # try parsing ourselves first
            pass
        else:
            return o
        if isinstance(o, collections.abc.Mapping):  # if it's a dict-alike
            return StreamableMapping(o)
        elif isinstance(o, collections.abc.Iterable):  # if it s a list-alike
            return StreamableList(o)
        else:
            return default(o)  # allow provided default to raise the error
    return streaming_default


def jsonify_stream(obj, encoder_class=json.JSONEncoder, default=json.JSONEncoder.default, chunk_size=1024 * 16):
    '''Streams a large JSON body, wrapping a provided default function and/or JSON encoder with the ability to handle dynamically-generated mappings and iterables.

    Arguments:
        obj: The object to encode and stream.
        encoder_class: The encoder class to use.
        default: An existing default function to try before wrapping in streaming classes.
        chunk_size: The size of chunk to generate at a time (default 16k, nginx next chunk default)'''

    # wrap the provided function with
    streaming_default = wrap_default(default)

    # instantiate the encoder with the wrapped default
    streaming_encoder = encoder_class(default=streaming_default)

    # now build a generator to return that generates bytestream chunks
    @stream_with_context  # flask wrapper that keeps request context on stack while generator is running
    def bytes_generator(
        streaming_encoder=streaming_encoder,
        obj=obj,
        chunk_size=chunk_size
    ):  # bring variables in as default args to avoid constant calls to closure scope

        buf = BytesIO()  # in-memory buffer handles iterative writes better
        size = 0  # cleaner than calling .tell() every loop

        for chunk in streaming_encoder.iterencode(obj):
            new_bytes = chunk.encode('ascii')
            size += buf.write(new_bytes)
            if size >= chunk_size:  # if the chunk is big enough, yield it and reset the buffer
                buf.seek(0)
                yield buf.read(size)
                size = 0
                buf.seek(size)
        else:  # catch anything remaining in the buffer
            if size:
                buf.seek(0)
                yield buf.read(size)

    return Response(
        bytes_generator(),
        200,
        {'content-type': 'application/json'}
    )
