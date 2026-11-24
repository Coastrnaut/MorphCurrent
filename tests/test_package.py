"""F28: portable project packages - export, safe inspection, migrations, sandboxed import and readiness."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

import pytest

from morph_studio import cli
from morph_studio import package as pk
from morph_studio.release import backup_run

from conftest import REPO

STORYBOARD = "configs/sequences/organic-machines.yaml"
STYLED = "configs/sequences/engineering-pilot.yaml"


@pytest.fixture()
def repo(tmp_path) -> Path:
    root = tmp_path / "repo"
    for rel in (STORYBOARD, STYLED, "configs/model_catalogue.json"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes((REPO / rel).read_bytes())
    for folder in ("configs/profiles", "workflows", "configs/styles"):
        (root / folder).mkdir(parents=True, exist_ok=True)
        for f in (REPO / folder).iterdir():
            if f.is_file():
                (root / folder / f.name).write_bytes(f.read_bytes())
    return root


@pytest.fixture()
def run(repo) -> Path:
    """Synthetic run under repo/outputs/runs with relative and absolute paths and two jobs."""
    runs = repo / "outputs" / "runs"
    run_dir = runs / "run-0123456789abcdef"
    (run_dir / "final").mkdir(parents=True)
    (run_dir / "final" / "movie.mp4").write_bytes(b"movie-bytes")
    (run_dir / "anchors_contact_sheet.png").write_bytes(b"png-bytes")
    stages = {}
    for i, task in enumerate(["anchor:orchid", "bridge:orchid->butterfly"]):
        job = runs / f"job{i:012d}"
        (job / "outputs").mkdir(parents=True)
        name = "a.png" if task.startswith("anchor") else "b.mp4"
        (job / "outputs" / name).write_bytes(f"out{i}".encode())
        kind = {"image": {"local_path": f"outputs\\{name}"}} if i == 0 else \
            {"outputs": [{"kind": "video", "local_path": f"outputs\\{name}"}]}
        (job / "job.json").write_text(json.dumps(kind), encoding="utf-8")
        key = "image_sha256" if i == 0 else "video_sha256"
        stages[task] = {"state": "verified", "job_dir": f"outputs\\runs\\{job.name}",
                        key: hashlib.sha256(f"out{i}".encode()).hexdigest()}
    stages["final:movie"] = {"state": "verified"}
    manifest = {"schema": 1, "kind": "morphcurrent_run", "storyboard": STORYBOARD.replace("/", "\\"),
                "plan_sha256": "ab" * 32, "order": list(stages), "stages": stages,
                "final": {"output": "outputs\\runs\\run-0123456789abcdef\\final\\movie.mp4",
                          "note": str(run_dir / "final" / "movie.mp4"),
                          "elsewhere": "C:\\Users\\someone\\Desktop\\secret.mp4"}}
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "plan.json").write_text(json.dumps({"plan_sha256": "ab" * 32}), encoding="utf-8")
    (run_dir / "review.json").write_text(json.dumps({"bridge:orchid->butterfly": "approved"}), encoding="utf-8")
    return run_dir


def export(repo, out, **kw):
    return pk.export_project(repo / kw.pop("storyboard", STORYBOARD), out, repo_root=repo, **kw)


def names(path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        return z.namelist()


def read_json(path, member):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read(member))


def craft(path: Path, members: dict[str, bytes], description: dict | None = None, sums: bool = True) -> Path:
    """Write a zip with given members (+ project.json + checksum list unless disabled)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        all_members = dict(members)
        if description is not None:
            all_members[pk.DESCRIPTION] = json.dumps(description).encode()
        for name, data in all_members.items():
            z.writestr(name, data)
        if sums:
            z.writestr(pk.SUMS, json.dumps({n: hashlib.sha256(d).hexdigest() for n, d in all_members.items()}))
    return path


def good_description(**over):
    return {"format": 1, "kind": pk.KIND, "storyboard": {"name": "x", "path": "configs/sequences/x.yaml"},
            "anchors": ["a", "b"], "stage_ids": ["anchor:a", "anchor:b"], **over}


# --- foundational ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["../x", "a/../../x", "/etc/passwd", "C:/x", "c:x", "\\\\server\\share\\x",
                                  "a\\b", "file.txt:stream", "CON", "nul.txt", "dir/COM1.json", "lpt9",
                                  "trailing.", "space ", ""])
def test_unsafe_names(name):
    assert pk._unsafe_name(name)


@pytest.mark.parametrize("name", ["configs/sequences/x.yaml", "run/run-1/manifest.json", "media/a.png",
                                  "console.json", "con_trail/x"])
def test_safe_names(name):
    assert not pk._unsafe_name(name)


def test_redact(tmp_path):
    root = tmp_path / "repo"
    data = {"a": str(root / "outputs" / "x.mp4"), "b": ["C:\\Users\\me\\x.wav", "relative\\ok.mp4"],
            "c": {"d": "\\\\nas\\share\\y"}, "e": "/home/me/z", "f": "/object_info", "n": 3}
    out, count = pk.redact(data, [root])
    assert out["a"] == "outputs/x.mp4" and out["b"] == [pk.REDACTED, "relative\\ok.mp4"]
    assert out["c"]["d"] == pk.REDACTED and out["e"] == pk.REDACTED and out["f"] == "/object_info"
    assert count == 4 and not pk.absolute_paths(out)


# --- US1 export -----------------------------------------------------------------------------------

def test_export_project_files(repo, tmp_path):
    out = tmp_path / "p.zip"
    rec = export(repo, out)
    members = names(out)
    assert STORYBOARD in members and pk.DESCRIPTION in members and pk.SUMS in members
    assert {"configs/profiles/anchor_t2i.binding.json", "configs/profiles/anchor_edit.binding.json",
            "configs/profiles/wan22_flf2v.binding.json", "workflows/03_wan22_flf2v.json"} <= set(members)
    sums = read_json(out, pk.SUMS)
    assert set(sums) == set(members) - {pk.SUMS}
    desc = read_json(out, pk.DESCRIPTION)
    assert desc["format"] == 1 and desc["plan_sha256"] == rec["plan_sha256"] and "run" not in desc
    assert desc["storyboard"]["sha256"] == hashlib.sha256((repo / STORYBOARD).read_bytes()).hexdigest()
    assert {p["capability"] for p in desc["profiles"]} >= {"wan_flf2v"}
    assert all(m["bundled"] is False and m["licence"] for m in desc["models"])
    assert desc["media"]["included"] is False
    assert not list(tmp_path.glob("*.part"))
    with pytest.raises(FileExistsError):
        export(repo, out)


def test_export_style_chain(repo, tmp_path):
    out = tmp_path / "s.zip"
    export(repo, out, storyboard=STYLED)
    desc = read_json(out, pk.DESCRIPTION)
    assert desc["style_packs"] and all(p["path"] in names(out) for p in desc["style_packs"])


def test_export_with_run_redacts_and_excludes_media(repo, run, tmp_path):
    out = tmp_path / "r.zip"
    rec = export(repo, out, run_dir=run)
    members = names(out)
    assert {f"run/{run.name}/manifest.json", f"run/{run.name}/plan.json", f"run/{run.name}/review.json"} <= set(members)
    assert not any(m.endswith((".png", ".mp4", ".wav")) for m in members)
    manifest = read_json(out, f"run/{run.name}/manifest.json")
    assert not pk.absolute_paths(manifest) and rec["redactions"] >= 2
    assert manifest["final"]["elsewhere"] == pk.REDACTED
    assert manifest["final"]["note"] == f"outputs/runs/{run.name}/final/movie.mp4"
    desc = read_json(out, pk.DESCRIPTION)
    assert desc["run"]["stages"]["anchor:orchid"]["output_sha256"] == hashlib.sha256(b"out0").hexdigest()
    assert desc["run"]["final"]["sha256"] == hashlib.sha256(b"movie-bytes").hexdigest()
    excluded = [f for f in desc["media"]["files"] if not f["included"]]
    assert len(excluded) >= 4 and all(f["sha256"] for f in excluded)


def test_export_media_authorized(repo, run, tmp_path):
    out = tmp_path / "m.zip"
    export(repo, out, run_dir=run, include_media=True)
    media = [m for m in names(out) if m.startswith("media/")]
    assert len(media) >= 4 and read_json(out, pk.DESCRIPTION)["media"]["included"] is True
    with pytest.raises(pk.PackageError, match="media"):
        export(repo, tmp_path / "a.zip", include_audio=True)


def test_export_refuses_weights(repo, run, tmp_path):
    job_out = next((run.parent).glob("job000000000000/outputs/a.png"))
    weights = job_out.with_name("model.safetensors")
    weights.write_bytes(b"w")
    (job_out.parent.parent / "job.json").write_text(json.dumps({"image": {"local_path": "outputs\\model.safetensors"}}),
                                                   encoding="utf-8")
    with pytest.raises(pk.PackageError, match="weights"):
        export(repo, tmp_path / "w.zip", run_dir=run, include_media=True)
    assert not (tmp_path / "w.zip").exists()


# --- US2 inspection -------------------------------------------------------------------------------

def test_inspect_good(repo, run, tmp_path):
    out = tmp_path / "g.zip"
    export(repo, out, run_dir=run)
    before = sorted(p.name for p in tmp_path.iterdir())
    rep = pk.inspect_package(out)
    assert rep["ok"], rep["problems"]
    assert rep["format"] == 1 and rep["summary"]["media_included"] is False and rep["summary"]["members"] > 5
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def _problem(path) -> str:
    rep = pk.inspect_package(path)
    assert not rep["ok"]
    return " ".join(rep["problems"])


def test_inspect_tampered(repo, tmp_path):
    out = tmp_path / "t.zip"
    export(repo, out)
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(out) as src, zipfile.ZipFile(bad, "w") as dst:
        for info in src.infolist():
            data = src.read(info)
            dst.writestr(info.filename, data + b"#" if info.filename == STORYBOARD else data)
    assert STORYBOARD in _problem(bad)


def test_inspect_future_and_ids_and_paths(tmp_path):
    assert "newer" in _problem(craft(tmp_path / "f.zip", {}, good_description(format=99)))
    assert "duplicate anchor" in _problem(craft(tmp_path / "d.zip", {}, good_description(anchors=["a", "a"])))
    assert "duplicate stage" in _problem(craft(tmp_path / "s.zip", {}, good_description(stage_ids=["x", "x"])))
    assert "absolute" in _problem(craft(tmp_path / "p.zip", {}, good_description(note="D:\\work\\x.mp4")))
    assert pk.inspect_package(craft(tmp_path / "ok.zip", {"configs/a.json": b"{}"}, good_description()))["ok"]


@pytest.mark.parametrize("member", ["../evil.txt", "C:/evil.txt", "CON", "a/aux.json", "x.txt:ads",
                                    "\\\\srv\\x"])
def test_inspect_unsafe_member(tmp_path, member):
    assert "unsafe" in _problem(craft(tmp_path / "u.zip", {member: b"x"}, good_description()))


def test_inspect_duplicates_and_case(tmp_path):
    assert "case" in _problem(craft(tmp_path / "c.zip", {"A.json": b"1", "a.json": b"2"}, good_description()))
    dup = tmp_path / "dup.zip"
    with zipfile.ZipFile(dup, "w") as z:
        z.writestr(pk.DESCRIPTION, json.dumps(good_description()))
        with pytest.warns(UserWarning):
            z.writestr("x.json", b"1")
            z.writestr("x.json", b"2")
    assert "duplicate" in _problem(dup)


def test_inspect_limits(tmp_path, monkeypatch):
    p = craft(tmp_path / "l.zip", {f"f{i}.json": b"{}" for i in range(5)}, good_description())
    monkeypatch.setattr(pk, "MAX_MEMBERS", 3)
    assert "members" in _problem(p)
    monkeypatch.setattr(pk, "MAX_MEMBERS", 10_000)
    bomb = craft(tmp_path / "b.zip", {"zeros.json": b"0" * (2 * 1024 * 1024)}, good_description())
    assert "ratio" in _problem(bomb)
    monkeypatch.setattr(pk, "MAX_NON_MEDIA", 1000)
    assert "expand" in _problem(craft(tmp_path / "e.zip", {"big.json": os.urandom(2000)}, good_description()))


def test_inspect_not_zip_and_missing_sums(tmp_path):
    junk = tmp_path / "j.zip"
    junk.write_bytes(b"not a zip")
    assert "zip" in _problem(junk)
    assert "checksum" in _problem(craft(tmp_path / "n.zip", {"a.json": b"1"}, good_description(), sums=False))


# --- US3 migrations -------------------------------------------------------------------------------

def test_f20_backup_migrates(run, tmp_path):
    backup = tmp_path / "f20.zip"
    backup_run(run, backup)
    rep = pk.inspect_package(backup)
    assert rep["ok"], rep["problems"]
    assert rep["format"] == 1 and rep["migrated_from"] == 0
    assert rep["summary"]["run"] == run.name and rep["summary"]["plan_sha256"] == "ab" * 32


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    desc = {"format": 0, "run_manifest": {"plan_sha256": "x"}}
    snapshot = json.dumps(desc, sort_keys=True)

    def boom(d):
        d["format"] = 1
        raise ValueError("bad step")
    monkeypatch.setitem(pk.MIGRATIONS, 0, boom)
    with pytest.raises(pk.PackageError, match="0->1"):
        pk.migrate(desc, 0)
    assert json.dumps(desc, sort_keys=True) == snapshot


# --- US4 import / readiness -----------------------------------------------------------------------

def test_import_roundtrip(repo, run, tmp_path):
    out = tmp_path / "rt.zip"
    rec = export(repo, out, run_dir=run)
    dest = tmp_path / "second" / "restored"
    report = pk.import_project(out, dest)
    sums = read_json(out, pk.SUMS)
    for member, digest in sums.items():
        assert hashlib.sha256((dest / member).read_bytes()).hexdigest() == digest
    assert report["plan_matches"] is True and report["plan_sha256_recompiled"] == rec["plan_sha256"]
    assert report["restored_files"] == len(sums) + 1
    assert {p["status"] for p in report["profiles"]} == {"offline-unverified"}
    with pytest.raises(pk.PackageError, match="not empty"):
        pk.import_project(out, dest)
    assert not [p for p in dest.parent.iterdir() if p.name.startswith(".")]


def test_import_refusals(repo, tmp_path):
    bad = craft(tmp_path / "bad.zip", {"../evil": b"x"}, good_description())
    with pytest.raises(pk.PackageError, match="unsafe"):
        pk.import_project(bad, tmp_path / "d1")
    assert not (tmp_path / "d1").exists() and not (tmp_path / "evil").exists()
    out = tmp_path / "ok.zip"
    export(repo, out)
    afile = tmp_path / "afile"
    afile.write_text("x")
    with pytest.raises(pk.PackageError, match="file"):
        pk.import_project(out, afile)


def test_import_missing_models_and_cleanup(repo, tmp_path, monkeypatch):
    out = tmp_path / "mm.zip"
    export(repo, out)
    models = tmp_path / "models"
    models.mkdir()
    report = pk.import_project(out, tmp_path / "d2", models_root=models)
    assert report["missing_models"] and "owner approval" in report["note"]

    def fail(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(pk.os, "replace", fail)
    with pytest.raises(OSError):
        pk.import_project(out, tmp_path / "d3")
    assert not (tmp_path / "d3").exists() and not [p for p in tmp_path.iterdir() if p.name.startswith(".d3")]
    (tmp_path / "d4").mkdir()
    with pytest.raises(OSError):
        pk.import_project(out, tmp_path / "d4")
    assert (tmp_path / "d4").is_dir() and not any((tmp_path / "d4").iterdir())


def test_export_lists_missing_job_outputs(repo, run, tmp_path):
    import shutil
    shutil.rmtree(run.parent / "job000000000001")
    out = tmp_path / "x.zip"
    export(repo, out, run_dir=run, include_media=True)
    files = read_json(out, pk.DESCRIPTION)["media"]["files"]
    gone = [f for f in files if f["sha256"] == "not found"]
    assert len(gone) == 1 and gone[0]["recorded_sha256"] == hashlib.sha256(b"out1").hexdigest()
    assert not gone[0]["included"] and ":" not in gone[0]["path"]


# --- CLI / safety ---------------------------------------------------------------------------------

def test_cli(repo, run, tmp_path, capsys):
    out = tmp_path / "c.zip"
    assert cli.main(["project-export", str(repo / STORYBOARD), "--out", str(out), "--run", str(run),
                     "--repo-root", str(repo)]) == 0
    capsys.readouterr().out.encode("ascii")
    assert cli.main(["project-export", str(repo / STORYBOARD), "--out", str(out), "--repo-root", str(repo)]) == 2
    assert cli.main(["project-inspect", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert cli.main(["project-import", str(out), "--dest", str(tmp_path / "cli-dest")]) == 0
    assert json.loads(capsys.readouterr().out)["plan_matches"] is True
    assert cli.main(["project-import", str(out), "--dest", str(tmp_path / "cli-dest")]) == 2
    junk = tmp_path / "junk.zip"
    junk.write_bytes(b"x")
    assert cli.main(["project-inspect", str(junk)]) == 2


def test_no_network_or_inference():
    source = (REPO / "src/morph_studio/package.py").read_text(encoding="utf-8")
    for banned in ("ComfyClient", "httpx", "urlopen", "comfy_client", "queue_prompt"):
        assert banned not in source
