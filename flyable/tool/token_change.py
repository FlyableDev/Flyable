"""
Module that includes functions to manipulate the AST
"""

import ast


def find_token_store(token):
    """
    Find the token that contains the store context
    Return : the parent, the token with all the values
    """

    class TokenStoreFinderVisitor(ast.NodeVisitor):
        """
        PreParse visitor is a class that visit all available nodes to find all possibles functions and classes so we can
        supply them to the Code Generator and the
        """

        def __init__(self):
            self.__found_token = None

        def generic_visit(self, node):
            if isinstance(node, list):
                for e in node:
                    super().visit(e)
            else:
                super().generic_visit(node)

        def visit(self, token):
            if hasattr(token, 'ctx') and isinstance(token.ctx, ast.Store):
                self.__found_token = token
            else:
                self.generic_visit(token)

        def get_found_token(self):
            return self.__found_token

    a = TokenStoreFinderVisitor()
    a.visit(token)
    return a.get_found_token()
