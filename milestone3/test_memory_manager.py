import unittest
from engine.memory_manager import (
    simulate_fifo,
    simulate_lru,
    compare_algorithms,
    parse_trace
)


class TestMemoryManager(unittest.TestCase):

    def test_empty_trace(self):
        fifo = simulate_fifo([], capacity=3)
        lru = simulate_lru([], capacity=3)
        self.assertEqual(fifo["total_references"], 0)
        self.assertEqual(fifo["faults"], 0)
        self.assertEqual(fifo["fault_rate"], 0.0)
        self.assertEqual(lru["total_references"], 0)
        self.assertEqual(lru["evictions"], 0)

    def test_all_hits_after_initial_load(self):
        trace = [1, 2, 1, 2, 1, 2]
        fifo = simulate_fifo(trace, capacity=2)
        lru = simulate_lru(trace, capacity=2)
        self.assertEqual(fifo["faults"], 2)
        self.assertEqual(fifo["hits"], 4)
        self.assertEqual(fifo["evictions"], 0)
        self.assertEqual(lru["faults"], 2)
        self.assertEqual(lru["hits"], 4)
        self.assertEqual(lru["evictions"], 0)

    def test_fifo_vs_lru_eviction_behavior(self):
        trace = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
        res = compare_algorithms(trace, capacity=3)
        self.assertEqual(res["fifo"]["faults"], 15)
        self.assertEqual(res["fifo"]["evictions"], 12)
        self.assertEqual(res["lru"]["faults"], 12)
        self.assertEqual(res["lru"]["evictions"], 9)

    def test_different_frame_capacities(self):
        trace = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        cap3 = simulate_lru(trace, capacity=3)
        cap4 = simulate_lru(trace, capacity=4)
        self.assertGreater(cap3["faults"], cap4["faults"])

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            simulate_fifo([1, 2, 3], capacity=0)

    def test_parse_trace(self):
        self.assertEqual(parse_trace("1, 2, 3 4"), [1, 2, 3, 4])
        self.assertEqual(parse_trace(""), [])


if __name__ == "__main__":
    unittest.main()