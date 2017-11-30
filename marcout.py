#!/usr/bin/python3

import marcout_common as common
import marcout_parser as parser
import marcout_serializer as serializer


# =============================================================================
#
# ================== CONSTANTS ================================================






# =============================================================================
#
# ================== FUNCTIONS ================================================


def parse_unified_json(param):

    # the Flask catcher gets the JSON object as an ImmutableMultiDict
    # which looks VERY messed up when serialized... can we just treat it

    # assume it's already a parsed JSON object
    retval = param

    if isinstance(param, (str, bytes,)):
        # param might be a filepath, or raw content
        jsontext, filepath, errors = common.get_param_content(param)

    if jsontext:
        if verbose:
            print('JSON content:')
            print(common.truncate_msg(jsontext, 120))
    else:
        print('NONE FOUND.')



        unified_json_obj = json.loads(unified_json_parameter)




def resolve_unified_json(unified_jsonobj):
    '''This function accepts a parsed JSON object, interprets it,
    and returns a dictionary containing four items:
        - the MARCout Engine parsed from "marcout_text";
        - the requested serialization, by name;
        - the collection info;
        - the list of records to be exported.
    Obvious missing, wrong, or inconsistent elements raise a ValueError.
    '''
    retval = {}

    # defaults for parameter content
    marcout_text = None
    requested_serialization = None
    collection_info = []
    records_to_export = []

    marcout_structures = {}
    sz_name = None


    # extract unified content into discrete variables
    errors = []
    json_contentnames = ('marcout_text', 'requested_serialization', 
        'collection_info', 'records',)
    
    for contentname in json_contentnames:
        if not contentname in unified_jsonobj:
            errors.append('Missing "' + contentname + '" in Unified JSON.')
    if errors:
        raise ValueError('\n'.join(errors) + '\n')

    # populate convenience variables
    marcout_text = unified_jsonobj['marcout_text']
    requested_serialization = unified_jsonobj['requested_serialization']
    collection_info = unified_jsonobj['collection_info']
    records_to_export = unified_jsonobj['records']

    sz_name = requested_serialization['serialization-name']
    # does the serializer know about this?
    if sz_name not in serializer.serializations:
        raise ValueError('Requested serialization `' + sz_name + '` not known.')

    # ------------- PARSE MARCout text ----------------
    # unescape characters escaped for JSON
    marcout_text = marcout_text.replace('\\n', '\n')
    marcout_text = marcout_text.replace('\\"', '"')

    # one of the returned values. The MARCout Engine is a set of
    # statements to govern selection, content, and formatting for
    # exported MARC record fields.

    # cut the text clob into array of lines, and parse
    marcout_lines = marcout_text.split('\n')
    marcout_engine = parser.parse_marcexport_deflines(marcout_lines)

    # Sanity:
    # (This is a likely mistake when composing unified JSON parameter.)
    # Verify that the collection params specified in MARCout
    # are present in the JSON unified parameter, and vice versa
    marcout_paramnames = set(marcout_engine['known_parameters'])
    json_paramnames = set(collection_info.keys())
    # Using set math: symmetric difference `^` operator will return empty 
    # set if no mismatch between operands:
    all_mismatches = marcout_paramnames ^ json_paramnames

    if all_mismatches:
        errmsg = 'Collection parameter mismatch.'
        marcout_not_in_json = marcout_paramnames - json_paramnames
        json_not_in_marcout = json_paramnames - marcout_paramnames

        if marcout_not_in_json:
            errmsg = '\nCollection params defined in MARCout but not supplied in JSON:'
            errmsg += '\n  ' + ', '.join(marcout_not_in_json)
        if json_not_in_marcout:
            errmsg += '\nCollection params in JSON that are not defined in MARCout:'
            errmsg += '\n  ' + ', '.join(json_not_in_marcout)
        raise ValueError(errmsg)

    # We're still here, so the JSON was broadly OK: Not validated,
    # but at least claims to have the right content.
    retval = {'marcout_engine': marcout_engine,
        'serialization': sz_name,
        'collection_info': collection_info,
        'records_to_export': records_to_export,
    }

    return retval
