astcheck
========

astcheck compares Python Abstract Syntax Trees against a template. This is
useful for testing software that automatically generates or modifies Python code.

Installation::

    pip install astcheck

Example use:

.. code:: python

    import ast, astcheck

    template = ast.Module(body=[
        ast.FunctionDef(name='double', args=ast.arguments(args=[ast.arg(arg='a')])),
        ast.Assign(value=ast.Call(func=ast.Name(id='double')))
    ])

    sample = """
    def double(a):
        do_things()
        return a*2
    b = double(a)
    """

    astcheck.assert_ast_like(ast.parse(sample), template)

Only the parts specified in the template are checked. In this example, the code
inside the function, and the assignment target (``b``) could be anything.

For more details, see `the documentation <http://astcheck.readthedocs.org/en/latest/index.html>`_.
