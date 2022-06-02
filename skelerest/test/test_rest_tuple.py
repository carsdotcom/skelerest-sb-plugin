import unittest
from ..rest_tuple import RestTuple

class TestRestTuple(unittest.TestCase):

    def test_str_cast(self):
        rest_tuple = RestTuple("name", "test")

        self.assertEqual(rest_tuple.__str__(), "name test")
        self.assertEqual(str(rest_tuple), "name test")

if __name__ == '__main__':
    unittest.main()
