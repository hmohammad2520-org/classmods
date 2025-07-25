import os
from typing import Callable
from classmods import ENVMod

class TestClass:
    @ENVMod.register(exclude=['service'])
    def __init__(self, name: str, age: int, service: Callable|None = None):
        """
        Test Class.

        Args:
            name: your name.
            age: your age.
        """
        self.name = name
        self.age = age

    @ENVMod.register()
    def _connect(self, host: str, timeout: float, port: int = 80):
        """ No Doc For Args"""
        self.host = host
        self.timeout = timeout
        self.port = port

    @ENVMod.register()
    def _disconnect(cls):
        ...


def test_file_creations():
    ENVMod.save_example('dev_env_example.txt')
    ENVMod.sync_env_file()
    assert os.path.exists('dev_env_example.txt')
    assert os.path.exists('.env')

    with open('.env', 'w') as f:
        f.writelines([
            'TESTCLASS_NAME=test_name\n',
            'TESTCLASS_AGE=25\n',
            'TESTCLASS_HOST=127.0.0.1\n',
            'TESTCLASS_TIMEOUT=1.43\n',
        ])

def test_env_vars():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    keys = os.environ.keys()
    assert 'TESTCLASS_NAME' in keys
    assert 'TESTCLASS_AGE' in keys
    assert 'TESTCLASS_HOST' in keys
    assert 'TESTCLASS_TIMEOUT' in keys

def test_env_values():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    assert os.environ.get('TESTCLASS_NAME') == 'test_name'
    assert os.environ.get('TESTCLASS_AGE') == '25'
    assert os.environ.get('TESTCLASS_HOST') == '127.0.0.1'
    assert os.environ.get('TESTCLASS_TIMEOUT') == '1.43'

def test_load_args():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    test_object = TestClass(**ENVMod.load_args(TestClass.__init__))
    test_object._connect(**ENVMod.load_args(TestClass._connect))
    assert test_object.name == 'test_name'
    assert test_object.age == 25
    assert test_object.host == '127.0.0.1'
    assert test_object.timeout == 1.43
    assert test_object.port == 80