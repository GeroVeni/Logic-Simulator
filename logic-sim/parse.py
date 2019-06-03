"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
import wx

from names import Names
from scanner import Scanner, Symbol
from devices import Devices
from network import Network
from monitors import Monitors
import wx
# add translation macro to builtin similar to what gettext does
import builtins
builtins.__dict__['_'] = wx.GetTranslation


class Parser:

    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.

    get_error_codes(self): Return the error codes list generated while
                           running parse_network()

    All other methods are considered non public
    """

    # Static variables to define error codes for availbility for unitests
    [SYNTAX_ERROR, UNDEFINED_DEVICE_ERROR, DEVICE_VALUE_ERROR,
     KEYWORD_ERROR, REPEATED_IDENTIFIER_ERROR, CONNECTION_INPUT_ERROR,
     OUTPUT_ERROR, MONITOR_INPUT_ERROR, INVALID_DEVICE_OUTPUT_ERROR,
     REPEATED_MONITOR_ERROR, UNMATCHED_INPUT_OUTPUT_ERROR,
     MISSING_INPUTS_ERROR, REPEATED_INPUT_ERROR, INVALID_PORT_ERROR,
     NOT_GATE_ERROR, OUT_OF_BOUND_INPUTS_ERROR] = range(16)

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        # Initialise parameters as variables of class
        self.scanner = scanner
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        # Initialise symbol as an empty symbol
        self.symbol = Symbol()
        # Variable to store nº errors
        self.error_count = 0
        # List of error codes used in get_error_codes
        self.error_codes = []
        # Flag changed when an error is encountered and
        # set back to true when the parser recovers
        self.recovered_from_definition_error = True
        # Variables for  storing info for parsing
        self.current_device = Symbol()
        self.current_number = Symbol()
        self.identifier_list = []
        self.current_name = Symbol()
        self.current_port = Symbol()
        self.outputs_list = []
        self.inputs_list = []
        self.monitors_list = []

    def parse_network(self):
        """ Parse the circuit definition file.

        The EBNF grammar is:
        device_list, connection_list, [ monitor_list ] ;
        """
        self.symbol = self.scanner.get_symbol()
        self.device_list()
        self.connection_list()
        # Check for EOF inside monitors_list if MONITORS not given
        self.monitor_list()
        if (self.error_count == 0):
            return True
        else:
            # Error message
            print(_("Number of errors encountered:"), self.error_count)
            return False

    def device_list(self):
        """Parse a device list.

        The EBNF grammar is the following:
        "DEVICES", ":", device_definition, { device_definition },
        "END", ";" ;
        """
        # Must check that its both a KEYWORD and the correct id as for
        # example numbers can have the same id as DEVICES_ID.
        if (self.symbol.type == self.scanner.KEYWORD and
                self.symbol.id == self.scanner.DEVICES_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                # Ensure all variables and lists are empty
                self.clear_all()
                self.device_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    # If it has returned to the while loop it must
                    # have recovered from the error during device_definition.
                    self.recovered_from_definition_error = True
                    # Ensure all variables and lists are empty
                    self.clear_all()
                    self.device_definition()
                # Recovered from error as KEYWORD or EOF found
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and
                        self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        # Recover to KEYWORD so it can parse CONNECTIONS
                        self.error(self.SYNTAX_ERROR, ";",
                                   stopping_symbol="KEYWORD")
                else:
                    # Recover to KEYWORD so it can parse CONNECTIONS
                    self.error(self.SYNTAX_ERROR, "END",
                               stopping_symbol="KEYWORD")
            else:
                # Recover to END so it can parse CONNECTIONS
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol="END")
        else:
            # Recover to END so it can parse CONNECTIONS
            self.error(self.SYNTAX_ERROR, "DEVICES",
                       stopping_symbol="END")

    def connection_list(self):
        """Parse a connection list.

        The EBNF grammar is the following:
        "CONNECTIONS", ":", connection_definition,
        { connection_definition }, "END", ";" ;
        """
        # Must check that its both a KEYWORD and the correct id as for
        # example numbers can have the same id as DEVICES_ID.
        if (self.symbol.type == self.scanner.KEYWORD and
                self.symbol.id == self.scanner.CONNECTIONS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                # Ensure all variables and lists are empty
                self.clear_all()
                self.connection_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    self.clear_all()
                    # If it has returned to the while loop it must
                    # have recovered from the error during device_definition.
                    self.recovered_from_definition_error = True
                    self.connection_definition()
                # Recovered from error as KEYWORD or EOF found
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and
                        self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        # Only throw missing inputs if no errors occured
                        # previously as probably missing ip from errors.
                        if ((not self.network.check_network()) and
                                self.error_count == 0):
                            # Store all the device names in a string
                            devices = ""
                            # Iterate over all devices
                            for device_id in self.devices.find_devices():
                                device = self.devices.get_device(device_id)
                                for input_id in device.inputs:
                                    # Check if the input has a connection
                                    if (self.network.get_connected_output(
                                            device_id, input_id) is None):
                                        # Add device to missing inputs string
                                        devices = devices + \
                                            self.names.get_name_string(
                                                device_id) + " "
                                        # Move to next device
                                        break
                            self.error(self.MISSING_INPUTS_ERROR,
                                       message=devices,
                                       stopping_symbol=None)
                        self.symbol = self.scanner.get_symbol()
                    else:
                        # Recover to KEYWORD so it can parse MONITORS
                        self.error(self.SYNTAX_ERROR, ";",
                                   stopping_symbol="KEYWORD")
                else:
                    # Recover to KEYWORD so it can parse MONITORS
                    self.error(self.SYNTAX_ERROR, "END",
                               stopping_symbol="KEYWORD")
            else:
                # Recover to END so it can parse MONITORS
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol="END")
        else:
            # Recover to END so it can parse MONITORS
            self.error(self.SYNTAX_ERROR, "CONNECITIONS",
                       stopping_symbol="END")

    def monitor_list(self):
        """Parse a connection list.

        The EBNF grammar is the following:
        "MONITORS", ":", signal, { "," , signal }, ";", "END", ";" ;
        """
        # Must check that its both a KEYWORD and the correct id as for
        # example numbers can have the same id as DEVICES_ID.
        if (self.symbol.type == self.scanner.KEYWORD and
           self.symbol.id == self.scanner.MONITORS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                # Ensure all variables and lists are empty
                self.clear_all()
                # The signals on monitors should be only outputs
                self.monitors_list.append(self.signal("M"))
                while (self.symbol.type == self.scanner.COMMA and
                       self.recovered_from_definition_error):
                    self.clear_vars()
                    self.symbol = self.scanner.get_symbol()
                    self.monitors_list.append(self.signal("M"))
                if (self.symbol.type == self.scanner.SEMICOLON):
                    # Only make monitors if count is zero
                    if(self.error_count == 0):
                        self.make_monitors()
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.id == self.scanner.END_ID and
                            self.symbol.type == self.scanner.KEYWORD):
                        self.symbol = self.scanner.get_symbol()
                        if (self.symbol.type == self.scanner.SEMICOLON):
                            self.symbol = self.scanner.get_symbol()
                            if(self.symbol.type == self.scanner.EOF):
                                pass
                            else:
                                self.error(self.SYNTAX_ERROR, "EOF",
                                           skipt_to_symbol="EOF")
                        else:
                            self.error(self.SYNTAX_ERROR, ";",
                                       stopping_symbol="EOF")
                    else:
                        self.error(self.SYNTAX_ERROR, "END",
                                   stopping_symbol="EOF")
                elif(not self.recovered_from_definition_error):
                    # Check that monitors has END; if error encountered
                    self.recovered_from_definition_error = True
                    if (self.symbol.id == self.scanner.END_ID and
                            self.symbol.type == self.scanner.KEYWORD):
                        self.symbol = self.scanner.get_symbol()
                        if (self.symbol.type == self.scanner.SEMICOLON):
                            self.symbol = self.scanner.get_symbol()
                            if(self.symbol.type == self.scanner.EOF):
                                pass
                            else:
                                self.error(self.SYNTAX_ERROR, "EOF",
                                           skipt_to_symbol="EOF")
                        else:
                            self.error(self.SYNTAX_ERROR, ";",
                                       stopping_symbol="EOF")
                    else:
                        self.error(self.SYNTAX_ERROR, "END",
                                   stopping_symbol="EOF")
                else:
                    self.error(self.SYNTAX_ERROR, ";",
                               stopping_symbol="END")
            else:
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol="END")
        elif(self.symbol.type == self.scanner.EOF):
            pass
        else:
            self.error(self.SYNTAX_ERROR, "MONITORS OR EOF",
                       stopping_symbol="EOF")

    def device_definition(self):
        """Parse a device defintion.

        The EBNF grammar is the following:
        identifier, { "," , identifier }, ":=",
        device_type, [ "(" , number , ")" ], ";" ;
        """
        self.identifier()
        # Throught device definition only enter if statements and while
        # loops if we have recovered from an error. Equivalent to
        # stop parsing device_definition if an error occurs.
        while (self.symbol.type == self.scanner.COMMA and
               self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.identifier()
        if (self.symbol.type == self.scanner.DEVICE_DEF and
                self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.device_type()
            if (self.symbol.type == self.scanner.BRACKET_LEFT and
                    self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
                self.number()
                if(self.symbol.type == self.scanner.BRACKET_RIGHT and
                   self.recovered_from_definition_error):
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.error(self.SYNTAX_ERROR, ")")
            # If the symbol is not a bracket but a number must
            # be missing left bracket from grammar.
            elif (self.symbol.type == self.scanner.NUMBER and
                  self.recovered_from_definition_error):
                self.error(self.SYNTAX_ERROR, "(")
            else:
                # If no number specified in file set variable current_number
                # by default to an empty symbol.
                self.current_number = Symbol()
            if (self.symbol.type == self.scanner.SEMICOLON and
                    self.recovered_from_definition_error):
                # Making devices does not break if errors have occured
                # previously but not during device_definition
                self.make_devices()
                self.symbol = self.scanner.get_symbol()
            else:
                self.error(self.SYNTAX_ERROR, ";")
        # From grammar name followed by name possibly indicates mising coma
        elif (self.symbol.type == self.scanner.NAME):
            self.error(self.SYNTAX_ERROR, ",")
        else:
            self.error(self.SYNTAX_ERROR, ":=")

    def connection_definition(self):
        """Parse a connection defintion.

        The EBNF grammar is the following:
        signal, { "," , signal }, "=>", signal, { "," , signal }, ";" ;
        """
        # Beginning clear all variables
        self.clear_vars()
        # The signals on the left hand side should be outputs
        self.outputs_list.append(self.signal("O"))
        while (self.symbol.type == self.scanner.COMMA and
               self.recovered_from_definition_error):
            self.clear_vars()
            self.symbol = self.scanner.get_symbol()
            self.outputs_list.append(self.signal("O"))
        if (self.symbol.type == self.scanner.CONNECTION_DEF and
                self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.clear_vars()
            self.inputs_list.append(self.signal("I"))
            while (self.symbol.type == self.scanner.COMMA and
                   self.recovered_from_definition_error):
                self.clear_vars()
                self.symbol = self.scanner.get_symbol()
                # The signals on the right hand side should be inputs
                self.inputs_list.append(self.signal("I"))
            if (self.symbol.type == self.scanner.SEMICOLON and
                    self.recovered_from_definition_error):
                # Only make connection if there have been no errors
                # or might through unexpected errors
                if (self.error_count == 0):
                    self.make_connection()
                self.symbol = self.scanner.get_symbol()
            # From grammar name followed by name possibly indicates mising coma
            elif (self.symbol.type == self.scanner.NAME):
                self.error(self.SYNTAX_ERROR, ",")
            else:
                self.error(self.SYNTAX_ERROR, ";")
        # From grammar name followed by name possibly indicates mising coma
        elif (self.symbol.type == self.scanner.NAME):
            self.error(self.SYNTAX_ERROR, ",")
        else:
            self.error(self.SYNTAX_ERROR, "=>")

    def clear_all(self):
        """Clear all symbols and lists used during parsing."""
        self.clear_vars()
        self.identifier_list = []
        self.outputs_list = []
        self.inputs_list = []
        self.monitors_list = []

    def clear_vars(self):
        """Clear all symbols used during parsing."""
        self.current_device = Symbol()
        self.current_number = Symbol()
        self.current_name = Symbol()
        self.current_port = Symbol()

    def error(self, error_type, message=None, stopping_symbol="KEYWORD or ;"):
        """Calls function to display and record error."""
        # Only record error if it has recovered from any previous errors
        if (self.recovered_from_definition_error):
            self.error_count += 1
            self.error_codes.append(error_type)
            self.display_error(error_type, message)
            self.skip_to_stopping_symbol(stopping_symbol)

    def display_error(self, error_type, message):
        """Display specific error depending on error_type."""
        # TODO change names of errors raised (NameError) e.g ConnectionError
        # TODO Make sure caret prints at correct points
        if (error_type == self.SYNTAX_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***SyntaxError: invalid syntax. Expected"), message)
        elif (error_type == self.DEVICE_VALUE_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***ValueError:"), message)
        elif (error_type == self.KEYWORD_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***NameError: Keywords, devices and ports names ") +
                  _("are reserved and cannot be used as identifiers."))
        elif (error_type == self.REPEATED_IDENTIFIER_ERROR):
            print("Line: {}".format(message.line))
            self.scanner.get_error_line(message)
        # TODO display correct carret
        # TODO display the other identifier using id in lookup names
        # TODO display name with forma
            print(_("***NameError: An identifier was repeated. ") +
                  _("All identifiers must have unique names."))
        elif (error_type == self.CONNECTION_INPUT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***TypeError: Inputs must be on the right") +
                  _(" hand side of the connection definition"))
        elif (error_type == self.OUTPUT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***TypeError: Outputs must be on the left") +
                  _(" hand side of the connection definition"))
        elif (error_type == self.MONITOR_INPUT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***TypeError: Monitors can only be outputs."))
        elif (error_type == self.REPEATED_MONITOR_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(message)
            print(_("***NameError: A monitor was repeated. ") +
                  _("All monitors must be unique."))
        elif (error_type == self.INVALID_DEVICE_OUTPUT_ERROR):
            print("Line: {}".format(message.line))
            self.scanner.get_error_line(message)
            print(_("***TypeError: The device has no such output."))
        elif (error_type == self.UNDEFINED_DEVICE_ERROR):
            print("Line: {}".format(message.line))
            self.scanner.get_error_line(message)
            print(_("***NameError: The device has not been previously") +
                  _(" defined in DEVICES."))
        elif (error_type == self.UNMATCHED_INPUT_OUTPUT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***TypeError: The number of inputs and outputs ") +
                  _("must match unless you are specifying one output to") +
                  _(" many inputs or all the inputs of a device at once"))
        elif (error_type == self.REPEATED_INPUT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***ValueError: The input has already been ") +
                  _("specified previously. Repeated assignment of ") +
                  _("inputs is not allowed."))
        elif (error_type == self.INVALID_PORT_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***ValueError: The port specified does not exist ") +
                  _("for such device or is out of bounds"))
        elif (error_type == self.NOT_GATE_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            print(_("***TypeError: Only gates can have simultaneous ") +
                  _("assignment of all of its inputs."))
        elif (error_type == self.OUT_OF_BOUND_INPUTS_ERROR):
            print("Line: {}".format(self.symbol.line))
            self.scanner.get_error_line(self.symbol)
            # TODO specify  too many or too few
            print(_("***TypeError: Too many or too few inputs ") +
                  _("have been assigned simultaneously to the device.") +
                  _(" When using simultaneous defintion the same number") +
                  _(" of inputs as the device has must be given."))
        elif (error_type == self.MISSING_INPUTS_ERROR):
            print(_("***ValueError: Some inputs have not been specificed") +
                  _(" for these devices: ") + message)

    def skip_to_stopping_symbol(self, stopping_symbol):
        """Use scanner to skip to stopping_symbol specificed."""
        # KEYWORD or ; if the default
        if (stopping_symbol == "KEYWORD or ;"):
            # Not fully recovered by skipping to symbol
            self.recovered_from_definition_error = False
            while (self.symbol.type != self.scanner.SEMICOLON and
                   self.symbol.type != self.scanner.KEYWORD and
                   self.symbol.type != self.scanner.EOF):
                self.symbol = self.scanner.get_symbol()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.symbol = self.scanner.get_symbol()
        elif (stopping_symbol == "KEYWORD"):
            while (self.symbol.type != self.scanner.KEYWORD and
                   self.symbol.type != self.scanner.EOF):
                self.symbol = self.scanner.get_symbol()
        elif (stopping_symbol == ";"):
            # Not fully recovered by skipping to symbol
            self.recovered_from_definition_error = False
            while (self.symbol.type != self.scanner.SEMICOLON and
                   self.symbol.type != self.scanner.EOF):
                self.symbol = self.scanner.get_symbol()
            self.symbol = self.scanner.get_symbol()
        elif (stopping_symbol == "END"):
            while ((self.symbol.type != self.scanner.KEYWORD or
                    self.symbol.id != self.scanner.END_ID) and
                   self.symbol.type != self.scanner.EOF):
                self.symbol = self.scanner.get_symbol()
            if (self.symbol.type == self.scanner.EOF):
                self.error(self.SYNTAX_ERROR, "END")
            else:
                self.symbol = self.scanner.get_symbol()
                if (self.symbol.type == self.scanner.SEMICOLON):
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.error(self.SYNTAX_ERRPR, ";")
        elif (stopping_symbol == "EOF"):
            while (self.symbol.type != self.scanner.EOF):
                self.symbol = self.scanner.get_symbol()
        elif (stopping_symbol is None):
            pass

    def make_monitors(self):
        """Make monitors using signals in monitors_list."""
        for monitors in self.monitors_list:
            (identifier, port) = monitors
            error = self.monitors.make_monitor(identifier.id,
                                               port.id)
            if (error == self.network.DEVICE_ABSENT):
                self.error(self.UNDEFINED_DEVICE_ERROR, identifier,
                           stopping_symbol=None)
            elif (error == self.monitors.NOT_OUTPUT):
                self.error(self.INVALID_DEVICE_OUTPUT_ERROR,
                           identifier, stopping_symbol=None)
            elif (error == self.monitors.MONITOR_PRESENT):
                self.error(self.REPEATED_MONITOR_ERROR, identifier,
                           stopping_symbol=None)

    def signal(self, I_O_M):
        """ Pars a signal.

        Return the signal if parsed correctly as a tuple (name, port)

        Parameters
        ----------
        I_O_M: Denotes wether we are expecting an input
               port or ouptut port during connection definition
               or if it is a monitor port.
        """
        if (self.symbol.type == self.scanner.NAME and
                self.recovered_from_definition_error):
            self.current_name = self.symbol
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.DOT):
                self.symbol = self.scanner.get_symbol()
                self.port(I_O_M)
            return (self.current_name, self.current_port)
        else:
            self.error(self.SYNTAX_ERROR, "signal")

    def port(self, I_O_M):
        """Parse a port.

        Parameter
        ---------
        I_O_M: Denotes wether we are expecting an input
               port or ouptut port during connection definition
               or if it is a monitor port.
        """
        # Outputs and monitors cannot be input ports
        if (self.symbol.type == self.scanner.PORT and
            (I_O_M == "O" or I_O_M == "M") and
            (self.symbol.id == self.scanner.I_ID or
             self.symbol.id == self.scanner.DATA_ID or
             self.symbol.id == self.scanner.CLK_ID or
             self.symbol.id == self.scanner.SET_ID or
             self.symbol.id == self.scanner.CLEAR_ID)):
            if (I_O_M == "O"):
                self.error(self.CONNECTION_INPUT_ERROR)
            elif (I_O_M == "M"):
                self.error(self.MONITOR_INPUT_ERROR)
        # Inputs cannot have output ports
        elif (self.symbol.type == self.scanner.PORT and
              I_O_M == "I" and (self.symbol.id == self.scanner.Q_ID or
                                self.symbol.id == self.scanner.QBAR_ID)):
            self.error(self.OUTPUT_ERROR)
        # If its and I port save the number as the port
        elif (self.symbol.id == self.scanner.I_ID and
              self.symbol.type == self.scanner.PORT and
              self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.number()
            self.current_port = self.current_number
        # If it is another type of port save that symbol as the port
        elif (self.symbol.type == self.scanner.PORT and
              self.recovered_from_definition_error):
            self.current_port = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "port")

    def number(self):
        """Parse a number."""
        # Only parse if recovered from an error
        if (self.symbol.type == self.scanner.NUMBER and
           self.recovered_from_definition_error):
            self.current_number = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "number")

    def identifier(self):
        """Parse an identifier."""
        # Only parse if recoverd from the error
        if (self.symbol.type == self.scanner.NAME and
                self.recovered_from_definition_error):
            self.identifier_list.append(self.symbol)
            self.symbol = self.scanner.get_symbol()
        # If symbol is KEYWORD, DEVICE or PORT raise semantic error
        elif((self.symbol.type == self.scanner.KEYWORD or
              self.symbol.type == self.scanner.DEVICE or
              self.symbol.type == self.scanner.PORT) and
             self.recovered_from_definition_error):
            self.error(self.KEYWORD_ERROR, stopping_symbol=";")
        else:
            self.error(self.SYNTAX_ERROR, "identifier")

    def device_type(self):
        """Parse a device."""
        # Only parse if recovered from an error
        if (self.symbol.type == self.scanner.DEVICE and
                self.recovered_from_definition_error):
            self.current_device = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "device")

    def make_devices(self):
        """Make specified device for each identifier in identifier_list."""
        for identifier in self.identifier_list:
            # Check for repeated identifiers
            if (self.devices.get_device(identifier.id) is not None):
                # Should not skip to a symbol as currently at ;
                # Applies to all the errors called in make_devices()
                self.error(self.REPEATED_IDENTIFIER_ERROR,
                           identifier, None)
                # Don't exit as other identifiers might not be repeated
            elif (self.current_device.id == self.scanner.DTYPE_ID):
                error = self.devices.make_device(identifier.id,
                                                 self.devices.D_TYPE,
                                                 self.current_number.id)
                # Invalid device error already checked in device_type()
                # so not checked for in any of the devices below
                if (error == self.devices.QUALIFIER_PRESENT):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("DTYPE takes no number"), None)
                    # Exit make_devices if error occured as devices
                    # creation not valid for any of the identifiers
                    return
            elif (self.current_device.id == self.scanner.SWITCH_ID):
                # Set default value to 0 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 0
                error = self.devices.make_device(identifier.id,
                                                 self.devices.SWITCH,
                                                 self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("SWITCH takes only 0 or 1"), None)
                    return
            elif (self.current_device.id == self.scanner.CLOCK_ID):
                # Set default value to 1 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 1
                error = self.devices.make_device(identifier.id,
                                                 self.devices.CLOCK,
                                                 self.current_number.id)
                # This error can only hapen with zero as trying to define a
                # negative number will give a syntax error as - is invalid
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("CLOCK takes only values greater than 0"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.NAND_ID):
                # Set default value to 2 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 2
                error = self.devices.make_device(identifier.id,
                                                 self.devices.NAND,
                                                 self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("NAND gates can only have 1 to 16 inputs"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.AND_ID):
                # Set default value to 2 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 2
                error = self.devices.make_device(identifier.id,
                                                 self.devices.AND,
                                                 self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("AND gates can only have 1 to 16 inputs"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.NOR_ID):
                # Set default value to 2 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 2
                error = self.devices.make_device(identifier.id,
                                                 self.devices.NOR,
                                                 self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("NOR gates can only have 1 to 16 inputs"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.OR_ID):
                # Set default value to 2 if no value specified
                if (self.current_number.id is None):
                    self.current_number.id = 2
                error = self.devices.make_device(identifier.id,
                                                 self.devices.OR,
                                                 self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("OR gates can only have 1 to 16 inputs"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.XOR_ID):
                # XOR must have None in device_property
                # If 2 specificied change to None
                # Default value already None if no number assigned
                if (self.current_number.id == 2):
                    self.current_number.id = None
                error = self.devices.make_device(identifier.id,
                                                 self.devices.XOR,
                                                 self.current_number.id)
                # If number specificied not 2 an error raised
                # as device_type wont be None
                if (error == self.devices.QUALIFIER_PRESENT):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("XOR gates can only have 2 inputs"),
                               None)
                    return
            elif (self.current_device.id == self.scanner.SIGGEN_ID):
                error = self.devices.make_device(identifier.id,
                                                 self.devices.SIGGEN,
                                                 self.current_number.id)
                if (error == self.devices.NO_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("SIGGEN requires a parameter to be"
                                 "specified."), None)
                    return
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                               _("SIGGEN requires a 4 or 8 followed by a "
                                 "binary number."), None)
                    return

    def make_connection(self):
        """" Create a connection between the inputs and ouputs specified.

        There are 4 different types of specifyinf connections:
        *many outputs to many inputs simultaneously
        *one output to one input
        *defining all the inputs of a device at once (gates only)
        *one output to many inputs

        """
        # many to many or one to one
        if (len(self.outputs_list) == len(self.inputs_list)):
            for output, device_ip in zip(self.outputs_list,
                                         self.inputs_list):
                [in_device_id, in_port_id] = self.get_in(output)
                [out_device_id, out_port_id] = self.get_out(device_ip)
                # For devices with one input only and no port specified
                # We must add the port .I1 as its id
                # Equivalent to defining all the inputs at once.
                # Check device has one input and no port specified
                if (len(self.inputs_list) == 1 and out_port_id is None):
                    device = self.devices.get_device(out_device_id)
                    # check_connection_error will raise undefined_device
                    if (device is None):
                        pass
                    # check_connection_error will raise OUTPUT_TO_OUTPUT
                    elif (len(device.inputs) != 1):
                        pass
                    else:
                        input_name = "".join(["I", str(1)])
                        [out_port_id] = self.names.lookup([input_name])
                error_type = self.network.make_connection(in_device_id,
                                                          in_port_id,
                                                          out_device_id,
                                                          out_port_id)
                self.check_connection_error(error_type)
        # Many to one
        elif (len(self.inputs_list) == 1):
            # Device to connect all the inputs
            [device_input] = self.inputs_list
            [out_device_id, out_port] = self.get_out(device_input)
            device = self.devices.get_device(out_device_id)
            # TODO add many to one for DTYPE and make sure keys sorted as
            # the .SET .CLEAR .DATA, .CLOCK ids assigned in specific order
            # Only works for gates
            if (device.device_kind not in self.devices.gate_types):
                self.error(self.NOT_GATE_ERROR, stopping_symbol=None)
            else:
                # Check the nº inputs given matches the nº the device has
                if (len(device.inputs) == len(self.outputs_list)):
                    device_inputs = list(device.inputs.keys())
                    # Iterate of the out devices to make connections
                    for output, out_port_id in zip(self.outputs_list,
                                                   device_inputs):
                        [in_device_id, in_port_id] = self.get_in(output)
                        error_type = self.network.make_connection(
                            in_device_id, in_port_id,
                            out_device_id, out_port_id)
                        self.check_connection_error(error_type)
                else:
                    self.error(self.OUT_OF_BOUND_INPUTS_ERROR,
                               stopping_symbol=None)
        # one to many
        elif (len(self.outputs_list) == 1):
            # Output to connect to all inputs
            [output] = self.outputs_list
            [in_device_id, in_port_id] = self.get_in(output)
            # Iterate over all the inputs
            for device_ip in self.inputs_list:
                [out_device_id, out_port_id] = self.get_out(device_ip)
                error_type = self.network.make_connection(
                    in_device_id, in_port_id, out_device_id,
                    out_port_id)
                self.check_connection_error(error_type)
        # If the lengths dont match and the ip and op are not one
        # the nº of ip and nº ops dont match
        else:
            self.error(self.UNMATCHED_INPUT_OUTPUT_ERROR,
                       stopping_symbol=None)

    def get_in(self, output):
        """Get ids for name and port of device going to inputs."""
        # Output ports can only be None, Q or QBAR
        # Port symbol id already specifiec with correct id
        name, port = output
        return name.id, port.id

    def get_out(self, device_ip):
        """Get ids for name and port of device being connected to."""
        name, port = device_ip
        # Input ports of the form .IX have a number symbol for the port
        # The correct id for port .IX must be retrieved using the number
        if (port.type == self.scanner.NUMBER):
            input_name = "".join(["I", str(port.id)])
            [port.id] = self.names.lookup([input_name])
        return name.id, port.id

    def check_connection_error(self, error_type):
        """Raise the appropriate error from the error_type given."""
        # TODO errors raised point to correct symbols
        if (error_type == self.network.NO_ERROR):
            pass
        elif (error_type == self.network.DEVICE_ABSENT):
            # TODO print the actual problem place MUSTDO!!!
            self.error(self.UNDEFINED_DEVICE_ERROR, self.symbol,
                       stopping_symbol=None)
        elif (error_type == self.network.INPUT_CONNECTED):
            # TODO print actual place
            self.error(self.REPEATED_INPUT_ERROR,
                       stopping_symbol=None)
        elif (error_type == self.network.PORT_ABSENT):
            # TODO specific check for I out of bounds (ValueError)
            # compared to invalid port used like .Q by non DTYPE (TypeError)
            # also show appropriate symbol or no ports given at all!
            self.error(self.INVALID_PORT_ERROR,
                       stopping_symbol=None)
        elif(error_type == self.network.INPUT_TO_INPUT):
            self.error(self.CONNECTION_INPUT_ERROR,
                       stopping_symbol=None)
        elif(error_type == self.network.OUTPUT_TO_OUTPUT):
            self.error(self.OUTPUT_ERROR,
                       stopping_symbol=None)

    def get_error_codes(self):
        """Return the error codes list generated while running
        parse_network().

        This method is used during unit testing to check
        that parse_network correctly identifies all errors
        in a definition file.

        Returns
        -------
        A list of int, corresponding to the error codes.
        """
        return self.error_codes
