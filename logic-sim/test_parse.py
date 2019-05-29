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
    # Correct definition files
    ("test_spec_1.txt", True, []),
    ("test_spec_2.txt", True, []),
    # Semantic error files
    ("test_semantic_con_input.txt", False, [Parser.CONNECTION_INPUT_ERROR]),
    ("test_semantic_con_output.txt", False, [Parser.OUTPUT_ERROR]),
    ("test_semantic_device_value.txt", False, [
        Parser.DEVICE_VALUE_ERROR] * 8 + [Parser.SYNTAX_ERROR]),
    # TODO Change this test to use Parser.INVALID_PORT_ERROR
    ("test_semantic_invalid_device_output.txt", False, [Parser.INVALID_DEVICE_OUTPUT_ERROR]),
    ("test_semantic_invalid_port.txt", False, [Parser.INVALID_PORT_ERROR]),
    ("test_semantic_keyword.txt", False, [Parser.KEYWORD_ERROR] * 2 + [Parser.SYNTAX_ERROR]),
    ("test_semantic_missing_inputs.txt", False, [Parser.MISSING_INPUTS_ERROR]),
    ("test_semantic_mon_input.txt", False, [Parser.MONITOR_INPUT_ERROR]),
    ("test_semantic_not_gate.txt", False, [Parser.NOT_GATE_ERROR]),
    ("test_semantic_out_of_bounds_inputs.txt", False, [Parser.OUT_OF_BOUND_INPUTS_ERROR]),
    ("test_semantic_repeated_identifier.txt", False, [
        Parser.REPEATED_IDENTIFIER_ERROR] * 2 + [Parser.SYNTAX_ERROR]),
    ("test_semantic_repeated_input.txt", False, [Parser.REPEATED_INPUT_ERROR]),
    ("test_semantic_repeated_monitor.txt", False, [Parser.REPEATED_MONITOR_ERROR]),
    ("test_semantic_undefined_device.txt", False, [Parser.UNDEFINED_DEVICE_ERROR]),
    ("test_semantic_unmatched_input_output.txt", False, [Parser.UNMATCHED_INPUT_OUTPUT_ERROR]),
    # Syntax error files
    ("test_syntax_con_def_invalid_symbol.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_con_def_missing_comma.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_con_def_missing_semicolon.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_dev_def_missing_comma.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_dev_def_missing_parenthesis.txt", False, [Parser.SYNTAX_ERROR] * 2),
    ("test_syntax_dev_def_missing_semicolon.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_argument.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_device.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_names.txt", False, [
        Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_port.txt", False, [Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_signal.txt", False, [Parser.SYNTAX_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_invalid_symbol.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_cons_1.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_cons_2.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_cons_3.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_devs_1.txt", False, [Parser.SYNTAX_ERROR] * 2),
    ("test_syntax_missing_devs_2.txt", False, [Parser.SYNTAX_ERROR] * 2),
    ("test_syntax_missing_devs_3.txt", False, [Parser.SYNTAX_ERROR] * 2),
    ("test_syntax_missing_mons_1.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_missing_mons_2.txt", False, [Parser.SYNTAX_ERROR] * 2),
    ("test_syntax_missing_mons_3.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_mon_def_missing_comma.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_mon_def_missing_semicolon.txt", False, [Parser.SYNTAX_ERROR]),
    ("test_syntax_no_devices.txt", False, [Parser.KEYWORD_ERROR, Parser.SYNTAX_ERROR]),
    ("test_syntax_wrong_symbol.txt", False, [Parser.SYNTAX_ERROR]),
])
def test_parse(new_parser, success, error_list):
    """Test that Parser.parse_network() returns the correct
    value and identifies the corresponding errors.
    """
    assert new_parser.parse_network() == success
    assert new_parser.get_error_codes() == error_list
