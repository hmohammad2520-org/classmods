import os
from typing import Callable, Optional
from classmods import ENVMod

class TestClass:
    @ENVMod.register(exclude=['service'], cast={'path': str})
    def __init__(
            self,
            name: str,
            path: os.PathLike,
            host: str,
            port: int,
            timeout: float,
            password: Optional[int] = None,
            service: Callable | None = None,
        ) -> None:
        """
        Test Class.

        Args:
            name: your name.
            path: service Pathlike Object.
            host: Connection host.
            port: connection port.
            timeout: connection timeout.
            password: connection password.
            service: service object.
        """
        self.name = name
        self.path = path
        self.host = host
        self.port = port
        self.timeout = timeout
        self.password = password
        self.service = service

def test_file_creations():
    if not os.path.exists('.temp'):
        os.mkdir('.temp')

    ENVMod.save_example('.temp/env_example.txt')
    ENVMod.sync_env_file()
    assert os.path.exists('.temp/env_example.txt')
    assert os.path.exists('.env')

    with open('.env', 'w') as f:
        f.writelines([
            'TESTCLASS_NAME=test_name\n',
            'TESTCLASS_PATH=/opt/my_service\n',
            'TESTCLASS_PORT=123\n',
            'TESTCLASS_HOST=127.0.0.1\n',
            'TESTCLASS_TIMEOUT=1.43\n',
            'TESTCLASS_PASSWORD=\n',
        ])

def test_env_vars():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    assert 'TESTCLASS_NAME' in os.environ
    assert 'TESTCLASS_PATH' in os.environ
    assert 'TESTCLASS_PORT' in os.environ
    assert 'TESTCLASS_HOST' in os.environ
    assert 'TESTCLASS_TIMEOUT' in os.environ
    assert 'TESTCLASS_PASSWORD' in os.environ

def test_env_values():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    assert os.environ.get('TESTCLASS_NAME') == 'test_name'
    assert os.environ.get('TESTCLASS_PATH') == '/opt/my_service'
    assert os.environ.get('TESTCLASS_PORT') == '123'
    assert os.environ.get('TESTCLASS_HOST') == '127.0.0.1'
    assert os.environ.get('TESTCLASS_TIMEOUT') == '1.43'
    assert os.environ.get('TESTCLASS_PASSWORD') == ''

def test_load_args():
    ENVMod.sync_env_file()
    ENVMod.load_dotenv()
    test_object = TestClass(**ENVMod.load_args(TestClass.__init__))
    assert test_object.name == 'test_name'
    assert test_object.path == '/opt/my_service'
    assert test_object.port == 123
    assert test_object.host == '127.0.0.1'
    assert test_object.timeout == 1.43
    assert test_object.password == None
