import unittest
import re

import ast
import astcheck
from astcheck import assert_ast_like, is_ast_like, mkarg, format_path

sample1_code = """
def foobar(z, y, a, x, d):
    pass

b, subfunc, a, x = foobar(z, y, a, x, d)
"""
sample1 = ast.parse(sample1_code)

template1 = ast.Module(body=[
    ast.FunctionDef(name="foobar", args=ast.arguments(args=[
                mkarg(name) for name in ['z', 'y', 'a', 'x', 'd']
    ])),
    ast.Assign(targets=[ast.Tuple(ctx=ast.Store(), names=[
            ast.Name(id=id, ctx=ast.Store()) for id in ['b', 'subfunc', 'a', 'x']
            ])],
         value = ast.Call(func=ast.Name(id="foobar", ctx=ast.Load()),
                          args=[
              ast.Name(id=id, ctx=ast.Load()) for id in ['z', 'y', 'a', 'x', 'd']
            ])
        )
])

template1_wrongnode = ast.Module(body=[
    ast.FunctionDef(name="foobar", args=ast.arguments(args=[
                mkarg(name) for name in ['z', 'y', 'a', 'x', 'd']
    ])),
    ast.Pass()
])

template1_wrongnodelist = ast.Module(body=[
    ast.FunctionDef(name="foobar", args=ast.arguments(args=[
                mkarg(name) for name in ['z', 'y', 'a', 'x']
    ])),
    ast.Assign(targets=[ast.Tuple(ctx=ast.Store(), names=[
            ast.Name(id=id, ctx=ast.Store()) for id in ['b', 'subfunc', 'a', 'x']
            ])],
         value = ast.Call(func=ast.Name(id="foobar", ctx=ast.Load()),
                          args=[
              ast.Name(id=id, ctx=ast.Load()) for id in ['z', 'y', 'a', 'x', 'd']
            ])
        )
])

template1_wrongvalue = ast.Module(body=[
    ast.FunctionDef(name="foobar", args=ast.arguments(args=[
                mkarg(name) for name in ['z', 'y', 'a', 'x', 'e']
    ])),
    ast.Assign(targets=[ast.Tuple(ctx=ast.Store(), names=[
            ast.Name(id=id, ctx=ast.Store()) for id in ['b', 'subfunc', 'a', 'x']
            ])],
         value = ast.Call(func=ast.Name(id="foobar", ctx=ast.Load()),
                          args=[
              ast.Name(id=id, ctx=ast.Load()) for id in ['z', 'y', 'a', 'x', 'd']
            ])
        )
])

sample2_code = """
def foo():
  global x
"""

sample2 = ast.parse(sample2_code)

template2 = ast.Module(body=[
    ast.FunctionDef(name="foo", args=ast.arguments(args=[]), body=[
        ast.Global(names=['x'])
    ])
])

template2_wronglist = ast.Module(body=[
    ast.FunctionDef(name="foo", args=ast.arguments(args=[]), body=[
        ast.Global(names=['x', 'y'])
    ])
])

class AstCheckTests(unittest.TestCase):
    def test_matching(self):
        assert_ast_like(sample1, template1)
        assert is_ast_like(sample1, template1)
        assert_ast_like(sample2, template2)
        assert is_ast_like(sample2, template2)
    
    def test_wrongnode(self):
        with self.assertRaises(astcheck.ASTNodeTypeMismatch):
            assert_ast_like(sample1, template1_wrongnode)
        assert not is_ast_like(sample1, template1_wrongnode)

    def test_wrong_nodelist(self):
        with self.assertRaisesRegexp(astcheck.ASTNodeListMismatch, re.escape("5 node(s) instead of 4")):
            assert_ast_like(sample1, template1_wrongnodelist)
        assert not is_ast_like(sample1, template1_wrongnodelist)
    
    def test_wrong_plain_value(self):
        with self.assertRaisesRegexp(astcheck.ASTPlainObjMismatch, "'d' instead of 'e'"):
            assert_ast_like(sample1, template1_wrongvalue)
        assert not is_ast_like(sample1, template1_wrongvalue)
    
    def test_wrong_plain_list(self):
        with self.assertRaisesRegexp(astcheck.ASTPlainListMismatch, re.escape("Expected: ['x', 'y']")):
            assert_ast_like(sample2, template2_wronglist)
        assert not is_ast_like(sample2, template2_wronglist)

def test_format_path():
    assert format_path(['tree', 'body', 0, 'name']) == 'tree.body[0].name'
