"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
from names import Names

class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self):
        """Initialise symbol properties."""
        self.type = None
        self.id = None
        self.line = None
        self.column = None # position on line

    def __repr__(self):
        return "type: {}, id: {}, line: {}, column: {}".format(self.type, self.id, self.line, self.column)


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        # open file
        self.fileIn = self.open_file(path)

        # initialize symbol types
        self.names = names
        self.symbol_type_list = [self.KEYWORD, self.DEVICE, self.PORT, self.NAME, self.NUMBER, self.COLON, self.SEMICOLON, self.COMMA, self.DEVICE_DEF, self.BRACKET_LEFT, self.BRACKET_RIGHT, self.CONNECTION_DEF, self.DOT, self.INVALID_SYMBOL, self.EOF] = range(15)
        # (DEVICE_DEF: ":="), (CONNECTION_DEF: "=>"), (INVALID_SYMBOL: anything not in the symbol_type_list)

        # split syntax reserved words into keywords, devices and ports
        self.keywords_list = ["DEVICES", "CONNECTIONS", "MONITORS", "END"]
        self.devices_list = ["NAND", "AND", "NOR", "OR", "XOR", "DTYPE", "CLOCK", "SWITCH"]
        self.ports_list = ["Q", "QBAR", "DATA", "CLK", "SET", "CLEAR", "I"]
        [self.DEVICES_ID, self.CONNECTIONS_ID, self.MONITORS_ID, self.END_ID] = self.names.lookup(self.keywords_list)
        [self.NAND_ID, self.AND_ID, self.NOR_ID, self.OR_ID, self.XOR_ID, self.DTYPE_ID, self.CLOCK_ID, self.SWITCH_ID] = self.names.lookup(self.devices_list)
        [self.Q_ID, self.QBAR_ID, self.DATA_ID, self.CLK_ID, self.SET_ID, self.CLEAR_ID, self.I_ID] = self.names.lookup(self.ports_list)
        # keep track of the beginning of the current line in self.fileIn
        self.current_line_pos = 1
        self.current_line = 1
        self.current_character = None
        self.advance() # place first character in current_character


    def open_file(self, path):
        """Open and return the file specified by path."""
        try:
            file = open(path)
        except IOError as err:
            print("\nError occured when opening file for reading\n", err)
            sys.exit()
        return file

    def advance(self):
        """Update current_character with next character in self.fileIn, and also check for new line."""
        # print("current_line_pos: {}".format(self.current_line_pos)) # TODO remove
        if self.current_character == "\n":
            self.current_character = self.fileIn.read(1)
            self.current_line += 1
            self.current_line_pos = self.fileIn.tell()
        else:
            self.current_character = self.fileIn.read(1)

    def look_ahead(self):
        """Return the next character in the definition file, without updating current_character and without incrementing the current position within the file"""
        ch = self.fileIn.read(1)
        self.fileIn.seek(self.fileIn.tell()-1, 0)
        return ch

    def skip_spaces(self):
        """advances in self.fileIn until it finds the first non whitespace character"""
        while self.current_character != '' and self.current_character.isspace():
            self.advance()

    def skip_line(self):
        """"Skips the rest of the current line but not the new line character in self.fileIn"""
        self.advance()
        while self.current_character != '' and self.current_character != "\n":
            self.advance()

    def get_name(self):
        """Return the name string that starts at the current_character in self.fileIn, and advance to the next character after the name string.

        This method assumes that the current_character is already a letter.
        """
        name = self.current_character
        self.advance()
        while self.current_character != '' and (self.current_character.isalnum() or self.current_character == "_"):
            name += self.current_character
            self.advance()
        return name

    def get_number(self):
        """Return the number that starts at the current_character in self.fileIn, and advance to the next character after the number.

        This method assumes that the current_character is already a digit.
        """
        numList = self.current_character
        self.advance()
        while self.current_character != '' and self.current_character.isdigit():
            numList += self.current_character
            self.advance()

        return int(numList)

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        symbol = Symbol()
        self.skip_spaces() # current character now not whitespace

        symbol.line = self.current_line
        symbol.column = self.fileIn.tell() - self.current_line_pos + 1

        # handle names, keywords, devices, ports
        if self.current_character.isalpha():
            name_string = self.get_name()
            if name_string in self.keywords_list:
                symbol.type = self.KEYWORD
            elif name_string in self.devices_list:
                symbol.type = self.DEVICE
            elif name_string in self.ports_list:
                symbol.type = self.PORT
            else:
                symbol.type = self.NAME
            [symbol.id] = self.names.lookup([name_string])
        # handle numbers
        elif self.current_character.isdigit():
            # NOTE that here the symbol.id is the number itself
            symbol.id = self.get_number()
            symbol.type = self.NUMBER
        # handle punctuation
        elif self.current_character == ":": # handle ":", ":="
            if (self.look_ahead() == "="):
                symbol.type = self.DEVICE_DEF
                self.advance()
            else:
                symbol.type = self.COLON
            self.advance()
        elif self.current_character == ";":
            symbol.type = self.SEMICOLON
            self.advance()
        elif self.current_character == ",":
            symbol.type = self.COMMA
            self.advance()
        elif self.current_character == "(":
            symbol.type = self.BRACKET_LEFT
            self.advance()
        elif self.current_character == ")":
            symbol.type = self.BRACKET_RIGHT
            self.advance()
        elif self.current_character == "=": # handle special case "=>"
            if (self.look_ahead() == ">"):
                symbol.type = self.CONNECTION_DEF
                self.advance()
            else:
                symbol.type = self.INVALID_SYMBOL
            self.advance()
        elif self.current_character == ".":
            symbol.type = self.DOT
            self.advance()
        elif self.current_character == "/": # handle comments
            if (self.look_ahead() == "/"):
                self.advance()
                self.skip_line()
                # return next symbol right after the comment or any immediately following comments
                symbol = self.get_symbol()
            else:
                symbol.type = self.INVALID_SYMBOL
                self.skip_line()
        elif self.current_character == "": # end of file
            symbol.type = self.EOF
        else: # not a valid character
            symbol.type = self.INVALID_SYMBOL
            self.advance()

        return symbol

if __name__ == "__main__":
    names = Names()
    path = 'testfiles/tmp_scanner/specfile1.txt'
    scanner = Scanner(path, names)
    while (scanner.current_character != ''):
        print(scanner.get_symbol())
