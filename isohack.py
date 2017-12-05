
import marcout_iso2709 as iso
import sys

isofilepath = sys.argv[1]
isofile = open(isofilepath)
isocontent = isofile.read()
isofile.close()

datastruct = iso.iso_record_2_raw(isocontent)

print()
print(datastruct)
print()
print()

serial = iso.raw_record_2_iso(datastruct)
print()
print(serial)
print()
print()

print('is new serialized ISO2709 same as source file?')
print(serial == isocontent)

isolen = len(isocontent)
serialen = len(serial)

print()
print('len(isocontent): ' + str(isolen))
print('len(serial): ' + str(serialen))
print()

for indx in range(isolen):
    if isocontent[indx] != serial[indx]:
        print()
        print('discrepancy at ' + str(indx) + ':')
        print(isocontent[indx])
        print(serial[indx])

print('|' + isocontent[299: 302] + '|')
print('|' + serial[299: 302] + '|')
