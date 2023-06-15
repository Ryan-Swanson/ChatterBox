from django import template
from email.header import decode_header

register = template.Library()


@register.filter(name='proper_case')
def proper_case(value):
    return value.title()

@register.filter(name='decode_subject')
def decode_subject(subject):
    decoded_subject_parts = []
    for text, encoding in decode_header(subject):
        if isinstance(text, bytes):
            try:
                decoded_subject_parts.append(text.decode(encoding or 'utf-8', errors='replace'))
            except (UnicodeDecodeError, LookupError):
                decoded_subject_parts.append(text.decode('utf-8', errors='replace'))
        else:
            decoded_subject_parts.append(text)
    return ' '.join(decoded_subject_parts)