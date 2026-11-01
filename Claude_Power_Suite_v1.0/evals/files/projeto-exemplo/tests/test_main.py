import unittest
from app.main import shorten


class ShortenTests(unittest.TestCase):
    def test_same_url_same_code(self):
        self.assertEqual(shorten("https://a.com"), shorten("https://a.com"))


if __name__ == "__main__":
    unittest.main()
