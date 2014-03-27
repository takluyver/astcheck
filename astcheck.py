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

def assert_ast_like(sample, template, _path=None):
    if _path is None:
        _path = ['tree']
    assert isinstance(sample, type(template)), "At {}, found {} node instead of {}"\
        .format(format_path(_path), type(sample).__name__, type(template).__name__)

    for name, template_field in ast.iter_fields(template):
        sample_field = getattr(sample, name)
        
        if isinstance(template_field, list):
            if isinstance(template_field[0], ast.AST):
                # List of nodes, e.g. function body
                assert len(sample_field) == len(template_field)
                for i, (sample_node, template_node) in \
                        enumerate(zip(sample_field, template_field)):
                    assert_ast_like(sample_node, template_node, _path+[name,i])
            
            else:
                # List of plain values, e.g. 'global' statement names
                assert sample_field == template_field, "Lists differ at {}:{}\n{}\n"\
                    .format(format_path(_path), sample_field, template_field)
        
        elif isinstance(template_field, ast.AST):
            assert_ast_like(sample_field, template_field, _path+[name])
        
        else:
            # Single value, e.g. Name.id
            assert sample_field == template_field, "At {}, found {!r} instead of {!r}"\
                    .format(format_path(_path), sample_field, template_field)