import subprocess


def test_uj_help_exits_zero():
    """Test that 'uj --help' exits with code 0"""
    result = subprocess.run(["python", "-m", "uc", "--help"], capture_output=True)
    assert result.returncode == 0
    assert "devin" in result.stdout.decode()


def test_devin_command_exists():
    """Test that devin command is available in help"""
    result = subprocess.run(["python", "-m", "uc", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "devin" in result.stdout
