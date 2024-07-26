import os

def is_system_file(file_name):
    """Determine if a file is a system file or not."""
    system_files = [
        'build', '.gradle', '.idea', 'gradlew', 'gradlew.bat', '.gitignore',
        '__pycache__', '.vscode', 'node_modules', 'env', 'venv', 'migrations', '.git'
    ]
    for sys_file in system_files:
        if file_name.startswith(sys_file):
            return True
    return False

def collect_python_code(src_directory, output_file):
    """Collect all Python source files from src_directory and write their contents to output_file."""
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(src_directory):
            # Skip system directories
            dirs[:] = [d for d in dirs if not is_system_file(d)]
            
            for file in files:
                if file.endswith(".py") and not is_system_file(file):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(f"# File: {file_path}\n\n")
                        outfile.write(infile.read())
                        outfile.write("\n\n")
                    print(f"Added: {file_path}")

def main():
    src_directory = r'C:\Users\m-tahsin\suams_project'  # Change this to your Django project path
    output_file = 'collected_python_code.txt'  # The name of the output text file

    collect_python_code(src_directory, output_file)
    print(f"All Python code has been collected into {output_file}")

if __name__ == "__main__":
    main()
