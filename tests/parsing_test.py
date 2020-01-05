import unittest
from pathlib import Path

from ruamel.yaml.comments import CommentedMap

from gryml.cli import init_parser
from gryml.core import dispatch, load, process


class ParsingTest(unittest.TestCase):

    def setUp(self):
        self.parser = init_parser()
        self.path = Path(__file__).parent.resolve()

        self.values = {
            'api-version': {
                'deployment': 'apps/v1'
            },
            'name': 'custom-name',
            'replicas': 2,
            'service-account-name': 'custom-service-account',
            'image': 'custom-image',
            'tag': 'latest',
            'env': {
                'common': [
                    {
                        'name': "COMMON_GREETING",
                        'value': "Common hello"
                    },
                    {
                        'name': "DEMO_GREETING",
                        'value': "Hello from the custom environment"
                    }
                ]
            }
        }

    def test_some_path(self):
        some_path = 'some_path'
        parsed = self.parser.parse_args([some_path])
        self.assertEqual(parsed.path, some_path)

    def test_negative_path_not_found(self):
        some_path = 'some_path'
        parsed = self.parser.parse_args([some_path])

        with self.assertRaises(FileNotFoundError):
            dispatch(parsed)

    def test_path_found_file(self):
        loaded = load('fixtures/simple/deployment.gryml.yml')
        for _, it in loaded:
            self.assertIsInstance(it, CommentedMap)

    def test_path_found_folder(self):
        loaded = load('fixtures/simple')
        for _, it in loaded:
            self.assertIsInstance(it, CommentedMap)

    def test_simple_comment_processing(self):

        _, it = next(load('fixtures/simple/deployment.gryml.yml'))
        process(it, self.values)

        self.assertIsInstance(it, CommentedMap)
        self.assertEqual(it['apiVersion'], self.values['api-version']['deployment'])

    def test_nested_map_comment_processing(self):

        _, it = next(load('fixtures/simple/deployment.gryml.yml'))
        process(it, self.values)
        self.assertEqual(it['metadata']['name'], self.values['name'])
        self.assertEqual(it['spec']['replicas'], self.values['replicas'])
        self.assertEqual(it['spec']['selector']['matchLabels']['application'], self.values['name'])

    def test_complex_string_comment_processing(self):

        _, it = next(load('fixtures/complex/complex.deployment.gryml.yml'))
        process(it, self.values)

        self.assertEqual(f"prefix-{self.values['name']}-suffix", it['metadata']['name'])

    def test_nested_list_append_comment_processing(self):

        _, it = next(load('fixtures/complex/complex.deployment.gryml.yml'))
        process(it, self.values)

        env = it['spec']['template']['spec']['containers'][1]['env']

        self.assertEqual(3, len(env))

        self.assertEqual(env[0]['name'], "DEMO_FAREWELL")
        self.assertEqual(env[0]['value'], "Such a sweet sorrow")

        self.assertEqual(env[1]['name'], "COMMON_GREETING")
        self.assertEqual(env[1]['value'], "Common hello")

        self.assertEqual(env[2]['name'], "DEMO_GREETING")
        self.assertEqual(env[2]['value'], "Hello from the custom environment")

    def test_nested_list_merge_using_comment_processing(self):

        _, it = next(load('fixtures/complex/complex.deployment.gryml.yml'))
        process(it, self.values)

        env = it['spec']['template']['spec']['containers'][0]['env']

        self.assertEqual(3, len(env))

        self.assertEqual(env[0]['name'], "DEMO_GREETING")
        self.assertEqual(env[0]['value'], "Hello from the custom environment")

        self.assertEqual(env[1]['name'], "DEMO_FAREWELL")
        self.assertEqual(env[1]['value'], "Such a sweet sorrow")

        self.assertEqual(env[2]['name'], "COMMON_GREETING")
        self.assertEqual(env[2]['value'], "Common hello")

    def test_nested_list_complex_comment_processing(self):

        _, it = next(load('fixtures/complex/complex.deployment.gryml.yml'))
        process(it, self.values)

        image = it['spec']['template']['spec']['containers'][0]['image']

        self.assertEqual(f"{self.values['image']}:{self.values['tag']}", image)

    def test_example_deployment_whole(self):

        _, it = next(load('fixtures/complex/example.deployment.gryml.yml'))
        process(it, self.values)
