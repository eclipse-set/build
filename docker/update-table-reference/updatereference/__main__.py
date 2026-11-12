import argparse
from updatereference.github_api_request import get_artifact, get_issue_info
from updatereference.constant import CONSTANT
import os
from zipfile import ZipFile
from io import BytesIO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issueNumber", required=True, type=str)
    parser.add_argument("--commentBody", required=True, type=str)
    issue_number = str(parser.parse_args().issueNumber)
    commentBody = str(parser.parse_args().commentBody)
    issue_info = get_issue_info(issue_number)
    if not issue_info or not issue_info.branch_name:
        raise SystemError("Can't find relevant pull request/branch")
    new_reference_zip = get_artifact(
        issue_info, CONSTANT.TABLE_REFERENCE_ARTIFACT_NAME_PATTERN
    )
    if not new_reference_zip:
        raise SystemError("Can't download the new reference artifact")
    table_to_update = commentBody.replace("/update-table-reference", "").strip()
    table_reference_dirs = collect_table_reference_dirs()
    update_table_reference(new_reference_zip, table_to_update, table_reference_dirs)


def update_table_reference(new_reference_zip, table_to_update: str = None, table_reference_dirs: list[str] = []):
    try:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as new_zip:
            with ZipFile(new_reference_zip) as zip_file:
                for zip_content in zip_file.filelist:
                    if zip_content.filename.endswith("current.csv") and (
                        not table_to_update
                        or table_to_update.lower() in zip_content.filename
                    ):
                        new_zip.writestr(
                            zip_content.filename.replace(
                                "current.csv", "reference.csv"
                            ),
                            zip_file.read(zip_content.filename),
                        )
                if table_to_update and not new_zip.filelist:
                    raise SystemError("The target table no need to update reference")
                for new_zip_content in new_zip.filelist:
                    for table_reference_dir in table_reference_dirs:
                        if os.path.exists(f"{table_reference_dir}/{new_zip_content.filename}"):
                            new_zip.extract(new_zip_content, table_reference_dir)
                            print(f"Update table reference: {new_zip_content.filename}")
    except:
        raise SystemError()


def collect_table_reference_dirs(table_reference_dir_list: list[str] = [], repo_path: str = None) -> list[str]:
    if not repo_path:
        repo_path = f"{CONSTANT.REPO_LOCAL_PATH}/{CONSTANT.OSGI_TEST_BUNDLES_PATH}"
    for sub_dir in os.listdir(repo_path):
        sub_dir_path = f"{repo_path}/{sub_dir}"
        if os.path.exists(sub_dir_path) and os.path.isdir(sub_dir_path):
            if sub_dir == CONSTANT.TABLE_REFERENCE_DIR_NAME:
                table_reference_dir_list.append(sub_dir_path)
            else:
                collect_table_reference_dirs(table_reference_dir_list, sub_dir_path)
    return table_reference_dir_list

main()
