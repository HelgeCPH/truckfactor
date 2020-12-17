import os
import re
import csv
import sys
import tempfile
import subprocess


LINE_RE = r"(-|\d+)+\s+(-|\d+)+\s+(.*)"
RENAME_RE = r"\{(.*) => (.*)\}"
RENAME2_RE = r"(.*) => (.*)"


def parse_numstat_block(commit_line, block):
    if block:
        for line in block:
            # '-\t-\twww/static/screenshots/tree.png'
            m = re.match(LINE_RE, line)
            added, removed, file_name = m.groups()
            if added == "-":
                added = f'"{added}"'
            if removed == "-":
                removed = f'"{removed}"'

            csv_line = ",".join((commit_line, added, removed, f'"{file_name}"'))
            yield csv_line
    else:
        csv_line = ",".join((commit_line, "", "", ""))
        yield csv_line


def convert(report_file):
    with open(report_file) as fp:
        lines = fp.readlines()

    commit_blocks = []
    commit_block = []
    for idx, line in enumerate(lines):
        line = line.rstrip()
        if idx + 1 < len(lines):
            next_line = lines[idx + 1].rstrip()
        else:
            next_line = ""
        if line.startswith('"') and next_line.startswith('"'):
            # Next line is a commit too and they where no changes...
            commit_block.append(line)
            commit_blocks.append(commit_block[:])
            commit_block = []
        else:
            if line:
                commit_block.append(line)
            else:
                commit_blocks.append(commit_block[:])
                commit_block = []

    out_file = f"{report_file}.csv"
    out_path = os.path.join(tempfile.gettempdir(), out_file)
    with open(out_path, "w") as fp:
        fp.write("hash,author,date,added,removed,fname\n")
        for block in commit_blocks:
            commit_line = block[0]
            for csv_line in parse_numstat_block(commit_line, block[1:]):
                fp.write(csv_line + "\n")
    return out_path


if __name__ == "__main__":
    convert(sys.argv[1])
