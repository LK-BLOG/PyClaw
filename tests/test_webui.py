"""WebUI 的接口与插件契约测试（不真的调用模型）。"""
import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import webapp  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    webapp.ACCESS_TOKEN = "test-token"
    return TestClient(webapp.app)


@pytest.fixture()
def config_guard():
    """改动 pyclaw.json 的测试前后备份并还原。"""
    path = ROOT / "pyclaw.json"
    backup = path.read_text(encoding="utf-8")
    yield path
    path.write_text(backup, encoding="utf-8")
    webapp.CONFIG = None
    webapp.AGENTS.clear()


def test_providers_catalog(client):
    data = client.get("/api/providers").json()
    ids = [p["id"] for p in data["providers"]]
    assert "deepseek" in ids
    assert len(ids) >= 15
    assert all("key_hint" in p for p in data["providers"])


def test_models_falls_back_without_base(client):
    data = client.get("/api/models", params={"provider": "custom", "base": ""}).json()
    assert data["ok"] is False
    assert isinstance(data["models"], list)


def test_plugins_loaded(client):
    rows = client.get("/api/plugins").json()["plugins"]
    names = {row["name"] for row in rows}
    assert {"file", "web", "time", "memory", "process", "ppt"} <= names
    file_row = next(row for row in rows if row["name"] == "file")
    assert file_row["tools"] == 4
    assert file_row["errors"] == []


def test_info_shape(client):
    data = client.get("/api/info").json()
    assert data["kernel"] == "pyclaw-lite"
    assert data["approval"] in ("request", "auto", "full")
    assert isinstance(data["effort"], str) and data["effort"]
    assert "legacy" in data and "old_sessions" in data["legacy"]


def test_config_roundtrip(client, config_guard):
    resp = client.post("/api/config", json={"approval": "full", "effort": "low", "agent_name": "PyClawTest"})
    assert resp.status_code == 200
    saved = resp.json()["saved"]
    assert saved["APPROVAL_MODE"] == "full"
    raw = json.loads(config_guard.read_text(encoding="utf-8"))
    assert raw["APPROVAL_MODE"] == "full"
    assert raw["REASONING_EFFORT"] == "low"
    assert raw["AGENT_NAME"] == "PyClawTest"


def test_ws_rejects_bad_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=wrong") as ws:
            ws.receive_json()


def test_ws_list_sessions(client):
    with client.websocket_connect("/ws?token=test-token") as ws:
        ws.send_json({"type": "list_sessions"})
        payload = ws.receive_json()
        assert payload["type"] == "sessions_list"
        assert isinstance(payload["sessions"], list)


def test_plugin_contract():
    from pyclaw import plugins as plugins_mod

    rows = plugins_mod.discover([ROOT / "plugins"], None, {})
    assert rows, "至少应该发现自带插件"
    for plugin in rows:
        assert not plugin.errors, f"{plugin.name} 加载报错: {plugin.errors}"
        for tool in plugin.tools:
            fn = tool.get("_handler")
            assert callable(fn)
            assert fn.__code__.co_argcount >= 2, f"{plugin.name}.{tool['function']['name']} 需要 (args, ctx)"


def test_time_plugin_runs():
    from pyclaw import plugins as plugins_mod

    rows = {p.name: p for p in plugins_mod.discover([ROOT / "plugins"], None, {})}
    tool = next(t for t in rows["time"].tools if t["function"]["name"] == "now")
    out = tool["_handler"]({}, {})
    assert ":" in out and len(out) > 8


def test_migrate_sessions(tmp_path, monkeypatch):
    legacy_dir = tmp_path / "pyclaw_data"
    legacy_dir.mkdir()
    (legacy_dir / "pyclaw_sessions.json").write_text(json.dumps({
        "version": 1,
        "sessions": {
            "legacy-1": {
                "id": "legacy-1",
                "created_at": 1700000000,
                "last_active_at": 1700000001,
                "metadata": {"name": "旧会话"},
                "messages": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"},
                    {"role": "tool", "content": "ok", "tool_name": "exec"},
                ],
            }
        },
    }), encoding="utf-8")
    monkeypatch.setattr(webapp, "ROOT", tmp_path)
    result = webapp.migrate_sessions()
    assert result["migrated"] == 1
    out = tmp_path / "history" / "sessions" / "legacy-1.jsonl"
    assert out.exists()
    lines = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert [x["type"] for x in lines] == ["user", "assistant", "tool"]

def test_migrate_memory(tmp_path, monkeypatch):
    import sqlite3

    legacy = tmp_path / "pyclaw_data"
    legacy.mkdir()
    db = legacy / "pyclaw_memory.db"
    con = sqlite3.connect(str(db))
    con.execute("create table memories (id integer primary key, memory_type text, session_id text,"
                " key text, value text, importance integer, created_at real, updated_at real, tags text)")
    con.execute("insert into memories values (1,'global',null,'user-name','小戡',10,1700000000,1700000000,'[]')")
    con.commit()
    con.close()

    monkeypatch.setattr(webapp, "ROOT", tmp_path)
    result = webapp.migrate_memory()
    assert result["migrated"] == 1
    files = sorted(p.name for p in (tmp_path / "memory").glob("*.md"))
    assert files == ["user-name.md"]
    body = (tmp_path / "memory" / "user-name.md").read_text(encoding="utf-8")
    assert "小戡" in body and "legacy memory" in body
    assert webapp.migrate_memory()["reason"] == "already_migrated"
