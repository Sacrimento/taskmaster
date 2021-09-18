#! /usr/bin/python3

import pytest

def read(filename):
    return open(filename, "r").read()

@pytest.mark.parametrize(
    "content", 
    [read("./log/autorestart.log")]
)
def test_autorestart(content):
    assert "never" not in content
    assert "always" in content

@pytest.mark.parametrize(
    "content", 
    [read("./log/autostart.log")]
)
def test_autostart(content):
    assert "autostart does not works" not in content
    assert "autostart works" in content

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stderr.log"), read("./output/bad_stderr.log"))],
)
def test_stderr_redirection(program_log, server_log):
    assert "autostart does not works" not in program_log
    assert "echo its not stderr, it will be printed" in program_log
    assert "[Errno 21] Is a directory: '/'" in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stdout.log"), read("./output/bad_stdout.log"))],
)
def test_stdout_redirection(program_log, server_log):
    assert "autostart does not works" not in program_log
    assert "Must not be print since its echo" in program_log
    assert "[Errno 21] Is a directory: '/'" in server_log

@pytest.mark.parametrize(
    "content", 
    [read("./log/dir.log")]
)
def test_dir(content):
    assert "/tmp" in content

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stdout.log"), read("./output/bad_stdout.log"))],
)
def test_path(program_log, server_log):
    assert "coucou" not in program_log
    assert "[Errno 2] No such file or directory: 'echo'" in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stdout.log"), read("./output/bad_stdout.log"))],
)
def test_path(program_log, server_log):
    assert "exitcode = 1" not in program_log
    assert "Restarting invalid exitcode (1)" in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stdout.log"))],
)
def test_path(program_log, server_log):
    assert program_log.count('MULTIPROC') == 4


