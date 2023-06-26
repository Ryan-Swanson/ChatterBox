from django import template
from email.header import decode_header
import re

register = template.Library()


@register.filter(name='proper_case')
def proper_case(value):
    return value.title()

@register.filter(name='decode_subject')
def decode_subject(subject):
    if subject is None:
        return ''

    decoded_subject_parts = []
    for text, encoding in decode_header(subject):
        if isinstance(text, bytes):
            try:
                decoded_subject_parts.append(text.decode(encoding or 'utf8', errors='replace'))
            except (UnicodeDecodeError, LookupError):
                decoded_subject_parts.append(text.decode('utf8', errors='replace'))
        else:
            decoded_subject_parts.append(text)
    return ' '.join(decoded_subject_parts)

@register.filter(name='test')
def test(value):
    return value['Message-ID']

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='parse_email_address')
def parse_email_address(value):
    email_regex = r'[\w\.-]+@[\w\.-]+'
    match = re.search(email_regex, value)
    if match:
        return match.group(0)
    return ''
