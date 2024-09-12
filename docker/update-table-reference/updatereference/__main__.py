import argparse
from updatereference.github_api_request import get_artifact
from updatereference.constant import CONSTANT
import os
from zipfile import ZipFile
from io import BytesIO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prNumber", required=True, type=str)
    pr_number = str(parser.parse_args().prNumber)
    if not pr_number or not pr_number.isnumeric():
        raise SystemError("Invalid pull request number")
    new_reference_zip = get_artifact(
        pr_number, CONSTANT.TABLE_REFERENCE_ARTIFACT_NAME_PATTERN
    )
    if not new_reference_zip:
        raise SystemError("Can't download the new reference artifact")
    update_table_reference(new_reference_zip)


def update_table_reference(new_reference_zip):
    reference_path = f"{CONSTANT.REPO_LOCAL_PATH}/{CONSTANT.SET_TABLE_REFERENCE_PATH}"
    try:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as new_zip:
            with ZipFile(new_reference_zip) as zip_file:
                for zip_content in zip_file.filelist:
                    if zip_content.filename.endswith("current.csv"):
                        new_zip.writestr(
                            zip_content.filename.replace(
                                "current.csv", "reference.csv"
                            ),
                            zip_file.read(zip_content.filename),
                        )
                for new_zip_content in new_zip.filelist:
                    if os.path.exists(f"{reference_path}/{new_zip_content.filename}"):
                        new_zip.extract(new_zip_content, reference_path)
                        print(f"Update table reference: {new_zip_content.filename}")
    except:
        raise SystemError()


main()
