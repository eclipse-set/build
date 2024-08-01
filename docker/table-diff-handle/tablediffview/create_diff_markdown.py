import csv
import html2text
import re
from tablediffview.config import CONFIG
from itertools import zip_longest
from os import listdir
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
    test_file_diffs = get_diff_tables_map(diff_dir)
    csv_path_pattern = "{0}/{1}/{2}_{3}.csv"
    mds: list[diffmarkdown] = []
    for test_file, diff_tables in test_file_diffs.items():
        for table_name in diff_tables:
            print("Create diff view for: " + table_name)
            with open(
                csv_path_pattern.format(diff_dir, test_file, table_name, "current"),
                encoding="utf-8"
            ) as current:
                with open(
                    csv_path_pattern.format(diff_dir, test_file, table_name, "reference"),
                    encoding="utf-8",
                ) as reference:
                    diff_md = tabulate(
                        create_diff_table(current, reference),
                        headers="firstrow",
                        tablefmt="github",
                    )
                    mds.append(diffmarkdown(test_file, table_name,diff_md))    

    return mds

def get_diff_tables_map(diff_dir: str) -> dict[str, set[str]]:
    result = {}
    csv_current_pattern = re.compile(".+_current.csv")
    for dir in listdir(diff_dir):
        tables = set()
        test_file_dir = f'{diff_dir}/{dir}'
        if not isfile(test_file_dir):
            for f in listdir(test_file_dir):
                if isfile(f'{test_file_dir}/{f}') and csv_current_pattern.match(f):
                    tables.add(str(f).replace("_current.csv", ""))  
            result[f'{str(dir)}'] = tables
    return result

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
