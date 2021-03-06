import unittest
from pathlib import Path

from gryml.core import Gryml


class StrategyIfTest(unittest.TestCase):

    def setUp(self):
        self.gryml = Gryml()
        self.path = Path(__file__).parent.resolve()
        definition_file = self.path / '../fixtures/core/strategy_if.yaml'
        self.res = self.gryml.process_first_definition(definition_file)
        self.gryml.print(self.res)

    def test_basics(self):
        self.assertIn("simple_list", self.res)
        self.assertIn("dict_list", self.res)
        self.assertNotIn("bad_dict", self.res)

    def test_lists(self):
        simple_list = self.res.get("simple_list")

        self.assertIn("should_be_included_1", simple_list)
        self.assertIn("should_be_included_2", simple_list)
        self.assertIn("should_be_included_3", simple_list)
        self.assertIn("should_be_included_4", simple_list)
        self.assertIn("new", simple_list)
        self.assertIn("replacement", simple_list)

        self.assertNotIn("should_be_removed_1", simple_list)
        self.assertNotIn("should_be_removed_2", simple_list)
        self.assertNotIn("should_be_removed_3", simple_list)

        self.assertEqual(7, len(simple_list))
