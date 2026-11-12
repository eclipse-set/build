import os
class Constanst:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_API_URL = "https://api.github.com/repos"
    SET_REPO = os.environ.get("GITHUB_REPO", "eclipse-set/set")
    TABLE_REFERENCE_ARTIFACT_NAME_PATTERN = "table-diff-files-{}"
    TEST_WORK_FLOW_ID = os.environ.get("TEST_WORKFLOW_ID", 240889456)
    REPO_LOCAL_PATH = os.environ.get("REPO_LOCAL_PATH", "")
    OSGI_TEST_BUNDLES_PATH = (
        "java/osgi-test"
    )
    TABLE_DIFF_ISSUE_TITLE_TRAIL = "- Tables different"
    TABLE_REFERENCE_DIR_NAME = "table_reference"
CONSTANT = Constanst()

