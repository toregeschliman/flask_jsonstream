from setuptools import setup, find_packages

setup(
    name='flask_jsonstream',
    author='Tore G. Eschliman',
    author_email='toregeschliman@gmail.com',
    packages=find_packages(exclude=['test*']),
    version='0.1',
    description='Allows streaming of dynamic iterables as JSON objects via Flask app',
    install_requires=[
        'flask'
    ],
    test_suite='test.test_stream',
    python_requires=">=3.4"
)