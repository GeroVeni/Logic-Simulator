#!/usr/bin/env python3
"""Preliminary exercises for Part IIA Project GF2."""
import sys

from mynames import MyNames


def open_file(path):
    """Open and return the file specified by path."""
    try:
        f = open(path)
    except IOError as err:
        print("\nError occured when opening file for reading\n", err)
        sys.exit()

    return f


def get_next_character(input_file):
    """Read and return the next character in input_file."""
    return input_file.read(1)


def get_next_non_whitespace_character(input_file):
    """Seek and return the next non-whitespace character in input_file."""
    ch = get_next_character(input_file)
    while ch != '' and ch.isspace():
        ch = get_next_character(input_file)
    return ch


def get_next_number(input_file):
    """Seek the next number in input_file.

    Return the number (or None) and the next non-numeric character.
    """

    # NOTE: Should we use the get_next_character OR the get_next_non_whitespace_character method ?
    # NOTE: Should we convert numList to int OR leave it as string ?

    # Reading until finding a number or the end of file
    ch = get_next_character(input_file)
    while ch != '' and (not ch.isdigit()):
        ch = get_next_character(input_file)

    # If no number is found
    if ch == '':
        return [None, '']

    # Else a number was found so start reading it
    numList = ''
    while ch != '' and ch.isdigit():
        numList += ch
        ch = get_next_character(input_file)

    return [int(numList), ch]


def get_next_name(input_file):
    """Seek the next name string in input_file.

    Return the name string (or None) and the next non-alphanumeric character.
    """

    # Reading until finding a letter or end of file
    ch = get_next_character(input_file)
    while ch != '' and (not ch.isalpha()):
        ch = get_next_character(input_file)

    # If not letter found
    if ch == '':
        return [None, '']

    # Else a letter was found, so start reading the name
    name = ''
    while ch != '' and ch.isalnum():
        name += ch
        ch = get_next_character(input_file)

    return [name, ch]


def main():
    """Preliminary exercises for Part IIA Project GF2."""

    # Check command line arguments
    arguments = sys.argv[1:]
    if len(arguments) != 1:
        print("Error! One command line argument is required.")
        sys.exit()

    else:

        print("\nNow opening file...")
        # Print the path provided and try to open the file for reading
        path = arguments[0]
        print("\nFile path: " + path)
        fileIn = open_file(path)

        print("\nNow reading file...")
        # Print out all the characters in the file, until the end of file
        ch = get_next_character(fileIn)
        while ch != '':
            print(ch, end='')
            ch = get_next_character(fileIn)

        print("\nNow skipping spaces...")
        # Print out all the characters in the file, without spaces
        fileIn.seek(0, 0)
        ch = get_next_non_whitespace_character(fileIn)
        while ch != '':
            print(ch, end='')
            ch = get_next_non_whitespace_character(fileIn)

        print("\nNow reading numbers...")
        # Print out all the numbers in the file
        fileIn.seek(0, 0)
        num = get_next_number(fileIn)
        while num[0] is not None:
            print(num[0])
            num = get_next_number(fileIn)

        print("\nNow reading names...")
        # Print out all the names in the file
        fileIn.seek(0, 0)
        name = get_next_name(fileIn)
        while name[0] is not None:
            print(name[0])
            name = get_next_name(fileIn)

        print("\nNow censoring bad names...")
        # Print out only the good names in the file
        fileIn.seek(0, 0)
        names = MyNames()
        bad_name_ids = [names.lookup("Terrible"), names.lookup("Horrid"),
                        names.lookup("Ghastly"), names.lookup("Awful")]
        name = get_next_name(fileIn)
        while name[0] is not None:
            if names.lookup(name[0]) not in bad_name_ids:
                print(name[0])
            name = get_next_name(fileIn)


if __name__ == "__main__":
    main()
