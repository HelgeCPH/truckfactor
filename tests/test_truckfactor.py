from truckfactor import __version__


def test_version():
    import toml

    with open("pyproject.toml") as fp:
        contents = toml.load(fp)

    assert __version__ == contents["tool"]["poetry"]["version"]


def test_end_to_end_human_output():
    import subprocess

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
    import subprocess

    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"
    cmd = f"truckfactor ../truckfactor/ {commit_sha} --output=csv"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    expected_output = (
        "../truckfactor/,84f0d6c6b7080388889652bbf8589e7036ef4ffb,1"
    )

    assert output == expected_output


def test_end_to_end_verbose_output():
    import subprocess

    commit_sha = "84f0d6c6b7080388889652bbf8589e7036ef4ffb"
    cmd = f"truckfactor ../truckfactor/ {commit_sha} --output=verbose"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    expected_output = """Repository: ../truckfactor/
Commit: 84f0d6c6b7080388889652bbf8589e7036ef4ffb
Truckfactor: 1"""

    assert output == expected_output
