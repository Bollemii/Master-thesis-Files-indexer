import re

def space_between_word(text):
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return result[0].upper() + result[1:].lower()