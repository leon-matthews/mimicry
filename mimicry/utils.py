
import math
import re


def file_size(size: float, traditional: bool = False) -> str:
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
    for suffix in suffixes[multiple]:
        size /= multiple
        if size < multiple:
            size = round_significant(size, 2)
            size = int(size) if size >= 10 else size
            return '{:,}{}'.format(size, suffix)

    # Greater than 1000 Yottabytes!? That is a pile of 64GB MicroSD cards
    # as large as the Great Pyramid of Giza!  You're dreaming, but in the
    # interests of completeness...
    # http://en.wikipedia.org/wiki/Yottabyte
    return '{:,}{}'.format(int(round(size)), suffix)


def round_significant(number: float, digits: int = 2):
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


def normalise(string):
    cleaned = string.lower()
    cleaned = normalise.pattern.sub('', cleaned)
    return cleaned.strip()
normalise.pattern = re.compile(r'[^a-z0-9 ]+')
