import sys

import pytest

from codex_bot.scheduler import ScheduleRequest, build_schtasks_command


def test_command_is_argument_list(tmp_path):
    request = ScheduleRequest("Weekly Post", "MON", "09:30", "Write captions")
    command = build_schtasks_command(request, tmp_path)
    assert command[0] == "schtasks.exe"
    assert command[command.index("/TN") + 1] == "Codex Bot\\Weekly Post"
    assert sys.executable in command[command.index("/TR") + 1]


def test_rejects_unsafe_name():
    with pytest.raises(ValueError):
        ScheduleRequest("bad & name", "MON", "09:00", "Prompt").validate()

