import csv
import html2text
import re
from config import CONFIG
from itertools import zip_longest
from os import listdir
from os.path import isfile
from tabulate import tabulate

class htmlcelldata:
    def __init__(self, text: str, align: str) -> None:
        self.text = text
        self.align = align
class diffmarkdown:
    def __init__(self, table: str, md: str) -> None:
        self.table = table
        self.md = md

def create_diffs(diff_dir: str) -> list[diffmarkdown]: 
    tables = get_diff_tables_name(diff_dir)
    csv_path_pattern = "{0}/{1}_{2}.csv"
    mds: list[diffmarkdown] = []
    for table_name in tables:
        print("Create diff view for: " + table_name)
        with open(
            csv_path_pattern.format(diff_dir, table_name, "current"),
            encoding="utf-8"
        ) as current:
            with open(
                csv_path_pattern.format(diff_dir, table_name, "reference"),
                encoding="utf-8",
            ) as reference:
                diff_md = tabulate(
                    create_diff_table(current, reference),
                    headers="firstrow",
                    tablefmt="github",
                )
                mds.append(diffmarkdown(table_name,diff_md))
    return mds


def get_diff_tables_name(diff_dir: str) -> set[str]:
    csv_files = [f for f in listdir(diff_dir) if isfile(diff_dir + "/" + f)]
    diff_tables_name = set()
    csv_current_pattern = re.compile(".+_current.csv")
    for file in csv_files:
        if csv_current_pattern.match(file):
            diff_tables_name.add(str(file).replace("_current.csv", ""))
        else:
            diff_tables_name.add(str(file).replace("_reference.csv", ""))
    return diff_tables_name


def create_diff_table(c_list, r_list):
    c_list = list(csv.reader(c_list, delimiter=";", skipinitialspace=True))
    r_list = list(csv.reader(r_list, delimiter=";", skipinitialspace=True))
    diff_table = []
    create_diff_rows(diff_table, c_list, r_list)
    return diff_table


def create_diff_rows(
    diff_table: list[list[str]], c_list: list[list[str]], r_list: list[list[str]]
):
    i = 0
    for c_row, r_row in zip_longest(c_list, r_list):
        diff_row = []
        if c_row is None:
            c_row = []
        if r_row is None:
            r_row = []
        is_diff = False
        for c_cell, r_cell in zip_longest(list(c_row), list(r_row)):
            c_data = parse_cell(c_cell)
            r_data = parse_cell(r_cell)
            if c_cell == r_cell:
                diff_row.append(c_data.text)
            else:
                is_diff = True
                diff_row.append(set_content_color(c_data, r_data))
        if i < 5 or is_diff:
            diff_table.append(diff_row)
        i += 1


def parse_cell(cell: str | None) -> htmlcelldata | None:
    if cell is None:
        return cell
    parse = html2text.HTML2Text()
    parse.body_width = 0
    cell_text = re.sub(r"(\r\n|\n|\r)", "<br>", parse.handle(cell))
    align = re.findall("text-align:(left|right|center)", cell)
    # Remove last line break and get fisrt aglin
    return htmlcelldata(re.sub("<br>$", "", cell_text), next(iter(align), None))


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
