######################################################################
# URL validation
import re
from werkzeug.routing import BaseConverter

from butypes import name2type

class ValidationError(Exception) : pass

class Hex256Converter(BaseConverter):
    def to_python(self, value):
        if len(value) != 64 or not re.match("^[a-fA-F0-9]{64}$", value):
            raise ValidationError("'%s' is not a 32-byte hex string." % value)
        return value
    
    def to_url(self, value):
        return value
    
class ObjTypeConverter(BaseConverter):
    def to_python(self, value):
        if value not in name2type:
            raise ValidationError("Invalid object type '%s'." % value)
        return value

    def to_url(self, value):
        return value
    
def register(app): # pragma: no cover
    # meant to be 'hex256' but apparently bottle.py doesn't like numbers in names
    app.url_map.converters["shex"] = Hex256Converter
    app.url_map.converters["objtype"] = ObjTypeConverter
