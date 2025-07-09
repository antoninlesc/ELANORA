import os

from dotenv import load_dotenv

DEV_ENV_FILE = ".env.dev"


def load_env() -> None:
    """Load environment variables from a specific .env file based on the environment."""
    # Absolute path to the root of the repository (where `env/` is located)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    env = os.getenv("ENVIRONMENT", "dev").lower()

    # Map environment names to file names
    env_file_map = {
        "dev": DEV_ENV_FILE,
        "dev.docker": ".env.dev.docker",
        "prod": ".env.prod",
        "server": ".env.server",
    }

    # Get the appropriate env file, default to .env.dev if ENVIRONMENT not recognized
    env_file = env_file_map.get(env, DEV_ENV_FILE)
    path_to_env = os.path.join(repo_root, "env", env_file)

    if os.path.exists(path_to_env):
        load_dotenv(path_to_env)
    else:
        # Fallback to .env.dev if the specified env file doesn't exist
        fallback_path = os.path.join(repo_root, "env", ".env.dev")
        if os.path.exists(fallback_path):
            load_dotenv(fallback_path)
