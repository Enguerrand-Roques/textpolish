import plistlib

from platforms.macos import login_item


def _plist(tmp_path, run_at_load):
    path = tmp_path / "agent.plist"
    with open(path, "wb") as f:
        plistlib.dump({"Label": "com.user.textpolish", "RunAtLoad": run_at_load,
                       "ProgramArguments": ["python", "main.py"]}, f)
    return str(path)


def test_reads_run_at_load(tmp_path):
    assert login_item.enabled(_plist(tmp_path, True))
    assert not login_item.enabled(_plist(tmp_path, False))


def test_toggle_keeps_the_rest_of_the_plist(tmp_path):
    path = _plist(tmp_path, False)
    login_item.set_enabled(True, path)
    assert login_item.enabled(path)
    with open(path, "rb") as f:
        assert plistlib.load(f)["ProgramArguments"] == ["python", "main.py"]
    login_item.set_enabled(False, path)
    assert not login_item.enabled(path)


def test_no_launch_agent_means_unavailable(tmp_path):
    missing = str(tmp_path / "none.plist")
    assert not login_item.available(missing)
    assert not login_item.enabled(missing)
