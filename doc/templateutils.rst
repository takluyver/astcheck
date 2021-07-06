Template building utilities
===========================

.. currentmodule:: astcheck

astcheck includes some utilities for building AST templates to check against.

.. autofunction:: must_exist

.. autofunction:: must_not_exist

.. autoclass:: name_or_attr

.. autoclass:: single_assign

.. class:: listmiddle

   Helper to check only the beginning and/or end of a list. Instantiate it and
   add lists to it to match them at the start or the end. E.g. to test the final
   return statement of a function, while ignoring any other code in the function::
   
       template = ast.FunctionDef(name="myfunc", 
            body= astcheck.listmiddle()+[ast.Return(value=ast.Name(id="retval"))]
       )

       sample = ast.parse("""
       def myfunc():
           retval = do_something() * 7
           return retval
       """)

       astcheck.assert_ast_like(sample.body[0], template)
