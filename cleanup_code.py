import os
import re
import ast

def strip_python_comments(source):
    # Remove docstrings using AST, then remove # comments
    try:
        parsed = ast.parse(source)
        for node in ast.walk(parsed):
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
                continue
            if not len(node.body):
                continue
            if not isinstance(node.body[0], ast.Expr):
                continue
            if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
                continue
            node.body[0] = ast.Pass()
        import astor
        source = astor.to_source(parsed)
    except:
        pass
    
    # regex for comments
    source = re.sub(r'(?m)^ *#.*\n?', '', source)
    return source

def strip_js_comments(source):
    # Basic regex to remove /* */ and // 
    # Warning: might catch // in strings, but good enough for a rough sweep
    source = re.sub(r'/\*[\s\S]*?\*/', '', source)
    source = re.sub(r'//.*', '', source)
    return source

def clean_directory(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if 'node_modules' in root or '.git' in root or '.next' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                if file.endswith('.py'):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    cleaned = strip_python_comments(content)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(cleaned)
                    print(f"Cleaned {path}")
                elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    cleaned = strip_js_comments(content)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(cleaned)
                    print(f"Cleaned {path}")
            except Exception as e:
                print(f"Failed on {path}: {e}")

if __name__ == "__main__":
    print("Starting cleanup of backend...")
    clean_directory(r"d:\SynthHire-Interview-Platform\backend")
    print("Starting cleanup of frontend...")
    clean_directory(r"d:\SynthHire-Interview-Platform\frontend")
    print("Done!")
