import sys
import unittest
from pathlib import Path

from gryml.core import Gryml


class ParsingTest(unittest.TestCase):

    def setUp(self):
        self.gryml = Gryml(sys.stdout)
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
        self.assertFalse(values['gryml']['settings']['useSomeOutput'])
        self.assertTrue(values['gryml']['settings']['derivedSetting'])

        self.assertNotIn('some.yaml', values['gryml']['output'])
        self.assertIn('tag_placement.yaml', values['gryml']['output'])

    def test_auto_load(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, load_nested=True, mutable=True, load_sources=True)

        # TODO: asserts, now it's just a smoke test
        self.assertIsNotNone(values)
