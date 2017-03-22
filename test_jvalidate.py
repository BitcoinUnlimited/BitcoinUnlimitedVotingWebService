import pytest
from unittest.mock import Mock
from jvalidate import *


def test_sha256():
    assert is_sha256("0"*64)
    assert not is_sha256("0"*63)
    assert not is_sha256("0"*65)
    assert not is_sha256("x"*64)

def test_float():
    assert is_float("3")
    assert is_float("3.3")
    assert not is_float("3a.3")
    
def test_is_str_less1k():
    assert is_str_less1k("x"*1023)
    assert not is_str_less1k("x"*1024)
    
def test_is_dict():
    assert is_dict({1 : 2})
    assert not is_dict([])

def test_is_int():
    assert is_int("3")
    assert is_int(3)
    assert not is_int("a")

def test_general():
    obj = Mock()
    obj.typename="test-type"

    j={"version" : 1,
       "type" : "test-type"}
    
    general(j, obj)
    
    j["version"]=2
    with pytest.raises(ValidationError):
        general(j, obj)

    j["version"]=1
    j["type"]="invalid"
    with pytest.raises(ValidationError):
        general(j, obj)
        
    del j["version"]
    with pytest.raises(ValidationError):
        general(j, obj)
