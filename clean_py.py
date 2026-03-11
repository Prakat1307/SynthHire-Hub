import os
import ast

def clean_docstrings_and_comments(source):
    parsed = ast.parse(source)
    for node in ast.walk(parsed):
        if hasattr(node, "body") and isinstance(node.body, list) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body.pop(0)

    try:
        return ast.unparse(parsed)
    except Exception:
        return source

def clean_backend(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if any(ignored in dirpath for ignored in ['__pycache__', '.venv', 'venv', '.git']):
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    cleaned = clean_docstrings_and_comments(source)
                    
                    if cleaned != source:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(cleaned)
                        print(f"Cleaned {file_path}")
                except Exception as e:
                    print(f"Failed to clean {file_path}: {e}")

if __name__ == '__main__':
    clean_backend(r"d:\SynthHire-Interview-Platform\backend")
