"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""


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
        self.fileIn = open_file(path)

        # initialize symbol types
        self.names = names
        self.symbol_type_list = [self.KEYWORD, self.DEVICE, self.PORT, self.NAME, self.NUMBER, self.COLON, self.SEMICOLON, self.COMMA, self.DEVICE_DEF, self.BRACKET_LEFT, self.BRACKET_RIGHT, self.CONNECTION_DEF, self.DOT, self.UNDERSCORE, self.EOF, self.INVALID_SYMBOL] = range(16)
        # (DEVICE_DEF: ":="), (CONNECTION_DEF: "=>"), (INVALID_SYMBOL: anything not in the symbol_type_list)

        self.keywords_list = ["DEVICES", "CONNECTIONS", "MONITORS", "END", "NAND", "AND", "NOR", "OR", "XOR", "DTYPE", "CLOCK", "SWITCH", "Q", "QBAR", "DATA", "CLK", "SET", "CLEAR", "I"]
        [self.DEVICES_ID, self.CONNECTIONS_ID, self.MONITORS_ID, self.END_ID, self.NAND_ID, self.AND_ID, self.NOR_ID, self.OR_ID, self.XOR_ID, self.DTYPE_ID, self.CLOCK_ID, self.SWITCH_ID, self.Q_ID, self.QBAR_ID, self.DATA_ID, self.CLK_ID, self.SET_ID, self.CLEAR_ID, self.I_ID] = self.names.lookup(self.keywords_list)
        self.current_character = ""


    def open_file(path):
        """Open and return the file specified by path."""
        try:
            file = open(path)
        except IOError as err:
            print("\nError occured when opening file for reading\n", err)
            sys.exit()

        return file

    def advance():
        """Update current_character with next character in self.fileIn."""
        self.current_character = self.fileIn.read(1)

    def skip_spaces():
        """Advances in self.fileIn until it finds the first non whitespace character"""
        advance()
        while self.current_character != '' and self.current_character.isspace():
            advance()

    def get_name():
        """Return the name string that starts at the current_character in self.fileIn, and advance to the next character after the name string.

        This method assumes that the current_character is already a letter.
        """
        name = self.current_character
        advance()
        while self.current_character != '' and (self.current_character.isalnum() or self.current_character == "_"):
            name += self.current_character
            advance()

        return name

    def get_number():
        """Return the number that starts at the current_character in self.fileIn, and advance to the next character after the number.

        This method assumes that the current_character is already a digit.
        """
        numList = self.current_character
        advance()
        while self.current_character != '' and self.current_character.isdigit():
            name += self.current_character
            advance()

        return int(numList)
