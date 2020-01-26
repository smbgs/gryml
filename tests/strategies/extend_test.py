import sys
import unittest
from pathlib import Path

from gryml.cli import init_parser
from gryml.core import Gryml


class ExtendStrategyTest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()
        self.path = Path(__file__).parent.resolve()
        self.gryml = Gryml()

    def test_simple(self):
        values_file = (self.path / '../../examples/extend-strategy/simple+extend.yml').absolute()
        values = self.gryml.load_values(values_file, {}, True, True, True, True)

        self.gryml.yaml.dump(values['derived'], sys.stdout)
        # TODO: compare
        #print(values['result'])

    def test_repeat(self):
        values_file = (self.path / '../../examples/extend-strategy/repeat+extend.yml').absolute()
        values = self.gryml.load_values(values_file, {}, True, True, True, True)

        self.gryml.yaml.dump(values['derived'], sys.stdout)

    def test_with(self):
        values_file = (self.path / '../../examples/extend-strategy/with+extend.yml').absolute()
        values = self.gryml.load_values(values_file, {}, True, True, True, True)

        self.gryml.yaml.dump(values['derived'], sys.stdout)
