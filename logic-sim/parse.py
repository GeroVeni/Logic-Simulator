"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
from names import Names
from scanner import Scanner, Symbol
from devices import Devices
from network import Network
from monitors import Monitors

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
    """

    [SYNTAX_ERROR, UNDEFINED_DEVICE_ERROR, DEVICE_VALUE_ERROR,
    KEYWORD_ERROR, REPEATED_IDENTIFIER_ERROR, CONNECTION_INPUT_ERROR,
    OUTPUT_ERROR, MONITOR_INPUT_ERROR, INVALID_DEVICE_OUTPUT_ERROR,
    REPEATED_MONITOR_ERROR, UNMATCHED_INPUT_OUTPUT_ERROR,
    MISSING_INPUTS_ERROR, REPEATED_INPUT_ERROR, INVALID_PORT_ERROR,
    NOT_GATE_ERROR, OUT_OF_BOUND_INPUTS_ERROR] = range(16)

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        #from above
        #use Symbol to create an empty Symbol type
        self.symbol = Symbol()
        self.scanner = scanner
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        #for errors
        self.error_count = 0
        #List of error codes used in get_error_codes
        self.error_codes = []
        self.recovered_from_definition_error = True
        #For storing info for parsing
        #used to clear symbols
        self.current_device = Symbol()
        self.current_number = Symbol()
        self.identifier_list = []
        self.current_name = Symbol()
        self.current_port = Symbol()
        self.outputs_list = []
        self.inputs_list = []
        self.monitors_list = []

    def error(self, error_type, message = None,
              stopping_symbol="KEYWORD or ;" ):
        if (self.recovered_from_definition_error):
            self.error_count +=1
            self.error_codes.append(error_type)
            self.display_error(error_type, message)
            self.skip_to_stopping_symbol(stopping_symbol)

    def display_error(self, error_type, message):
        if (error_type == self.SYNTAX_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***SyntaxError: invalid syntax. Expected", message)
        elif (error_type == self.DEVICE_VALUE_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***ValueError:", message)
        elif (error_type == self.KEYWORD_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***NameError: Keywords, devices and ports names " \
                  "are reserved and cannot be used as identifiers.")
        elif (error_type == self.REPEATED_IDENTIFIER_ERROR):
            self.scanner.get_error_line(message)
#TODO also add get_error_line by comparing identifier ids lookup names
            print("***NameError: An identifier was repeated. " \
                  "All identifiers must have unique names.")
        elif (error_type == self.CONNECTION_INPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Inputs must be on the right" \
                  " hand side of the connection definition")
        elif (error_type == self.OUTPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Outputs must be on the left" \
                  " hand side of the connection definition")
        elif (error_type == self.MONITOR_INPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Monitors can only be outputs.")
        elif (error_type == self.REPEATED_MONITOR_ERROR):
            self.scanner.get_error_line(message)
            print("***NameError: A monitor was repeated. " \
                  "All monitors must be unique.")
        elif (error_type == self.INVALID_DEVICE_OUTPUT_ERROR):
            self.scanner.get_error_line(message)
            print("***TypeError: The device has no such output.")
        elif (error_type == self.UNDEFINED_DEVICE_ERROR):
            self.scanner.get_error_line(message)
            print("***NameError: The device has not been previously" \
                   " defined in DEVICES.")
        elif (error_type == self.UNMATCHED_INPUT_OUTPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: The number of inputs and outputs " \
                  "must match unless you are specifying one output to" \
                  " many inputs or all the inputs of a device at once")
        elif (error_type == self.REPEATED_INPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***ValueError: The input has already been " \
                  "specified previously. Repeated assignment of " \
                  "inputs is not allowed.")
        elif (error_type == self.INVALID_PORT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***ValueError: The port specified does not exist " \
                  "for such device or is out of bounds")
        elif (error_type == self.NOT_GATE_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Only gates can have simultaneous " \
                  "assignment of all of its inputs.")
        elif (error_type == self.OUT_OF_BOUND_INPUTS_ERROR):
            self.scanner.get_error_line(self.symbol)
            #TODO specify if too many or too few just add elif and message for few or too many with > or <
            print("***TypeError: Too many or too few inputs " \
                  "have been assigned simultaneously to the device." \
                  " When using simultaneous defintion the same number" \
                  " of inputs as the device has must be given.")
        elif (error_type == self.MISSING_INPUTS_ERROR):
        #TODO which inputs have not been specified
            print("***ValueError: Inputs have not been specificed" \
                   " for all DEVICES.")

    def skip_to_stopping_symbol(self, stopping_symbol):
        if (stopping_symbol == "KEYWORD or ;"):
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
        if (stopping_symbol == ";"):
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
        elif (stopping_symbol == None):
            pass

    def clear_vars(self):
        #For storing info for parsing
        #used to clear symbols
        self.current_device = Symbol()
        self.current_number = Symbol()
        self.current_name = Symbol()
        self.current_port = Symbol()

    def clear_all(self):
        self.clear_vars()
        self.identifier_list = []
        self.outputs_list = []
        self.inputs_list = []
        self.monitors_list = []

    def identifier(self):
        if (self.symbol.type == self.scanner.NAME and
            self.recovered_from_definition_error):
            self.identifier_list.append(self.symbol)
            self.symbol = self.scanner.get_symbol()
        elif((self.symbol.type == self.scanner.KEYWORD
              or self.symbol.type == self.scanner.DEVICE
              or self.symbol.type == self.scanner.PORT)
            and self.recovered_from_definition_error):
            self.error(self.KEYWORD_ERROR, stopping_symbol = ";")
        else:
            self.error(self.SYNTAX_ERROR, "identifier")

    def device_type(self):
        if (self.symbol.type == self.scanner.DEVICE and
            self.recovered_from_definition_error):
            self.current_device = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "device")

    def number(self):
        if (self.symbol.type == self.scanner.NUMBER and
            self.recovered_from_definition_error):
            self.current_number = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "number")

    def make_devices(self):
        for identifier in self.identifier_list:
            if (self.devices.get_device(identifier.id) is not None):
                self.error(self.REPEATED_IDENTIFIER_ERROR,
                           identifier, None)
            elif (self.current_device.id == self.scanner.DTYPE_ID):
                error = self.devices.make_device(
                identifier.id, self.devices.D_TYPE,
                self.current_number.id)
                #should not raise bad devices as self.devices
                #has been used
                if (error == self.devices.QUALIFIER_PRESENT):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "DTYPE takes no number", None)
                #should not recover to semicolon as already got to ;
                    return
            elif (self.current_device.id == self.scanner.SWITCH_ID):
                if (self.current_number.id == None):
                    #default value to 0
                    self.current_number.id = 0
                error = self.devices.make_device(
                identifier.id, self.devices.SWITCH,
                self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "SWITCH takes only 0 or 1", None)
                #should not recover to semicolon as already got to ;
                    #reset identifier_list to zero so later on dont get extra devices
                    self.identifier_list = []
                    return
            elif (self.current_device.id == self.scanner.CLOCK_ID):
                if (self.current_number.id == None):
                    #default value to 1
                    self.current_number.id = 1
                error = self.devices.make_device(
                identifier.id, self.devices.CLOCK,
                self.current_number.id)
                #this can only hapen if given a zero as - will be invalid
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "CLOCK takes only values greater than 0", None)
                #should not recover to semicolon as already got to ;
                #reset identifier_list to zero so later on dont get extra devices as all of these devices are instantiaing the same
                    return
#TODO tidy up this so is one single elif
            elif (self.current_device.id == self.scanner.NAND_ID):
                if (self.current_number.id == None):
                    #default value to 2
                    self.current_number.id = 2
                error = self.devices.make_device(
                identifier.id, self.devices.NAND,
                self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "NAND gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.AND_ID):
                if (self.current_number.id == None):
                    #default value to 2
                    self.current_number.id = 2
                error = self.devices.make_device(
                identifier.id, self.devices.AND,
                self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "AND gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.NOR_ID):
                if (self.current_number.id == None):
                    #default value to 2
                    self.current_number.id = 2
                error = self.devices.make_device(
                identifier.id, self.devices.NOR,
                self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "NOR gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.OR_ID):
                if (self.current_number.id == None):
                    #devault value to 2
                    self.current_number.id = 2
                error = self.devices.make_device(
                identifier.id, self.devices.OR,
                self.current_number.id)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "OR gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.XOR_ID):
                if (self.current_number.id == 2):
                    #devices module need Xor to have none in device_property so if number that is not 2 assigne will rasie problem
                    self.current_number.id = None
                error = self.devices.make_device(
                identifier.id, self.devices.XOR,
                self.current_number.id)
                if (error == self.devices.QUALIFIER_PRESENT):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "XOR gates can only have 2 inputs", None)
                    return

    def device_definition(self):
        self.identifier()
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
            elif (self.symbol.type == self.scanner.NUMBER and
                    self.recovered_from_definition_error):
                self.error(self.SYNTAX_ERROR, "(")
            else:
                self.current_number = Symbol()
            if (self.symbol.type == self.scanner.SEMICOLON and
                self.recovered_from_definition_error):
                self.make_devices()
                self.symbol = self.scanner.get_symbol()
            else:
                self.error(self.SYNTAX_ERROR, ";")
#name followed by name possibly mising comma 
        elif (self.symbol.type == self.scanner.NAME):
            self.error(self.SYNTAX_ERROR, ",")
        else:
            self.error(self.SYNTAX_ERROR, ":=")

    def device_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and
            self.symbol.id == self.scanner.DEVICES_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.clear_all()
                self.device_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                #Beginning erase all variables
                    self.recovered_from_definition_error = True
                    self.clear_all()
                    self.device_definition()
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and
                    self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error(self.SYNTAX_ERROR, ";",
                                   stopping_symbol = "KEYWORD")
                else:
                    self.error(self.SYNTAX_ERROR, "END",
                               stopping_symbol = "KEYWORD")
            else:
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol = "END")
        else:
            self.error(self.SYNTAX_ERROR, "DEVICES",
                       stopping_symbol = "END")

    def port(self, I_O):
        if (self.symbol.type == self.scanner.PORT and
            (I_O == "O" or I_O == "M") and
            (self.symbol.id == self.scanner.I_ID or
            self.symbol.id == self.scanner.DATA_ID or
            self.symbol.id == self.scanner.CLK_ID or
            self.symbol.id == self.scanner.SET_ID or
            self.symbol.id == self.scanner.CLEAR_ID)):
            if (I_O == "O"):
                self.error(self.CONNECTION_INPUT_ERROR)
            elif (I_O == "M"):
                self.error(self.MONITOR_INPUT_ERROR)
        elif (self.symbol.type == self.scanner.PORT and
            I_O == "I" and (self.symbol.id == self.scanner.Q_ID
            or self.symbol.id == self.scanner.QBAR_ID)):
            self.error(self.OUTPUT_ERROR)
        elif (self.symbol.id == self.scanner.I_ID and
            self.symbol.type == self.scanner.PORT and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.number()
            self.current_port = self.current_number
        elif (self.symbol.type == self.scanner.PORT and
              self.recovered_from_definition_error):
            self.current_port = self.symbol
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "port")

    def signal(self, I_O):
        if (self.symbol.type == self.scanner.NAME and
            self.recovered_from_definition_error):
            self.current_name = self.symbol
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.DOT):
                self.symbol = self.scanner.get_symbol()
                self.port(I_O)
            return (self.current_name, self.current_port)
        else:
            self.error(self.SYNTAX_ERROR, "signal")

    def get_in(selfi, output):
        #input ports can only be None, Q or QBAR
        #input port are already specifiec as 
        name, port = output
        return name.id, port.id

    def get_out(self, device_ip):
        name, port = device_ip
        if (port.type == self.scanner.NUMBER):
            input_name = "".join(["I", str(port.id)])
            [port.id] = self.names.lookup([input_name])
        return name.id, port.id

    def check_connection_error(self, error_type):
        if (error_type == self.network.NO_ERROR):
            return True
        elif (error_type == self.network.DEVICE_ABSENT):
            #TODO print the actual problem place
            self.error(self.UNDEFINED_DEVICE_ERROR, self.symbol,
                       stopping_symbol = None)
        elif (error_type == self.network.INPUT_CONNECTED):
            #TODO print actual place
            self.error(self.REPEATED_INPUT_ERROR,
                       stopping_symbol = None)
        elif (error_type == self.network.PORT_ABSENT):
            #TODO specific check for I out of bounds compared to invalid port used like .Q by non DTYPE, also show appropriate symbol
            self.error(self.INVALID_PORT_ERROR,
                       stopping_symbol = None)

    def make_connection(self):
        #one to one or many to many
        if (len(self.outputs_list) == len(self.inputs_list)):
            for output, device_ip in zip(self.outputs_list,
                                         self.inputs_list):
                [in_device_id, in_port_id] = self.get_in(output)
                [out_device_id, out_port_id] = self.get_out(device_ip)
                error_type = self.network.make_connection(
                             in_device_id, in_port_id, out_device_id,
                             out_port_id)
                self.check_connection_error(error_type)
        #many to one
        elif (len(self.inputs_list) == 1):
            [device_input] = self.inputs_list
            [out_device_id, out_port] = self.get_out(device_input)
            device = self.devices.get_device(out_device_id)
            if (device.device_kind not in self.devices.gate_types):
                self.error(self.NOT_GATE_ERROR, stopping_symbol = None)
            else:
                if (len(device.inputs) == len(self.outputs_list)):
                    device_inputs = list(device.inputs.keys())
                    for output, out_port_id in zip(self.outputs_list,
                                                  device_inputs):
                        [in_device_id, in_port_id] = self.get_in(output)
                        error_type = self.network.make_connection(
                                     in_device_id, in_port_id,
                                     out_device_id, out_port_id)
                        self.check_connection_error(error_type)
                else:
                    self.error(self.OUT_OF_BOUND_INPUTS_ERROR,
                               stopping_symbol = None)
        #one to many
        elif (len(self.outputs_list) == 1):
            [output] = self.outputs_list
            [in_device_id, in_port_id] = self.get_in(output)
            for device_ip in self.inputs_list:
                [out_device_id, out_port_id] = self.get_out(device_ip)
                error_type = self.network.make_connection(
                             in_device_id, in_port_id, out_device_id,
                             out_port_id)
                self.check_connection_error(error_type)
        else:
            self.error(self.UNMATCHED_INPUT_OUTPUT_ERROR,
                       stopping_symbol = None)

    def connection_definition(self):
        #beginning erase all variables
        self.clear_vars()
        self.outputs_list.append(self.signal("O"))
        while (self.symbol.type == self.scanner.COMMA and
               self.recovered_from_definition_error):
            #beginning erase all variables
            self.clear_vars()
            self.symbol = self.scanner.get_symbol()
            self.outputs_list.append(self.signal("O"))
        if (self.symbol.type == self.scanner.CONNECTION_DEF and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            #beginning erase all variables
            self.clear_vars()
            self.inputs_list.append(self.signal("I"))
            while (self.symbol.type == self.scanner.COMMA and
                   self.recovered_from_definition_error):
                #beginning erase all variables
                self.clear_vars()
                self.symbol = self.scanner.get_symbol()
                self.inputs_list.append(self.signal("I"))
            if (self.symbol.type == self.scanner.SEMICOLON and
                self.recovered_from_definition_error):
                if (self.error_count == 0):
                    self.make_connection()
                self.symbol = self.scanner.get_symbol()
            elif (self.symbol.type == self.scanner.NAME):
                self.error(self.SYNTAX_ERROR, ",")
            else:
                self.error(self.SYNTAX_ERROR, ";")
        elif (self.symbol.type == self.scanner.NAME):
            self.error(self.SYNTAX_ERROR, ",")
        else:
            self.error(self.SYNTAX_ERROR, "=>")

    def connection_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and
            self.symbol.id == self.scanner.CONNECTIONS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.clear_all()
                self.connection_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    self.clear_all()
                    self.recovered_from_definition_error = True
                    self.connection_definition()
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and
                    self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        if ((not self.network.check_network()) and
                             self.error_count == 0):
                            self.error(self.MISSING_INPUTS_ERROR,
                                       stopping_symbol = None)
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error(self.SYNTAX_ERROR, ";",
                                   stopping_symbol = "KEYWORD")
                else:
                    self.error(self.SYNTAX_ERROR, "END",
                               stopping_symbol = "KEYWORD")
            else:
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol = "END")
        else:
            self.error(self.SYNTAX_ERROR, "CONNECITIONS",
                       stopping_symbol = "END")

    def make_monitors(self):
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

    def monitor_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and
            self.symbol.id == self.scanner.MONITORS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.clear_all()
                self.monitors_list.append(self.signal("M"))
                while (self.symbol.type == self.scanner.COMMA and
                       self.recovered_from_definition_error):
                    self.clear_vars()
                    self.symbol = self.scanner.get_symbol()
                    self.monitors_list.append(self.signal("M"))
                if (self.symbol.type == self.scanner.SEMICOLON):
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
                                           skipt_to_symbol = "EOF")
                        else:
                            self.error(self.SYNTAX_ERROR, ";",
                                       stopping_symbol = "EOF")
                    else:
                        self.error(self.SYNTAX_ERROR, "END",
                                   stopping_symbol = "EOF")
                elif(not self.recovered_from_definition_error):
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
                                           skipt_to_symbol = "EOF")
                        else:
                            self.error(self.SYNTAX_ERROR, ";",
                                       stopping_symbol = "EOF")
                    else:
                        self.error(self.SYNTAX_ERROR, "END",
                                   stopping_symbol = "EOF")
                else:
                    self.error(self.SYNTAX_ERROR, ";",
                               stopping_symbol = "END")
            else:
                self.error(self.SYNTAX_ERROR, ":",
                           stopping_symbol = "END")
        elif(self.symbol.type == self.scanner.EOF):
            pass
        else:
            self.error(self.SYNTAX_ERROR, "MONITORS OR EOF",
                       stopping_symbol = "EOF")

    def parse_network(self):
        """Parse the circuit definition file."""
        self.symbol = self.scanner.get_symbol()
        self.device_list()
        self.connection_list()
        self.monitor_list()
        if (self.error_count == 0):
            return True
        else:
        #Error message
            print("Number of errors encountered:", self.error_count)
            return False

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

if __name__ == "__main__":
    name = Names()
    path = "testfiles/parser/temporary_test.txt"
    scanner = Scanner(path, name)
    devices = Devices(name)
    network = Network(name, devices)
    monitors = Monitors(name, devices, network)
    parser = Parser(name, devices, network, monitors, scanner)
    parser.parse_network()
