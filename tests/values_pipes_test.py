import unittest

from gryml.cli import init_parser
from gryml.core import load, process


class ValuesPipesTest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()
        self.values = {
            'api-version': {
                'deployment': 'apps/v1'
            },
            'application': {
                'name': 'app-name'*10,  # Very long name
                'role': 'MASTER',
                'version': 'app-version',
                'replicas': 1,
                'labels': {
                    'app': 'app-name1',
                },
                'service-account': 'demo',
                'priorityClassName': 'tooooolong'
            },
            'build': {
                'image': 'some/test',
                'tag': 'latest'
            }
        }

    def test_simple_pipe_length(self):
        _, it = next(load('fixtures/complex/pipes.deployment.gryml.yml'))
        process(it, self.values)
        self.assertEqual(64, len(it['metadata']['name']))

    def test_simple_pipe_limit(self):
        _, it = next(load('fixtures/complex/pipes.deployment.gryml.yml'))
        process(it, self.values)
        spec = it['spec']['template']['spec']
        self.assertEqual(4, len(spec['serviceAccountName']))
        self.assertEqual(5, len(spec['priorityClassName']))

    def test_complex_limit(self):
        _, it = next(load('fixtures/complex/pipes.deployment.gryml.yml'))
        process(it, self.values)
        container = it['spec']['template']['spec']['containers'][0]
        self.assertEqual('main-app-nameap-master-container', container['name'])
