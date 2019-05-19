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
    ("test-syntax-missing-cons-1.txt", True, []),
    ("spec2.txt", True, []),
])
def test_parse(new_parser, success, error_list):
    """Test that Parser.parse_network() returns the correct
    value and identifies the corresponding errors.
    """
    assert new_parser.parse_network() == success
    assert new_parser.get_error_codes() == error_list
