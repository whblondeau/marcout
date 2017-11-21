#!/usr/bin/python3

# This module contains functions for creating the subparts of an ISO 2709
# serialization of a MARC 21 bibliographic record

def iso_foreach(foreach_expr):
    '''The foreach expression comes with textual demarcators '?'
    preloaded. This function changes those demarcators to the 
    ISO2709 value, without changing any other '?' in the foreach.
    TODO fix this in foreach computation: send a list of subfield
    expressions instead of prestitching.
    '''

    retval = ''
    #first position
    if foreach_expr[0] == '$':
        retval = subfield_delimiter
    retval += foreach_expr.replace('--$', '--' + subfield_delimiter)

    return retval


def record_leader_positional(record, leader):
    '''This function computes record leader information knowable 
    from the record content, and from invariant field content
    defined for MARC 21 encoded as ISO 2709.
    '''

    retval = ['0','0','0','0','0','.','.','.','.','a','2','2',
        '.','.','.','.','.','.','.','#','4','5','0','0']

    # Record label—the first 24 characters of the record. 
    # This is the only portion of the record that is fixed in length.
    # The record label includes the record length and the base address 
    # of the data contained in the record. It also has data elements that 
    # indicate how many characters are used for indicators and subfield 
    # identifiers.
    
    # RECORD LABEL
    # 24 characters
    
    # In MARC, called "Leader"
    
    #     Character Positions 
            
    #     00-04 - Record length
    #         Computer-generated, five-character number equal to the
    #             length of the entire record, including itself and 
    #             the record terminator. 
                
    #         The number is right justified and unused positions contain zeros. 
        
    #     05 - Record status

    #         a - Increase in encoding level
    #         c - Corrected or revised
    #         d - Deleted
    #         n - New
    #         p - Increase in encoding level from prepublication

    #     06 - Type of record

    #         a - Language material
    #         c - Notated music
    #         d - Manuscript notated music
    #         e - Cartographic material
    #         f - Manuscript cartographic material
    #         g - Projected medium
    #         i - Nonmusical sound recording
    #         j - Musical sound recording
    #         k - Two-dimensional nonprojectable graphic
    #         m - Computer file
    #         o - Kit
    #         p - Mixed materials
    #         r - Three-dimensional artifact or naturally occurring object
    #         t - Manuscript language material

    #     07 - Bibliographic level

    #         a - Monographic component part
    #         b - Serial component part
    #         c - Collection
    #         d - Subunit
    #         i - Integrating resource
    #         m - Monograph/Item
    #         s - Serial

    #     08 - Type of control

    #         # - No specified type
    #         a - Archival

    #     09 - Character coding scheme

    #         # - MARC-8
    #         a - UCS/Unicode

    #     10 - Indicator count

    #         2 - Number of character positions used for indicators

    
    #     11 - Subfield code count

    #         2 - Number of character positions used for a subfield code

    
    #     12-16 - Base address of data

    #         [number] - Length of Leader and Directory

    
    #     17 - Encoding level

    #         # - Full level
    #         1 - Full level, material not examined
    #         2 - Less-than-full level, material not examined
    #         3 - Abbreviated level
    #         4 - Core level
    #         5 - Partial (preliminary) level
    #         7 - Minimal level
    #         8 - Prepublication level
    #         u - Unknown
    #         z - Not applicable

    #     18 - Descriptive cataloging form

    #         # - Non-ISBD
    #         a - AACR 2
    #         c - ISBD punctuation omitted
    #         i - ISBD punctuation included
    #         n - Non-ISBD punctuation omitted
    #         u - Unknown

    #     19 - Multipart resource record level

    #         # - Not specified or not applicable
    #         a - Set
    #         b - Part with independent title
    #         c - Part with dependent title

    #     20 - Length of the length-of-field portion

    #         4 - Number of characters in the length-of-field portion of a Directory entry

    #     21 - Length of the starting-character-position portion

    #         5 - Number of characters in the starting-character-position portion of a Directory entry 
    
    #     22 - Length of the implementation-defined portion

    #         0 - Number of characters in the implementation-defined portion of a Directory entry

    #     23 - Undefined

    return 'x' * 24

# Subfield_delimiter is ASCII 1F hex 
# (ref: http://www.nla.gov.au/librariesaustralia/cathelp/bib/concise.html)
# Also, working with http://www.loc.gov/standards/marcxml/Sandburg/sandburg.mrc,
# cross-referencing with the AMRCXML form of the same record at
# http://www.loc.gov/standards/marcxml/Sandburg/sandburg.xml, we get this:

# the field delimiter within a record is ASCII 1E hex.
# appears immediately before the indicator_1 and indicator_2.
field_delimiter = chr(0x1E)
# the subfield delimiter within a field is ACII 1E hex.
# usually represented in text as "$"
# appears immediately before the single-character subfield code.
subfield_delimiter = chr(0x1F) 
# the record terminator is ASCII 1D hex.
record_terminator = chr(0x1D)

# other observations:
# spaces are never escaped. (in marc text, they are represented as "\")


def field_content(variable_field):
    '''This function concatenates all field data content into
    a single string with correct demarcation.
    '''

    # note that in ISO2709 (.mrc) format, the tag number resides 
    # ONLY in the Directory.
    retval = ''

    if 'indicator_1' in variable_field:
        ind_1 = variable_field['indicator_1']
        if not ind_1.strip():
            # substitute '\' for an empty space
            ind_1 = '\\'
        retval += ind_1
    if 'indicator_2' in variable_field:
        ind_2 = variable_field['indicator_2']
        if not ind_2.strip():
            ind_2 = '\\'
        retval += ind_2

    if 'content' in variable_field:
        # This has only a single undifferentiated value. With no demarcators.
        # and there will be no 'subfields' nor 'foreach'.
        retval += variable_field['content']

    else:
        if 'subfields' in variable_field:
            # this will be a list of dicts. preserve order.
            for subfield in variable_field['subfields']:
                # subfield_delimiter comes first; then subfield code; then data
                retval += subfield_delimiter 
                # subfield will be a dict with a single mapping 
                subfield_code = list(subfield.keys())[0]
                retval += subfield_code
                retval += subfield[subfield_code]

        if 'foreach' in variable_field:
            # foreach has already been resolved to a single composite string,
            # with baked-in demarcation.
            # TODO this should probably be pushed to the serializations...

            retval += iso_foreach(variable_field['foreach'])

    if 'terminator'  in variable_field:
        retval += variable_field['terminator']

    return retval


def serialize_fields(raw_record):
    '''This function receives a record in raw MARCout datastructure form, 
    and returns the record as a list (with field order preserved) of
    individually rendered composite strings of field data appropriate for
    inclusion in an ISO 2709 serialization of the record.
    '''
    retval = []

    for field in raw_record:
        retval.append(field_content(field))

    return retval



def directory_entry(variable_field, start_position):
    '''Generates a single directory entry, 12 characters long, of format:
        00-02 - Tag
        03-06 - Field length
        07-11 - Starting character position
    '''

    entry = variable_field['tag']

    entry += len(content)





# LAUNCH FROM COMMAND LINE

test_record = [
    {'tag': '001', 'content': 'nbb_a7ff441a', 'terminator': '.'}, 
    {'tag': '003', 'content': 'BoomBox MUSICat', 'terminator': '.'}, 
    {
        'indicator_2': ' ', 
        'indicator_1': '1', 
        'terminator': '.', 
        'export_if_not': False, 
        'subfields': [
            {'a': 'Lively, Mischa'}
        ], 
        'tag': '100'
    }, 
    {
        'indicator_2': '0', 
        'tag': '245', 
        'subfields': [
            {'a': 'Pillow'}, 
            {'c': 'Mischa Lively'}
        ], 
        'indicator_1': '1', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '260', 
        'subfields': [
            {'a': '[Place of publication not indicated] :'}, 
            {'b': 'RACECAR'}, 
            {'c': '2016'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '300', 
        'subfields': [
            {
                '1': 'online resource (1 audio file (26:23)) ;'}, 
            {'b': 'digital'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '500', 
        'subfields': [
            {'a': 'MUSICat Submission Round: boombox-fall-2016'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    },
    {
        'indicator_2': ' ', 
        'tag': '506', 
        'subfields': [
            {'a': 'Streaming available to Library patrons.'}, 
            {'m': 'BoomBox content provided by MUSICat'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '511', 
        'subfields': [
            {'a': 'Performed by Mischa Lively'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': '0', 
        'foreach': '$tPillow$g(8:30) --$tBlakeup$g(5:09) --$tA Posture For Learning$g(6:05) --$tHeld Open$g(6:40) --', 
        'tag': '505', 
        'indicator_1': '0', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '546', 
        'subfields': [
            {'a': 'Sung in English'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': '0', 
        'tag': '650', 
        'subfields': [
            {'a': 'Dance & Electronic'}, 
            {'y': '2011-2020'}
        ], 
        'indicator_1': ' ', 
        'terminator': '.'
    }, 
    {
        'indicator_2': ' ', 
        'tag': '710', 
        'subfields': [
            {'a': 'Rabble, LLC'}, 
            {'u': 'MUSICat'}
        ], 
        'indicator_1': '2', 
        'terminator': '.'
    }, 
    {
        'indicator_2': '2', 
        'tag': '856', 
        'subfields': [
            {'z': 'Cover image'}, 
            {'u': 'https://boombox-jsfs.library.nashville.org/complete-submission/albums/mischa-lively-album/1500x1500_300ppi_pillow_digi_ep_art_rgb.jpg'}
        ], 
        'indicator_1': '4', 
        'terminator': '.'
    }, 
    {
        'indicator_2': '0', 
        'tag': '856', 
        'subfields': [
            {'u': 'https://boombox.library.nashville.org/albums/mischa-lively-album'}, 
            {'z': 'Click here to access this electronic item'}
        ], 
        'indicator_1': '4', 
        'terminator': '.'
    }
]

print('OK')
print()
serialized_record = serialize_fields(test_record)
print('How many records?')
print(len(serialized_record))
print()
for iso_field in serialized_record:
    print(iso_field)
print()