import unittest
import re

import ast
import astcheck
from astcheck import (assert_ast_like, is_ast_like, mkarg, format_path,
                      listmiddle, name_or_attr,
                     )

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

sample3_code = """
del a
del b
del c
del d
"""

sample3 = ast.parse(sample3_code)

template3 = ast.Module(body=[ast.Delete(targets=[ast.Name(id='a')])] \
                        + listmiddle() \
                        + [ast.Delete(targets=[ast.Name(id='d')])])

template3_too_few_nodes = ast.Module(
    body=[ast.Delete(targets=[ast.Name(id=n)]) for n in 'abcde'] + listmiddle()
)

template3_wrong_front = ast.Module(
    body=[ast.Delete(targets=[ast.Name(id='q')])] + listmiddle()
)

template3_wrong_back = ast.Module(
    body= listmiddle() + [ast.Delete(targets=[ast.Name(id='q')])]
)

template3_wrong_node_type = ast.Module(
    body=listmiddle() + [ast.Pass()]
)

class TestPartialNodeLists(unittest.TestCase):
    def test_matching(self):
        assert_ast_like(sample3, template3)
        assert is_ast_like(sample3, template3)
        assert isinstance(template3.body.front[0], ast.Delete)
        assert isinstance(template3.body.back[0], ast.Delete)

    def test_too_few_nodes(self):
        with self.assertRaises(astcheck.ASTNodeListMismatch) as raised:
            assert_ast_like(sample3, template3_too_few_nodes)

        assert raised.exception.path == ['tree', 'body', '<front>']

    def test_wrong_front(self):
        with self.assertRaises(astcheck.ASTPlainObjMismatch) as raised:
            assert_ast_like(sample3, template3_wrong_front)

        assert raised.exception.path[:3] == ['tree', 'body', 0]

    def test_wrong_back(self):
        with self.assertRaises(astcheck.ASTPlainObjMismatch) as raised:
            assert_ast_like(sample3, template3_wrong_back)

        assert raised.exception.path[:3] == ['tree', 'body', -1]

    def test_wrong_node_type(self):
        with self.assertRaises(astcheck.ASTNodeTypeMismatch) as raised:
            assert_ast_like(sample3, template3_wrong_node_type)

        assert raised.exception.path == ['tree', 'body', -1]

sample4_code = "a.b * c + 4"
sample4 = ast.parse(sample4_code, mode='eval')

template4 = ast.Expression(body=ast.BinOp(
    left=ast.BinOp(left=name_or_attr('b'), op=ast.Mult(), right=name_or_attr('c')),
    op = ast.Add(), right=ast.Num(n=4)
    )
)

template4_not_name_or_attr = ast.Expression(body=ast.BinOp(right=name_or_attr('x')))

template4_name_wrong = ast.Expression(body=ast.BinOp(
                            left=ast.BinOp(right=name_or_attr('d'))
))

template4_attr_wrong = ast.Expression(body=ast.BinOp(
                            left=ast.BinOp(left=name_or_attr('d'))
))

class TestNameOrAttr(unittest.TestCase):
    def test_name_or_attr_correct(self):
        assert_ast_like(sample4, template4)
        assert is_ast_like(sample4, template4)

    def test_not_name_or_attr(self):
        with self.assertRaises(astcheck.ASTNodeTypeMismatch) as raised:
            assert_ast_like(sample4, template4_not_name_or_attr)

        assert raised.exception.path == ['tree', 'body', 'right']

    def test_name_wrong(self):
        with self.assertRaises(astcheck.ASTPlainObjMismatch) as raised:
            assert_ast_like(sample4, template4_name_wrong)

        assert raised.exception.path == ['tree', 'body', 'left', 'right', 'id']

    def test_attr_wrong(self):
        with self.assertRaises(astcheck.ASTPlainObjMismatch) as raised:
            assert_ast_like(sample4, template4_attr_wrong)

        assert raised.exception.path == ['tree', 'body', 'left', 'left', 'attr']

number_sample_code = "9 - 4"
number_sample = ast.parse(number_sample_code, mode='eval')

def less_than_seven(node, path):
    if not isinstance(node, ast.Num):
        raise astcheck.ASTNodeTypeMismatch(path, node, ast.Num())
    if node.n >= 7:
        raise astcheck.ASTMismatch(path+['n'], node.n, '< 7')

number_template_ok = ast.Expression(body=ast.BinOp(left=ast.Num(n=9),
                                op=ast.Sub(), right=less_than_seven
))

number_template_wrong = ast.Expression(body=ast.BinOp(left=less_than_seven))

class TestCheckerFunction(unittest.TestCase):
    def test_lt_7(self):
        assert_ast_like(number_sample, number_template_ok)

    def test_lt_7_wrong(self):
        with self.assertRaisesRegexp(astcheck.ASTMismatch, "Expected: < 7") as raised:
            assert_ast_like(number_sample, number_template_wrong)

        assert raised.exception.path == ['tree', 'body', 'left', 'n']
