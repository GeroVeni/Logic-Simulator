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

    [SYNTAX_ERROR, UNDEFINED_DEVICE_ERROR, VALUE_ERROR] = range(6)

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.symbol = None
        self.scanner = scanner
        self.names = names
        self.error_count = 0
        #List of error codes used in get_error_codes
        self.error_codes = []
        self.recovered_from_definition_error = True

    def error(self, message, skip_to_symbol="KEYWORD or ;" ):
        if (self.recovered_from_definition_error):
            self.error_count +=1
            print("ERROR", message,  self.symbol)
            if (skip_to_symbol == "KEYWORD or ;"):
                self.recovered_from_definition_error = False
                while (self.symbol.type != self.scanner.SEMICOLON and
                       self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    self.symbol = self.scanner.get_symbol()
                if self.symbol.type == self.scanner.SEMICOLON:
                    self.symbol = self.scanner.get_symbol()
            elif (skip_to_symbol == "KEYWORD"):
                while (self.symbol.type != self.scanner.KEYWORD and
                       self.symbol.type != self.scanner.EOF):
                    self.symbol = self.scanner.get_symbol()
            elif (skip_to_symbol == "END"):
                while ((self.symbol.type != self.scanner.KEYWORD or
                       self.symbol.id != self.scanner.END_ID) and
                       self.symbol.type != self.scanner.EOF):
                    self.symbol = self.scanner.get_symbol()
                if (self.symbol.type == self.scanner.EOF):
                    self.error("EXPECTED END")
                else:
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error("EXPECTED SEMICOLON")
            elif (skip_to_symbol == "EOF"):
                while (self.symbol.type != self.scanner.EOF):
                    self.symbol = self.scanner.get_symbol()

    def identifier(self):
        if (self.symbol.type == self.scanner.NAME and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error("EXPECTED NAME (IDENTIFIER)")

    def device_type(self):
        if (self.symbol.type == self.scanner.DEVICE and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error("EXPECTED DEVICE")

    def number(self):
        if (self.symbol.type == self.scanner.NUMBER and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error("EXPECTED NUMBER")

    def device_definition(self):
        self.identifier()
        while (self.symbol.type == self.scanner.COMMA and \
               self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.identifier()
        if (self.symbol.type == self.scanner.DEVICE_DEF and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.device_type()
            if (self.symbol.type == self.scanner.BRACKET_LEFT and \
                self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
                self.number()
                if(self.symbol.type == self.scanner.BRACKET_RIGHT and \
                    self.recovered_from_definition_error):
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.error("EXPECTED RIGHT BRACKET")
            elif (self.symbol.type == self.scanner.NUMBER and \
                    self.recovered_from_definition_error):
                self.error("EXPECTED LEFT BRACKET")
            if (self.symbol.type == self.scanner.SEMICOLON and \
                    self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
            else:
                self.error("EXPECTED SEMICOLON")
        else:
            self.error("EXPECTED DEVICE DEFINITION")

    def device_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and \
            self.symbol.id == self.scanner.DEVICES_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.device_definition()
                while (self.symbol.type != self.scanner.KEYWORD and \
                       self.symbol.type != self.scanner.EOF):
                    self.recovered_from_definition_error = True
                    self.device_definition()
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and \
                    self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error("EXPECTED SEMICOLON",
                                   skip_to_symbol = "KEYWORD")
                else:
                    self.error("EXPECTED END (DEVICES)",
                               skip_to_symbol = "KEYWORD")
            else:
                self.error("EXPECTED COLON (DEVICES)",
                           skip_to_symbol = "END")
        else:
            self.error("EXPECTED DEVICES", skip_to_symbol = "END")

    def port(self):
        if (self.symbol.id == self.scanner.I_ID and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.number()
        elif (self.symbol.type == self.scanner.PORT and \
              self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error("EXPECTED PORT")

    def signal(self):
        if (self.symbol.type == self.scanner.NAME and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.DOT):
                self.symbol = self.scanner.get_symbol()
                self.port()
        else:
            self.error("EXPECTED NAME (SIGNAL)")

    def connection_definition(self):
        self.signal()
        while (self.symbol.type == self.scanner.COMMA and \
               self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal()
        if (self.symbol.type == self.scanner.CONNECTION_DEF and \
            self.recovered_from_definition_error):
            self.symbol = self.scanner.get_symbol()
            self.signal()
            while (self.symbol.type == self.scanner.COMMA and\
                   self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
                self.signal()
            if (self.symbol.type == self.scanner.SEMICOLON and\
                self.recovered_from_definition_error):
                self.symbol = self.scanner.get_symbol()
            else:
                self.error("EXPECTED SEMICOLON")
        else:
            self.error("EXPECTED CONNECTION DEFINTION")

    def connection_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and \
            self.symbol.id == self.scanner.CONNECTIONS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.connection_definition()
                while (self.symbol.type != self.scanner.KEYWORD and \
                       self.symbol.type != self.scanner.EOF):
                    self.recovered_from_definition_error = True
                    self.connection_definition()
                self.recovered_from_definition_error = True
                if (self.symbol.id == self.scanner.END_ID and \
                    self.symbol.type == self.scanner.KEYWORD):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error("EXPECTED SEMICOLON",
                                   skip_to_symbol = "KEYWORD")
                else:
                    self.error("EXPECTED END (CONNECTIONS)",
                               skip_to_symbol = "KEYWORD")
            else:
                self.error("EXPECTED COLON (CONNECTIONS)",
                           skip_to_symbol = "END")
        else:
            self.error("EXPECTED DEVICES", skip_to_symbol = "END")

    def monitor_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and \
            self.symbol.id == self.scanner.MONITORS_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.signal()
                while (self.symbol.type == self.scanner.COMMA and\
                       self.recovered_from_definition_error):
                    self.symbol = self.scanner.get_symbol()
                    self.signal()
                if (self.symbol.type == self.scanner.SEMICOLON):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.id == self.scanner.END_ID and \
                        self.symbol.type == self.scanner.KEYWORD):
                        self.symbol = self.scanner.get_symbol()
                        if (self.symbol.type == self.scanner.SEMICOLON):
                            self.symbol = self.scanner.get_symbol()
                            if(self.symbol.type == self.scanner.EOF):
                                pass
                            else:
                                self.error("EXPECTED EOF",
                                           skipt_to_symbol = "EOF")
                        else:
                            self.error("EXPECTED SEMICOLON",
                                       skip_to_symbol = "EOF")
                    else:
                        self.error("EXPECTED END (MONITORS)",
                                   skip_to_symbol = "EOF")
                elif(not self.recovered_from_definition_error):
                    self.recovered_from_definition_error = True
                    if (self.symbol.id == self.scanner.END_ID and \
                        self.symbol.type == self.scanner.KEYWORD):
                        self.symbol = self.scanner.get_symbol()
                        if (self.symbol.type == self.scanner.SEMICOLON):
                            self.symbol = self.scanner.get_symbol()
                            if(self.symbol.type == self.scanner.EOF):
                                pass
                            else:
                                self.error("EXPECTED EOF",
                                           skipt_to_symbol = "EOF")
                        else:
                            self.error("EXPECTED SEMICOLON",
                                       skip_to_symbol = "EOF")
                    else:
                        self.error("EXPECTED END (MONITORS)",
                                   skip_to_symbol = "EOF")
#TODO make sure it still checks for END
                else:
                    self.error("EXPECTED SEMICOLON",
                               skip_to_symbol = "END")
            else:
                self.error("EXPECTED COLON (MONITORS)",
                           skip_to_symbol = "END")
        elif(self.symbol.type == self.scanner.EOF):
            pass
        else:
            self.error("EXPECTED MONITORS OR END OF FILE",
                       skip_to_symbol = "EOF")

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
            print(self.error_count)
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
    print(parser.parse_network())
