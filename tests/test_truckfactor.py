import subprocess
import toml
from truckfactor import __version__
from truckfactor.compute import is_git_url, main


def test_version():

    with open("pyproject.toml") as fp:
        contents = toml.load(fp)

    assert __version__ == contents["tool"]["poetry"]["version"]


def test_end_to_end_human_output():
    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"
    cmd = f"truckfactor ../truckfactor/ {commit_sha}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    expected_output = (
        "The truck factor of ../truckfactor/ "
        + "(84f0d6c6b7080388889652bbf8589e7036ef4ffb) is: 1"
    )
    assert output == expected_output


def test_end_to_end_csv_output():
    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"
    cmd = f"truckfactor ../truckfactor/ {commit_sha} --output=csv"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    expected_output = "../truckfactor/,84f0d6c6b7080388889652bbf8589e7036ef4ffb,1"

    assert output == expected_output


def test_end_to_end_verbose_output():
    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"
    cmd = f"truckfactor ../truckfactor/ {commit_sha} --output=verbose"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    expected_output = """Repository: ../truckfactor/
Commit: 84f0d6c6b7080388889652bbf8589e7036ef4ffb
Truckfactor: 1"""

    assert output == expected_output


def test_non_git_repo_dir():
    script = """rm -rf /tmp/truckfactor_test
mkdir /tmp/truckfactor_test
echo 'uiuiui' > /tmp/truckfactor_test/README.md
"""
    subprocess.run(script, shell=True)

    cmd = f"truckfactor /tmp/truckfactor_test"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert result.returncode == 1


def test_empty_repo():
    script = """rm -rf /tmp/truckfactor_test
mkdir /tmp/truckfactor_test
echo 'uiuiui' > /tmp/truckfactor_test/README.md
git -C /tmp/truckfactor_test init
"""
    subprocess.run(script, shell=True)

    cmd = f"truckfactor /tmp/truckfactor_test"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert result.returncode == 1
    msg = "Seems to be an empty repository. Cannot compute truck factor for it."
    assert result.stderr.strip().endswith(msg)


def test_single_commit_repo():
    script = """rm -rf /tmp/truckfactor_test
mkdir /tmp/truckfactor_test
echo 'uiuiui' > /tmp/truckfactor_test/README.md
git -C /tmp/truckfactor_test init
git -C /tmp/truckfactor_test add README.md
git -C /tmp/truckfactor_test commit -m"Added file"
"""

    subprocess.run(script, shell=True)

    cmd = f"truckfactor /tmp/truckfactor_test --output=csv"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    output = result.stdout.strip()
    assert result.returncode == 0
    assert int(output.split(",")[-1]) == 0


def test_two_commits_repo():
    script = """rm -rf /tmp/truckfactor_test
mkdir /tmp/truckfactor_test
echo 'uiuiui' > /tmp/truckfactor_test/README.md
git -C /tmp/truckfactor_test init
git -C /tmp/truckfactor_test add README.md
git -C /tmp/truckfactor_test commit -m"Added file"
echo 'uiuiui' > /tmp/truckfactor_test/aiaiai.md
git -C /tmp/truckfactor_test add aiaiai.md
git -C /tmp/truckfactor_test commit -m"Added file"
"""

    subprocess.run(script, shell=True)

    cmd = f"truckfactor /tmp/truckfactor_test --output=csv"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    output = result.stdout.strip()
    assert result.returncode == 0
    assert int(output.split(",")[-1]) == 1


def test_programatic_call():
    path_to_repo = "../truckfactor/"
    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"

    assert is_git_url(path_to_repo) == False

    truckfactor, out_commit_sha = main(
        path_to_repo,
        is_url=is_git_url(path_to_repo),
        commit_sha=commit_sha,
    )

    assert truckfactor == 1
    assert out_commit_sha == commit_sha
