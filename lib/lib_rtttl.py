# Based on:
#  https://github.com/asdwsda/rtttl
# GNU GENERAL PUBLIC LICENSE
#                       Version 3, 29 June 2007

import re

def remove_whitespaces(string):
    return ''.join(string.split())

def parse_rtttl(rtttl_str, strict_note_syntax=False):
    """Parse RTTTL ringtone
    Args:
        rtttl_str (str): RTTTL string to parse
        strict_note_syntax (bool): Some RTTTL generator doesn't strictly follow
            the RTTTL specification and generates a form like
                <note> := [<duration>] <note> [<dot>] [<octave>] <delimiter>
            instead of
                <note> := [<duration>] <note> [<octave>] [<dot>] <delimiter>
            parse_rtttl accepts both forms by default, but it can be set to
            accept valid rtttl notes only.
    Returns:
        A dict containing the ringtone title and notes as frequency, duration pairs.
        For example:
        {'notes': [{'duration': 952.381 , 'frequency': 1396.8},
                   {'duration': 178.571,  'frequency': 1661.2},
                   {'duration': 1904.762, 'frequency': 0},
                   {'duration': 952.381,  'frequency': 1975.6}],
         'title': 'Example ringtone'}
    """
    rt = rtttl_str.split("=")
    pp = -1
    try:
     pp = rt[3].find(":")
    except:
     return {'title':False,'notes':False}
    if pp==-1:
     rt[3] = rt[3].replace(",",":",1)
     rtttl_str = rt[0]+"="+rt[1]+"="+rt[2]+"="+rt[3]
    rtttl_parts = rtttl_str.split(':')
    if len(rtttl_parts) != 3:
     return {'title':False,'notes':False}
    if len(rtttl_parts[2]) == 0:
     return {'title':False,'notes':False}
    defaults = parse_defaults(remove_whitespaces(rtttl_parts[1]))
    parsed_notes = parse_data(remove_whitespaces(rtttl_parts[2]).lower(), strict_note_syntax)
    converted_notes = [convert_note(note, defaults) for note in parsed_notes]
    return {'title': rtttl_parts[0], 'notes': converted_notes}

def parse_defaults(defaults_str):
    if defaults_str == '':
        return {'duration': 4, 'octave': 6, 'bpm': 63}
    try:
        if re.match(r'^(d=\d{1,2},o=\d,b=\d{1,3})?$', defaults_str):
            defaults = dict([d.split('=') for d in defaults_str.split(',')])
            parsed_defaults = {
                'duration': parse_duration(defaults['d']),
                'octave': parse_octave(defaults['o']),
                'bpm': parse_bpm(defaults['b'])
                }
        else:
         return {'duration': 4, 'octave': 6, 'bpm': 63}
    except InvalidElementError as element:
         return {'duration': 4, 'octave': 6, 'bpm': 63}
    return parsed_defaults

def parse_data(notes, strict_note_syntax):
    raw_notes = notes.split(',')
    if not strict_note_syntax:
        raw_notes = [correct_note_syntax(note) for note in raw_notes]
    return [parse_note(note) for note in raw_notes]

def correct_note_syntax(note):
    return re.sub(r'^(\d{0,2})([pbeh]|[cdfga]#?)(\.?)(\d*)$', r'\1\2\4\3', note)

def parse_note(note_str):
    try:
        elements = re.findall(r'^(\d{0,2})([pbeh]|[cdfga]#?)(\d?)(\.?)$', note_str)[0]
        funcs = (parse_duration, parse_pitch, parse_octave, has_dot)
        elements = [func(element) for func, element in zip(funcs, elements)]
    except:
        return False
    keys = ('duration', 'pitch', 'octave', 'dot')
    return dict(zip(keys, elements))

def parse_duration(duration):
    allowed_duration = [1, 2, 4, 8, 16, 32]
    return parse_int(duration, allowed_duration)

def parse_octave(octave):
    allowed_octave = [4, 5, 6, 7]
    return parse_int(octave, allowed_octave)

def parse_bpm(bpm):
    allowed_bpm = [
        25, 28, 31, 35, 40, 45, 50, 56, 63, 70, 80, 90,
        100, 112, 125, 140, 160, 180, 200, 225, 250, 285,
        320, 355, 400, 450, 500, 565, 635, 715, 800, 900]
    return parse_int(bpm, allowed_bpm)

def parse_pitch(pitch):
    allowed_pitch = ['p', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'h', 'b']
    return parse_element(pitch, allowed_pitch)

def parse_int(element, allowed):
    if element:
        return parse_element(int(element), allowed)
    return None

def parse_element(element, allowed):
    if element in allowed:
        return element
    else:
        return False

def has_dot(dot):
    return dot == '.'

def convert_note(note, defaults):
    octave_multiplier = {4: 1, 5: 2, 6: 4, 7: 8}
    pitch_frequencies = {
        'p':  0,
        'c':  261.6,
        'c#': 277.2,
        'd':  293.7,
        'd#': 311.1,
        'e':  329.6,
        'f':  349.2,
        'f#': 370.0,
        'g':  392.0,
        'g#': 415.3,
        'a':  440.0,
        'a#': 466.2,
        'b':  493.9,
        'h':  493.9
    }
    try:
     msec_per_beat = (60.0 / defaults['bpm']) * 4 * 1000
    except Exception as e:
     print("bpm",e,defaults)#debug
    frequency = pitch_frequencies[note['pitch']] * octave_multiplier[note['octave'] or defaults['octave']]
    if note['dot']:
        multiplier = 1.5
    else:
        multiplier = 1
    try:
     duration = round((msec_per_beat / (note['duration'] or defaults['duration'])) * multiplier, 3)
    except Exception as e:
     print("dur",e,defaults)#debug
    return {'frequency': frequency, 'duration': duration}
