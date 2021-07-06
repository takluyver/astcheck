"""Check Python ASTs against templates"""
import ast

__version__ = '0.3.0'

def mkarg(name):
    # This was defined for Python 2-3 compatibility, and now left in place to
    # avoid breaking code that uses it.
    return ast.arg(arg=name)

def must_exist(node, path):
    """Checker function for an item or list that must exist
    
    This matches any value except None and the empty list.
    
    For instance, to match for loops with an else clause::
    
        ast.For(orelse=astcheck.must_exist)
    """
    if (node is None) or (node == []):
        raise ASTMismatch(path, node, "non empty")

def must_not_exist(node, path):
    """Checker function for things that must not exist
    
    This accepts only None and the empty list.
    
    For instance, to check that a function has no decorators::
    
        ast.FunctionDef(decorator_list=astcheck.must_not_exist)
    """
    if (node is None) or (node == []):
        return
    raise ASTMismatch(path, node, "nothing")

class name_or_attr(object):
    """Checker for :class:`ast.Name` or :class:`ast.Attribute`
    
    These are often used in similar ways - depending on how you do imports,
    objects will be referenced as names or as attributes of a module. By using
    this function to build your template, you can allow either. For instance,
    this will match both ``f()`` and ``mod.f()``::
    
        ast.Call(func=astcheck.name_or_attr('f'))
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "astcheck.name_or_attr(%r)" % self.name

    def __call__(self, node, path):
        if isinstance(node, ast.Name):
            if node.id != self.name:
                raise ASTPlainObjMismatch(path+['id'], node.id, self.name)
        elif isinstance(node, ast.Attribute):
            if node.attr != self.name:
                raise ASTPlainObjMismatch(path+['attr'], node.attr, self.name)
        else:
            raise ASTNodeTypeMismatch(path, node, "Name or Attribute")

class single_assign:
    """Checker for :class:`ast.Assign` or :class:`ast.AnnAssign`

    :class:`~ast.Assign` is a plain assignment. This will match only assignments
    to a single target (``a = 1`` but not ``a = b = 1``).
    :class:`~ast.AnnAssign` is an annotated assignment, like ``a: int = 7``.
    *target* and *value* may be AST nodes to check, so this would match any
    assignment to ``a``::

        astcheck.single_assign(target=ast.Name(id='a'))

    Annotated assignments don't necessarily have a value: ``a: int`` is parsed
    as an :class:`~ast.AnnAssign` node. Use :func:`must_exist` to avoid matching
    these::

        astcheck.single_assign(target=ast.Name(id='a'), value=astcheck.must_exist)
    """
    def __init__(self, target=None, value=None):
        self.target = target
        self.value = value

    def __repr__(self):
        return "astcheck.single_assign(%r, %r)" % (self.target, self.value)

    def __call__(self, node, path):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                raise ASTNodeListMismatch(path+['targets'], node.targets, [self.target])
            if self.target is not None:
                assert_ast_like(node.targets[0], self.target, path + ['targets', 0])
            if self.value is not None:
                assert_ast_like(node.value, self.value, path + ['value'])
        elif hasattr(ast, 'AnnAssign') and isinstance(node, ast.AnnAssign):
            if self.target is not None:
                assert_ast_like(node.target, self.target, path + ['target'])
            if self.value is not None:
                assert_ast_like(node.value, self.value, path + ['value'])
        else:
            raise ASTNodeTypeMismatch(path, node, "Assign or AnnAssign")

class listmiddle(object):
    def __init__(self, front=None, back=None):
        super(listmiddle, self).__init__()
        self.front = front or []
        self.back = back or []

    def __radd__(self, other):
        if not isinstance(other, list):
            raise TypeError("Cannot add {} and listmiddle objects".format(type(other)))
        return listmiddle(other+self.front, self.back)

    def __add__(self, other):
        if not isinstance(other, list):
            raise TypeError("Cannot add listmiddle and {} objects".format(type(other)))
        return listmiddle(self.front, self.back + other)

    def __call__(self, sample_list, path):
        if not isinstance(sample_list, list):
            raise ASTNodeTypeMismatch(path, sample_list, list)

        if self.front:
            nfront = len(self.front)
            if len(sample_list) < nfront:
                raise ASTNodeListMismatch(path+['<front>'], sample_list, self.front)
            _check_node_list(path, sample_list[:nfront], self.front)
        if self.back:
            nback = len(self.back)
            if len(sample_list) < nback:
                raise ASTNodeListMismatch(path+['<back>'], sample_list, self.back)
            _check_node_list(path, sample_list[-nback:], self.back, -nback)

def format_path(path):
    formed = path[:1]
    for part in path[1:]:
        if isinstance(part, int):
            formed.append("[%d]" % part)
        else:
            formed.append("."+part)
    return "".join(formed)

class ASTMismatch(AssertionError):
    """Base exception for differing ASTs."""
    def __init__(self, path, got, expected):
        self.path = path
        self.expected = expected
        self.got = got

    def __str__(self):
        return ("Mismatch at {}.\n"
                "Found   : {}\n"
                "Expected: {}").format(format_path(self.path), self.got, self.expected)

class ASTNodeTypeMismatch(ASTMismatch):
    """An AST node was of the wrong type."""
    def __str__(self):
        expected = type(self.expected).__name__ if isinstance(self.expected, ast.AST) else self.expected
        return "At {}, found {} node instead of {}".format(format_path(self.path), 
                        type(self.got).__name__, expected)

class ASTNodeListMismatch(ASTMismatch):
    """A list of AST nodes had the wrong length."""
    def __str__(self):
        return "At {}, found {} node(s) instead of {}".format(format_path(self.path),
                len(self.got), len(self.expected))

class ASTPlainListMismatch(ASTMismatch):
    """A list of non-AST objects did not match.
    
    e.g. A :class:`ast.Global` node has a ``names`` list of plain strings
    """
    def __str__(self):
        return ("At {}, lists differ.\n"
                "Found   : {}\n"
                "Expected: {}").format(format_path(self.path), self.got, self.expected)

class ASTPlainObjMismatch(ASTMismatch):
    """A single value, such as a variable name, did not match."""
    def __str__(self):
        return "At {}, found {!r} instead of {!r}".format(format_path(self.path),
                    self.got, self.expected)

def _check_node_list(path, sample, template, start_enumerate=0):
    """Check a list of nodes, e.g. function body"""
    if len(sample) != len(template):
        raise ASTNodeListMismatch(path, sample, template)

    for i, (sample_node, template_node) in enumerate(zip(sample, template), start=start_enumerate):
        if callable(template_node):
            # Checker function inside a list
            template_node(sample_node, path+[i])
        else:
            assert_ast_like(sample_node, template_node, path+[i])

def assert_ast_like(sample, template, _path=None):
    """Check that the sample AST matches the template.
    
    Raises a suitable subclass of :exc:`ASTMismatch` if a difference is detected.
    
    The ``_path`` parameter is used for recursion; you shouldn't normally pass it.
    """
    if _path is None:
        _path = ['tree']

    if callable(template):
        # Checker function at the top level
        return template(sample, _path)

    if not isinstance(sample, type(template)):
        raise ASTNodeTypeMismatch(_path, sample, template)

    for name, template_field in ast.iter_fields(template):
        sample_field = getattr(sample, name)
        field_path = _path + [name]
        
        if isinstance(template_field, list):
            if template_field and (isinstance(template_field[0], ast.AST)
                                     or callable(template_field[0])):
                _check_node_list(field_path, sample_field, template_field)
            else:
                # List of plain values, e.g. 'global' statement names
                if sample_field != template_field:
                    raise ASTPlainListMismatch(field_path, sample_field, template_field)

        elif isinstance(template_field, ast.AST):
            assert_ast_like(sample_field, template_field, field_path)
        
        elif callable(template_field):
            # Checker function
            template_field(sample_field, field_path)

        else:
            # Single value, e.g. Name.id
            if sample_field != template_field:
                raise ASTPlainObjMismatch(field_path, sample_field, template_field)

def is_ast_like(sample, template):
    """Returns True if the sample AST matches the template."""
    try:
        assert_ast_like(sample, template)
        return True
    except ASTMismatch:
        return False
