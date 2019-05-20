"""Test the parse module."""
import pytest

from names import Names
from scanner import Scanner
from devices import Devices
from network import Network
from monitors import Monitors
from parse import Parser

@pytest.fixture
def new_parser(filename):
    """Return a new instance of the Parser class and
    parse the definition file.

    Parameters
    ----------
    filename: The name of the definition file in the specfiles directory
    """
    SPECFILES_DIR = "testfiles/parser/"
    path = SPECFILES_DIR + filename
    names = Names()
    scanner = Scanner(path, names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    return Parser(names, devices, network, monitors, scanner)

@pytest.mark.parametrize("filename, success, error_list", [
    ("test_spec_1.txt", True, []),
    ("test_spec_2.txt", True, []),
    ("test_syntax_dev_def_missing_comma.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_dev_def_missing_parenthesis.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_BAD_DEVICE,
        Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_dev_def_missing_semicolon.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_invalid_argument.txt", False, [
        Parser.ERROR_INVALID_ARGUMENT, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_invalid_device.txt", False, [
        Parser.ERROR_BAD_DEVICE, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_invalid_names.txt", False, [
        Parser.ERROR_BAD_NAME, Parser.ERROR_BAD_NAME]),
    ("test_syntax_invalid_symbol.txt", False, [
        Parser.ERROR_BAD_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_missing_cons_1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_cons_2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_cons_3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_devs_1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_devs_2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_devs_3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_mons_1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_mons_2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_missing_mons_3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_mon_def_missing_comma.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_mon_def_missing_semicolon.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test_syntax_no_devices.txt", False, [Parser.ERROR_UNDEFINED_DEVICE]),
    ("test_syntax_wrong_symbol.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
])
def test_parse(new_parser, success, error_list):
    """Test that Parser.parse_network() returns the correct
    value and identifies the corresponding errors.
    """
    assert new_parser.parse_network() == success
    assert new_parser.get_error_codes() == error_list
