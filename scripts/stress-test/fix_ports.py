import os
import glob

paths = glob.glob('scripts/stress-test/**/*.py', recursive=True)
for p in paths:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content.replace('http://localhost', 'http://localhost')
    new_content = new_content.replace('check_port("localhost", 80', 'check_port("localhost", 80')

    if new_content != content:
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print(f"Updated {p}")
