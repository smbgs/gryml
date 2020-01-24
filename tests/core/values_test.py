import sys
import unittest
from pathlib import Path

from gryml.core import Gryml


class ValueLoadingTest(unittest.TestCase):

    def setUp(self):
        self.gryml = Gryml()
        self.path = Path(__file__).parent.resolve()

    def test_value_processing(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, mutable=True)

        # TODO: asserts, now it's just a smoke test
        self.assertIsNotNone(values)

    def test_load_before(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, load_nested=True, mutable=True)

        self.assertEqual("v2", values['apiVersion']['deployment'])

    def test_auto_process(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, load_nested=True, mutable=True, load_sources=True)

        all(self.gryml.process_sources())

        # TODO: asserts, now it's just a smoke test
        self.assertIsNotNone(values)
        self.assertGreater(self.gryml.output.tell(), 1)

    def test_merge(self):
        values_file = self.path / '../fixtures/core/strategy_merge.yaml'
        self.res = self.gryml.load_values(values_file, {}, True, True, True, True)
        print(self.res)
        self.assertEqual(2, len(self.res['data']['res']))
