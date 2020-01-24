import unittest
from io import StringIO
from pathlib import Path

from gryml.core import Gryml


class StrategyRepeatTest(unittest.TestCase):

    def setUp(self):
        self.gryml = Gryml()
        self.path = Path(__file__).parent.resolve()

        definition_file = self.path / '../fixtures/core/strategy_repeat.yaml'
        self.res = self.gryml.process_first_definition(definition_file)

    def test_basics(self):
        simple_list = self.res.get('simple_list')  # type: list

        self.assertEqual(1, simple_list.count("basic_value"))
        self.assertEqual(3, simple_list.count("repeated_value"))
        self.assertEqual(2, simple_list.count("repeated_value2"))
        self.assertEqual(1, simple_list.count("some_other_value"))

        self.assertEqual(0, simple_list.index("basic_value"))
        self.assertEqual(len(simple_list) - 1, simple_list.index("some_other_value"))

        dict_list = self.res.get('dict_list')  # type: list

        for i in range(3):
            self.assertEqual(f"name is {i + 1}", dict_list[i]['name'])
            self.assertEqual(i, dict_list[i]['value'])
            self.assertEqual(f"index-{i}-with-value-{i + 1}", dict_list[i]['extra'])

        self.assertFalse(any(it.get('name') == "false_name"  for it in dict_list))

    def test_conditional(self):
        conditional_inside = self.res.get('conditional_inside')  # type: list

        for i, it in enumerate(conditional_inside):
            if i % 2 == 0:
                self.assertIn("conditional", it)
            else:
                self.assertNotIn("conditional", it)

    def test_nested(self):
        nested_config = self.res.get('nested_config')  # type: list
        for i, it in enumerate(nested_config):
            self.assertEqual(f"root-{i}", it['name'])
            self.assertEqual(f"same", it['value'])

            for ii, iit in enumerate(it['nested']):
                self.assertEqual(f"nested-{i}-{ii}", iit['name'])

    def test_strings(self):
        strings = self.res.get('strings')  # type: list
        strings2 = self.res.get('strings2')  # type: list
        self.assertEqual(3, len(strings))
        self.assertEqual(3, len(strings2))

        self.gryml.print(self.res)
        self.gryml.output.seek(0)
        output = self.gryml.output.read()
        self.assertNotIn("bad", output)
        print(output)
