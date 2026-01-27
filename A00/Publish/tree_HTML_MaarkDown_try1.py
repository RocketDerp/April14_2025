import subprocess
import os
import sys


def index_git_files(repo_path, extensions=['.md', '.html']):
    """
    Uses 'git ls-files' to list only tracked and non-ignored files,
    then filters them by extension.
    """
    try:
        # --cached: list tracked files
        # --others: list untracked files
        # --exclude-standard: respect .gitignore, .git/info/exclude, and global ignores
        # git -C . ls-files --cached --others --exclude-standard
        cmd = ['git', '-C', repo_path, 'ls-files', '--cached', '--exclude-standard']
        
        # Run command and capture output
        # print(f"{cmd}")
        # sys.exit(1)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        all_files = result.stdout.splitlines()
        
        # Filter files based on requested extensions
        indexed_files = {ext: [] for ext in extensions}
        for file_path in all_files:
            _, ext = os.path.splitext(file_path)
            if ext in extensions:
                indexed_files[ext].append(file_path)
        
        return indexed_files
    except subprocess.CalledProcessError as e:
        print(f"Error accessing Git repository: {e}")
        return {ext: [] for ext in extensions}


# Usage
repo_root = "." # Change this to your repo path if needed
files_index = index_git_files(repo_root)

print("Indexed Markdown Files:  ")
for path in files_index['.md']:
    print(f"- [{path}]({path})  ")

print("")
print("")

print("Indexed HTML Files:  ")
for path in files_index['.html']:
    print(f"- [{path}]({path})  ")
