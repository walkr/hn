import unittest
import oi

from hn import workers


class TestWorkers(unittest.TestCase):

    def test_init(self):
        p = oi.Program('test program', None)
        a = workers.HNWorker(p)
        b = workers.WatchWorker(p)
        c = workers.NotifyWorker(p)
        self.assertTrue(None not in [a, b, c])
