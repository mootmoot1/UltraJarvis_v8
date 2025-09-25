import os


def repo_snapshot(max_chars: int = 80000) -> str:
    """Concatenate small files in the repository up to a maximum character limit."""
    file_extensions = [".py", ".md", ".toml", ".yml", ".json", ".ini"]
    repo_root = os.path.dirname(os.path.abspath(__file__))
    concatenated_content = ""

    for root, _, files in os.walk(repo_root):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if len(concatenated_content) + len(content) <= max_chars:
                        concatenated_content += content
                    else:
                        return concatenated_content
    return concatenated_content
