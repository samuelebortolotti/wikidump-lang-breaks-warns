"""
WIKIBREAKS DOCUMENTATION
There are many wikibreaks templates as I can see:
https://en.wikipedia.org/wiki/Template:Wikibreak:
# Basics attributes I need to scrape
{{wikibreak | [Name] | back = | type = | message  = | align = | image = | noimage = | imagesize = | spacetype = | style = }}
# to consider {{in-house switch}} {{At school}} {{Exams}} {{Vacation}} {{Out of town}} {{Personal issues}}
"""

import regex as re
from .. import wikibreaks
from typing import Iterable, Iterator, Mapping, NamedTuple, Optional, Mapping
from .common import CaptureResult, Identifier, Span
from .types.wikibreak import Wikibreak
from .utils.language_utils_functions import (
    write_error,
    write_error_level_not_recognized,
    is_level
)

# exports 
__all__ = ['wikibreaks_extractor', 'Wikibreak', ]

# https://regex101.com/r/BK0q6s/1
wikibreak_pattern = r'''
    \{\{                    # match {{
        (?:                 # non-capturing group
            \s              # match any spaces
            |               # or
            \_              # match underscore (count as space)
        )*                  # match 0 or multiple times
        (?P<type>           # namedgroup named type
            %s              # wikibreak word to substitute
        )                   # closed named group
        (?:                 # start of a non capturing group
            \s              # match any spaces
            |               # or
            \_              # match _
        )*                  # repeat the group 0 or n times
        \|                  # match pipe
        (?P<options>        # named group options
            [^{]*           # match anything but closed curly brakets
        )                   # end of the named group
    \}\}'''                 # match }}

# https://regex101.com/r/Cuey3K/1
wikibreak_empty_pattern = r'''
    \{\{                    # match {{
        (?:                 # non-capturing group
            \s              # match any spaces
            |               # or
            \_              # match underscore (count as space)
        )*                  # match 0 or multiple times
        (?P<type>           # named group named type
            %s              # wikibreak word to substitute
        )                   # closed named group
        (?P<options>        # named group named options
            (?:             # non-capturing group
                \s          # match any spaces
                |           # or
                \_          # match _
            )*              # repeat the group 0 or n times
        )                   # end of a non captuiring group
    \}\}'''                 # match }}

# BACK/NOT CATEGORY 
wikibreak_back_not_words = wikibreaks.wikibreak_cant_retire + \
    wikibreaks.wikibreak_considering_retirement + \
    wikibreaks.wikibreak_off_and_on

# BREAK CATEGORY
wikibreak_words = wikibreaks.wikibreak_standard_words + \
    wikibreaks.wikibreak_in_house + \
    wikibreaks.wikibreak_switch + \
    wikibreaks.wikibreak_at_school + \
    wikibreaks.wikibreak_exams + \
    wikibreaks.wikibreak_vacation + \
    wikibreaks.wikibreak_out_of_town + \
    wikibreaks.wikibreak_personal_issue

# HEALTH-RELATED
wikibreak_health_words = wikibreaks.wikibreak_user_bonked + \
    wikibreaks.wikibreak_user_grieving + \
    wikibreaks.wikibreak_user_health_inactive + \
    wikibreaks.wikibreak_user_covid19

# MENTAL
wikibreak_mental_words = wikibreaks.wikibreak_busy + \
    wikibreaks.wikibreak_discouraged + \
    wikibreaks.wikibreak_user_contempt + \
    wikibreaks.wikibreak_user_frustrated

# HEALTH-RELATED AND MENTAL
wikibreak_health_mental_words = wikibreaks.wikibreak_user_stress + \
    wikibreaks.wikibreak_user_mental_health

# TECHNICAL
wikibreak_technical_words = wikibreaks.wikibreak_computer_death + \
    wikibreaks.wikibreak_no_internet + \
    wikibreaks.wikibreak_no_power + \
    wikibreaks.wikibreak_storm_break

# OTHER
wikibreak_other_words = wikibreaks.wikibreak_deceased + \
    wikibreaks.wikibreak_not_around + \
    wikibreaks.wikibreak_retired + \
    wikibreaks.wikibreak_semi_retired + \
    wikibreaks.wikibreak_userbox_ex_wikipedia

# ALL
all_wikibreaks_words = wikibreak_back_not_words + \
    wikibreak_words + \
    wikibreak_health_words + \
    wikibreak_mental_words + \
    wikibreak_health_mental_words + \
    wikibreak_technical_words + \
    wikibreak_other_words

WIKIBREAKS_PATTERN_REs = [ 
    re.compile(wikibreak_pattern%(w_word.lower()), re.IGNORECASE | re.UNICODE | re.VERBOSE | re.MULTILINE) 
    for w_word in all_wikibreaks_words
]

WIKIBREAKS_EMPTY_PATTERN_REs = [
    re.compile(wikibreak_empty_pattern%(w_word.lower()), re.IGNORECASE | re.UNICODE | re.VERBOSE | re.MULTILINE) 
    for w_word in all_wikibreaks_words
]

WIKIBREAKS_REs = WIKIBREAKS_PATTERN_REs + WIKIBREAKS_EMPTY_PATTERN_REs

def wikibreaks_extractor(text: str) -> Iterator[CaptureResult[Wikibreak]]:
    for pattern in WIKIBREAKS_REs:
        for match in pattern.finditer(text): # returns an iterator of match object
            if check_wikibreaks_presence(match): # extract a named group called type (name of the wikipause template used)
                wiki_name = match.group('type')
                
                if not wiki_name:
                    write_error(pattern, match)
                    return
                
                # Wikipause object: basically the name and the list of options
                wikipause_obj = Wikibreak(wiki_name, list())

                # Parse the options if any
                if check_options(match):
                    # parse the options
                    parsed_options = match.group('options').strip().replace('_', '') .split('|') # retrieve the options
                    # remove spaces, remove _ which count as spaces and split for parameters)
                    # Assign the parsed options to the wikipause_obj
                    if not (len(parsed_options) == 1 and parsed_options[0] == ''):
                        wikipause_obj.options.extend(parsed_options)

                yield CaptureResult(
                    data=(wikipause_obj), span=(match.start(), match.end())
                )

def check_options(match: Iterator[re.Match]) -> bool:
    """Checks if some groups is present inside the match object"""
    try:
        match.group('options')
        return True
    except IndexError:
        return False

def check_wikibreaks_presence(match: Iterator[re.Match]) -> bool:
    """Checks if some groups is present inside the match object"""
    try:
        match.group('type')
        return True
    except IndexError:
        return False