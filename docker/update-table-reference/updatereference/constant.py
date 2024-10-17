import os


class Constanst:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_API_URL = "https://api.github.com/repos"

    SET_REPO = "truongquangsb/set"

    TABLE_REFERENCE_ARTIFACT_NAME_PATTERN = "table-csv-{}"
    BUILD_SET_WORK_FLOW_ID = 63604658
    REPO_LOCAL_PATH = os.environ.get("REPO_LOCAL_PATH", "")
    SET_TABLE_REFERENCE_PATH = (
        "java/bundles/org.eclipse.set.swtbot/test_res/table_reference"
    )
    TABLE_DIFF_ISSUE_TITLE_TRAIL = "- Tables different"


CONSTANT = Constanst()
