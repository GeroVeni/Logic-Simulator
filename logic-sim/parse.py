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
    KEYWORD_ERROR, REPEATED_IDENTIFIER_ERROR] = range(5)

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.symbol = None
        self.scanner = scanner
        self.names = names
        self.devices = devices
        self.identifier_list = []
        self.error_count = 0
        self.current_number = None
        self.current_identifier = None
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
            print("***NameError: Keywords are reserved and" \
                  "cannot be used as identifiers.")
        elif (error_type == self.REPEATED_IDENTIFIER_ERROR):
            self.scanner.get_error_line(self.current_identifier)
#TODO also add get_error_line by comparing identifier ids lookup names
            print("***NameError: An identifier was repeated." \
                  "All identifiers must have unique names.")

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

    def identifier(self):
        if (self.symbol.type == self.scanner.NAME and
            self.recovered_from_definition_error):
            self.identifier_list.append(self.symbol)
            self.symbol = self.scanner.get_symbol()
        elif(self.symbol.type == self.scanner.KEYWORD and
             self.recovered_from_definition_error):
            self.error(self.KEYWORD_ERROR)
#TODO skip to ; remove keyword problems with this think about it change s to END in temp_file
        else:
            self.error(self.SYNTAX_ERROR, "name")

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
        while len(self.identifier_list) != 0:
            self.current_identifier = self.identifier_list.pop()
            if (self.devices.get_device(self.current_identifier.id)
                is not None):
                #TODO fix issue with END not working jumping wrong
                self.error(self.REPEATED_IDENTIFIER_ERROR, None)
            if (self.current_device.id == self.scanner.DTYPE_ID):
                error = self.devices.make_device(
                self.current_identifier.id, self.devices.D_TYPE,
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
                self.current_identifier.id, self.devices.SWITCH,
                self.current_number)
                if (error == self.devices.INVALID_QUALIFIER):
                    self.error(self.DEVICE_VALUE_ERROR,
                    "SWITCH takes only 0 or 1", None)
                #should not recover to semicolon as already got to ;
                    #reset identifier_list to zero so later on dont get extra devices
                    self.identifier_list = []
                    return
#TODO add clock and gates think of elegant way to do
            else:
                print("SHOULDNT HAPPEN")
                print(self.symbol)
                self.identifier_list.pop()

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
                    self.recovered_from_definition_error = True
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

    def port(self):
        if (self.symbol.id == self.scanner.I_ID and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.number()
        elif (self.symbol.type == self.scanner.PORT and
              self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(self.SYNTAX_ERROR, "port")

    def signal(self):
        if (self.symbol.type == self.scanner.NAME and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.DOT):
                self.symbol = self.scanner.get_symbol()
                self.port()
        else:
            self.error(self.SYNTAX_ERROR, "name")

    def connection_definition(self):
        self.signal()
        while (self.symbol.type == self.scanner.COMMA and
               self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal()
        if (self.symbol.type == self.scanner.CONNECTION_DEF and
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal()
            while (self.symbol.type == self.scanner.COMMA and
                   self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
                self.signal()
            if (self.symbol.type == self.scanner.SEMICOLON and
                self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
            else:
                self.error(self.SYNTAX_ERROR, ";")
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
                self.signal()
                while (self.symbol.type == self.scanner.COMMA and
                       self.recovered_from_definition_error):
                    self.symbol = self.scanner.get_symbol()
                    self.signal()
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
