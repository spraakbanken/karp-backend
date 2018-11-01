import unittest
from karp.util import cool_case

class UtilTest(unittest.TestCase):

    def test_cool_case(self):
        assert "TeStInGtEsT" == cool_case("testingtest")
