import argparse
import os
from tablediffview.create_diff_markdown import create_diffs
from tablediffview.github_api_handle import (
    get_issue_number,
    remove_old_comments,
    create_issue_comment,
)
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diffDir", required=True, type=str)
    parser.add_argument("--branchName", required=True, type=str)
    parser.add_argument("--prNumber", required=False, type=str)
    diff_dir = parser.parse_args().diffDir
    branch_name = parser.parse_args().branchName
    pr_number = parser.parse_args().prNumber
    issue_number = ""
    if pr_number:
        issue_number = pr_number
    else:
        issue_number = get_issue_number(branch_name)
    if not issue_number:
        raise SystemError(
            f"Pull Request/Issue number for branch: '{branch_name}' not found"
        )
    remove_old_comments(issue_number)
    if not os.path.exists(diff_dir) or not os.listdir(diff_dir):
        return

    diff_mds = create_diffs(diff_dir)
    diff_md_dir = f"{diff_dir}/diff-md"
    os.makedirs(diff_md_dir)
    for diff in diff_mds:
        with open(
            f"{diff_md_dir}/{diff.test_file}_{diff.table}_diff.csv",
            "w",
            encoding="utf-8",
        ) as out:
            out.write(diff.md)
        create_issue_comment(diff.test_file, diff.table, diff.md, issue_number)


main()
