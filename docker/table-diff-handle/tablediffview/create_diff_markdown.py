import csv
import html2text
import re
from tablediffview.config import CONFIG
from itertools import zip_longest
from os import listdir, path
from os.path import isfile
from tabulate import tabulate


class htmlcelldata:
    def __init__(self, text: str, align: str) -> None:
        self.text = text
        self.align = align


class diffmarkdown:
    def __init__(self, test_file: str, table: str, md: str) -> None:
        self.test_file = test_file
        self.table = table
        self.md = md


def create_diffs(diff_dir: str) -> list[diffmarkdown]:
    test_file_diffs = get_changed_test_files(diff_dir)
    csv_path_pattern = "{0}/{1}/{2}_{3}.csv"
    mds: list[diffmarkdown] = []
    for test_file, diff_tables in test_file_diffs.items():
        for table_name in diff_tables:
            print("Create diff view for: " + table_name)
            with open(
                csv_path_pattern.format(diff_dir, test_file, table_name, "current"),
                encoding="utf-8",
            ) as current:
                reference_csv_path = csv_path_pattern.format(
                    diff_dir, test_file, table_name, "reference"
                )
                reference = None
                if path.exists(reference_csv_path):
                    reference = open(
                        reference_csv_path,
                        encoding="utf-8",
                    )

                diff_md = tabulate(
                    create_diff_table(current, reference),
                    headers="firstrow",
                    tablefmt="github",
                )
                mds.append(diffmarkdown(test_file, table_name, diff_md))

    return mds


# Get the list of table, which haved changed
def get_changed_test_files(diff_dir: str) -> dict[str, set[str]]:
    result = {}
    csv_current_pattern = re.compile(".+_current.csv")
    for dir in listdir(diff_dir):
        tables = set()
        test_file_dir = f"{diff_dir}/{dir}"
        if not isfile(test_file_dir):
            for f in listdir(test_file_dir):
                if isfile(f"{test_file_dir}/{f}") and csv_current_pattern.match(f):
                    tables.add(str(f).replace("_current.csv", ""))
            result[f"{str(dir)}"] = tables
    return result


def create_diff_table(changed_list, reference_list):
    changed_list = list(csv.reader(changed_list, delimiter=";", skipinitialspace=True))
    reference_list = (
        list(csv.reader(reference_list, delimiter=";", skipinitialspace=True))
        if reference_list
        else [[]]
    )
    diff_table = []
    create_diff_rows(diff_table, changed_list, reference_list)
    return diff_table


def create_diff_rows(
    diff_table: list[list[str]],
    changed_list: list[list[str]],
    reference_list: list[list[str]],
):
    for changed_row, reference_row in zip_longest(changed_list, reference_list):
        # Skip csv header
        if (
            changed_row
            and reference_row
            and len(changed_row) < 2
            and len(reference_row) < 2
        ):
            continue
        diff_row = []

        # When one of compare row is empty
        if changed_row is None or reference_row is None:
            create_diff_cells(
                diff_row,
                [] if changed_row is None else changed_row,
                [] if reference_row is None else reference_row,
            )
            diff_table.append(diff_row)
            continue

        is_diff = create_diff_cells(diff_row, changed_row, reference_row)
        # Only changed row will be added to diff_table, expect header row.
        if (
            not reference_row
            or is_table_header_row(changed_row, reference_row)
            or is_diff
        ):
            diff_table.append(diff_row)


def is_table_header_row(changed_row: list[str], reference_row: list[str]) -> bool:
    changed_first_cell = next(iter(changed_row), None)
    reference_first_cell = next(iter(reference_row), None)
    # The first cell of table data row is always a number
    if changed_first_cell is None and reference_first_cell is None:
        return True
    return not changed_first_cell.isnumeric() and not reference_first_cell.isnumeric()


def create_diff_cells(
    diff_row: list[str], changed_row: list[str], reference_row: list[str]
) -> bool:
    is_diff = False
    for changed_cell, reference_cell in zip_longest(
        list(changed_row), list(reference_row)
    ):
        changed_data = parse_cell(changed_cell)
        refernece_data = parse_cell(reference_cell)
        if changed_cell == reference_cell:
            diff_row.append(changed_data.text)
        else:
            is_diff = True
            diff_row.append(set_content_color(changed_data, refernece_data))
    return is_diff


def parse_cell(cell: str | None) -> htmlcelldata | None:
    if cell is None:
        return cell
    parse = html2text.HTML2Text()
    parse.body_width = 0
    # Replace normal line break sytax with line break syntax in markdown
    cell_text = re.sub(r"(\r\n|\n|\r)", "<br>", parse.handle(cell))
    align = re.findall("text-align:(left|right|center)", cell)
    # Remove last line break and get fisrt aglin
    return htmlcelldata(re.sub("<br>$", "", cell_text), next(iter(align), None))


# The GitHub Markdown can't parse CSS, here will extract the content of the cell and use LaTeX syntax to highlight the differences.
# Otherwise the changed by alignment will be visualation as  X (align: old) / x (align: new)
def set_content_color(c_data: htmlcelldata | None, r_data: htmlcelldata | None) -> str:
    different_text_pattern = "${{\\color{{{0}}}{1}}}$"
    different_align_pattern = "{0} (align: ${{\\color{{{1}}}{2}}}$)"
    if r_data is None:
        return different_text_pattern.format(CONFIG.NEW_DATA_COLOR, c_data.text)
    if c_data is None:
        return different_text_pattern.format(CONFIG.OLD_DATA_COLOR, r_data.text)
    if c_data.text == r_data.text and c_data.align != r_data.align:
        return (
            different_align_pattern.format(
                r_data.text, CONFIG.OLD_DATA_COLOR, r_data.align
            )
            + " <br> "
            + different_align_pattern.format(
                c_data.text, CONFIG.NEW_DATA_COLOR, c_data.align
            )
        )
    return (
        different_text_pattern.format(CONFIG.OLD_DATA_COLOR, r_data.text)
        + " <br> "
        + different_text_pattern.format(CONFIG.NEW_DATA_COLOR, c_data.text)
    )
