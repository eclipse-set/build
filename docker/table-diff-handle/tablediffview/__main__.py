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
    if issue_number == "":
        raise SystemError(
            f"Pull Request/Issue number for branch: '{branch_name}' not found"
        )
    remove_old_comments(issue_number)
    if not os.path.exists(diff_dir) or not os.listdir(diff_dir):
        return

    diff_mds = create_diffs(diff_dir)
    for diff_md in diff_mds:
        with open(
            f"{diff_dir}/diff-md/{diff_md.test_file}_{diff_md.table}_diff.csv",
            "w",
            encoding="utf-8",
        ) as out:
            out.write(diff_md.md)
        create_issue_comment(diff_md.test_file, diff_md.table, diff_md.md, issue_number)


main()
