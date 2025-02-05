import re
import requests
from tablediffview.config import CONFIG
from functools import reduce
from requests import request, Response
from typing import Literal
import urllib.parse

GITHUB_API_ISSUE_URL = f"{CONFIG.GITHUB_API_URL}/{CONFIG.GITHUB_REPO}/issues"

ISSUE_NAME_REGEX = r"main|^release/\d*.\d*|^v\d*.\d*.\d*"
REQUEST_HEADER = {
    "Authorization": f"token {CONFIG.GITHUB_TOKEN}",
    "Content-Type": "application/vnd.github+json",
}


class requestargs:
    def __init__(self, branch_name: str, run_id: str, pr_number: str = None):
        self.branch_name = branch_name
        self.run_id = run_id
        self.pr_number = pr_number
        self.issue_title = self.__get_issue_title()

    def __get_issue_title(self):
        extract_issue_name = re.match(ISSUE_NAME_REGEX, self.branch_name)
        issue_title_pattern = "{0} - Tables different"
        if extract_issue_name:
            return issue_title_pattern.format(next(iter(extract_issue_name)))
        return issue_title_pattern.format(self.branch_name)


def get_issue_number(request_args: requestargs):
    get_issues_response = __github_api_resquest(
        method="get",
        access_path="issues",
        params={"labels": CONFIG.TABLE_DIFF_ISSUE_LABEL},
    )
    if get_issues_response.status_code != 200:
        raise SystemExit(get_issues_response.json())
    open_issues = get_issues_response.json()
    for issue in open_issues:
        if issue["title"] == request_args.issue_title:
            update_issue_body(
                issue["number"],
                __get_issue_body_content(request_args.run_id, request_args.pr_number),
            )
            return issue["number"]

    return create_new_issue(request_args)


def update_issue_body(issue_number: str, new_content: str):
    update_body_resposne = __github_api_resquest(
        method="patch",
        access_path=f"issues/{issue_number}",
        content={"body": new_content},
    )
    if update_body_resposne.status_code != 200:
        raise SystemError(f"Cant update issue body of issue#{issue_number}")


def create_new_issue(request_args: requestargs) -> str | None:
    create_issue_response = __github_api_resquest(
        method="post",
        access_path="issues",
        content={
            "title": request_args.issue_title,
            "body": __get_issue_body_content(
                run_id=request_args.run_id, pr_number=request_args.pr_number
            ),
            "labels": [CONFIG.TABLE_DIFF_ISSUE_LABEL],
        },
    )

    if create_issue_response.status_code == 201:
        print(f"Create issue {request_args.issue_title} successfully!")
        return create_issue_response.json()["number"]
    else:
        raise SystemError(create_issue_response.json())


def __get_issue_body_content(run_id: str, pr_number: str = None):
    link_to_pr = f"- Link to eclipse-set/set#{pr_number}\n" if pr_number else ""
    update_table_command = CONFIG.UPDATE_REFERENCE_COMMAND + " { table_shortcut }"

    update_command_text = f"- Table reference can update via by commenting:\n  - All table: `{CONFIG.UPDATE_REFERENCE_COMMAND}`\n - Single table: `{update_table_command}`.\n"
    get_run_response = __github_api_resquest(
        method="get", access_path=f"actions/runs/{run_id}"
    )
    if get_run_response.status_code != 200:
        raise SystemError(f"Can't find run with id: {run_id}")
    run_data = get_run_response.json()
    link_to_diff_artifact = f"- Download Diff Artifact at [run#{run_data['run_number']}]({run_data["html_url"]})"
    return "\n".join((link_to_pr, update_command_text, link_to_diff_artifact))


def create_issue_comment(
    test_file: str, table_name: str, diff_md: str, issue_number: str
):
    comment_content = CONFIG.ISSUE_COMMENT_PATTERN.format(
        test_file.upper(), table_name.capitalize(), diff_md
    )
    content_ln = reduce((lambda x, y: x + y), map(len, (comment_content).split()))
    if content_ln > CONFIG.GITHUB_COMMENT_MAX_CHARACTER:
        comment_content = CONFIG.ISSUE_COMMENT_PATTERN.format(
            test_file.upper(),
            table_name.capitalize(),
            (
                "The difference can't be presented because there are too many changes."
                "To see the different please download the diff-file artifact"
            ),
        )

    create_comment_response = __github_api_resquest(
        method="post",
        access_path=f"issues/{issue_number}/comments",
        content={"body": comment_content},
    )
    if create_comment_response.status_code == 201:
        print("Create comment successfully!")
        return create_comment_response.json()["id"]
    else:
        print(f"Failed to create comment: {create_comment_response.status_code}")
        raise SystemError(create_comment_response.json())


def remove_old_comments(issue_number: str):
    get_comments_response = __github_api_resquest(
        method="get", access_path=f"issues/{issue_number}/comments"
    )
    if get_comments_response.status_code != 200:
        raise ValueError(f"Not exsist Issue/PR with number {issue_number}")
    comment_pattern = re.compile((r"<h2>Table difference view: \w* - \w*<\/h2>"))
    comments = get_comments_response.json()
    for comment in comments:
        if comment and comment["id"]:
            comment_text = comment["body"] if isinstance(comment["body"], str) else None
            if comment_text and comment_pattern.findall(comment_text):
                delete_response = __github_api_resquest(
                    method="delete", access_path=f"issues/comments/{comment['id']}"
                )
                if delete_response.status_code != 204:
                    print(f"Delete comment with number: \"{comment['id']}\" failed")
                    raise SystemError(delete_response.json())


def close_diff_issues(branch_name: str):
    get_issues_response = __github_api_resquest(method="get", access_path="issues")
    if get_issues_response.status_code != 200:
        raise SystemError("Can't get issues of the repository")
    for issue in get_issues_response.json():
        if issue["title"] and issue["title"].startswith(branch_name):
            __close_issue_request(issue["number"])


def close_diff_issues_of_closed_pr(branch_name: str):
    if branch_name != "main":
        return
    get_issues_response = __github_api_resquest(method="get", access_path="issues")
    if get_issues_response.status_code != 200:
        raise SystemError("Can't get issues of the repository")
    for issue in get_issues_response.json():
        if issue["title"] and issue["title"].endswith(
            CONFIG.TABLE_DIFF_ISSUE_TITLE_TRAIL
        ):
            branch_name = (
                issue["title"].replace(CONFIG.TABLE_DIFF_ISSUE_TITLE_TRAIL, "").strip()
            )
            get_branch_response = requests.get(
                f"{CONFIG.GITHUB_API_URL}/{CONFIG.GITHUB_REPO}/branches/{branch_name}",
                headers=REQUEST_HEADER,
            )
            if get_branch_response.status_code == 200:
                continue
            __close_issue_request(issue["number"])


def __close_issue_request(issue_number: str):
    if not issue_number:
        raise SystemError("To close issue, issue number must gived")
    close_issue_response = __github_api_resquest(
        method="patch",
        access_path=f"issues/{issue_number}",
        content={"state": "closed"},
    )
    if close_issue_response.status_code != 200:
        raise SystemError(f"Can't close issue #{issue_number}")
    print(f"Close issues #{issue_number}")


def __github_api_resquest(
    method: Literal["get", "post", "delete", "patch"],
    access_path: str,
    content={},
    params={},
) -> Response:
    return request(
        method,
        f"{CONFIG.GITHUB_API_URL}/{CONFIG.GITHUB_REPO}/{urllib.parse.quote(access_path)}",
        headers={
            "Authorization": f"token {CONFIG.GITHUB_TOKEN}",
            "Content-Type": "application/vnd.github+json",
        },
        json=content,
        params=params,
    )
