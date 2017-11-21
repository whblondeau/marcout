#!/usr/bin/python3

field_delimiter = chr(0x1E)
subfield_delimiter = chr(0x1F) 
record_terminator = chr(0x1D)


def entries_in_directory(directory_string):
    '''returns the list of 12-character substrings if:
    all characters are digits; 
    there are at least 12 characters; 
    and the length of 
    the string is evenly divisible by 12 (because a directory entry
    is exactly 12 characters long).
    Otherwise raises a ValueError.
    '''
    dir_entry_size = 12

    if not len(directory_string) >= dir_entry_size:
        raise ValueError('Directory string parameter requires a minimum of ' 
            + str(dir_entry_size) + 'chars.')
    if not directory_string.isdigit():
        raise ValueError('Directory string parameter contains non-numeric characters.')
    if len(directory_string) % 12:
        raise ValueError('Directory string parameter length is not an integer multiple of 12.')

    # list comprehension on a range, with slicing syntax applied to directory_string
    return [ directory_string[i:i+dir_entry_size] for i in range(0, len(directory_string), dir_entry_size) ]


def get_content(dir_entry, fields_text):
    tag = dir_entry[:3]
    length = int(dir_entry[3:7])
    startpos = int(dir_entry[7:])

    return tag, fields_text[startpos:startpos + length]

def remove_demarcators(field_content):
    removals = (field_delimiter, subfield_delimiter, record_terminator)
    return field_content.translate({ord(c): None for c in removals})



def iso_2_raw(iso_content):

    print('len(ISO 2709 content): ' + str(len(iso_content)))

    LDR = iso_content[:24]
    print(LDR)
    print()
    rest = iso_content[24:]
    print(rest)
    print()
    first_delim_pos = rest.find(field_delimiter)
    print('first field delimiter found at pos: ' + str(first_delim_pos))
    print()
    directory = rest[:first_delim_pos]
    print(directory)
    print()
    print('entries in directory:')
    dir_entries = entries_in_directory(directory)
    print(len(dir_entries))

    fields = rest[first_delim_pos:]
    print(fields)
    print()

    for entry in dir_entries:
        pair = get_content(entry, fields)
        print()
        print('tag: ' + pair[0])
        print(pair[1])
        print(remove_demarcators(pair[1]))





# EXECUTE
import sys


marcfilename = sys.argv[1]
marcfile = open(marcfilename)
marcstuff = marcfile.read()
marcfile.close()

conversion = iso_2_raw(marcstuff)