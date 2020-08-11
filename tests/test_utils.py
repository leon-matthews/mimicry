
import decimal
import functools
from pprint import pprint as pp
from unittest import TestCase

from mimicry.utils import file_size, normalise, round_significant


class TestFileSize(TestCase):
    def test_decimal(self):
        """
        Decimal values should be handled properly.
        """
        size = decimal.Decimal('54100')
        self.assertEqual(file_size(size), '54kB')

    def test_invalid(self):
        with self.assertRaises(ValueError):
            file_size(-245)
        with self.assertRaises(ValueError):
            file_size('banana')

    def test_iso(self):
        data = (
            (0, '0B'),
            (1, '1B'),
            (21, '21B'),
            (321, '321B'),
            (4321, '4.3kB'),
            (54321, '54kB'),
            (654321, '650kB'),
            (7654321, '7.7MB'),
            (87654321, '88MB'),
            (987654321, '990MB'),
            (1987654321, '2.0GB'),
            (21987654321, '22GB'),
            (321987654321, '320GB'),
            (4321987654321, '4.3TB'),
            (54321987654321, '54TB'),
            (654321987654321, '650TB'),
            (7654321987654321, '7.7PB'),
            (87654321987654321, '88PB'),
            (987654321987654321, '990PB'),
            (1987654321987654321, '2.0EB'),
            (12987654321987654321, '13EB'),
            (123987654321987654321, '120EB'),
            (1234987654321987654321, '1.2ZB'),
            (12345987654321987654321, '12ZB'),
            (123456987654321987654321, '120ZB'),
            (1234567987654321987654321, '1.2YB'),
            (12345678987654321987654321, '12YB'),
            (123456789876543219876543210, '120YB'),
            (1234567898765432198765432100, '1,235YB'),
            (12345678987654321987654321000, '12,346YB'),
            (123456789876543219876543210000, '123,457YB'),
            (1234567898765432198765432100000, '1,234,568YB'),
        )
        for size, expected in data:
            self.assertEqual(file_size(size), expected)

    def test_traditional(self):
        data = (
            (0, '0B'),
            (1, '1B'),
            (21, '21B'),
            (321, '321B'),
            (4321, '4.2KiB'),
            (54321, '53KiB'),
            (654321, '640KiB'),
            (7654321, '7.3MiB'),
            (87654321, '84MiB'),
            (987654321, '940MiB'),
            (1987654321, '1.9GiB'),
            (21987654321, '20GiB'),
            (321987654321, '300GiB'),
            (4321987654321, '3.9TiB'),
            (54321987654321, '49TiB'),
            (654321987654321, '600TiB'),
            (7654321987654321, '6.8PiB'),
            (87654321987654321, '78PiB'),
            (987654321987654321, '880PiB'),
            (1987654321987654321, '1.7EiB'),
            (12987654321987654321, '11EiB'),
            (123987654321987654321, '110EiB'),
            (1234987654321987654321, '1.0ZiB'),
            (12345987654321987654321, '10ZiB'),
            (123456987654321987654321, '100ZiB'),
            (1234567987654321987654321, '1.0YiB'),
            (12345678987654321987654321, '10YiB'),
            (123456789876543219876543210, '100YiB'),
            (1234567898765432198765432100, '1,000YiB'),
            (12345678987654321987654321000, '10,212YiB'),
            (123456789876543219876543210000, '102,121YiB'),
            (1234567898765432198765432100000, '1,021,211YiB'),
        )
        for size, expected in data:
            self.assertEqual(file_size(size, traditional=True), expected)


class TestNormalise(TestCase):
    def test_normalise(self):
        strings = [
            ' ABC  ',
            '[season 1] Episode One',
        ]
        expected = [
            'abc',
            'season 1 episode one',
        ]
        normalised = [normalise(s) for s in strings]
        self.assertEqual(normalised, expected)


class TestRoundSignificant(TestCase):
    def test_1_significant_figure(self):
        """
        Round to one significant figure
        """
        rs = functools.partial(round_significant, digits=1)

        self.assertEqual(rs(0), 0)
        self.assertEqual(rs(0.0), 0)
        self.assertEqual(rs(1), 1)
        self.assertEqual(rs(-1), -1)
        self.assertEqual(rs(12), 10)
        self.assertEqual(rs(-12), -10)
        self.assertEqual(rs(153), 200)
        self.assertEqual(rs(-153), -200)
        self.assertEqual(rs(1234567890), 1000000000)
        self.assertEqual(rs(-1234567890), -1000000000)

        self.assertEqual(rs(10.12345), 10)
        self.assertEqual(rs(-10.12345), -10)
        self.assertEqual(rs(0.0012345), 0.001)
        self.assertEqual(rs(-0.0012345), -0.001)

    def test_2_significant_figures(self):
        """
        Round to two significant digits
        """
        rs = functools.partial(round_significant, digits=2)

        self.assertEqual(rs(0), 0)
        self.assertEqual(rs(1), 1)
        self.assertEqual(rs(12), 12)
        self.assertEqual(rs(123), 120)
        self.assertEqual(rs(1234567890), 1200000000)

        self.assertEqual(rs(-1), -1)
        self.assertEqual(rs(-12), -12)
        self.assertEqual(rs(-123), -120)
        self.assertEqual(rs(-1234567890), -1200000000)

        self.assertEqual(rs(0.0), 0)
        self.assertEqual(rs(0.0012345), 0.0012)
        self.assertEqual(rs(3.9000000000000004), 3.9)
        self.assertEqual(rs(4.321), 4.3)
        self.assertEqual(rs(4.991), 5.0)
        self.assertEqual(rs(45.12345), 45)

        self.assertEqual(rs(-0.0012345), -0.0012)
        self.assertEqual(rs(-3.9000000000000004), -3.9)
        self.assertEqual(rs(-4.321), -4.3)
        self.assertEqual(rs(-4.991), -5.0)
        self.assertEqual(rs(-45.12345), -45)

    def test_bad_number_of_significant_figures(self):
        # Zero significant digits
        message = "Must have more than zero significant digits"
        with self.assertRaisesRegex(ValueError, message):
            round_significant(1230, 0)

        # Non-numeric number of significant digits
        message = "invalid literal for int\(\) with base 10: 'sausage'"
        with self.assertRaisesRegex(ValueError, message):
            round_significant(1230, 'sausage')

    def test_bad_number(self):
        message = "could not convert string to float..."
        with self.assertRaisesRegex(ValueError, message):
            round_significant('watch', 3)
