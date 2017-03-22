import pytest
from urlvalidate import *

def testHexConv():
    hc = Hex256Converter({})

    assert hc.to_python("0"*64) == "0" * 64
    
    with pytest.raises(ValidationError):
        hc.to_python("0"*63)
    with pytest.raises(ValidationError):
        hc.to_python("0"*65)
    with pytest.raises(ValidationError):
        hc.to_python("x"*64)

    assert hc.to_url("123") == "123"
        
def testObjType():
    oc = ObjTypeConverter({})

    assert oc.to_python("raw_file") == "raw_file"
    
    with pytest.raises(ValidationError):
        oc.to_python("doesnt-exist")

    assert oc.to_url("raw_file") == "raw_file"
    
        
        

    
        

    
