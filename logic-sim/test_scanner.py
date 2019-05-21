""" Test the scanner module """
import pytest
from tempfile import NamedTemporaryFile

from scanner import Scanner
from names import Names

############
# FIXTURES #
############

@pytest.fixture
def new_names():
    """Return a new instance of the Names class."""
    return Names()

@pytest.fixture
def new_file():
    """" Creates a temporary file to store the data to be scanned and returns the names of the file """
    def _file(string):
        f = NamedTemporaryFile(mode='w+', delete=False)
        f.write(string)
        f.close()
        return f.name
    return _file

@pytest.fixture
def new_Scanner():
    """Return a new instance of the Scanner class with the path specificed and empty names object"""
    def _scanner(path):
        return Scanner(path, Names())
    return _scanner

####################
# TEST EXCEPCTIONS #
####################

#I0Error File
#Names object not given
#Give it not a string
#File path is .txt

###################
# TEST get_symbol #
###################

def test_get_symbol_emptyfile(new_Scanner, new_names):
    scanner = new_Scanner("testfiles/scanner/test_empty_file.txt")
    assert scanner.get_symbol().type == scanner.EOF
    scanner = new_Scanner("testfiles/scanner/test_only_white_space.txt")
    assert scanner.get_symbol().type == scanner.EOF

def test_get_symbol_types(new_Scanner, new_file):
    types = new_file("MONITORS AND Q PYSLINDERS 12345 : ; , := ( ) => . %")
    scanner = new_Scanner(types)
    current_symbol = scanner.get_symbol()
    i = 0
    while current_symbol.type != scanner.EOF:
        assert current_symbol.type == i
        current_symbol = scanner.get_symbol()
        i += 1

def test_get_symbol_keywords(new_Scanner, new_file):
    keywords = new_file("CONNECTIONS DEVICES MONITORS END")
    scanner = new_Scanner(keywords)
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        assert current_symbol.type == scanner.KEYWORD
        current_symbol = scanner.get_symbol()

def test_get_symbol_devices(new_Scanner, new_file):
    devices = new_file("NAND AND NOR OR XOR DTYPE CLOCK SWITCH")
    scanner = new_Scanner(devices)
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        assert current_symbol.type == scanner.DEVICE
        current_symbol = scanner.get_symbol()

def test_get_symbol_ports(new_Scanner, new_file):
    ports = new_file("Q QBAR DATA CLK SET CLEAR I")
    scanner = new_Scanner(ports)
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        assert current_symbol.type == scanner.PORT
        current_symbol = scanner.get_symbol()

def test_get_symbol_comments(new_Scanner, new_file):
    valid_comment = new_file("//this is a valid comment")
    scanner = new_Scanner(valid_comment)
    assert scanner.get_symbol().type == scanner.EOF
    same_line_comment = new_file("COMMENT//this is a valid inline comment")
    scanner = new_Scanner(same_line_comment)
    assert scanner.get_symbol().type == scanner.NAME
    assert scanner.get_symbol().type == scanner.EOF
    invalid_comment = new_file("/this is a wrong comment")
    scanner = new_Scanner(invalid_comment)
    assert scanner.get_symbol().type == scanner.INVALID_SYMBOL
    assert scanner.get_symbol().type == scanner.EOF


@pytest.mark.parametrize("example_string, number_symbols", [
    ("AND,CONNECTIONS.;=>GOOD", 7),
    ("IS:this,working", 5),
    ("Lets()try:again", 6 ),
    ("DEVICES:=just,I.N&case", 9),
])

#TODO append what you expect to get

def test_get_symbol_no_spaces(new_Scanner, new_file, example_string, number_symbols):
    no_spaces_string = new_file(example_string)
    scanner = new_Scanner(no_spaces_string)
    symbol_list = []
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        symbol_list.append(current_symbol)
        current_symbol = scanner.get_symbol()
    assert len(symbol_list) == number_symbols

#TODO also test for the types expected in the files instead of only number

def test_get_symbol_ignore_white_spaces(new_Scanner):
    scanner = new_Scanner("testfiles/scanner/test_ignore_white_spaces.txt")
    symbol_list = []
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        symbol_list.append(current_symbol)
        current_symbol = scanner.get_symbol()
    assert len(symbol_list) == 7

#TODO as above

def test_get_symbol_one_per_line(new_Scanner):
    scanner = new_Scanner("testfiles/scanner/test_one_symbol_per_line.txt")
    symbol_list = []
    current_symbol = scanner.get_symbol()
    while current_symbol.type != scanner.EOF:
        symbol_list.append(current_symbol)
        current_symbol = scanner.get_symbol()
    assert len(symbol_list) == 8

@pytest.mark.parametrize("invalid_symbol", [
    ("&"),
    ("¬"),
    ("$"),
    ("|"),
    ("@"),
    ("["),
    ("}"),
])

def test_get_symbols_invalid_symbols(new_Scanner, new_file, invalid_symbol):
    invalid = new_file(invalid_symbol)
    scanner = new_Scanner(invalid)
    assert scanner.get_symbol().type == scanner.INVALID_SYMBOL


@pytest.mark.parametrize("invalid_valid_string", [
    ("=:="),
    ("==>"),
    ("_UNDERSCORE"),
])

def test_get_symbol_invalid_valid_string(new_Scanner, new_file, invalid_valid_string):
    invalid_valid_symbols = new_file(invalid_valid_string)
    scanner = new_Scanner(invalid_valid_symbols)
    assert scanner.get_symbol().type == scanner.INVALID_SYMBOL
    assert scanner.get_symbol().type != scanner.INVALID_SYMBOl

@pytest.mark.parametrize("valid_invalid_string", [
    (":=="),
    ("=>="),
    (";_"),
])

def test_get_symbol_invalid_valid_string(new_Scanner, new_file, valid_invalid_string):
    valid_invalid_symbols = new_file(valid_invalid_string)
    scanner = new_Scanner(valid_invalid_symbols)
    assert scanner.get_symbol().type != scanner.INVALID_SYMBOL
    assert scanner.get_symbol().type == scanner.INVALID_SYMBOL

@pytest.mark.parametrize("number_name_string", [
    ("1s1"),
    ("1234asdf"),
    ("123asd123asd"),
])

def test_get_symbol_numbers_names(new_Scanner, new_file, number_name_string):
   number_name = new_file(number_name_string)
   scanner = new_Scanner(number_name)
   assert scanner.get_symbol().type == scanner.NUMBER
   assert scanner.get_symbol().type == scanner.NAME

@pytest.mark.parametrize("complex_name", [
    ("asdf1234"),
    ("asdf1234asdf1234asdf"),
    ("CONECCTIONSEND"),
    ("ANDNORCONNECTIOSQBAR"),
    ("asdf_"),
    ("asdf_asdf"),
    ("asdf_1234"),
    ("DEVICES_1234_asdf"),
])

def test_get_symbol_names_with_numbers_and_underscores_and_grouped_keyowrds(new_Scanner, new_file, complex_name):
   name = new_file(complex_name)
   scanner = new_Scanner(name)
   assert scanner.get_symbol().type == scanner.NAME
   assert scanner.get_symbol().type == scanner.EOF

def test_get_symbol_correct_name_id(new_Scanner, new_names, new_file):
    names = new_names
    names.lookup(["george", "jorge", "dimitris"])
    names_file = new_file("george jorge dimitris")
    scanner = Scanner(names_file, names)
    current_symbol = scanner.get_symbol()
    i = 0
    while current_symbol.type != scanner.EOF:
        assert current_symbol.id == i
        current_symbol = scanner.get_symbol()
        i += 1

@pytest.mark.parametrize("lines, actual_lines", [
    ("1\n2\n3\n4\n5", [1,2,3,4,5]),
    ("1\n2\n\n4\n\n\n7", [1,2,4,7]),
    ("\n\n3\n4\n5\n\n\n8", [3,4,5,8]),
])

def test_get_symbol_correct_line(new_Scanner, new_file, lines, actual_lines):
    lines_file = new_file(lines)
    scanner = new_Scanner(lines_file)
    for line in actual_lines:
        assert scanner.get_symbol().line == line

@pytest.mark.parametrize("column_data, actual_columns", [
    (",,,,,", [1,2,3,4,5]),
    (",, ,  ,       ,", [1,2,4,7,15]),
    ("  ,,  ,  ,   ,", [3,4,7,10,14]),
])

def test_get_symbol_correct_column(new_Scanner, new_file, column_data, actual_columns):
    columns = new_file(column_data)
    scanner = new_Scanner(columns)
    for column in actual_columns:
        assert scanner.get_symbol().column == column

@pytest.mark.parametrize("data, lines_columns", [
    (",,,,,", [(1,1),(1,2),(1,3),(1,4),(1,5)]),
    (",\n,\n,\n,\n,", [(1,1),(2,1),(3,1),(4,1),(5,1)]),
    (",\n ,\n  ,\n   ,\n    ,", [(1,1),(2,2),(3,3),(4,4),(5,5)]),
    ("\n\n   ,   ,\n,   ,   ,\n\n\n  ,", [(3,4),(3,8),(4,1),(4,5),(4,9),(7,3)]),
])

def test_get_symbol_correct_line_and_column(new_Scanner, new_file, data, lines_columns):
    data_file = new_file(data)
    scanner = new_Scanner(data_file)
    for line, column in lines_columns:
        current_symbol = scanner.get_symbol()
        assert current_symbol.column == column
        assert current_symbol.line == line
