
import math
import re


def file_size(size: int, traditional: bool = False) -> str:
    """
    Convert a file size in bytes to a easily human-parseable form, using only
    one or two significant figures.

    Raises ValueError if given size has an error in its... ah... value.

    size
        file size in bytes
    traditional
        Use traditional base-2 units, otherwise default to using
        'proper' SI multiples of 1000.
    """
    try:
        size = int(size)
    except (ValueError, TypeError):
        raise ValueError("Given file size '{}' not numeric.".format(size))

    if size < 0:
        raise ValueError("Given file size '{}' not positive".format(size))

    if size < 1000:
        return '{}B'.format(size)

    suffixes = {
        1000: ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        1024: ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    }

    multiple = 1024 if traditional else 1000
    value = float(size)
    for suffix in suffixes[multiple]:
        value /= multiple
        if value < multiple:
            value = round_significant(value, 2)
            value = int(value) if value >= 10 else value
            return '{:,}{}'.format(value, suffix)

    # Greater than 1000 Yottabytes!? That is a pile of 64GB MicroSD cards
    # as large as the Great Pyramid of Giza!  You're dreaming, but in the
    # interests of completeness...
    # http://en.wikipedia.org/wiki/Yottabyte
    return '{:,}{}'.format(int(round(value)), suffix)


def round_significant(number: float, digits: int = 2) -> float:
    """
    Round number to the given number of sigificant digits. eg::

        >>> round_significant(1235, digits=2)
        1200

    Returns: Number rounded to the given number of digits
    """
    digits = int(digits)
    if digits <= 0:
        raise ValueError("Must have more than zero significant digits")

    if not number:
        return 0
    number = float(number)
    magnitude = int(math.floor(math.log10(abs(number))))
    ndigits = digits - magnitude - 1
    return round(number, ndigits)


normalise_pattern = re.compile(r'[^a-z0-9 ]+')


def normalise(string: str) -> str:
    cleaned = string.lower()
    cleaned = normalise_pattern.sub('', cleaned)
    return cleaned.strip()

