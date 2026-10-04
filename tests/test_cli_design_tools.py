"""diff_design, new_client, registry and the .env loader."""

from __future__ import annotations

import copy
import subprocess
import sys

import pytest

from tools import diff_design, new_client
from tools.cli_common import load_env, parse_env_file
from tools.crm import registry
from tools.crm.safety import SafetyError, get_credential
from tools.design import REPO_ROOT, load_design
from tools.diff_design import diff_designs


def variant(design_dict, mutate):
    data = copy.deepcopy(design_dict)
    mutate(data)
    return data


def plan_between(write_design, old, new):
    return diff_designs(load_design(write_design(old, "old.yaml")), load_design(write_design(new, "new.yaml")))


def test_added_field_option_and_stage_are_safe(write_design, design_dict):
    def add(d):
        d["add_fields"].append({"object": "deal", "key": "source", "label": "Source", "type": "text",
                                "description": "Where it came from."})
        d["add_fields"][0]["options"]["other"] = "Other"
        d["pipelines"][0]["stages"].insert(1, {
            "key": "proposal", "label": "Proposal", "type": "open", "probability": 50,
            "exit_criteria": "Entered when a proposal is sent."})
    plan = plan_between(write_design, design_dict, variant(design_dict, add))
    by_kind = {c.kind: c.risk for c in plan.changes}
    assert by_kind["add_field"] == by_kind["add_option"] == by_kind["add_stage"] == "safe"
    assert not [m for m in plan.manual_steps]


def test_removed_field_is_destructive(write_design, design_dict, capsys):
    new = variant(design_dict, lambda d: d["add_fields"].pop(2))  # next_step_date
    new["pipelines"][0]["stages"][0].pop("required_fields")
    plan = plan_between(write_design, design_dict, new)
    (step,) = [m for m in plan.manual_steps if m.risk == "destructive"]
    assert "deal.next_step_date" in step.title and step.instructions
    assert not plan.changes
    old_path, new_path = write_design(design_dict, "o.yaml"), write_design(new, "n.yaml")
    assert diff_design.main([str(old_path), str(new_path)]) == 0
    assert "[DESTRUCTIVE] Remove field deal.next_step_date" in capsys.readouterr().out
    assert diff_design.main([str(old_path), str(new_path), "--exit-code"]) == 1


def test_identical_designs_have_no_changes(write_design, design_dict, capsys):
    p = write_design(design_dict)
    assert diff_design.main([str(p), str(p), "--exit-code"]) == 0
    assert "Nothing to do" in capsys.readouterr().out


def test_diff_reads_a_git_ref(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (repo / "design.yaml").write_text("name: One\ndescription: x\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "one")
    (repo / "design.yaml").write_text(
        "name: Two\ndescription: x\nadd_objects:\n  - {key: thing, label: Thing, description: A thing.}\n",
        encoding="utf-8")
    git("commit", "-qam", "two")
    monkeypatch.setattr(diff_design, "REPO_ROOT", repo)
    assert diff_design.main(["HEAD~1:design.yaml", str(repo / "design.yaml")]) == 0
    assert "[add_object]" in capsys.readouterr().out


def test_diff_bad_spec_is_an_error(capsys):
    assert diff_design.main(["nope", "nope2"]) == 2


# --- new_client ---------------------------------------------------------------------------------


def test_new_client_creates_the_folder(tmp_path):
    rc = new_client.main(["b2b-saas-sales-led", "acme-ltd", "--name", "Acme Ltd", "--clients-dir", str(tmp_path)])
    assert rc == 0
    folder = tmp_path / "acme-ltd"
    assert sorted(p.name for p in folder.iterdir()) == ["CHANGELOG.md", "build", "design.yaml", "notes.md"]
    design = load_design(folder / "design.yaml")
    assert design.name.startswith("Acme Ltd (")
    assert "b2b-saas-sales-led" in (folder / "notes.md").read_text()


def test_new_client_refuses_to_overwrite(tmp_path, capsys):
    (tmp_path / "acme").mkdir()
    (tmp_path / "acme" / "keep.txt").write_text("mine", encoding="utf-8")
    rc = new_client.main(["b2b-saas-sales-led", "acme", "--clients-dir", str(tmp_path)])
    assert rc == 1 and "already exists" in capsys.readouterr().err
    assert [p.name for p in (tmp_path / "acme").iterdir()] == ["keep.txt"]


@pytest.mark.parametrize("bad", ["Acme", "a/b", "../x", "a_b", ""])
def test_new_client_rejects_bad_names(tmp_path, bad):
    assert new_client.main(["b2b-saas-sales-led", bad, "--clients-dir", str(tmp_path)]) == 1


def test_new_client_unknown_blueprint(tmp_path):
    assert new_client.main(["no-such-blueprint", "acme", "--clients-dir", str(tmp_path)]) == 1
    assert not (tmp_path / "acme").exists()


# --- registry and .env ----------------------------------------------------------------------------


def test_registry_rejects_unknown_platform():
    with pytest.raises(registry.RegistryError, match="Unknown platform"):
        registry.get_adapter("zoho", {}, None, False)


def test_registry_missing_module(monkeypatch):
    def boom(name):
        raise ModuleNotFoundError(f"No module named {name!r}", name=name)

    monkeypatch.setattr(registry, "import_module", boom)
    with pytest.raises(registry.RegistryError, match="does not exist yet"):
        registry.get_adapter("attio", {}, None, False)


def test_registry_module_without_factory(monkeypatch):
    monkeypatch.setattr(registry, "import_module", lambda name: object())
    with pytest.raises(registry.RegistryError, match="make_adapter"):
        registry.get_adapter("attio", {}, None, False)


def test_registry_missing_credentials_and_success(monkeypatch):
    class Module:
        @staticmethod
        def make_adapter(env, *, target, production):
            return ("adapter", get_credential("ATTIO_API_KEY", dict(env)), target, production)

    monkeypatch.setattr(registry, "import_module", lambda name: Module)
    with pytest.raises(registry.RegistryError, match="ATTIO_API_KEY"):
        registry.get_adapter("attio", {}, None, False)
    got = registry.get_adapter("attio", {"ATTIO_API_KEY": "abc"}, "sbx", False)
    assert got == ("adapter", "abc", "sbx", False)


def test_registry_imports_the_real_module_name(monkeypatch):
    seen = []
    monkeypatch.setattr(registry, "import_module", lambda name: seen.append(name) or type("M", (), {"make_adapter": staticmethod(lambda env, *, target, production: 1)}))
    registry.get_adapter("hubspot", {}, None, False)
    assert seen == ["tools.crm.hubspot"]


def test_env_file_parsing_and_precedence(tmp_path):
    f = tmp_path / ".env"
    f.write_text('# c\nA=1\nexport B="two words"\nC=\'x\'\nD=val # note\nbad line\n', encoding="utf-8")
    assert parse_env_file(f.read_text()) == {"A": "1", "B": "two words", "C": "x", "D": "val"}
    merged = load_env(f, {"A": "from-env"})
    assert merged["A"] == "from-env" and merged["B"] == "two words"
    assert load_env(tmp_path / "missing", {"Z": "1"}) == {"Z": "1"}


def test_scripts_run_directly_with_help():
    for name in ("crm_pull", "crm_plan", "crm_apply", "crm_drift", "diff_design", "new_client"):
        for argv in ([sys.executable, f"tools/{name}.py", "--help"], [sys.executable, "-m", f"tools.{name}", "--help"]):
            r = subprocess.run(argv, cwd=REPO_ROOT, capture_output=True, text=True)
            assert r.returncode == 0 and "usage" in r.stdout.lower(), (argv, r.stderr)
