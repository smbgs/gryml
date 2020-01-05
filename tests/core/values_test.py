import unittest
from pathlib import Path

from gryml.core import Gryml


class ParsingTest(unittest.TestCase):

    def setUp(self):
        self.gryml = Gryml()
        self.path = Path(__file__).parent.resolve()

    def test_value_processing(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, mutable=True)

        self.gryml.print(values)

        # TODO: asserts

    def test_load_before(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        values = self.gryml.load_values(values_file, process=True, load_nested=True, mutable=True)
        self.gryml.print(values)

        # TODO: asserts

    def test_auto_load(self):
        values_file = self.path / '../fixtures/core/values.yaml'
        self.gryml.load_values(values_file, process=True, load_nested=True, mutable=True, load_sources=True)
        self.gryml.output.seek(0)
        print(self.gryml.output.read())

        # TODO: asserts
