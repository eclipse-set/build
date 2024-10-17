import os


# Configuration constants.
class Configuration:
    # Highlight color for new data
    NEW_DATA_COLOR = "red"
    # Highlight color for old data
    OLD_DATA_COLOR = "gold"
    # Github repository
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "eclipse-set/set")
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
    # Pattern for issue comment
    # 0. Test file name
    # 1. Table name shortcut
    # 2. Diff table
    ISSUE_COMMENT_PATTERN = (
        "<details>\n"
        "<summary>\n"
        "<h2>Table difference view: {0} - {1}</h2>\n"
        "</summary>\n"
        "\n{2}\n"
        "</details>"
    )

    DIFF_TABLE_ARTIFACT_NAME_PREFIX = "table-diff-files"


CONFIG = Configuration()
