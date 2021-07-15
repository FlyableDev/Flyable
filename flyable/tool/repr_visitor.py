import ast


class ReprVisitor(ast.NodeVisitor):
    """
    Internal class used to look at parser tree
    """

    def generic_visit(self, node):
        print(type(node).__name__)
        if isinstance(node, list):
            for e in node:
                super().visit(e)
        else:
            super().generic_visit(node)
