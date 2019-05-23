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
    ("test_syntax_con_def_invalid_symbol.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_con_def_missing_comma.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_con_def_missing_semicolon.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_dev_def_missing_comma.txt", False, [
        Parser.SYNTAX_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_dev_def_missing_parenthesis.txt", False, [
        Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR,
        Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_dev_def_missing_semicolon.txt", False, [
        Parser.SYNTAX_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_invalid_argument.txt", False, [
        Parser.VALUE_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_invalid_device.txt", False, [
        Parser.SYNTAX_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_invalid_names.txt", False, [
        Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_port.txt", False, [Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_signal.txt", False, [Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_symbol.txt", False, [
        Parser.SYNTAX_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_missing_cons_1.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_cons_2.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_cons_3.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_devs_1.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_devs_2.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_devs_3.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_mons_1.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_mons_2.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_mons_3.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_mon_def_missing_comma.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_mon_def_missing_semicolon.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_no_devices.txt", False, [Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_syntax_wrong_symbol.txt", False, [
        Parser.SYNTAX_ERROR, Parser.UNDEFINED_DEVICE_ERROR]),
])
def test_parse(new_parser, success, error_list):
    """Test that Parser.parse_network() returns the correct
    value and identifies the corresponding errors.
    """
    assert new_parser.parse_network() == success
    assert new_parser.get_error_codes() == error_list
