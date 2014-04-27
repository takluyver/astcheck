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
