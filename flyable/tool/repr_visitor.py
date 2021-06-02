import ast


class ReprVisitor(ast.NodeVisitor):
    """
    Internal class used to look at parser tree
    """

    def generic_visit(self, node):
        print(type(node).__name__)
        super().generic_visit(node)
