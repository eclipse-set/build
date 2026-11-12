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
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diffDirName", required=True, type=str)
    parser.add_argument("--parentDir", required=True, type=str)
    parser.add_argument("--branchName", required=True, type=str)
    parser.add_argument("--prNumber", required=False, type=str)
    parser.add_argument("--runId", required=True, type=str)
    diff_dir_name = parser.parse_args().diffDirName
    parent_dir = parser.parse_args().parentDir
    branch_name = parser.parse_args().branchName
    pr_number = parser.parse_args().prNumber
    run_id = parser.parse_args().runId
    request_args = requestargs(branch_name, run_id, pr_number)
    close_diff_issues_of_closed_pr(branch_name)
    diff_dir_list = collect_diff_dir(parent_dir, diff_dir_name)

    if not diff_dir_list:
        close_diff_issues(branch_name)
        return
    issue_number = get_issue_number(request_args)
    if not issue_number:
        raise SystemError(
            f"Pull Request/Issue number for branch: '{branch_name}' not found"
        )

    remove_old_comments(issue_number)
    diff_mds = []
    diff_md_dir = f"{parent_dir}/diff-md"
    if not os.path.exists(diff_md_dir):
        os.makedirs(diff_md_dir)
    
    for diff_dir in diff_dir_list:
        for child in os.listdir(diff_dir):
            shutil.copytree(f"{diff_dir}/{child}", f"{diff_md_dir}/{child}", dirs_exist_ok=True)
        diff_mds.extend(create_diffs(diff_dir))
   
    for diff in diff_mds:
        subDir = f"{diff_md_dir}/{diff.test_file}"
        if not os.path.exists(subDir):
            os.makedirs(subDir)
        with open(
            f"{subDir}/{diff.table}_diff.md",
            "w",
            encoding="utf-8",
        ) as out:
            out.write(diff.md)
        create_issue_comment(diff.test_file, diff.table, diff.md, issue_number)

def collect_diff_dir(parent_dir: str, diff_dir_name: str, diff_dir_list: list[str] = []) -> list[str]:
    if not os.path.exists(parent_dir) or not os.path.isdir(parent_dir) or not os.listdir(parent_dir):
        return []
    for sub_dir in os.listdir(parent_dir):
        sub_dir_path = f"{parent_dir}/{sub_dir}"
        if os.path.exists(sub_dir_path) and os.path.isdir(sub_dir_path) and os.listdir(sub_dir_path):
            if sub_dir == diff_dir_name:
                diff_dir_list.append(sub_dir_path)
            else:
                collect_diff_dir(sub_dir_path, diff_dir_name, diff_dir_list)
    return diff_dir_list

main()
