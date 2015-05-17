import unittest
import oi

from hn import commands


class TestCommands(unittest.TestCase):

    def setUp(self):
        self.p = oi.Program('test program', None)
        self.c = commands.Commands(self.p)

    def test_init(self):
        self.assertIsNotNone(self.c)
