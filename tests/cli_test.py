import unittest
from argparse import Namespace

from gryml.cli import dispatch


class CLITest(unittest.TestCase):

    def setUp(self):
        # default self.namespace built from parser defaults
        self.namespace = Namespace()

    def test_dispatch_simple_path(self):
        setattr(self.namespace, 'path', 'fixtures/simple/deployment.gryml.yml')
        setattr(self.namespace, 'values_file', None)
        setattr(self.namespace, 'set', None)
        setattr(self.namespace, 'with_values', None)
        setattr(self.namespace, 'preserve_comments', True)
        setattr(self.namespace, 'echo', False)

        dispatch(self.namespace)

    def test_dispatch_complex_path(self):

        setattr(self.namespace, 'path', 'fixtures/complex/complex.deployment.gryml.yml')
        setattr(self.namespace, 'values_file', 'fixtures/values.gryml.yml')
        setattr(self.namespace, 'set', None)
        setattr(self.namespace, 'with_values', None)
        setattr(self.namespace, 'preserve_comments', True)
        setattr(self.namespace, 'echo', False)

        dispatch(self.namespace)
