import hashlib
import pytest
from jvalidate import ValidationError
from aparser import sanitize_input, AExpr
from atypes import atypes

testhash=hashlib.sha256(b"").hexdigest()

def verr_at(g, i):
    for j, x in enumerate(g):
        if i == j:
            raise ValueError
        else:
            yield x


def test_ap_sanitize():
    sanitize_input("012345")
    sanitize_input("a-test_string")
    sanitize_input("this is a test-action 12345")

    with pytest.raises(ValidationError):
        sanitize_input(">")

    with pytest.raises(ValidationError):
        sanitize_input("test1\ntest2")

    with pytest.raises(ValidationError):
        sanitize_input("")

    with pytest.raises(ValidationError):
        sanitize_input("<tag>")


def test_parsing1():
    ae=AExpr("test template exact", atypes)
    ae2=AExpr("test template exact", {})

    ae("test template exact")
    ae2("test template exact")

    with pytest.raises(ValidationError):
        ae("test template eyact")

    with pytest.raises(ValidationError):
        ae2("test template eyact")

def test_parsing2():
    ae=AExpr("some %i:int %sha:sha256 values", atypes)

    avars = ae("some 3 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 values")

    assert len(avars) == 2
    assert avars["i"] == 3
    assert avars["sha"] == testhash

    with pytest.raises(ValidationError):
        ae("some 3.1 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 values")

    with pytest.raises(ValidationError):
        ae("some 3 3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 values")

    with pytest.raises(ValidationError):
        ae("some 3 ee3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 values")


def test_parsing_lists():
    ae=AExpr("some intlist [i:int]", atypes)

    assert ae("some intlist [ 4 5 6 ]") == {"i": [4, 5, 6] }
    assert ae("some intlist []") == { "i": [] }

    with pytest.raises(ValidationError):
        ae("")

    with pytest.raises(ValidationError):
        ae("some")

    with pytest.raises(ValidationError):
        ae("some intlist [ 4 de 6]")

    with pytest.raises(ValidationError):
        ae("some intlist 3")

    with pytest.raises(ValidationError):
        ae("some intlist [ 3 4 5")

def test_parsing_subexpr():
    ae=AExpr("some subexpression now (i:tokenlist)", atypes)

    assert ae("some subexpression now (3 4 5)") == {"i" : ["3", "4", "5"] }
    assert ae("some subexpression now ()") == {"i" : [] }

    assert ae("some subexpression now ((()))") == {"i" : ["(", "(", ")", ")"] }

    assert (ae("some subexpression now (8 9 10 ( asd 3 4 ) (a b c) (d e (()) f))") ==
            { "i" : ["8", "9", "10", "(", "asd", "3", "4", ")", "(", "a", "b", "c", ")", "(", "d",
                     "e", "(", "(", ")", ")", "f", ")"]})

    with pytest.raises(ValidationError):
        ae("some subexpression now (((()))")

    with pytest.raises(ValidationError):
        ae("some subexpression now (3 4 5")

    with pytest.raises(ValidationError):
        ae("some subexpression now 3 4 5")

    with pytest.raises(ValidationError):
        ae("some subexpression now ( 3 ( 4 5")

def test_parsing_strings():
    ae=AExpr("some string %s:safestring", atypes)

    assert ae("some string 'a b c'") == {"s": "a b c"}
    assert ae('some string "a b c"') == {"s": "a b c"}
    with pytest.raises(ValidationError):
        ae('some string "a < b c"')

    with pytest.raises(ValidationError):
        ae('some string ">"')

    with pytest.raises(ValidationError):
        ae('some string "a')

    with pytest.raises(ValidationError):
        ae('some string a')

    with pytest.raises(ValidationError):
        ae('some string "a\'')


def test_tooshort():
    ae=AExpr("", atypes)
    with pytest.raises(ValidationError):
        ae("")


    ae=AExpr("x", atypes)
    with pytest.raises(ValidationError):
        ae.parse([])

    with pytest.raises(ValidationError):
        ae.parse(verr_at(["a"], 0))

    with pytest.raises(ValidationError):
        ae("")

def test_verr():
    ae=AExpr("[a:int]", atypes)
    with pytest.raises(ValidationError):
        ae.parse(verr_at(["[", "1", "2"], 1))

    ae=AExpr("(a:int)", atypes)
    with pytest.raises(ValidationError):
        ae.parse(verr_at(["(", "1", "2"], 1))

def test_optional():
    ae=AExpr("some string %s:safestring and ?( optional string %t:safestring ) also", atypes)

    r1 = ae.parse("some string 'abc' and optional string 'def' also".split())
    assert r1 == { "s" : "abc", "t": "def" }

    r2 = ae.parse("some string 'abc' and also".split())
    assert r2 == { "s" : "abc" }

    with pytest.raises(ValidationError):
        ae.parse("some string 'abc' and".split())

    with pytest.raises(ValidationError):
        ae.parse("some string 'abc' and optional".split())
