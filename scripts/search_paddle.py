import os
import sys

def search_files(directory, keyword):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if keyword in line:
                                print(f"{path}:{i+1}:{line.strip()}")
                except Exception:
                    pass

if __name__ == "__main__":
    search_files(sys.argv[1], sys.argv[2])
