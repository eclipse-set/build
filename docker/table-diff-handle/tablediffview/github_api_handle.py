import re
import requests
from tablediffview.config import CONFIG
from functools import reduce

GITHUB_API_ISSUE_URL = f"{CONFIG.GITHUB_API_URL}/{CONFIG.GITHUB_REPO_OWNER}/{CONFIG.GITHUB_REPO_NAME}/issues"

ISSUE_NAME_REGEX = r"main|^release/\d*.\d*|^v\d*.\d*.\d*"
REQUEST_HEADER = {
    "Authorization": f"token {CONFIG.GITHUB_TOKEN}",
    "Content-Type": "application/vnd.github+json",
}


@staticmethod
def get_issue_number(branch_name: str):
    extract_issue_name = re.findall(ISSUE_NAME_REGEX, branch_name)
    issue_title = "{0} - Tables different"
    if extract_issue_name:
        issue_title = issue_title.format(next(iter(extract_issue_name)))
    else:
        issue_title = issue_title.format(branch_name)
    get_issues_response = requests.get(
        GITHUB_API_ISSUE_URL, headers=REQUEST_HEADER, json={"state": "open"}
    )
    if get_issues_response.status_code != 200:
        raise SystemExit(get_issues_response.json())
    open_issues = get_issues_response.json()
    for issue in open_issues:
        if issue["title"] == issue_title:
            return issue["number"]

    return create_new_issue(issue_title)


@staticmethod
def create_new_issue(issue_title: str, pr_number: str = None) -> str | None:
    create_issue_response = requests.post(
        GITHUB_API_ISSUE_URL,
        headers=REQUEST_HEADER,
        json={
            "title": issue_title,
            "body": f"- Link to eclipse-set/set#{pr_number} \n" if pr_number else "",
        },
    )

    if create_issue_response.status_code == 201:
        print(f"Create issue {issue_title} successfully!")
        return create_issue_response.json()["number"]
    else:
        raise SystemError(create_issue_response.json())


@staticmethod
def create_issue_comment(
    test_file: str, table_name: str, diff_md: str, issue_number: str
):
    url = f"{GITHUB_API_ISSUE_URL}/{issue_number}/comments"
    comment_header = f"{CONFIG.DIFF_MD_HEADER} {test_file.upper()} - {table_name.capitalize()} \n ### Table reference can update via by commenting `{CONFIG.UPDATE_REFERENCE_COMMAND}`."
    comment_content = f"{diff_md}"
    content_ln = reduce(
        (lambda x, y: x + y), map(len, (comment_header + comment_content).split())
    )
    if content_ln > CONFIG.GITHUB_COMMENT_MAX_CHARACTER:
        comment_content = f"The difference can't be presented because there are too many changes. To see the different please download the diff-file artifact"
    create_comment_reponse = requests.post(
        url,
        headers=REQUEST_HEADER,
        json={"body": f"{comment_header} \n {comment_content}"},
    )
    if create_comment_reponse.status_code == 201:
        print("Create comment successfully!")
    else:
        print(f"Failed to create comment: {create_comment_reponse.status_code}")
        raise SystemError(create_comment_reponse.json())


@staticmethod
def remove_old_comments(issue_number: str):
    get_comments_response = requests.get(
        f"{GITHUB_API_ISSUE_URL}/{issue_number}/comments", headers=REQUEST_HEADER
    )
    if get_comments_response.status_code != 200:
        raise ValueError(f"Not exsist Issue/PR with number {issue_number}")
    comments = get_comments_response.json()
    for comment in comments:
        if comment and comment["id"]:
            comment_text = comment["body"] if isinstance(comment["body"], str) else None
            if comment_text and comment_text.startswith(CONFIG.DIFF_MD_HEADER):
                delete_response = requests.delete(
                    f"{GITHUB_API_ISSUE_URL}/comments/{comment['id']}",
                    headers=REQUEST_HEADER,
                )
                if delete_response.status_code != 204:
                    print(f"Delete comment with number: \"{comment['id']}\" failed")
                    raise SystemError(delete_response.json())
