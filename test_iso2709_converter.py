
usage = '''USAGE: python3 test_iso2709_converter.py <
'''


# EXECUTE
import sys

import marcout_iso2709 as iso

rawfilename = sys.argv[1]
rawfile = open(rawfilename)
rawfile_content = rawfile.read()
rawfile.close()

print(rawfile_content)
print()
print()

raw_struct = eval(rawfile_content)

print(raw_struct)
print()
print()

serial = raw_record_2_iso(raw_struct)
print(serial)
print()
print()

first_record_pos = serial.find(field_delimiter)     # 203 in mischa's raw rep
print('FIRST RECORD STARTS AT POS ' + str(first_record_pos))
print()
directory_string = serial[24:first_record_pos]
fields_text = serial[first_record_pos:]
print('DIRECTORY STRING:')
print(directory_string)
print()
print()

fields = entries_in_iso_directory(directory_string)
for field in fields:
    print(field)
    print(read_iso_field_content(field, fields_text))
    print()

# marcfilename = sys.argv[1]
# marcfile = open(marcfilename)
# marcstuff = marcfile.read()
# marcfile.close()

# conversion = iso_record_2_raw(marcstuff)

# print(conversion)

# print()
# print('=====================================')
# print()

# roundtripped_record = raw_record_2_iso(conversion)

# print('Is roundtripped_record == original .mrc file content? ')
# print(roundtripped_record == marcstuff)
