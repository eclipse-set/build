
import re
import requests
from tablediffview.config import CONFIG

GITHUB_API_ISSUE_URL = (
    f"{CONFIG.GITHUB_API_URL}/{CONFIG.GITHUB_REPO_OWNER}/{CONFIG.GITHUB_REPO_NAME}/issues"
)

ISSUE_NAME_REGEX = r'main|^release/\d*.\d*|^v\d*.\d*.\d*'
REQUEST_HEADER = {
    "Authorization": f"token {CONFIG.GITHUB_TOKEN}",
    "Content-Type": "application/vnd.github+json"
}
@staticmethod
def get_issue_number(branch_name: str):
    extract_issue_name = re.findall(ISSUE_NAME_REGEX, branch_name)
    issue_title = "{0} - Tables different"
    if not extract_issue_name:
        issue_title = issue_title.format(next(iter(extract_issue_name)))
    else:
        issue_title = issue_title.format(branch_name)
    get_issues_response = requests.get(GITHUB_API_ISSUE_URL, headers=REQUEST_HEADER, json={"state": "open"})
    if get_issues_response.status_code != 200:
        raise SystemExit(get_issues_response.json())
    open_issues = get_issues_response.json()
    for issue in open_issues:
        if issue["title"] == issue_title:
            return issue["number"]
    
    return create_new_issue(issue_title)

@staticmethod
def create_new_issue(issue_title: str) -> str | None:
    create_issue_response = requests.post(
        GITHUB_API_ISSUE_URL,
        headers=REQUEST_HEADER,
        json={"title": issue_title},
    )
    
    if create_issue_response.status_code == 201:
        print(f"Create issue {issue_title} successfully!")
        create_issue_response.json()["number"]
    else:
        raise SystemError(create_issue_response.json()) 

@staticmethod
def create_issue_comment(table_name: str, diff_md: str, issue_number: str):
    url = f"{GITHUB_API_ISSUE_URL}/{issue_number}/comments"
    data = {"body": f"{CONFIG.DIFF_MD_HEADER} {table_name.capitalize()}\n {diff_md}"}
    create_comment_reponse = requests.post(
        url, headers=REQUEST_HEADER, json=data
    )
    if create_comment_reponse.status_code == 201:
        print("Create comment successfully!")
    else:
        print(f"Failed to create comment: {create_comment_reponse.status_code}")
        raise SystemError(create_comment_reponse.json())

@staticmethod
def remove_old_comments(issue_number: str):
    url = f'{GITHUB_API_ISSUE_URL}/comments'
    get_comments_response = requests.get(url, headers=REQUEST_HEADER)
    if get_comments_response.status_code != 200:
        raise ValueError(f"Not exsist Issue/PR with number {issue_number}")
    comments = get_comments_response.json()
    for comment in comments:
        if comment and comment["id"]:
            comment_text = comment["body"] if isinstance(comment["body"], str) else ''
            if comment_text.startswith(CONFIG.DIFF_MD_HEADER):
                delete_response = requests.delete(f'{url}/{comment["id"]}', headers=REQUEST_HEADER)
                if delete_response.status_code != 204:
                    print(f"Delete comment with number: \"{comment["id"]}\" failed")
                    raise SystemError(delete_response.json())
            
