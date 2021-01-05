"""
This program computes the truck factor (also called bus factor) for a given 
Git repository.

The truck factor specifies "...the number of people on your team that have to 
be hit by a truck (or quit) before the project is in serious trouble..."" 
L. Williams and R. Kessler, Pair Programming Illuminated

Note, do not call it from within a Git repository.

More on the truck factor:
  * https://en.wikipedia.org/wiki/Bus_factor
  * https://legacy.python.org/search/hypermail/python-1994q2/1040.html


Usage:
  truckfactor <repository> [<commit_sha>] [--output=<kind>]
  truckfactor -h | --help
  truckfactor --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --output=<kind>  Kind of output, either csv or verbose.
"""
import csv
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from shutil import rmtree, which
from urllib.parse import urlparse

import pandas as pd
from docopt import docopt

from truckfactor import __version__
from truckfactor.evo_log_to_csv import convert
from truckfactor.repair_git_move import repair


TMP = tempfile.gettempdir()


def write_git_log_to_file(path_to_repo, commit_sha=None):
    p = Path(path_to_repo)
    outfile = os.path.join(TMP, p.name + "_evo.log")

    if not commit_sha:
        commit_sha = get_head_commit_sha(path_to_repo)
    cmd = f"""git -C {path_to_repo} log {commit_sha} \
    --pretty=format:'"%h","%an","%ad"' \
    --date=short \
    --numstat > \
    {outfile}"""

    subprocess.run(cmd, shell=True)

    return outfile


def preprocess_git_log_data(path_to_repo, commit_sha=None):
    evo_log = write_git_log_to_file(path_to_repo, commit_sha=commit_sha)
    evo_log_csv = convert(evo_log)
    try:
        evo_log_csv = repair(evo_log_csv)
    except ValueError:
        msg = (
            "Seems to be an empty repository."
            + " Cannot compute truck factor for it.\n"
        )
        sys.stderr.write(msg)
        sys.exit(1)
    return evo_log_csv


def create_file_owner_data(df):
    """Currently, we count up how many lines each author added per file.
    That is, we do not compute churn, where we would also detract the amount of
    lines that are removed.

    The author with knowledge ownership is the one that just added the most to
    file. We do not apply a threshold like one must own above 80% or similar.
    """
    new_rows = []

    for fname in set(df.current.values):
        view = df[df.current == fname]
        sum_series = view.groupby(["author"]).added.sum()
        view_df = sum_series.reset_index(name="sum_added")
        total_added = view_df.sum_added.sum()

        if total_added > 0:  # For binaries there are no lines counted
            view_df["owning_percent"] = view_df.sum_added / total_added
            owning_author = view_df.loc[view_df.owning_percent.idxmax()]
            new_rows.append(
                (
                    fname,
                    owning_author.author,
                    owning_author.sum_added,
                    total_added,
                    owning_author.owning_percent,
                )
            )
        # All binaries are silently skipped in this report...

    owner_df = pd.DataFrame(
        new_rows,
        columns=["artifact", "main_dev", "added", "total_added", "owner_rate"],
    )

    owner_freq_series = owner_df.groupby(["main_dev"]).artifact.count()
    owner_freq_df = owner_freq_series.reset_index(name="owns_no_artifacts")
    owner_freq_df.sort_values(by="owns_no_artifacts", inplace=True)

    return owner_df, owner_freq_df


def compute_truck_factor(df, freq_df):
    """Similar to G. Avelino et al.
    [*A novel approach for estimating Truck Factors*](https://ieeexplore.ieee.org/stamp)/stamp.jsp?arnumber=7503718)
    we remove low-contributing authors from the dataset as long as still more
    than half of the files have an owner. The amount of remaining owners is the
    bus-factor of that project.
    """
    no_artifacts = len(df.artifact)
    half_no_artifacts = no_artifacts // 2
    count = 0

    for owner, freq in freq_df.values:
        no_artifacts -= freq
        if no_artifacts < half_no_artifacts:
            break
        else:
            count += 1

    truckfactor = len(freq_df.main_dev) - count
    return truckfactor


def main(path_to_repo, is_url=False, commit_sha=None, ouputkind="human"):
    path_to_repo_url = path_to_repo
    if is_url:
        path_to_repo = clone_to_tmp(path_to_repo)
    evo_log_csv = preprocess_git_log_data(path_to_repo, commit_sha=commit_sha)
    complete_df = pd.read_csv(evo_log_csv)
    owner_df, owner_freq_df = create_file_owner_data(complete_df)
    truckfactor = compute_truck_factor(owner_df, owner_freq_df)

    if is_url:
        commit_sha = get_head_commit_sha(path_to_repo)
        create_ouput(path_to_repo_url, commit_sha, truckfactor, kind=ouputkind)
        rmtree(path_to_repo, ignore_errors=True)
    else:
        create_ouput(path_to_repo, commit_sha, truckfactor, kind=ouputkind)
    return truckfactor, commit_sha


def git_is_available():
    """Check whether `git` is on PATH"""
    if which("git"):
        return True
    else:
        return False


def is_git_url(potential_url):
    result = urlparse(potential_url)
    is_complete_url = all((result.scheme, result.netloc, result.path))
    is_git = result.path.endswith(".git")
    is_git_user = result.path.startswith("git@")
    if is_complete_url:
        return True
    elif is_git_user and is_git:
        return True
    else:
        return False


def is_git_dir(potential_repo_path):
    if not Path(potential_repo_path).is_dir():
        return False
    cmd = f"git -C {potential_repo_path} rev-parse --is-inside-work-tree"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip() == "true"


def clone_to_tmp(url):
    path = Path(urlparse(url).path)
    outdir = path.name.removesuffix(path.suffix)
    git_repo_dir = os.path.join(TMP, outdir + str(uuid.uuid4()))
    cmd = f"git clone {url} {git_repo_dir}"
    print(cmd)
    subprocess.run(cmd, shell=True)

    return git_repo_dir


def get_head_commit_sha(path_to_repo):
    cmd = f"git -C {path_to_repo} rev-parse HEAD"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    commit_sha = result.stdout.strip()

    return commit_sha


def create_ouput(path_to_repo, commit_sha, truckfactor, kind="human"):
    if not commit_sha:
        commit_sha = get_head_commit_sha(path_to_repo)

    if kind == "human":
        msg = (
            f"The truck factor of {path_to_repo} ({commit_sha}) is:" + f" {truckfactor}"
        )
        print(msg)
    elif kind == "csv":
        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow((path_to_repo, commit_sha, truckfactor))
    elif kind == "verbose":
        print(f"Repository: {path_to_repo}")
        print(f"Commit: {commit_sha}")
        print(f"Truckfactor: {truckfactor}")


def run():
    if not git_is_available():
        print("Truckfactor requires `git` to be installed and accessible on path")
        sys.exit(1)

    arguments = docopt(__doc__, version=__version__)

    commit_sha = arguments["<commit_sha>"]
    path_to_repo = arguments["<repository>"]
    if not arguments["--output"]:
        output = "human"
    else:
        output = arguments["--output"].lower()
        if not output in ["csv", "verbose"]:
            print(__doc__)
            sys.exit(1)
    if is_git_url(path_to_repo) or is_git_dir(path_to_repo):
        truckfactor, _ = main(
            path_to_repo,
            is_url=is_git_url(path_to_repo),
            commit_sha=commit_sha,
            ouputkind=output,
        )
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    run()
