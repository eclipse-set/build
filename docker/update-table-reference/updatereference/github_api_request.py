from typing import Literal
from requests import request, Response
import urllib.parse
from updatereference.constant import CONSTANT
import time
from io import BytesIO
from datetime import datetime, timezone

def get_artifact(pr_number: str, artifact_name: str):
    last_run = get_last_run(pr_number)
    target_artifact_name = artifact_name.format(last_run["run_number"])
    get_run_artifacts_response = github_api_request(
        method="get",
        access_path=f"actions/runs/{last_run["id"]}/artifacts"
    )
    if get_run_artifacts_response.status_code != 200:
        raise SystemError(get_run_artifacts_response.json())
    for artifact in get_run_artifacts_response.json()["artifacts"]:
        if artifact and artifact["name"] == target_artifact_name:
            download_artifact_response = github_api_request(method="get", access_path=f"actions/artifacts/{artifact["id"]}/zip")
            if download_artifact_response.status_code != 200:
                raise SystemError(f"Can't download artifact with url {artifact["url"]}")
            return BytesIO(download_artifact_response.content)
    # In normal case the artifact will be storage in 1 day
    last_run_completed_at = datetime.fromisoformat(last_run["updated_at"])
    now = datetime.now(timezone.utc)
    if (now - last_run_completed_at).days < 1:
        return None
    re_run_workflows(last_run)
    return get_artifact(pr_number, artifact_name)


def get_last_run(pr_number: str):
    branch_name = get_head_branch_name(pr_number)
    get_workflow_run_response = github_api_request(
        method="get",
        access_path=f"actions/workflows/{CONSTANT.BUILD_SET_WORK_FLOW_ID}/runs",
        params={"branch": urllib.parse.quote(branch_name)},
    )
    if get_workflow_run_response.status_code != 200:
        raise SystemError(f"Can't get workflow runs of branch {branch_name}")
    runs_data = get_workflow_run_response.json()["workflow_runs"]
    last_build = max(runs_data, key=lambda run: run["run_number"])
    while last_build["status"] == "in_progress":
        time.sleep(20)
    return last_build


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
