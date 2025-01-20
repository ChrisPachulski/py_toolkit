import os

def _get_env_path() -> str:
    """
    Returns the absolute path to:
        ~/Documents/py_toolkit/.env
    """
    home_dir = os.path.expanduser('~')
    env_dir = os.path.join(home_dir, 'Documents', 'py_toolkit')
    return os.path.join(env_dir, '.env')

def _update_env_file(key: str, value: str):
    """
    Updates or creates .env in the user's home ~/Documents/py_toolkit/.env folder.
    """
    env_path = _get_env_path()
    env_dir = os.path.dirname(env_path)

    if not os.path.exists(env_dir):
        os.makedirs(env_dir)

    if not os.path.exists(env_path):
        with open(env_path, "w") as new_env:
            new_env.write(f"{key}={value}\n")
        return

    # Read it, then rewrite
    with open(env_path, "r") as file:
        lines = file.readlines()

    key_found = False
    with open(env_path, "w") as file:
        for line in lines:
            if line.startswith(f"{key}="):
                file.write(f"{key}={value}\n")
                key_found = True
            else:
                file.write(line)
        if not key_found:
            file.write(f"{key}={value}\n")