# Parser for 'action expressions', used for both specifying votes as well as
# actions.
import re
import shlex

from jvalidate import ValidationError

def sanitize_input(s):
    if not re.match("^[\(\)\[\]a-zA-Z0-9_ \-'\"]+$", s):
        raise ValidationError("Invalid characters in action string '%s'." % s)


class AExpr:
    """ Parse string according to given template tmpl and type_map."""
    def __init__(self, tmpl, type_map):
        self.tmpl=tmpl
        self.type_map=type_map
        
    def __call__(self, s):
        sanitize_input(s)
        shl = shlex.shlex(s)
        shl.wordchars += "-%:"
        try:
            tokens = list(shl)
        except ValueError:
            raise ValidationError("Parse error.")
            
        return self.parse(tokens)
    
    def parse(self, tokens):
        avars = {}
        tmpl     = self.tmpl.split()
        type_map = self.type_map
        
        l = iter(tokens)
        
        for expect in tmpl:
            assert len(expect)>=1

            try:
                tok=next(l)
            except StopIteration:
                raise ValidationError("Expected '%s', got end-of-strings." % expect)
            except ValueError:
                raise ValidationError("Parse error.")
            
            # types of expressions parsed:
            # tok - just the token itself
            # %var:type - variable var of given type
            # [var:type] - list of variables of givne type
            # (var:type) - subexpression of given type
            
            if expect[0] == '%': # placeholder for typed variable
                # single variable
                varname, vartype = expect[1:].split(":")
                assert vartype in type_map
                avars[varname] = type_map[vartype](tok)
            elif expect[0] == '[': # list variable
                assert expect[-1] == ']'
                varname, vartype = expect[1:-1].split(":")
                assert vartype in type_map
                if tok != '[':
                    raise ValidationError("Expected '['.")
                vlist=[]
                while tok != ']':
                    try:
                        tok=next(l)
                    except StopIteration:
                        raise ValidationError("Expected ']', got end of expression.")
                    except ValueError: 
                        raise ValidationError("Parse error.")
                    if tok != ']':
                        vlist.append(type_map[vartype](tok))
                avars[varname]=vlist
            elif expect[0] == '(': # subexpression
                assert expect[-1] == ')'
                varname, vartype = expect[1:-1].split(":")
                assert vartype in type_map
                if tok != '(':
                    raise ValidationError("Expected '('.")
                subtokens=[]
                paren = 1
                
                while True:
                    try:
                        tok = next(l)
                    except StopIteration:
                        raise ValidationError("Expected ')' got end of expression.")
                    except ValueError: 
                        raise ValidationError("Parse error.")
                    if tok == '(':
                        paren += 1
                    elif tok == ')':
                        paren -=1

                    if not paren:
                        break
                    
                    subtokens.append(tok)
                avars[varname] = type_map[vartype](avars, subtokens)
            else:
                if tok != expect:
                    raise ValidationError("Expected '%s', got '%s'." % (expect, tok))
        return avars
        
