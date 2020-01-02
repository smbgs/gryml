import unittest

from gryml.cli import init_parser
from gryml.core import load_values


class ValuesNestingTest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()

    def test_simple_inheritance(self):

        values, sources = load_values('fixtures/derived.values.gryml.yml', {})

        self.assertEqual('example', values['application']['name'])
        self.assertEqual(123, values['application']['version'])

        # TODO: deep merge, list merge, etc
