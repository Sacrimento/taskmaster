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
    assert "its not stderr, it will be printed" in program_log
    assert "[Errno 21] Is a directory: '/'" in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/bad_stdout.log"), read("./output/bad_stdout.log"))],
)
def test_stdout_redirection(program_log, server_log):
    assert "Must not be print since its echo" not in program_log
    assert "[Errno 21] Is a directory: '/'" in server_log

@pytest.mark.parametrize(
    "content", 
    [read("./log/dir.log")]
)
def test_dir(content):
    assert "/tmp" in content

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/env.log"), read("./output/env.log"))],
)
def test_env(program_log, server_log):
    assert "coucou" not in program_log
    assert "[Errno 2] No such file or directory: 'echo'" in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/exitcodes.log"), read("./output/exitcodes.log"))],
)
def test_exitcode(program_log, server_log):
    assert server_log.count("Restarting invalid exitcode") == 2

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/multiple_proc.log"), read("./output/multiple_proc.log"))],
)
def test_multiproc(program_log, server_log):
    assert server_log.count('numprocs started !') == 4

@pytest.mark.parametrize(
    "program_log",
    [(read("./log/signal.log"))],
)
def test_signal(program_log):
    assert 'received SIGINT' in program_log


@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/manual_test_start_stop_restart.log"), read("./output/manual_test_start_stop_restart.log"))],
)
def test_start_stop_restart(program_log, server_log):
    assert 'stop started' in server_log
    assert 'start started' in server_log
    assert 'stop exited' in server_log

@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/startretries.log"), read("./output/startretries.log"))],
)
def test_start_retries(program_log, server_log):
    assert server_log.count('Restarting startretries') == 4


@pytest.mark.parametrize(
    "program_log, server_log",
    [(read("./log/starttime.log"), read("./output/starttime.log"))],
)
def test_start_time(program_log, server_log):
    assert server_log.count('Restarting starttime') == 2

   
