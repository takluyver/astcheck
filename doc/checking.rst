Checking ASTs
=============

.. module:: astcheck

Start by defining a template, a partial AST to compare against. You can fill in
as many or as few fields as you want. For example, to check for assignment to
a variable ``a``, but ignore the value:

.. code-block:: python

    template = ast.Module(body=[
                    ast.Assign(targets=[ast.Name(id='a')])
                ])
    sample = ast.parse("a = 7")
    astcheck.assert_ast_like(sample, template)

astcheck provides some helpers for defining flexible templates; see
:doc:`templateutils`.

.. autofunction:: assert_ast_like
.. autofunction:: is_ast_like

.. note::
   The parameter order matters! Only fields present in ``template`` will be
   checked, so you can leave out bits of the code you don't care about. Normally,
   ``sample`` will be the result of the code you want to test, and ``template``
   will be defined in your test file.

.. _checkerfuncs:

Checker functions
-----------------

You may want to write more customised checks for part of the AST. To do so, you
can attach 'checker functions' to any part of the template tree. Checker
functions should accept two parameters: the node or value at the corresponding
part of the sample tree, and the path to that node—a list of strings and integers
representing the attribute and index access used to get there from the root of
the sample tree.

If the value passed is not acceptable, the checker function should raise one
of the exceptions described below. Otherwise, it should return with no exception.
The return value is ignored.

For instance, this will test for a number literal less than 7:

.. code-block:: python

    def less_than_seven(node, path):
        if not isinstance(node, ast.Num):
            raise astcheck.ASTNodeTypeMismatch(path, node, ast.Num())
        if node.n >= 7:
            raise astcheck.ASTMismatch(path+['n'], node.n, '< 7')

    template = ast.Expression(body=ast.BinOp(left=less_than_seven))
    sample = ast.parse('4+9', mode='eval')
    astcheck.assert_ast_like(sample, template)

There are a few checker functions available in astcheck—see :doc:`templateutils`.

Exceptions
----------

.. autoexception:: ASTMismatch
   :show-inheritance:

The following exceptions are raised by :func:`assert_ast_like`. They should
all produce useful error messages explaining which part of the AST differed and
how:

.. autoexception:: ASTNodeTypeMismatch
   :show-inheritance:

.. autoexception:: ASTNodeListMismatch
   :show-inheritance:

.. autoexception:: ASTPlainListMismatch
   :show-inheritance:

.. autoexception:: ASTPlainObjMismatch
   :show-inheritance:
