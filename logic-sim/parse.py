"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
from names import Names
from scanner import Scanner
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
    KEYWORD_ERROR, REPEATED_IDENTIFIER_ERROR, INPUT_ERROR,
    OUTPUT_ERROR] = range(7)

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.symbol = None
        self.scanner = scanner
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.identifier_list = []
        self.error_count = 0
        self.current_number = None
        #List of error codes used in get_error_codes
        self.error_codes = []
        self.recovered_from_definition_error = True

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
        elif (error_type == self.INPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Inputs must be on the right" \
                  " hand side of the connection definition")
        elif (error_type == self.OUTPUT_ERROR):
            self.scanner.get_error_line(self.symbol)
            print("***TypeError: Outputs must be on the left" \
                  " hand side of the connection definition")

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
            self.current_number = self.symbol.id
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
                self.current_number)
                #should not raise bad devices as self.devices
                #has been used
                if (error == self.devices.QUALIFIER_PRESENT):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "DTYPE takes no number", None)
                #should not recover to semicolon as already got to ;
                    return
            elif (self.current_device.id == self.scanner.SWITCH_ID):
                if (self.current_number == None):
                    #default value to 0
                    self.current_number = 0
                error = self.devices.make_device(
                identifier.id, self.devices.SWITCH,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "SWITCH takes only 0 or 1", None)
                #should not recover to semicolon as already got to ;
                    #reset identifier_list to zero so later on dont get extra devices
                    self.identifier_list = []
                    return
            elif (self.current_device.id == self.scanner.CLOCK_ID):
                if (self.current_number == None):
                    #default value to 1
                    self.current_number = 1
                error = self.devices.make_device(
                identifier.id, self.devices.CLOCK,
                self.current_number)
                #this can only hapen if given a zero as - will be invalid
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "CLOCK takes only values greater than 0", None)
                #should not recover to semicolon as already got to ;
                #reset identifier_list to zero so later on dont get extra devices as all of these devices are instantiaing the same
                    return
#TODO tidy up this so is one single elif
            elif (self.current_device.id == self.scanner.NAND_ID):
                if (self.current_number == None):
                    #default value to 2
                    self.current_number = 2
                error = self.devices.make_device(
                identifier.id, self.devices.NAND,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "NAND gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.AND_ID):
                if (self.current_number == None):
                    #default value to 2
                    self.current_number = 2
                error = self.devices.make_device(
                identifier.id, self.devices.AND,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "AND gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.NOR_ID):
                if (self.current_number == None):
                    #default value to 2
                    self.current_number = 2
                error = self.devices.make_device(
                identifier.id, self.devices.NOR,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "NOR gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.OR_ID):
                if (self.current_number == None):
                    #devault value to 2
                    self.current_number = 2
                error = self.devices.make_device(
                identifier.id, self.devices.OR,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "OR gates can only have 1 to 16 inputs", None)
                    return
            elif (self.current_device.id == self.scanner.XOR_ID):
                if (self.current_number == 2):
                    #devices module need Xor to have none in device_property so if number that is not 2 assigne will rasie problem
                    self.current_number = None
                error = self.devices.make_device(
                identifier.id, self.devices.XOR,
                self.current_number)
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
                self.current_number = None
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
                self.device_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                #Beginning erase all variables
                    self.recovered_from_definition_error = True
                    self.identifier_list = []
                    self.current_device = None
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
            I_O == "O" and (self.symbol.id == self.scanner.I_ID
            or self.symbol.id == self.scanner.DATA_ID or
            self.symbol.id == self.scanner.CLK_ID or
            self.symbol.id == self.scanner.SET_ID or
            self.symbol.id == self.scanner.CLEAR_ID)):
            self.error(self.INPUT_ERROR)
        if (self.symbol.type == self.scanner.PORT and
            I_O == "I" and (self.symbol.id == self.scanner.Q_ID
            or self.symbol.id == self.scanner.QBAR_ID)):
            self.error(self.OUTPUT_ERROR)
        elif (self.symbol.id == self.scanner.I_ID and
            self.symbol.type == self.scanner.PORT and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.number()
        elif (self.symbol.type == self.scanner.PORT and
              self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "port")

    def signal(self, I_O):
        if (self.symbol.type == self.scanner.NAME and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.DOT):
                self.symbol = self.scanner.get_symbol()
                self.port(I_O)
        else:
            self.error(self.SYNTAX_ERROR, "signal")

    def get_input(self):
        return [None, None]

    def get_device(self):
        return [None, None]

    def make_connection(self):
        [in_device_id, in_port_id] = self.get_input()
        [out_device_id, out_port_id] = self.get_device()
        if (self.error_count == 0):
            error_type = self.network.make_connection(
                in_device_id, in_port_id, out_device_id,
                out_port_id)
            if (error_type != self.network.NO_ERROR):
                print("UPS error occurred in making connection")

    def connection_definition(self):
        self.signal("O")
        while (self.symbol.type == self.scanner.COMMA and
               self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal("O")
        if (self.symbol.type == self.scanner.CONNECTION_DEF and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal("I")
            while (self.symbol.type == self.scanner.COMMA and
                   self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
                self.signal("I")
            if (self.symbol.type == self.scanner.SEMICOLON and
                self.recovered_from_definition_error):
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
                self.connection_definition()
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    self.recovered_from_definition_error = True
                    self.connection_definition()
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
            self.error(self.SYNTAX_ERROR, "CONNECITIONS",
                       stopping_symbol = "END")

    def monitor_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and
            self.symbol.id == self.scanner.MONITORS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.signal("O")
                while (self.symbol.type == self.scanner.COMMA and
                       self.recovered_from_definition_error):
                    self.symbol = self.scanner.get_symbol()
                    self.signal("O")
                if (self.symbol.type == self.scanner.SEMICOLON):
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
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        #what about empty file how to raise errors for no connections, definitons, expected blabalbal
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
