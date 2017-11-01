#!/usr/bin/python3

import sys
import os, os.path
import json
import datetime
import hashlib
import copy

# change this to True for ridiculous detail output
debug_output = False

# =============================================================================
#
# ================== ONE FUNCTION TO RULE THEM ALL ============================

def export_records(unified_json_parameter, verbose=False):
    '''
    '''
    retval = ''

    # defaults for parameters and derived content
    marcout_text = None
    marcout_defn_structure = None
    collection_info = []
    records_to_export = []
    requested_serialization = None

    # the Flask catcher gets the JSON object as an ImmutableMultiDict
    # which looks VERY messed up when serialized... can we just treat it
    # as a JSON object?
    unified_json_obj = unified_json_parameter
    if isinstance(unified_json_parameter, str):
        unified_json_obj = json.loads(unified_json_parameter)


    # should be JSON
    # unified_json_parameter = str(unified_json_parameter)
    
    if verbose:
        retval += 'UNIFIED JSON PARAMETER PARSED SUCCESSFULLY.\n'

    # extract unified content into discrete variables
    marcout_text = unified_json_obj['marcout_text']
    records_to_export = unified_json_obj['records']
    collection_info = unified_json_obj['collection_info']
    requested_serialization = unified_json_obj['requested_serialization']

    print(requested_serialization)

    sz_name = requested_serialization['serialization-name']
    if sz_name not in serializations:
        raise ValueError('Requested serialization `' + sz_name + '` not known.')

    # ------------- PARSE MARCout text ----------------
    # unescape characters escaped for JSON
    marcout_text = marcout_text.replace('\\n', '\n')
    marcout_text = marcout_text.replace('\\"', '"')

    # cut the text clob into array of lines, and parse
    marcout_lines = marcout_text.split('\n')
    marcout_structures = parse_marcexport_deflines(marcout_lines)

    # convenience variables for MARCout export definitions
    expdef_functions = marcout_structures['functions']
    expdef_paramnames = marcout_structures['known_parameters']
    expdef_json_extracts = marcout_structures['json_extracted_properties']
    expdef_field_templates = marcout_structures['marc_field_templates']

    # Sanity:
    # (This is a likely mistake when composing unified JSON parameter.)
    # Verify that the collection params specified in MARCout
    # are present in the JSON unified parameter, and vice versa
    marcout_paramnames = set(expdef_paramnames)
    json_paramnames = set(collection_info.keys())
    # Set math: symmetric difference `^` operator will return empty 
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

    # Second:
    # Need to instantiate values for these variable names
    # for param_expr in expdef_paramnames:
    #     assign = param_expr + ' = \'' + collection_info[param_expr] + '\''
    #     if verbose:
    #         retval += 'executing: ' + assign + '\n'
    #     exec(assign)

    if verbose:
        retval += '\n'
        retval += 'MARCout STRUCTURES:\n'
        retval += '\n'

    # ------------- EXPORT RECORDS ---------------------
    if verbose:
        retval += '\n'
        retval += 'HOW MANY RECORDS TO EXPORT? ' + str(len(records_to_export)) + '\n'
        retval += '\n'


    exported_marc_records = []
    for record in records_to_export:
        album_json = record

        # Extract content of JSON record into locally scoped variables.
        # This reconstructs the assignment form in the original 
        # MARCout syntax.
        # These variables will then be referenceable in the
        # MARC field template expressions.

        current_rec_extracts = {}

        for key in expdef_json_extracts:
            # coerce to strings
            varname = str(key)
            varval = str(expdef_json_extracts[key])
            expr = varname + ' = ' + varval
            try:
                exec(expr)
            except Exception as ex:
                msg = 'Failure to execute "' + expr + '":'
                msg += str(ex)
                retval += msg + '\n'

            expr = 'current_rec_extracts[\'' + varname + '\'] = ' + varval
            try:
                exec(expr)
            except Exception as ex:
                msg = 'Failure to execute "' + expr + '":'
                msg += str(ex)
                retval += msg + '\n'

        if verbose:
            retval += '\n'
            retval += 'THESE ARE THE EXTRACTED VARIABLES:\n'
            for key in sorted(expdef_json_extracts.keys()):
                # coerce to strings
                varname = str(key)
            retval += '\n'

        # TODO ensure named functions are in scope.

        # Populate MARC field data structures by copying templates and
        # evaluating from the JSON content
        # and the application of the MARCout functions.

        record_output = []
        # need to use copy.deepcopy to avoid modifying templates: otherwise 
        # content would be propagated forward into a subsequent record, which
        # would blow things up: eval() on values, rather than parsed MARCout
        # expressions, would generally not work. (And in cases where it DID 
        # work, that would be even worse, creating corrupt records.)
        for template in copy.deepcopy(expdef_field_templates):

            # observe export conditionals
            if 'export_if' in template:
                evaluated_conditional = compute_expr(template['export_if'], current_rec_extracts, collection_info)
                if not evaluated_conditional:
                    # fail: this template does not get filled and
                    # placed in the return
                    continue

            if 'export_if_not' in template:
                evaluated_conditional = compute_expr(template['export_if_not'], current_rec_extracts, collection_info)
                # print('evaluates to: ' + str(evaluated_conditional))
                if evaluated_conditional:
                    # fail: the True condition prevents this template from 
                    # being filled and placed in the return
                    continue

            record_output.append(populate_marc_field(template, current_rec_extracts, collection_info))

        exported_marc_records.append(record_output)

        if verbose:   
            retval += '\n'
            retval += '-------------------------------\n'
            for item in exported_marc_records:
                retval += '\n'
                retval += str(item) + '\n'


    # SERIALIZE OUTPUT
    sz_func = serializations[sz_name]

    if verbose:
        retval += 'Serializing as ' + sz_name + '\n'
        retval += '\n'
        retval += '-------------------------------\n\n'

    for marc_record in exported_marc_records:
        serialized_record = sz_func(marc_record)
        # ensure exactly one blank line after record
        serialized_record = serialized_record.rstrip('\n')
        retval += serialized_record + '\n\n'

    return retval


# =============================================================================
#
# ================== CONSTANTS ================================================

# Characters significant for subfield expression parse operations
opaques = {'"': '"', "'": "'"}
nestables = {'(':')', '[':']', '{':'}'}


# less ambiguous substitutes for MARCout reserved phrases
marcout_keyword_replacements = {
    'IS NOT': 'IS_NOT',
    'IS TRUE': 'IS_TRUE',
    'IS FALSE': 'IS_FALSE',
    'HAS VALUE': 'HAS_VALUE',
    'HAS NO VALUE': 'HAS_NO_VALUE',
    'STARTS WITH': 'STARTS_WITH'
}

marcout_rewrites = {
    
    # - `IS`: operator that compares two sub-expressions for equality. 
    #     Equivalent to `==` in Python.
    ' IS ': [' == ', 'replace'],

    # - `IS NOT`: infix operator that compares two sub-expressions for inequality. 
    #     Equivalent to `!=` in Python.
    ' IS_NOT ': [' != ', 'replace'],

    # - `IS TRUE`: postfix operator that resolves to True if the preceding
    #     expression is a MARCout values of `TRUE`.
    ' IS_TRUE': ['marcout_is_true', 'postfix'],

    # - `IS FALSE`: postfix operator that resolves to True if the preceding
    #     expression is true, for MARCout values of `FALSE`.
    ' IS_FALSE': ['marcout_is_false', 'postfix'],

    # - `HAS VALUE`: postfix operator that resolves to True if the preceding 
    #     expression is PRESENT and not `EMPTY`. In other words, the expression
    #     has meaning over and above the ambiguous empty values.
    ' HAS_VALUE': ['marcout_has_value', 'postfix'],

    # - `HAS NO VALUE`: postfix operator that resolves to True if the preceding
    #     expression is not `PRESENT`, or, if `PRESENT`, is `EMPTY`.
    ' HAS_NO_VALUE': ['marcout_has_no_value', 'postfix'],

    # - `NOTHING`: alias (non-operator) keyword for generation of an empty value.
    #     Depending on context, makes an empty string, or a non-value such as 
    #     Python `None` or JSON `null`.
    'NOTHING': ['marcout_nothing_value', 'replace'],

    # - `STARTS WITH`: infix operator for string values. Resolves to True if the
    #     preceding string starts with the subsequent string.
    ' STARTS_WITH ': ['marcout_startswith', 'infix'],

    # - `CONTAINS`: infix operator for string values. Resolves to True if the
    #     preceding string starts with the subsequent string.
    ' CONTAINS ': ['marcout_contains', 'infix']

    # - `+`: the concatenation operator for string values. Does NOT represent
    #     numeric addition, date addition, etc.
}





# =============================================================================
#
# ================== UTILITY FUNCTIONS ========================================


# =============================================================================
#
# ================== MARCout PARSE FUNCTIONS ==================================


def value_after_first(expr, split_expr):
    '''This function prevents collision between differing usages of
    demarcators (":" in the current implementation.) Returns the portion
    of `expr` AFTER the first occurrence of `split_expr`. If `split_expr`
    does not appear in `expr`, returns `expr` unaltered.
    '''
    return split_expr.join(expr.split(split_expr)[1:]).strip()


def rewrite_keyword_expr(expr):
    '''This function replaces reserved keyword characters, words, and phrases
    with equivalent expressions in order to create an evaluable expression
    form. Sometimes, as in the case of postfix expressions, it's necessary to
    reorder the parts of the expression. Note that the resulting expression
    cannot, in general, be evaluated until the content of a JSON record is 
    available.
    '''
    retval = expr

    # replace token phrases with unified keyword forms
    for keyword in marcout_keyword_replacements:
        retval = retval.replace(keyword, marcout_keyword_replacements[keyword])

    # replace keyword expressions
    for keyword in marcout_rewrites:
        if keyword in retval:
            # the value of marcout_rewrites[keyword] is a list containing
            # [replacement, mode], where `mode` describes how the replacement
            # is applied.
            replacement = marcout_rewrites[keyword][0]
            replacement_mode = marcout_rewrites[keyword][1]

            if replacement_mode == 'replace':
                # the replacement val is a string that directly replaces
                # the keyword
                retval = retval.replace(keyword, replacement)

            elif replacement_mode == 'postfix':
                # the replacement value is a function name with a single
                # argument. The argument is the entire exression, but with the 
                # keyword removed)
                retval = replacement + '(' + retval.replace(keyword, '') + ')'

            elif replacement_mode == 'infix':
                # the replacement value is a function name with two arguments:
                # the portion of the expression before the keyword, and the
                # portion of the expression after the keyword.
                portions = retval.split(keyword)
                retval = replacement + '(' + portions[0] + ', ' + portions[1] + ')'

            else:
                raise ValueError('Unknown replacement mode "' + replacement_mode + '".')

    return retval


def parse_marcexport_deflines(deflines):
    '''This function turns the marcexport define text content into datastructures.
    It does this by reading the MARCout text line by line in multiple passes
    to accomplish different ends.

    From those blocks, it parses source content for the different
    categories of information. (It ignores "DESCRIPTION", which is
    non-machine-parseable documentation for humans.)
    
    From the content, it parses a dictionary/map/hash/object of marcexport
    datastructures:
        - 'known_parameters', required parameters
        - 'functions', function names anb brief signature/descriptions
        - 'json_extracted_properties', named expressions for pulling values from a
            JSON instance.
        - 'marc_field_templates', an ordered sequence of data structures listing
            desired fixed values, and album JSON extraction expressions, for MARC
            fields.
            This list of templates thus controls field order, subfield order,
            and instructions for pulling data from the expected JSON instance.

    This marcexport datastructures dictionary/map/hash/object is returned.
    '''

    # FIRST PASS: REMOVE COMMENTS (AND TRAILING NEWLINES)
    contentlines = []
    for line in deflines:
        if line.strip().startswith('#'):
            # it's only a comment line. ignore
            continue
        line = line.split('#')[0].rstrip()
        #note that we PRESERVE empty lines: they are significant
        contentlines.append(line.rstrip())

    # SECOND PASS: PARSE CONTENT INTO NAMED BLOCKS
    defblocks = {}      # dictionary: keys are block titles
    parse_order = []    # list: record order in which blocks were found
    current_blockname = None

    for line in contentlines:
        if line.strip().endswith('--------'):
            # transform block title in MARCout to lowercase with underscore
            line = line.strip()
            current_blockname = line[:line.find('----')]
            current_blockname = current_blockname.lower().replace(' ', '_')
            defblocks[current_blockname] = []
            parse_order.append(current_blockname)

        else:
            if current_blockname:
                defblocks[current_blockname].append(line.strip())

    # now evaluate marcexport define DATASTRUCTURE content as required.
    # do it block by block.
    marcdefs = {}
    marcdefs['parse_order'] = parse_order

    # KNOWN PARAMETERS:
    # what needs to be passed in for some things to work -- 
    # in codebase, some are environment variables;
    # at command line, they must be explicitly passed.
    paramnames = []
    for line in defblocks['known_parameters']:
        if line.strip():
            paramnames.append(line.strip())

    marcdefs['known_parameters'] = paramnames

    # FUNCTIONS:
    # function names and expressions
    marcdefs['functions'] = {}
    for line in defblocks['functions']:
        line = line.strip()
        if not line:
            continue

        # extract the function name
        funcname = line.split('(')[0]
        marcdefs['functions'][funcname] = line

    # EXTRACTORS:
    # expressions for pulling data out of JSON instances
    marcdefs['json_extracted_properties'] = {}
    for line in defblocks['json_extracted_properties']:
        line = line.strip()
        if not line:
            continue

        parts = line.split('=')
        # someone might put some equals signs in the expr - condition or something
        marcdefs['json_extracted_properties'][parts[0].strip()] = ('='.join(parts[1:])).strip()

    # FIELD TEMPLATES: 
    # ordered sequence of templates for MARC fields
    marcdefs['marc_field_templates'] = None

    field_data = [] # list of MARC field data assembled according to definitions
    current_field = None

    # using a while loop to have control over indx for readaheads
    indx = -1
    while indx < len(defblocks['marc_field_templates']) - 1:

        indx += 1
        line = defblocks['marc_field_templates'][indx]

        # indented_line is for processing indents. Otherwise, just strip
        # the line completely.
        indented_line = line.rstrip()
        line = line.strip()

        if line.endswith('----') or line.split('#')[0].rstrip().endswith('----'):
            # just a header
            continue

        if not line:
            # blank line --> field is done
            if current_field:
                # supply default properties
                if 'terminator' not in current_field:
                    current_field['terminator'] = '.'
                # data structures need a copy
                field_data.append(copy.copy(current_field))
                current_field = None

        if line.startswith('FIELD:'):
            # new field
            current_field = {}
            fieldtag = line.split(':')[1].strip()
            current_field['tag'] = fieldtag

        elif line.startswith('EXPORT UNLESS:'):
            expr = ':'.join(line.split(':')[1:])
            # perform initial prep for tokenization
            expr = rewrite_keyword_expr(expr)
            current_field['export_if_not'] = expr

        elif line.startswith('EXPORT WHEN:'):
            expr = ':'.join(line.split(':')[1:])
            # perform initial prep for tokenization
            expr = rewrite_keyword_expr(expr)
            current_field['export_if'] = expr

        elif line.startswith('INDC1:'):
            indc1 = line.split(':')[1].strip()
            if indc1 == 'blank':
                indc1 = ' '
            current_field['indicator_1'] = indc1

        elif line.startswith('INDC2:'):
            indc2 = line.split(':')[1].strip()
            if indc2 == 'blank':
                indc2 = ' '
            current_field['indicator_2'] = indc2

        elif line.startswith('CONTENT:'):
            content = ':'.join(line.split(':')[1:])
            # perform initial prep for tokenization
            content = rewrite_keyword_expr(content)
            current_field['content'] = content

        elif line.startswith('FOR EACH:'):
            # more complicated
            foreachexpr = line.split(':')[1].split(' in ')
            current_field['foreach'] = {}
            current_field['foreach']['eachitem'] = foreachexpr[0].strip()
            current_field['foreach']['itemsource'] = foreachexpr[1].strip()

        elif line.startswith('EACH-SUBFIELD:'):
            if 'subfields' not in current_field['foreach']:
                current_field['foreach']['subfields'] = []
            eachsub_code = line.split(':')[1].strip()
            eachsub_expr = defblocks['marc_field_templates'][indx + 1].strip()
            # perform initial prep for tokenization
            eachsub_expr = rewrite_keyword_expr(eachsub_expr)
            current_field['foreach']['subfields'].append({eachsub_code: eachsub_expr})

        elif line.startswith('SORT BY:'):
            # we may one day want to support "sort by a, b" expressions...
            # so make this an array, also
            if 'sortby' not in current_field['foreach']:
                current_field['foreach']['sortby'] = []
            sortby_expr = value_after_first(line, ':')
            current_field['foreach']['sortby'].append(sortby_expr)

        elif line.startswith('DEMARC WITH:'):
            demarc_expr = value_after_first(line, ':')
            current_field['foreach']['demarcator'] = demarc_expr

        # we do not want to grab subfields that are within a 
        elif line.startswith('SUBFIELD:'):
            if 'subfields' not in current_field:
                current_field['subfields'] = []
            subfield_code = line.split(':')[1].strip()
            subfield_expr = defblocks['marc_field_templates'][indx + 1].strip()
            # perform initial prep for tokenization
            subfield_expr = rewrite_keyword_expr(subfield_expr)
            current_field['subfields'].append({subfield_code: subfield_expr})

        # A "data" output line is CONTENT, SUBFIELDS, or FOREACH.
        # the DEFAULT is "."
        elif line.startswith('TERMINATE DATA WITH:'):
            terminator_expr = value_after_first(line, ':')
            if terminator_expr in ('', 'NONE', 'NOTHING'):
                terminator_expr = None
            current_field['terminator'] = terminator_expr

    marcdefs['marc_field_templates'] = field_data

    return marcdefs




# =============================================================================
#
# ================== MARCout EXPRESSION BUILT-IN IMPLEMENTATIONS ===============


# FUNCTIONS IMPLICITLY CALLED WHEN PARSER FINDS KEYWORD

# - `IS`: operator that compares two sub-expressions for equality. 
#     Equivalent to `==` in Python or JavaScript. No function: direct 
#     substitution in parser.

# `PRESENT`: an expression is `PRESENT` if it can be evaluated.
def marcout_is_present(expr_string):
    try:
        eval(expr_string)
        return True
    except:
        return False

# - `IS TRUE`: postfix operator that resolves to True if the preceding
#     expression is a MARCout distinguished value for `TRUE`.
def marcout_is_true(expr):

    # boolean is ok
    if isinstance(expr, bool):
        return expr

    # test for numeric 1 as distinguished value for `TRUE`
    elif isinstance(expr, int):
        return expr == 1

    elif isinstance(expr, types.StringTypes):
        check_expr = str(expr).lower()
        if check_expr in ('true', 'yes'):
            return True
        else:
            # complex string. evaluate expression
            try:
                expr = eval(expr)
                # if it comes out as a boolean, it was a proper
                # boolean function call
                if isinstance(expr, bool):
                    return expr
                else:
                    # not a boolean function call
                    return False
            except:
                # if it blows up, it's not `PRESENT`
                return False
    else:
        return False


# - `IS FALSE`: postfix operator that resolves to True if the preceding
#     expression is a MARCout distinguished value for `FALSE`

def marcout_is_false(expr):

    # boolean is ok
    if isinstance(expr, bool):
        # reverse the sense
        return not expr

    # test for numeric 0 as distinguished value for `FALSE`
    elif isinstance(expr, int):
        return expr == 0

    elif isinstance(expr, types.StringTypes):
        check_expr = str(expr).lower()
        if check_expr in ('false', 'no'):
            return True
        else:
            # complex string. evaluate expression
            try:
                expr = eval(expr)
                # if it comes out as a boolean, it was a proper
                # boolean function call.
                # reverse the sense
                if isinstance(expr, bool):
                    return notexpr
                else:
                    # not a boolean function call
                    return False
            except:
                # if it blows up, it's not `PRESENT`
                return False
    else:
        return False


# - `HAS VALUE`: postfix operator that resolves to True if the preceding 
    # expression is PRESENT and not `EMPTY`. In other words, the expression
    # has meaning over and above the ambiguous empty values.

def marcout_has_value(expr):

    if expr is None:
        return False

    if isinstance(expr, types.StringTypes):
        check_expr = expr.strip()
        # False if `EMPTY`: whitespace or empty string
        if len(check_expr) == 0:
            return False
        else:
            # `expr` might be an evaluable expression
            try:
                expr = eval(expr)
                # recurse with results of evaluation
                return marcout_has_value(expr)
            except:
                # not an evaluable expression. Just a non-empty string
                return True

    elif isinstance(expr, (list, tuple, dict, set)):
        # False if `expr` is a data structure with no content
        # otherwise True
        return len(expr) > 0

    else:
        # other types do not have defined `EMPTY` values
        return True

# - `HAS NO VALUE`: postfix operator that resolves to True if the preceding
#     expression is not `PRESENT`, or, if `PRESENT`, is `EMPTY`.
def marcout_has_no_value(expr_string):

    if expr is None:
        return True

    if isinstance(expr, types.StringTypes):
        check_expr = expr.strip()
        # True if `EMPTY`: whitespace or empty string
        if len(check_expr) == 0:
            return True
        else:
            # `expr` might be an evaluable expression
            try:
                expr = eval(expr)
                # recurse with results of evaluation
                return marcout_has_value(expr)
            except:
                # not an evaluable expression. Just a non-empty string
                return False

    elif isinstance(expr, (list, tuple, dict, set)):
        # True if `expr` is a data structure with no content
        # otherwise False
        return len(expr) == 0

    else:
        # other types do not have defined `EMPTY` values
        return False


# - `NOTHING`: keyword for an empty value. Depending on context, equivalent
#     to an empty string, or to a non-value such as Python `None` or
#     JSON `null`.

def marcout_nothing_value(type):
    if type in (str, unicode):
        return ''
    else:
        return None

# - `STARTS WITH`: operator for string values. Resolves to True if the
#     preceding string starts with the subsequent string.
def marcout_startswith(tested_expr, start_expr):
    return tested_expr.startswith(start_expr)

# - `CONTAINS`: operator for string values. Resolves to True if the
#     preceding string starts with the subsequent string
def marcout_contains(tested_expr, search_expr):
    return (search_expr in tested_expr)

# No function necessary: parser leaves in place.
# - `+`: the concatenation operator for string values. Does NOT represent
#     numeric addition.

# =============================================================================
#
# ================== EXPRESSION FUNCTIONS CALLABLE IN MARCEXPORT.DEFINE =======

# And their helper functions


def normalize_date(dateval):
    if not dateval:
        return ''
    dateval = str(dateval)
    dateval = dateval.split('T')[0]
    return dateval


def biblio_name(person_name):
    if ',' not in person_name:
        name_segments = person_name.split()     # split on spaces
        if len(name_segments) > 1:
            person_name = ', '.join([name_segments[-1], ' '.join(name_segments[:-1])])
    return person_name


def release_year(release_date):
    return str(release_date).split('-')[0]


def release_decade(release_date):
    decade_string = release_date.split("-")[0][0:3]    # first 3 chars of year
    decade_number = int(decade_string)
    decade_literal = str(decade_number) + "1-" + str(decade_number + 1) + "0";
    return decade_literal

    

def pretty_comma_list(listexpr, oxford=False):
    '''Accepts a comma separated list in string form, and a boolean
    that, if set to True, will stipulate use of the Oxford comma.
    Returns the list with leading and trailing whitespace stripped from 
    list items, separated by commas, with " and " inserted in lieu of
    the final separator.'''

    last_sep = ' and '
    if oxford:
        last_sep = ', and '

    # Python 3: changed `unicode.strip` to `str.strip`
    listexpr = map(str.strip, listexpr.split(','))
    # Python 3: `map` returns an iterator not a list. Convert.
    listexpr = list(listexpr)
    if len(listexpr) == 1:
        return listexpr[0]

    return ', '.join(listexpr[:-1]) + last_sep + listexpr[-1]


def zeropad(chars, length):
    retval = '0' * length
    # print('zeropad retval: ' + retval)
    retval = retval + chars
    # print('zeropad retval: ' + retval)
    return retval[-length:]


def h_m_s(duration_in_float_seconds):
    '''This function takes a high-precision number in seconds
    (e.g. 364.61401360544215) and returns an h:m:s value
    '''
    hours = 0
    minutes = 0
    seconds = 0

    seconds = int(round(duration_in_float_seconds))
    # print('raw integer seconds: ' + str(seconds))

    hours = seconds // 3600
    if hours:
        seconds -= hours * 3600

    minutes = seconds // 60
    if minutes:
        seconds -= minutes * 60

    retval = ':' + zeropad(str(seconds), 2)
    if minutes:
        if hours:
            retval = ':' + zeropad(str(minutes), 2) + retval
        else:
            retval = str(minutes) + retval
    if hours:
        retval = str(hours) + ':' + retval

    return retval


def render_duration(duration_in_float_seconds):
    '''Wrapper function that coerces representation to float
    (because JSON might wrap value in quotes) and rounds it to
    standard hours, minutes, seconds representation.
    '''
    return '(' + h_m_s(duration_in_float_seconds) + ')'


def total_play_length(tracks):
    float_seconds = 0.0
    for track in tracks:
        float_seconds += track['duration']
    return h_m_s(float_seconds)

def compute_control_number(album_id, collection_abbr):
    # Generation procedure:
    #  - obtain SHA1 hash of the album slug [here "album_id"]
    #  - take the last 7 digits of the hex digest
    #  - append 'a' as a collision shock absorber (intent is to go through
    #     the alphabet and then use single digits as necessary.)
    #  - prepend 3-character library collection code, demarcated with "_"
    #     Note that the collection code must be lower case, e.g. 'ccr', 'nbb', 'spb'
    # Javascript from musicat-api/utilities:
    # var album_slug_shasum = crypto.createHash("sha1");
    # album_slug_shasum.update(album_slug);
    # album_slug_shasum.id = album_slug_shasum.digest("hex");
    # last_seven_indx = album_slug_shasum.id.length - 7;
    # last_seven_chars = album_slug_shasum.id.slice(last_seven_indx);
    # control_number = collection_code + '_' + last_seven_chars + 'a';

    # sha1 of album_id
    # Python 3 specific: since album_id is unicode, it needs to be encoded
    # to bytes
    album_id = album_id.encode('utf-8')
    sha = hashlib.sha1(album_id).hexdigest()
    # put it all together
    control_number = collection_abbr.lower() + '_' + sha[-7:] + 'a'

    return control_number;



# =============================================================================
#
# ================== MARCout EXPRESSION PARSING FUNCTIONS =====================

# In MARC fields, the "tag", "indicator 1", and "indicator 2" values are
# fixed; their values are defined in the MARCout export definition.
#
# Subfield content, on the other hand, often includes values extracted from 
# the album JSON

# This is a simplistic stack-based recursive descent parse with implicit
# grammar for subfield expressions in marcexport.define. 
# The "delims" structure is a stack which grows as new opening delimiters
# occur, and shrinks as corresponding closing delimiters occur.
#
# In a subfield expression, quoted string literals are opaque objects: it
# doesn't matter what characters they contain, except the occurrence of
# the same quote character that begain the literal.
#
# The other kind of delimiter is the nestable structure token: (, [, {
# that open a nested sequence, and the corresponding ), ], } delimiters.
# As the name suggests, these kinds of delimiters can be meaningfully
# nested
#
# The parse separates the expression into syntactically significant 
# character sequences, as noted in the `tokenize` function string.


def closes_delim(delims, char):
    '''Returns True if char closes LAST value in delims'''
    if not delims:
        # Nothing to close
        return False

    # the last character in a delim sequence is looking for its closure
    openchar = delims[-1]

    if openchar in opaques:
        # We are in a string literal. Nothing but the corresponding 
        # close quote will have any effect.
        return (char == opaques[openchar])
    if openchar in nestables:
        # We're in a nestable expression
        if char == nestables[openchar]:
            # It's the right one
            return True
        elif char in nestables.values():
            # It's a wrong one. Invalid nesting!
            errmsg = 'BAD SUBFIELD EXPR: closing character `' + char
            errmsg += '` does not match opening character `' + openchar + '`.'
            raise Exception(errmsg)
    else:
        # Neither opaque nor nestable. Fix the tokenize script
        errmsg = 'CODE ERROR: invalid delimiter `' + delims[-1] + '`.'
        errmsg += ' Probably in tokenize function.'
        raise Exception(errmsg)

    return False


def opens_delim(delims, char):
    if not delims:
        # any opening delim will start a block
        return (char in opaques) or (char in nestables)

    if delims[-1] in opaques:
        # We are in a string literal, so no delimiter can open a nested block. 
        # This is what "opaque" means. A quoted literal can contain anything;
        # opening delimiters are insignificant.
        return False
    elif delims[-1] in nestables:
        # We're in a nested block. We can open either a string literal 
        # or a nested block here.
        return char in opaques or char in nestables
    else:
        # Neither opaque nor nestable. Fix the tokenize script
        errmsg = 'CODE ERROR: invalid delimiter `' + delims[-1] + '`.'
        errmsg += ' Probably in tokenize function.'
        raise Exception(errmsg)


def append_normalized_block(block, blocks):
    '''Strips leading & trailing whitespace; will not append a whitespace-only block.'''
    if block.strip():
        blocks.append(block.strip())


def tokenize(expr):

    '''This function returns the `expr` argument divided into a sequence of
    syntactically significant blocks of characters.

    Block types are:
     - string literals, explicitly quoted (treated as "opaque" to further parsing)
     - opening and closing nestable structure tokens: (, [, {, ), ], }
     - concatenation symbol: + with adjacent whitespace preserved
     - function names, invoked at JSON --> MARC export time
     - extracted property names, resolved at JSON --> MARC export time

    Concatenating the blocks in this return value recreates the `expr`
    parameter. This is a lossless transformation. 
    '''
    token_blocks = []     # sequence of blocks
    current_block = ''
    current_delims = []

    for char in expr:

        if closes_delim(current_delims, char):
            # we are matching an earlier opening. If quote, no thing.
            # if nestable... a little more involved.
            if char in opaques.values():
                # append it. Quotes don't get their own block like nestables do
                current_block += char
                append_normalized_block(current_block, token_blocks)

            elif char in nestables.values():
                append_normalized_block(current_block, token_blocks)
                # closing char gets its own block
                token_blocks.append(char)

            # reset
            current_block = ''
            current_delims.pop()

        elif opens_delim(current_delims, char):

            if char in nestables:
                append_normalized_block(current_block, token_blocks)
                # it gets its own block
                token_blocks.append(char)
                # reset
                current_block = ''
                current_delims.append(char)

            elif char in opaques:
                append_normalized_block(current_block, token_blocks)
                # put the char at the start of the new block
                current_block = ''
                current_block += char
                current_delims.append(char)

        elif char == '+':
            # give this a block of its own, but make no delim entry
            # because this is an operator
            append_normalized_block(current_block, token_blocks)
            # normalize whitespace for operator
            token_blocks.append(' + ')
            current_block = ''

        else:
            # non-delim, non-operator: content only:
            # neither opens nor closes
            current_block += char

    # flush accumulated content to return value
    append_normalized_block(current_block, token_blocks)

    return token_blocks





# =============================================================================
#
# ================== CORE FUNCTIONS FOR EXPORTING MARC RECORDS ================


def compute_extracts(extract_block, jsonobj):
    # print('COMPUTING EXTRACTS.')
    # print(extract_block)
    # print
    retval = {}
    album_json = jsonobj
    for propname in extract_block:
        if not propname:
            # empty key got in. gotta fix the parse
            continue
        # print(propname + ':')
        # print(extract_block[propname])
        extracted_val = eval(extract_block[propname])
        # print(extracted_val)
        retval[propname] = extracted_val
    return retval



def rewrite_for_context(marcout_expr, context_expr, context_varname):
    '''Translates context-identifying MARCout expression into an evaluable form.
    Parameters: `marcout_expr` is the MARCout expression.
    `context_expr` is the MARCout identifier for the context.
    `context_varname` is the evaluable variable reference for the context.
    EXAMPLE from FOREACH block:
    marcout_expr: 'render_duration(track::duration)'
    context_expr: 'track::'
    context_varname: 'current_item'
    return value: "render_duration(current_item['duration'])"
    '''
    tokens = tokenize(marcout_expr)
    for indx, token in enumerate(tokens):
        if token.startswith(context_expr):
            # change from MARCout notation to dict notation
            tokens[indx] = token.replace(context_expr, context_varname + '[\'') + '\']'
        # print(token)
    return ''.join(tokens)


def render_foreach(foreach_def_block, current_rec_extracts, collection_info):
    '''This function analyzes, sorts, and computes MARC subfield content that is defined
    in a MARCout FOREACH block, returning the subfield content properly rendered.

    '''
    retval = ''

    if debug_output:
        print('CURRENT REC EXTRACTS:')
        print(current_rec_extracts)
        print()
        print('FOREACH DEF BLOCK:')
        print(foreach_def_block)
        print()

    # local variables for notational clarity
    # itemsource = foreach_def_block['itemsource'] 
    # itemsource = eval(itemsource)
    itemsource_key = foreach_def_block['itemsource']
    itemsource = current_rec_extracts[itemsource_key]
    eachitem_name = foreach_def_block['eachitem']
    eachitem_expr = eachitem_name + '::'
    demarc = foreach_def_block['demarcator']
    # if you do not eval() a string expression, it will insert any accumulated enclosing quotes
    demarc = eval(demarc)

    sortkeys = foreach_def_block['sortby']
    # TODO: deal with sortby for cascade if more than one sort key in this list
    sortkey = sortkeys[0].lstrip(eachitem_expr)

    subfield_defs = foreach_def_block['subfields']

    # sort the list being iterated
    # TODO: make a better sort function for cascading sort
    itemsource.sort(key=lambda x: x[sortkey])

    # append rendered and demarcated subfields to retval
    for eachitem in itemsource:
        rendered_subfields = ''

        # this respects subfield definition order
        for subfield_def in subfield_defs:

            # a subfield_def is a dict of form 
            # {subfield_code: evaluable expression}
            for subcode in subfield_def.keys():
                subfield_expr = subfield_def[subcode]

                # print('  ' + subcode + ': ' + subfield_expr)

                subfield_expr = rewrite_for_context(subfield_expr, eachitem_expr, 'eachitem')
                # print('  ' + subcode + ': ' + subfield_expr)
                # print('  ' + subcode + ': ' + eval(subfield_expr))
                rendered_subfields += '$'
                rendered_subfields += subcode
                rendered_subfields += eval(subfield_expr)

        retval += rendered_subfields
        retval += demarc

    return retval


def compute_expr(expr, current_rec_extracts, collection_info):
    retval = expr

    # this is a parse 
    tokens = tokenize(expr)
    for indx, token in enumerate(tokens):
        if debug_output:
            print('TOKEN: ' + token)
        if token[0] in opaques:
            # this is a string literal. Don't mess with it.
            # print('skipping token:')
            # print(token)
            continue

        # For code expressions:

        # record-specific values
        # replace reference to extract name with actual value extracted from JSON.
        # ensure that the result is quotes as a literal.
        for extract in current_rec_extracts:
            if extract in token:
                if debug_output:
                    print('EXTRACT: ' + str(extract))

                extractval = current_rec_extracts[extract]
                if debug_output:
                    print('EXTRACTVAL: ' + str(extractval))
                    print('IS STR: ' + str(isinstance(extractval, str)))
                if isinstance(extractval, str):
                    # direct substitution WITH enclosing "" so it evals as a
                    # string literal on the way out of this function
                    token = token.replace(extract, '"' + extractval + '"')
                else:
                    token = token.replace(extract, str(extractval))
                if debug_output:
                    print('TOKEN: ' + token)

        # collection-specific parametric values
        for param in collection_info.keys():
            if param in token:
                if debug_output:
                    print('PARAM: ' + param)
                paramval = collection_info[param]
                if isinstance(paramval, str):
                    # direct substitution WITH enclosing "" so it evals as a
                    # string literal on the way out of this function
                    token = token.replace(param, '"' + paramval + '"')
                else:
                    token = token.replace(extract, str(extractval))
                if debug_output:
                    print('TOKEN: ' + token)

        # whatever modifications have been made to token, update the tokens list
        tokens[indx] = token

    # concat tokens into content
    evaluable = ''.join(tokens)

    retval = None

    # this second-stage eval applies functions, concats, etc
    if evaluable:
        if debug_output:
            print('EVALUATING "' + evaluable + '"')
        retval = eval(evaluable)
        if debug_output:
            print('EVALUATED TO: ' + str(retval))

    return retval


def populate_marc_field(template, current_rec_extracts, collection_info):
    '''This function returns a copy of the template, with record-specific
    values computed in place of the variouss expressions.
    '''

    # redundant use of deepcopy: belt, suspenders, 2 condoms & a bike helmet.
    retval = copy.deepcopy(template)

    for propname in retval:

        if propname in ('tag', 'indicator_1', 'indicator_2'):

            # do not evaluate. These are fixed, not computed.
            continue

        elif propname in ('content',):
            retval[propname] = compute_expr(retval[propname], current_rec_extracts, collection_info)

        elif propname == 'subfields':
            # "subfields" is a list to preserve order in which subfields
            # are defined. Each list item is a dict. Each dict is of the form
            # {subfield_code: expr} and has len() == 1
            for subfield_dict in retval[propname]:
                for subfield_code in subfield_dict:

                    subfield_dict[subfield_code] = compute_expr(subfield_dict[subfield_code], current_rec_extracts, collection_info)

        elif propname == 'foreach':
            # this is a dict. Keys are 
            # 'demarcator': literal, 
            # 'itemsource': expr, 
            # 'sortby': array of exprs, e.g. ['track::position'], 
            # 'subfields': array of subfield dicts, e.g. [{'t': 'track::title'}, {'g': 'render_duration(track::duration)'}],
            # 'eachitem': name assigned for notation. e.g. 'track', 
            retval[propname] = render_foreach(retval[propname], current_rec_extracts, collection_info)

        elif propname in('export_if', 'export_if_not'):
            # conditional
            retval[propname] = compute_expr(retval[propname], current_rec_extracts, collection_info)

    return retval




# =============================================================================
#
# ================== SERIALIZATION FUNCTIONS ==================================


def serialize_text(marc_record_fields):

    retval = ''

    for field in marc_record_fields:
        retval += '='
        retval += field['tag']
        retval += '  '
        for indcname in ('indicator_1', 'indicator_2'):
            # when there's no indicator at all, we represent in text as a single space
            indc_val = ' ' 
            if indcname in field:
                indc_val = field[indcname]
                if not indc_val.strip():
                    # the indicator is a space, which is represented as "\".
                    # We need to escape the backslash character by doubling it.
                    indc_val = '\\'
            retval += indc_val
        if 'content' in field:
            retval += field['content']
        elif 'foreach' in field:
            retval += field['foreach']
        elif 'subfields' in field:
            for subfield in field['subfields']:
                retval += '$'
                # subfield dict should only ever have one key & 
                # one associated value.
                subfield_code = list(subfield.keys())[0]
                subfield_val = subfield[subfield_code]
                retval += subfield_code
                retval += subfield_val
        if 'terminator' in field:
            if field['terminator']:
                retval += field['terminator']
        retval += '\n'

    return retval

def serialize_iso2709(marc_record_fields):

    retval = ''

    raise Exception('The `serialize_iso2709` function is not implemented yet.')

    return retval

def serialize_raw(marc_record_fields):
    '''Returns serialized data structures in Python/Javascript evaluable form.
    '''
    return str(marc_record_fields)

# serialization functions to be called, keyed by serialization_name
serializations = {
    'marc-text': serialize_text,
    'iso2709' : serialize_iso2709,
    'raw': serialize_raw
}