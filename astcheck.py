import ast
import sys
PY3 = sys.version_info[0] >= 3

__version__ = '0.2.1'

if PY3:
    def mkarg(name):
        return ast.arg(arg=name)
else:
    def mkarg(name):
        return ast.Name(id=name, ctx=ast.Param())

def name_or_attr(name):
    """Make a checker function for :class:`ast.Name` or :class:`ast.Attribute`.
    
    These are often used in similar ways - depending on how you do imports,
    objects will be referenced as names or as attributes of a module. By using
    this function to build your template, you can allow either.
    """
    def checker(node, path):
        if isinstance(node, ast.Name):
            if node.id != name:
                raise ASTPlainObjMismatch(path+['id'], node.id, name)
        elif isinstance(node, ast.Attribute):
            if node.attr != name:
                raise ASTPlainObjMismatch(path+['attr'], node.attr, name)
        else:
            raise ASTNodeTypeMismatch(path, node, "Name or Attribute")

    return checker

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
        expected = type(self.expected).__name__ if isinstance(ast.AST) else self.expected
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
        
        elif isinstance(template_field, listmiddle):
            if template_field.front:
                nfront = len(template_field.front)
                if len(sample_field) < nfront:
                    raise ASTNodeListMismatch(field_path+['<front>'],
                                              sample_field, template_field.front)
                _check_node_list(field_path, sample_field[:nfront], template_field.front)
            if template_field.back:
                nback = len(template_field.back)
                if len(sample_field) < nback:
                    raise ASTNodeListMismatch(field_path+['<back>'],
                                              sample_field, template_field.back)
                _check_node_list(field_path, sample_field[-nback:], template_field.back, -nback)

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