"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
import sys

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
        self.column = None  # position on line

    def __repr__(self):
        """Prints the attributes of the symbol instance to the terminal"""
        return "type: {}, id: {}, line: {}, column: {}"\
            .format(self.type, self.id, self.line, self.column)


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

    get_error_line(self, symbol): Prints the line from the definition file
                            containing the symbol, and a marker pointing to its
                            position.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        # Check validity of arguments
        if not isinstance(path, str):
            raise TypeError('path must be a string')
        if len(path) < 4:  # path has length >= 4 due to the extension ".txt"
            raise TypeError('File should have the extension .txt')
        if path[-4:] != '.txt':
            raise TypeError('File should have the extension .txt')
        if not isinstance(names, Names):
            raise TypeError('names must be an instance of Names class')
        # open file
        self.fileIn = self._open_file(path)

        self.names = names

        # initialize symbol types
        # (DEVICE_DEF is ":="), (CONNECTION_DEF is "=>"),
        # (INVALID_SYMBOL is anything not in the symbol_type_list)
        self.symbol_type_list = [self.KEYWORD, self.DEVICE, self.PORT,
                                 self.NAME, self.NUMBER, self.COLON,
                                 self.SEMICOLON, self.COMMA, self.DEVICE_DEF,
                                 self.BRACKET_LEFT, self.BRACKET_RIGHT,
                                 self.CONNECTION_DEF, self.DOT,
                                 self.INVALID_SYMBOL, self.EOF] = range(15)

        # split syntax reserved words into keywords, devices and ports
        self.keywords_list = ["DEVICES", "CONNECTIONS", "MONITORS", "END"]
        self.devices_list = ["NAND", "AND", "NOR", "OR", "XOR", "DTYPE",
                             "CLOCK", "SWITCH", "SIGGEN"]
        self.ports_list = ["Q", "QBAR", "DATA", "CLK", "SET", "CLEAR", "I"]
        [self.DEVICES_ID, self.CONNECTIONS_ID, self.MONITORS_ID, self.END_ID] \
            = self.names.lookup(self.keywords_list)
        [self.NAND_ID, self.AND_ID, self.NOR_ID, self.OR_ID, self.XOR_ID,
            self.DTYPE_ID, self.CLOCK_ID, self.SWITCH_ID, self.SIGGEN_ID] \
            = self.names.lookup(self.devices_list)
        [self.Q_ID, self.QBAR_ID, self.DATA_ID, self.CLK_ID, self.SET_ID,
            self.CLEAR_ID, self.I_ID] = self.names.lookup(self.ports_list)

        # keep track of the beginning position of each line
        self.current_line_pos = 0
        self.current_line = 1
        self.current_character = None
        self.line_pos_record = {}
        self._update_line_pos_record()
        self._advance()  # place first character in current_character

    def _open_file(self, path):
        """Open and return the file specified by path."""
        try:
            file = open(path)
        except IOError as err:
            print("\nError occured when opening file for reading\n", err)
            sys.exit()
        return file

    def _advance(self):
        """Update current_character, and line position record."""
        if self.current_character == "\n":
            self.current_character = self.fileIn.read(1)
            self.current_line += 1
            self.current_line_pos = self.fileIn.tell() - 1
            self._update_line_pos_record()
        else:
            self.current_character = self.fileIn.read(1)

    def _update_line_pos_record(self):
        """Update the record containing the beginning position of each line in
        the input file."""
        if self.current_line not in self.line_pos_record:
            self.line_pos_record[self.current_line] = self.current_line_pos

    def _get_line_pos(self, line_no):
        """Return the beginning position of the line in the input file."""
        if line_no not in self.line_pos_record:
            raise ValueError("The line requested from the definition file has\
                    not been encountered.")
        return self.line_pos_record[line_no]

    def _look_ahead(self):
        """Return the next character in the definition file, without updating
        current_character and without incrementing the current position within
        the file."""
        ch = self.fileIn.read(1)
        self.fileIn.seek(self.fileIn.tell()-1, 0)
        return ch

    def _skip_spaces(self):
        """_advance current position in input file until the first non
        whitespace character."""
        while self.current_character != '' \
                and self.current_character.isspace():
            self._advance()

    def _skip_line(self):
        """Skip the rest of the current line in the input file."""
        self._advance()
        while self.current_character != '' and self.current_character != "\n":
            self._advance()

    def _get_name(self):
        """Return the name string that starts at the current_character, and
        _advance to the next character after the name string.

        This method assumes that the current_character is already a letter."""
        name = self.current_character
        self._advance()
        while (self.current_character.isalnum() or
                self.current_character == "_") \
                and self.current_character != '':
            name += self.current_character
            self._advance()
        return name

    def _get_number(self):
        """Return the number that starts at the current_character, and _advance
        to the next character after the number.

        This method assumes that the current_character is already a digit."""
        numList = self.current_character
        self._advance()
        while self.current_character != '' \
                and self.current_character.isdigit():
            numList += self.current_character
            self._advance()

        return int(numList)

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        symbol = Symbol()
        self._skip_spaces()  # current character now not whitespace

        symbol.line = self.current_line
        symbol.column = self.fileIn.tell() - self.current_line_pos

        # handle names, keywords, devices, ports
        if self.current_character.isalpha():
            name_string = self._get_name()
            if name_string in self.keywords_list:
                symbol.type = self.KEYWORD
            elif name_string in self.devices_list:
                symbol.type = self.DEVICE
            elif name_string in self.ports_list:
                symbol.type = self.PORT
            # handle input names for AND, NAND, OR, NOR (e.g. I2)
            elif name_string[0] == "I" and name_string[1:].isdigit():
                # in this case we have "I" followed by a number. So, the parser
                # expects two symbols: first a symbol of type PORT for "I", and
                # next a symbol of type NUMBER. The number will be returned the
                # next time the method get_symbol() is called
                self.fileIn.seek(self.fileIn.tell()-len(name_string[1:]), 0)
                self.current_character = name_string[1]
                name_string = name_string[0]
                symbol.type = self.PORT
            else:
                symbol.type = self.NAME
            [symbol.id] = self.names.lookup([name_string])
        # handle numbers
        elif self.current_character.isdigit():
            # NOTE that here the symbol.id is the number itself
            symbol.id = self._get_number()
            symbol.type = self.NUMBER
        # handle punctuation
        elif self.current_character == ":":  # handle ":", ":="
            if (self._look_ahead() == "="):
                symbol.type = self.DEVICE_DEF
                self._advance()
            else:
                symbol.type = self.COLON
            self._advance()
        elif self.current_character == ";":
            symbol.type = self.SEMICOLON
            self._advance()
        elif self.current_character == ",":
            symbol.type = self.COMMA
            self._advance()
        elif self.current_character == "(":
            symbol.type = self.BRACKET_LEFT
            self._advance()
        elif self.current_character == ")":
            symbol.type = self.BRACKET_RIGHT
            self._advance()
        elif self.current_character == "=":  # handle special case "=>"
            if (self._look_ahead() == ">"):
                symbol.type = self.CONNECTION_DEF
                self._advance()
            else:
                symbol.type = self.INVALID_SYMBOL
            self._advance()
        elif self.current_character == ".":
            symbol.type = self.DOT
            self._advance()
        elif self.current_character == "/":  # handle comments
            if (self._look_ahead() == "/"):
                self._advance()
                self._skip_line()
                # return next symbol right after the comment or any
                # immediately following comments
                symbol = self.get_symbol()
            else:
                symbol.type = self.INVALID_SYMBOL
                self._skip_line()
        elif self.current_character == "":  # end of file
            symbol.type = self.EOF
        else:  # not a valid character
            symbol.type = self.INVALID_SYMBOL
            self._advance()

        return symbol

    def get_error_line(self, symbol):
        """Print the line from the definition file containing the symbol,
        and a marker pointing to its position."""
        if not isinstance(symbol, Symbol):
            raise TypeError('symbol must be an instance of the class Symbol')

        # save current state of the scanner
        current_pos = self.fileIn.tell()
        current_ch = self.current_character
        current_line_pos = self.current_line_pos
        current_line = self.current_line
        line_record = self.line_pos_record.copy()

        # go to start of the line of the requested symbol
        symbol_line_pos = self._get_line_pos(symbol.line)
        self.fileIn.seek(symbol_line_pos, 0)
        self.current_character = self._advance()

        # count line length
        if self.current_character != "\n":
            self._skip_line()
        line_length = self.fileIn.tell() - symbol_line_pos - 1

        # get contents of line in the circuit definition file
        self.fileIn.seek(symbol_line_pos, 0)
        line_retrieved = self.fileIn.read(line_length)
        # replace tabs in line_retrieved with a single space for correct
        # printing to the terminal
        print(line_retrieved.expandtabs(1))
        print(" "*(symbol.column - 1) + "^")  # pointer to the symbol

        # restore state of the scanner
        self.fileIn.seek(current_pos, 0)
        self.current_line = current_line
        self.current_character = current_ch
        self.current_line_pos = current_line_pos
        self.line_pos_record = line_record.copy()
