import re

import sys
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML


class Gryml:

    pass
    # TODO: not needed? ruamel parseds comments in a weird way, a bit unusable
    # def extract_comments(self, target):
    #
    #     result_comments = []
    #
    #     def add_comments(comments: List[CommentToken]):
    #         for comment in comments:
    #             if comment.value:
    #                 for i, value in enumerate(comment.value.split('\n')):
    #                     if value:
    #                         result_comments.append((comment.end_mark.line + i - 1, value))
    #
    #     if hasattr(target, 'ca'):
    #         for ca_item in target.ca.items.values():
    #             for ct in ca_item:
    #                 if ct:
    #                     if isinstance(ct, list):
    #                         add_comments(ct)
    #                     else:
    #                         add_comments([ct])
    #
    #     if isinstance(target, list):
    #         for item in target:
    #             result_comments.extend(self.extract_comments(item))
    #
    #     if isinstance(target, dict):
    #         for key, item in target.items():
    #             result_comments.extend(self.extract_comments(item))
    #
    #     return result_comments

