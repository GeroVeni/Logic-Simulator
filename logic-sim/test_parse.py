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
    SPECFILES_DIR = "../specfiles/"
    path = SPECFILES_DIR + filename
    names = Names()
    scanner = Scanner(path, names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    return Parser(names, devices, network, monitors, scanner)

@pytest.mark.parametrize("filename, success, error_list", [
    ("test-spec-1.txt", True, []),
    ("test-spec-2.txt", True, []),
    ("test-syntax-dev-def-missing-comma.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-dev-def-missing-parenthesis.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_BAD_DEVICE,
        Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-dev-def-missing-semicolon.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-invalid-argument.txt", False, [
        Parser.ERROR_INVALID_ARGUMENT, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-invalid-device.txt", False, [
        Parser.ERROR_BAD_DEVICE, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-invalid-names.txt", False, [
        Parser.ERROR_BAD_NAME, Parser.ERROR_BAD_NAME]),
    ("test-syntax-invalid-symbol.txt", False, [
        Parser.ERROR_BAD_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-missing-cons-1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-cons-2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-cons-3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-devs-1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-devs-2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-devs-3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-mons-1.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-mons-2.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-missing-mons-3.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-mon-def-missing-comma.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-mon-def-missing-semicolon.txt", False, [Parser.ERROR_WRONG_SYMBOL]),
    ("test-syntax-no-devices.txt", False, [Parser.ERROR_UNDEFINED_DEVICE]),
    ("test-syntax-wrong-symbol.txt", False, [
        Parser.ERROR_WRONG_SYMBOL, Parser.ERROR_UNDEFINED_DEVICE]),
])
def test_parse(new_parser, success, error_list):
    """Test that Parser.parse_network() returns the correct
    value and identifies the corresponding errors.
    """
    assert new_parser.parse_network() == success
    assert new_parser.get_error_codes() == error_list
