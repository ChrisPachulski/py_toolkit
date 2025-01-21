import os

def _get_env_path() -> str:
    """
    Returns the absolute path to:
        ~/Documents/py_toolkit/.env
    """
    home_dir = os.path.expanduser('~')
    env_dir = os.path.join(home_dir, 'Documents', 'py_toolkit')
    return os.path.join(env_dir, '.env')

