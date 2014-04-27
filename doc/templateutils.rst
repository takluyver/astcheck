Template building utilities
===========================

.. currentmodule:: astcheck

astcheck includes some utilities for building AST templates to care against.

.. function:: mkarg(name)

   Build an argument for a function definition. This returns a :class:`ast.arg`
   node in Python 3, and a :class:`ast.Name` node with ``ctx`` of
   :class:`ast.Param` in Python 2.

.. autofunction:: name_or_attr

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
