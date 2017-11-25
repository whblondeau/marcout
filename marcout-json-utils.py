#!/usr/bin/python3


# =============================================================================
#
# ================== FUNCTIONS ================================================


def evaluate_arg(argument):
    '''Returns content of argument as a -tuple: 
    (filepath, content, atatus_notes, errors). If the argument is a 
    valid filepath expression, `filepath` will be the path.
    If the filepath exists and is readable, `content` will
    be the content of the file; otherwise `content` will
    echo the argument. Exceptions are returned as Exception
    objects in the `complaints` list.
    '''
    abbrev = argument[:20] + '...'

    filepath = None
    content = None
    status_notes = []
    errors = []

    try:
        filepath = os.path.abspath(argument)
    except Exception as e:
        # not a valid filepath. 
        status_notes.append('arg "' + abbrev + '" is not a filepath.')
        content = argument

    if filepath:
        # it has the correct form for an absolute filepath
        if not os.path.isfile(filepath):
            # mistake in parameter
            errors.append('File "' + abbrev + '" is not a file on the system.')

        else:
            # read it.
            try:
                contentfile = open(filepath)
                content = contentfile.read()
            except Exception as e:
                # not a reachable file
                errors.append('Unable to read "' + abbrev + '":\n' + str(e))
            finally:
                contentfile.close()

    return filepath, content, status_notes, errors


def identify_content(content):
    '''This function returns 'JSON' if the parameter looks like
    a JSON MARCout file; 'MARCout' if the parameter looks like 
    a MARCout export definition; None if neither.
    THIS IS NOT A VALIDATOR. It just looks for occurrence of certain
    strings.
    '''

    retval = None
    # JSON
    content = content.strip()
    if content.startswith('{'):
        if '"marcout_text":' in content:
            retval = 'JSON'
    else:
        print(content[:10])
        marcout_consistent = True
        marcout_markers = ('KNOWN PARAMETERS----',
            'JSON EXTRACTED PROPERTIES----',
            'FUNCTIONS----',
            'MARC FIELD TEMPLATES----',)
        for marker in marcout_markers:
            print(marker + ' :: gouing in:')
            print(marcout_consistent)
            if not marker in content:
                marcout_consistent = False
                print('DIED ON ' + marker)
                break

        if marcout_consistent:
            print('MARCOUT OK')
            retval = 'MARCout'
        else:
            print('BIG NOPE')
    return retval


def extract_marcout_from_json(jsonobj):
    retval = None
    try:
        retval = jsonobj['marcout_text']
    except Exception as e:
        raise e
    return retval


def unescape_marcout(marcout_text):
    retval = marcout_text.replace('\\n', '\n')
    retval = retval.replace('\\"', '"')
    retval = retval.replace('\\t', '\t')
    return retval


def escape_marcout(marcout_text):
    retval = marcout_text.replace('\n', '\\n')
    retval = retval.replace('"', '\\"')
    retval = retval.replace('\t', '\\t')
    return retval


usage = '''USAGE:
    
    python3 marcout-json-utils.py <source> [<source>]

        --extract-marcout | --unescape-marcout | --escape-marcout | --update_json  

        [--verbose]

PARAMETERS:

    <source>: Either:

        - The location of a unified-json file, OR:

        - The serialized content of such a file, OR:

        - The location of a MARCout source file, OR:

        - The serialized content of such a file.

        The script will determine what kind of information is represented
        by each <source> parameter.

    --help: Print this message and exit. (Other arguments ignored.)

    --extract-marcout: *The unified-json parameter must be present*.
    This script will extract the raw MARCout content of the JSON's
    "marcout_text" property.

    --unescape-marcout: *If the unified-json source parameter is present,
        this script will unescape the value of its ./marcout-text property;
        otherwise, if the MARCout source is present this script will unescape
        the value of that.*. In either case, the unescaped content will
        be printed to stdout.

    --escape-marcout: *The MARCout source parameter must be present*.
        The script will read the MARCout source, and return it with all
        occurrences of  '\\n', '\\r', '\\"', and '\\t' escaped. (MARCout 
        convention for JSON is to use double quotes, not single quotes, 
        to delimit property values. If you want single quotes escaped,
        you're on your own.)

    --update-json: *Both unified-json and marcout-source parameters must be 
        present, AND the unified-json must be a file, not raw content*.
        The script will perforn an --escape-marcout on the MARCout source,
        and overwrite the JSON's "marcout_text" property with the result.

    --verbose: causes print of extra informative/diagnostic content to stdout.

This script is a convenience utility.
'''


import sys
import json
import os.path

if '--help' in sys.argv:
    print(usage)
    exit(0)

call_options = [arg for arg in sys.argv[1:] if arg.startswith('-')]
call_params = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

verbose = '--verbose' in call_options

# parse arguments
unified_json = None
marcout = None

for arg in call_params:
    (filepath, content, status_notes, errors) = evaluate_arg(arg)
    if verbose:
        print()
        if filepath:
            print('filepath:')
            print(filepath)
        if content:
            print('content begins with:')
            print(content[:50])

        if status_notes:
            print('\n'.join(status_notes))

    if errors:
        print('ERRORS:')
        print('\n'.join(errors))
        print()
        print('EXITING.')
        exit(0)


    if not content:
        # shouldn't happen, but this is cornercase insurance
        print('unable to extract content from arg.')
        print('EXITING.')
        exit(0)
    else:
        # we're good
        identified = identify_content(content)
        if verbose:
            print('identified as: ' + str(identified))

        if identified == 'JSON':
            try:
                unified_json = json.loads(content)
            except Exception as e:
                print('UNABLE TO PARSE JSON SOURCE.')
                print(e)
                exit(1)

            # print(unified_json)

        elif identified =='MARCout':
            marcout = content

exit(0)

if verbose:
    if unified_json:
        print('unified_json parsed.')
        print(unified_json)
    if marcout:
        print('MARCout present.')
        print(marcout)

# what action is being asked??

if call_options[0] == '--extract-marcout':
    if unified_json:
        extracted = extract_marcout_from_json(unified_json)
        print(extracted)

elif call_options[0] == '--escape-marcout':
    if marcout:
        # OK, try this:
        # TODO this is fucked up - unescapes itself??
        escaped = escape_marcout(marcout)
        print(escaped)

elif call_options[0] == '--update-json':
    arg_error = False
    if not unified_json: 
        arg_error = True
        print('No JSON to update.')
    if not marcout:
        arg_error = True
        print('No MARCout content.')

    if arg_error:
        exit(0)

    extracted = extract_marcout_from_json(unified_json)

    if extracted == marcout:
        print('THEY ARE THE SAME.')

    # MARCout is line-oriented
    extracted_lines = extracted.split('\n')
    marcout_lines = marcout.split('\n')

    counter = 0
    for mindx, line in marcout_lines:
        if line != extracted_lines[mindx]:
            if counter > 50:
                print('THAT IS ENOUGH.')
                break
            counter += 1
            print()
            print(('    ' + str(mindx))[-4:])
            print('NEW: ' + line)
            print('OLD: ' + extracted_lines[mindx])










