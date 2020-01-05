import unittest
from argparse import Namespace

from gryml.cli import init_parser, dispatch


class CLITest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()

    def test_dispatch(self):

        # default Namespace built from parser defaults
        namespace = Namespace()

        setattr(namespace, 'path', 'fixtures/simple/deployment.gryml.yml')
        setattr(namespace, 'values_file', None)
        setattr(namespace, 'set', None)
        setattr(namespace, 'with_values', None)
        setattr(namespace, 'preserve_comments', True)
        setattr(namespace, 'echo', True)

        dispatch(namespace)
