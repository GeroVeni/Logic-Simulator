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

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.symbol = None
        self.scanner = scanner
        self.names = names
        self.error_count = 0
        #List of error codes used in get_error_codes
        self.error_codes = []

    def error(self, number):
        self.error_count += 1
        print("ERROR", number,  self.symbol)
        while self.symbol.type != self.scanner.SEMICOLON:
            self.symbol = self.scanner.get_symbol()
        self.symbol = self.scanner.get_symbol()

    def identifier(self):
        if (self.symbol.type == self.scanner.NAME):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(1)

    def device_type(self):
        if (self.symbol.type == self.scanner.DEVICE):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(2)

    def number(self):
        if (self.symbol.type == self.scanner.NUMBER):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error(3)

    def device_definition(self):
        self.identifier()
        while self.symbol.type == self.scanner.COMMA:
            self.symbol = self.scanner.get_symbol()
            self.identifier()
        if (self.symbol.type == self.scanner.DEVICE_DEF):
            self.symbol = self.scanner.get_symbol()
            self.device_type()
            if (self.symbol.type == self.scanner.BRACKET_LEFT):
                self.symbol = self.scanner.get_symbol()
                self.number()
                if(self.symbol.type == self.scanner.BRACKET_RIGHT):
                    self.symbol = self.scanner.get_symbol()
                else:
                    self.error(5)
#TODO recovering from an error imagine it breaks in device_type has to recover back to calling device definition add argument of whether it has to do the search for ; or has just done it then reset flag

#TODO how to identify when they wanted left bracket but wasnt there imagine there is number
            elif (self.symbol.type == self.scanner.NUMBER):
                self.error(6)
            if (self.symbol.type == self.scanner.SEMICOLON):
                self.symbol = self.scanner.get_symbol()
            else:
                self.error(7)


    def device_list(self):
        if (self.symbol.type == self.scanner.KEYWORD and \
            self.symbol.id == self.scanner.DEVICES_ID):
            self.symbol = self.scanner.get_symbol()
            if(self.symbol.type == self.scanner.COLON):
                self.symbol = self.scanner.get_symbol()
                self.device_definition()
                while self.symbol.type != self.scanner.KEYWORD:
                    self.device_definition()
                if (self.symbol.id == self.scanner.END_ID):
                    self.symbol = self.scanner.get_symbol()
                    if (self.symbol.type == self.scanner.SEMICOLON):
                        self.symbol = self.scanner.get_symbol()
                    else:
                        self.error(8)
                else:
                    self.error(9)
            else:
                self.error(10)
        else:
            self.error(11)

    def connection_list(self):
        pass

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        #what about empty file how to raise errors for no connections, definitons, expected blabalbal
        self.symbol = self.scanner.get_symbol()
        self.device_list()
        self.connection_list()
        if (self.symbol.type == self.scanner.KEYWORD and \
            self.symbol.id == self.scanner.MONITORS_ID):
            self.monitor_list()
        elif(self.symbol.type == self.scanner.EOF and self.error_count == 0):
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
