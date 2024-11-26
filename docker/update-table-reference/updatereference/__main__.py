import argparse
from updatereference.github_api_request import get_artifact, get_reference_pr
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
    pr_number = get_reference_pr(issue_number)
    if not pr_number:
        raise SystemError("Invalid pull request number")
    new_reference_zip = get_artifact(
        pr_number, CONSTANT.TABLE_REFERENCE_ARTIFACT_NAME_PATTERN
    )
    if not new_reference_zip:
        raise SystemError("Can't download the new reference artifact")
    table_to_update = commentBody.replace("/update-table-reference", "").strip()
    update_table_reference(new_reference_zip, table_to_update)


def update_table_reference(new_reference_zip, table_to_update: str = None):
    reference_path = f"{CONSTANT.REPO_LOCAL_PATH}/{CONSTANT.SET_TABLE_REFERENCE_PATH}"
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
                for new_zip_content in new_zip.filelist:
                    if os.path.exists(reference_path):
                        new_zip.extract(new_zip_content, reference_path)
                        print(f"Update table reference: {new_zip_content.filename}")
    except:
        raise SystemError()


main()
