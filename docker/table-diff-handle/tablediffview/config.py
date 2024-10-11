import os


# Configuration constants.
class Configuration:
    # Highlight color for new data
    NEW_DATA_COLOR = "red"
    # Highlight color for old data
    OLD_DATA_COLOR = "gold"
    # Github repository
    GITHUB_REPO = "eclipse-set/set"
    # Github Token
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    # Github api url
    GITHUB_API_URL = "https://api.github.com/repos"
    # Diff markdown header
    DIFF_MD_HEADER = "# Table difference view:"
    GITHUB_COMMENT_MAX_CHARACTER = 65536
    UPDATE_REFERENCE_COMMAND = "/update-table-reference"
    TABLE_DIFF_ISSUE_LABEL = "table_diff"
    TABLE_DIFF_ISSUE_TITLE_TRAIL = "- Tables different"


CONFIG = Configuration()
