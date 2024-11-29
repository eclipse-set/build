from typing import Literal
from requests import request, Response
import urllib.parse
from updatereference.constant import CONSTANT
import time
from io import BytesIO
from datetime import datetime, timezone


class issueInfo:
    def __init__(self, issue_number: str, pr_number: str, branch_name: str):
        self.issue_number = issue_number
        self.pr_number = pr_number
        self.branch_name = branch_name


def get_issue_info(issue_number: str):
    if not issue_number:
        return None
    get_issue_reposne = github_api_request(
        method="get", access_path=f"issues/{issue_number}"
    )
    if get_issue_reposne.status_code != 200:
        raise SystemError(f"Can't get issues #{issue_number}")
    issue_tilte = get_issue_reposne.json()["title"]
    if not issue_tilte or not issue_tilte.endswith(
        CONSTANT.TABLE_DIFF_ISSUE_TITLE_TRAIL
    ):
        raise SystemError(f"Missing or Wrong title of talbe diff issue #{issue_number}")
    branch_name = issue_tilte.replace(CONSTANT.TABLE_DIFF_ISSUE_TITLE_TRAIL, "").strip()
    if branch_name == "main":
        return issueInfo(issue_number=issue_number, pr_number=None, branch_name="main")
    get_prs_response = github_api_request(method="get", access_path="pulls")
    if get_prs_response.status_code != 200:
        raise SystemError("Can't get pull request of repository")
    for pr in get_prs_response.json():
        if pr["head"]["ref"] == branch_name:
            return issueInfo(
                issue_number=issue_number,
                pr_number=pr["number"],
                branch_name=branch_name,
            )
    return None


def get_artifact(issue_info: issueInfo, artifact_name: str):
    last_run = get_last_run(issue_info)
    # Wait the build process
    while last_run["status"] == "in_progress":
        print(f"Wait build process: {datetime.now().ctime()}")
        time.sleep(120)
        last_run = get_last_run(issue_info, run_id=last_run["id"])

    target_artifact_name = artifact_name.format(last_run["run_number"])
    get_run_artifacts_response = github_api_request(
        method="get", access_path=f"actions/runs/{last_run['id']}/artifacts"
    )

    if get_run_artifacts_response.status_code != 200:
        raise SystemError(get_run_artifacts_response.json())

    print(
        f"Get artifact {target_artifact_name} from build number: {last_run['run_number']}, id: {last_run['id']}"
    )
    for artifact in get_run_artifacts_response.json()["artifacts"]:
        if (
            artifact
            and artifact["name"] == target_artifact_name
            and not artifact["expired"]
        ):
            download_artifact_response = github_api_request(
                method="get", access_path=f"actions/artifacts/{artifact['id']}/zip"
            )
            if download_artifact_response.status_code != 200:
                raise SystemError(f"Can't download artifact with url {artifact['url']}")
            return BytesIO(download_artifact_response.content)
    # In normal case the artifact will be storage in 1 day
    last_run_completed_at = datetime.fromisoformat(last_run["updated_at"])
    now = datetime.now(timezone.utc)
    if (now - last_run_completed_at).days < 1:
        return None
    re_run_workflows(last_run)

    return get_artifact(issue_info, artifact_name)


def get_last_run(issue_info: issueInfo, run_id: str = None):
    last_build = None
    if run_id:
        last_build = get_run(run_id)
    else:
        branch_name = issue_info.branch_name
        get_workflow_run_response = github_api_request(
            method="get",
            access_path=f"actions/workflows/{CONSTANT.BUILD_SET_WORK_FLOW_ID}/runs",
            params={"branch": urllib.parse.quote(branch_name)},
        )
        if get_workflow_run_response.status_code != 200:
            raise SystemError(f"Can't get workflow runs of branch {branch_name}")
        runs_data = get_workflow_run_response.json()["workflow_runs"]
        last_build = max(runs_data, key=lambda run: run["run_number"])
    if not last_build:
        raise SystemError(f"Can't get last build for branch: {issue_info.branch_name}")
    return last_build


def get_run(run_id: str):
    get_run_response = github_api_request(
        method="get", access_path=f"actions/runs/{run_id}"
    )
    if get_run_response.status_code != 200:
        print(f"Can't get run with id: {run_id}")
        raise SystemError(get_run_response.json())
    return get_run_response.json()


def get_head_branch_name(pr_number: str):
    get_pr_response = github_api_request(method="get", access_path=f"pulls/{pr_number}")
    if get_pr_response.status_code != 200:
        print(f"Can't get SET-PR#{pr_number}")
        raise SyntaxError(get_pr_response.json())
    return get_pr_response.json()["head"]["ref"]


def re_run_workflows(run_id: str):
    re_run_response = github_api_request(
        method="post", access_path=f"actions/runs/{run_id}/rerun"
    )
    if re_run_response.status_code != 201:
        raise SystemError(f"Can't rerun the run with id {run_id}")


def github_api_request(
    method: Literal["get", "post", "delete"], access_path: str, content={}, params={}
) -> Response:
    return request(
        method,
        f"{CONSTANT.GITHUB_API_URL}/{CONSTANT.SET_REPO}/{urllib.parse.quote(access_path)}",
        headers={
            "Authorization": f"token {CONSTANT.GITHUB_TOKEN}",
            "Content-Type": "application/vnd.github+json",
        },
        json=content,
        params=params,
    )
