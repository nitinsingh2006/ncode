"""
Nitin Editor — Unit tests for Terminal module (app/terminal)
"""
import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.terminal.command_runner import CommandRunner
from app.terminal.safety import check_command
from app.terminal.command_reference import get_reference_text, lookup_equivalents
from app.terminal.history import load_history, save_history, add_command


def test_linux_command_execution():
    runner = CommandRunner()
    result = runner.run("echo 'Hello Terminal'", target_os="Linux")
    assert result.exit_code == 0
    assert "Hello Terminal" in result.stdout
    print("✓ Linux command execution")


def test_stderr_and_exit_code():
    runner = CommandRunner()
    result = runner.run("ls /path/that/does/not/exist_12345", target_os="Linux")
    assert result.exit_code != 0
    assert "No such file or directory" in result.stderr or result.exit_code != 0
    print("✓ Stderr and non-zero exit code handling")


def test_command_timeout():
    runner = CommandRunner()
    result = runner.run("sleep 10", target_os="Linux", timeout=1)
    assert result.timed_out
    print("✓ Command execution timeout")


def test_windows_simulation_mode():
    runner = CommandRunner()
    result = runner.run("dir", target_os="Windows")
    assert result.simulated
    assert "Windows environment is not available" in result.error_message
    print("✓ Windows simulation mode")


def test_macos_simulation_mode():
    runner = CommandRunner()
    result = runner.run("sw_vers", target_os="macOS")
    assert result.simulated
    assert "macOS environment is not available" in result.error_message
    print("✓ macOS simulation mode")


def test_dangerous_command_detection():
    dangerous_list = [
        ("rm -rf /", "Linux"),
        ("mkfs.ext4 /dev/sda", "Linux"),
        ("dd if=/dev/zero of=/dev/sda", "Linux"),
        ("shutdown -h now", "Linux"),
        ("reboot", "Linux"),
        ("format C:", "Windows"),
    ]
    for cmd, os_type in dangerous_list:
        res = check_command(cmd, os_type)
        assert res.is_dangerous, f"Failed to flag dangerous command: {cmd}"
        assert len(res.reason) > 0

    safe_list = [
        ("ls -la", "Linux"),
        ("rm file.txt", "Linux"),
        ("mkdir test", "Linux"),
        ("echo hello", "Linux"),
    ]
    for cmd, os_type in safe_list:
        res = check_command(cmd, os_type)
        assert not res.is_dangerous, f"Falsely flagged safe command: {cmd}"
    print("✓ Dangerous command detection & safety check")


def test_command_history():
    hist = []
    hist = add_command(hist, "ls")
    hist = add_command(hist, "pwd")
    hist = add_command(hist, "whoami")
    assert len(hist) == 3
    assert hist[0] == "whoami"
    assert hist[1] == "pwd"
    assert hist[2] == "ls"

    for i in range(10):
        hist = add_command(hist, f"cmd_{i}", max_size=5)

    assert len(hist) == 5
    assert hist[0] == "cmd_9"
    print("✓ Command history manager")


def test_command_reference():
    full_ref = get_reference_text()
    assert "Cross-Platform Command Reference" in full_ref
    assert "dir" in full_ref
    
    eq = lookup_equivalents("pwd")
    assert eq is not None
    assert "Linux:" in eq
    assert "Windows:" in eq
    print("✓ Command compatibility reference")


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — Terminal Tests")
    print("======================================================\n")

    tests = [
        test_linux_command_execution,
        test_stderr_and_exit_code,
        test_command_timeout,
        test_windows_simulation_mode,
        test_macos_simulation_mode,
        test_dangerous_command_detection,
        test_command_history,
        test_command_reference,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*54}")
    print(f"  {len(tests)-failed}/{len(tests)} tests passed")
    print(f"{'='*54}\n")

    sys.exit(0 if failed == 0 else 1)
