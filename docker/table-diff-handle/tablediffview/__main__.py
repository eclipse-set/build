import argparse
import os
from tablediffview.create_diff_markdown import create_diffs
from tablediffview.github_api_handle import (
    get_issue_number,
    remove_old_comments,
    create_issue_comment,
    close_diff_issues,
    close_diff_issues_of_closed_pr,
    requestargs,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diffDir", required=True, type=str)
    parser.add_argument("--branchName", required=True, type=str)
    parser.add_argument("--prNumber", required=False, type=str)
    parser.add_argument("--runId", required=True, type=str)
    diff_dir = parser.parse_args().diffDir
    branch_name = parser.parse_args().branchName
    pr_number = parser.parse_args().prNumber
    run_id = parser.parse_args().runId
    request_args = requestargs(branch_name, run_id, pr_number)
    close_diff_issues_of_closed_pr(branch_name)
    if not os.path.exists(diff_dir) or not os.listdir(diff_dir):
        close_diff_issues(branch_name)
        return
    issue_number = get_issue_number(request_args)
    if not issue_number:
        raise SystemError(
            f"Pull Request/Issue number for branch: '{branch_name}' not found"
        )

    remove_old_comments(issue_number)

    diff_mds = create_diffs(diff_dir)
    diff_md_dir = f"{diff_dir}/diff-md"
    if not os.path.exists(diff_md_dir):
        os.makedirs(diff_md_dir)
    for diff in diff_mds:
        with open(
            f"{diff_md_dir}/{diff.test_file}_{diff.table}_diff.md",
            "w",
            encoding="utf-8",
        ) as out:
            out.write(diff.md)
        create_issue_comment(diff.test_file, diff.table, diff.md, issue_number)


main()
