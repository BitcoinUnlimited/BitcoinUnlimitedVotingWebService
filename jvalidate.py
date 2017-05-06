import re
import config

class ValidationError(RuntimeError):
    def __init__(self,
                 msg,
                 status=400,
                 error_page=None):
        super().__init__(msg)
        self.status=status
        self.error_page=error_page

def is_sha256(val):
    if len(val)!=64:
        return False
    if not re.match("^[a-fA-F0-9]{64}$", val):
        return False
    return True

def is_float(val):
    try:
        float(val)
    except:
        return False
    return True

#def is_any(val):
#    return True

def is_str_less1k(val):
    return isinstance(val, str) and len(val)<1024

def is_dict(val):
    return isinstance(val, dict)

def is_int(val):
    try:
        int(val)
    except:
        return False
    return True
    
is_bool=is_int # FIXME: maybe more checks here

######################################################################        
def general(j, obj):
    has(j, "version", lambda x : x == 1)
    has(j, "type", lambda x : x == obj.typename)
    #has(j, "timestamp", is_float)
    
def has(j, field, check):
    if field not in j:
        raise ValidationError("Expected field '%s'." % field)
    if not check(j[field]):
        raise ValidationError("Field '%s' does not validate." % field)
    

       
