import unittest
from pathlib import Path

from jinja2 import Undefined
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from gryml.cli import init_parser
from gryml.core2 import Gryml


class ParsingTest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()
        self.values = YAML().load(Path('../../experiments/grafana-gryml/values.yaml'))

        self.gryml = Gryml()

    def test_iterate_path(self):
        definition_file = Path('../fixtures/next/tag_placement.yaml')
        stream = self.gryml.iterate_path(Path(definition_file))
        directory, body, definition = next(stream)

        self.assertEqual(definition_file, directory)
        self.assertIsInstance(definition, CommentedMap)
        self.assertTrue(str(definition.ca.items['rules'][2].value).startswith("#[append]{rbac.extraClusterRoleRules}"))

        tags = self.gryml.extract_tags(body)
        result_values = self.gryml.process(definition, tags, definition.lc.line)

        self.assertIsInstance(result_values, dict)

    def test_expressions_raw(self):
        values_file = Path('../fixtures/next/values.yaml')
        self.gryml.load_values(values_file)
        self.assertIsInstance(self.gryml.eval('badValue'), Undefined)
        self.assertEqual("grafana", self.gryml.eval('chart.app'))
        self.assertEqual(2, self.gryml.eval('chart.labels.release + 1'))
        self.assertEqual(self.gryml.values['chart']['labels']['chart'] + "-suffix",
                         self.gryml.eval('chart.labels.chart + "-suffix"'))
        self.assertEqual(True, self.gryml.eval('not badValue'))

    def test_expressions_during_processing(self):
        definition_file = Path('../fixtures/next/tag_placement.yaml')
        values_file = Path('../fixtures/next/values.yaml')

        stream = self.gryml.iterate_path(Path(definition_file))
        self.gryml.load_values(values_file)

        directory, body, definition = next(stream)
        tags = self.gryml.extract_tags(body)

        result_values = self.gryml.process(definition, tags, definition.lc.line)
        self.gryml.print(result_values)
