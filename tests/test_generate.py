"""Generate orchestrator and the shared build sheet."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from tools import generate
from tools.design import load_design
from tools.generators.build_sheet import BuildSheetHooks, render_build_sheet

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def blueprint(tmp_path, write_design, design_dict) -> Path:
    bp = tmp_path / "bp"
    bp.mkdir()
    (bp / "design.yaml").write_text(write_design(design_dict).read_text())
    return bp


def install_fake(monkeypatch, platform, content="one"):
    """Register a fake generator module for a platform."""
    mod = types.ModuleType(f"tools.generators.{platform}")

    def gen(design, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        f = out_dir / "objects.json"
        f.write_text(content + "\n")
        return [f]

    mod.generate = gen
    mod._fake = True
    monkeypatch.setitem(sys.modules, f"tools.generators.{platform}", mod)
    return mod


@pytest.fixture(autouse=True)
def only_fake_generators(monkeypatch):
    """Use only generators installed by install_fake, so results do not depend on files on disk."""

    def fake_get(platform):
        mod = sys.modules.get(f"tools.generators.{platform}")
        return mod if getattr(mod, "_fake", False) else None

    monkeypatch.setattr(generate, "get_generator", fake_get)


def test_no_generator_reported_cleanly(blueprint, capsys):
    assert generate.main([str(blueprint)]) == 0
    out = capsys.readouterr().out
    for p in ("attio", "hubspot", "salesforce"):
        assert f"no generator yet for {p}" in out


def test_check_works_with_no_generators(blueprint, capsys):
    assert generate.main([str(blueprint), "--check"]) == 0
    assert "no generator yet" in capsys.readouterr().out


def test_generate_writes_and_check_passes(blueprint, monkeypatch, capsys):
    install_fake(monkeypatch, "attio")
    assert generate.main([str(blueprint), "--platform", "attio"]) == 0
    assert (blueprint / "attio" / "objects.json").read_text() == "one\n"
    assert generate.main([str(blueprint), "--platform", "attio", "--check"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_check_detects_changed_missing_and_unexpected(blueprint, monkeypatch, capsys):
    install_fake(monkeypatch, "attio")
    generate.main([str(blueprint), "--platform", "attio"])
    target = blueprint / "attio" / "objects.json"
    target.write_text("edited\n")
    assert generate.main([str(blueprint), "--platform", "attio", "--check"]) == 1
    assert "changed: objects.json" in capsys.readouterr().out
    target.unlink()
    assert generate.main([str(blueprint), "--platform", "attio", "--check"]) == 1
    assert "missing: objects.json" in capsys.readouterr().out
    generate.main([str(blueprint), "--platform", "attio"])
    (blueprint / "attio" / "stray.json").write_text("{}")
    assert generate.main([str(blueprint), "--platform", "attio", "--check"]) == 1
    assert "unexpected: stray.json" in capsys.readouterr().out


def test_check_does_not_write(blueprint, monkeypatch):
    install_fake(monkeypatch, "attio")
    generate.main([str(blueprint), "--platform", "attio", "--check"])
    assert not (blueprint / "attio").exists() or not any((blueprint / "attio").iterdir())


def test_invalid_design_refuses_to_generate(blueprint, monkeypatch, capsys):
    install_fake(monkeypatch, "attio")
    text = (blueprint / "design.yaml").read_text().replace("type: select", "type: bogus", 1)
    (blueprint / "design.yaml").write_text(text)
    assert generate.main([str(blueprint)]) == 1
    assert "error" in capsys.readouterr().out
    assert not (blueprint / "attio").exists()


def test_missing_generator_module_is_none(monkeypatch):
    monkeypatch.undo()
    monkeypatch.setitem(generate.GENERATOR_MODULES, "attio", "tools.generators._does_not_exist")
    assert generate.get_generator("attio") is None


def test_broken_generator_import_propagates(tmp_path, monkeypatch):
    monkeypatch.undo()
    pkg = tmp_path / "zz_gen_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "broken.py").write_text("import module_that_does_not_exist_xyz\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setitem(generate.GENERATOR_MODULES, "attio", "zz_gen_pkg.broken")
    with pytest.raises(ModuleNotFoundError):
        generate.get_generator("attio")


def test_cli_requires_input():
    with pytest.raises(SystemExit):
        generate.main([])


# --- build sheet -------------------------------------------------------------------------------


class _Hooks(BuildSheetHooks):
    platform_label = "TestCRM"

    def object_path(self, obj):
        return f"TestCRM > Settings > Objects > New ({obj.label})"

    def stage_rule(self, pipeline, stage):
        return f"RULE[{stage.key}]" if stage.required_fields else ""

    def manual_steps(self):
        return ["Enable the sandbox"]


def test_build_sheet_order_and_content():
    d = load_design(REPO / "blueprints" / "b2b-saas-sales-led")
    text = render_build_sheet(d, "attio", _Hooks())
    headings = [l for l in text.splitlines() if l.startswith("## ")]
    assert headings == [
        "## 1. Decisions",
        "## 2. Objects and relationships",
        "## 3. Pipelines and stage rules",
        "## 4. Fields",
        "## 5. Automations",
        "## 6. Views",
        "## 7. QA and go-live",
    ]
    assert "TestCRM > Settings > Objects > New (Subscription)" in text
    assert "RULE[discovery]" in text
    assert "Manual step: Enable the sandbox" in text
    assert "Entered when" in text
    # every checkbox task is followed by a Done when line before the next task
    blocks = text.split("- [ ] ")[1:]
    assert blocks and all("Done when:" in b.split("\n- [ ] ")[0] for b in blocks)


def test_build_sheet_is_deterministic_and_platform_aware():
    d = load_design(REPO / "blueprints" / "b2b-saas-sales-led")
    a = render_build_sheet(d, "hubspot", BuildSheetHooks())
    assert a == render_build_sheet(d, "hubspot", BuildSheetHooks())
    # native fields are confirmed, not created
    assert "Confirm standard field Amount (`amount`)" in a
    assert "Create field Amount" not in a
    attio = render_build_sheet(d, "attio", BuildSheetHooks())
    assert "Create field Close date" in attio  # not native on Attio
