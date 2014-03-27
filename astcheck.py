import ast
import sys
PY3 = sys.version_info[0] >= 3

if PY3:
    def mkarg(name):
        return ast.arg(arg=name)
else:
    def mkarg(name):
        return ast.Name(id=name, ctx=ast.Param())

def format_path(path):
    formed = path[:1]
    for part in path[1:]:
        if isinstance(part, int):
            formed.append("[%d]" % part)
        else:
            formed.append("."+part)
    return "".join(formed)

class ASTMismatch(AssertionError):
    def __init__(self, path, got, expected):
        self.path = path
        self.expected = expected
        self.got = got

    def __str__(self):
        return ("Mismatch at {}.\n"
                "Found   : {}\n"
                "Expected: {}").format(format_path(self.path), self.got, self.expected)

class ASTNodeTypeMismatch(ASTMismatch):
    def __str__(self):
        return "At {}, found {} node instead of {}".format(format_path(self.path), 
                        type(self.got).__name__, type(self.expected).__name__)

class ASTNodeListMismatch(ASTMismatch):
    def __str__(self):
        return "At {}, found {} node(s) instead of {}".format(format_path(self.path),
                len(self.got), len(self.expected))

class ASTPlainListMismatch(ASTMismatch):
    def __str__(self):
        return ("At {}, lists differ.\n"
                "Found   : {}\n"
                "Expected: {}").format(format_path(self.path), self.got, self.expected)

class ASTPlainObjMismatch(ASTMismatch):
    def __str__(self):
        return "At {}, found {!r} instead of {!r}".format(format_path(self.path),
                    self.got, self.expected)

def assert_ast_like(sample, template, _path=None):
    if _path is None:
        _path = ['tree']
    if not isinstance(sample, type(template)):
        raise ASTNodeTypeMismatch(_path, sample, template)

    for name, template_field in ast.iter_fields(template):
        sample_field = getattr(sample, name)
        field_path = _path + [name]
        
        if isinstance(template_field, list):
            if template_field and isinstance(template_field[0], ast.AST):
                # List of nodes, e.g. function body
                if len(sample_field) != len(template_field):
                    raise ASTNodeListMismatch(field_path, sample_field, template_field)

                for i, (sample_node, template_node) in \
                        enumerate(zip(sample_field, template_field)):
                    assert_ast_like(sample_node, template_node, field_path+[i])
            
            else:
                # List of plain values, e.g. 'global' statement names
                if sample_field != template_field:
                    raise ASTPlainListMismatch(field_path, sample_field, template_field)
        
        elif isinstance(template_field, ast.AST):
            assert_ast_like(sample_field, template_field, field_path)
        
        else:
            # Single value, e.g. Name.id
            if sample_field != template_field:
                raise ASTPlainObjMismatch(field_path, sample_field, template_field)

def is_ast_like(sample, template):
    try:
        assert_ast_like(sample, template)
        return True
    except ASTMismatch:
        return False