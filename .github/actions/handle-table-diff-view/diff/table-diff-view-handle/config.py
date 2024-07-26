import os

# Configuration constants.
class Configuration:
    env_file = os.getenv('GITHUB_ENV')
    # Table header count
    TABLE_HEADER_COUNT = 5
    # Highlight color for new data
    NEW_DATA_COLOR = "red"
    # Highlight color for old data
    OLD_DATA_COLOR = "gold"
    # Github repository owner
    GITHUB_REPO_OWNER = "eclipse-set"
    # Github repository name
    GITHUB_REPO_NAME = "set"
    # Github Token
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    # Github api url
    GITHUB_API_URL = "https://api.github.com/repos"
    # Diff markdown header
    DIFF_MD_HEADER = "# Table difference view:"


CONFIG = Configuration()
