from __future__ import annotations

from readme_forge.detect import (
    detect_languages,
    parse_manifests,
)
from readme_forge.scanner import ScannedFile


def test_detect_languages_weights_and_order() -> None:
    files = [
        ScannedFile("a.py", ".py", 10),
        ScannedFile("b.py", ".py", 10),
        ScannedFile("c.py", ".py", 10),
        ScannedFile("d.js", ".js", 10),
        ScannedFile("README.md", ".md", 10),
    ]
    stats = detect_languages(files)
    assert stats[0].name == "Python"
    assert stats[0].file_count == 3
    assert stats[0].weight == 0.75
    assert stats[1].name == "JavaScript"
    assert stats[1].weight == 0.25


def test_detect_languages_empty_when_no_recognized_extensions() -> None:
    files = [ScannedFile("README.md", ".md", 10), ScannedFile("LICENSE", "", 5)]
    assert detect_languages(files) == []


def test_parse_package_json_valid() -> None:
    notes: list[str] = []
    content = (
        '{"name": "x", "description": "d", "version": "1.0.0", '
        '"scripts": {"build": "tsc"}, "dependencies": {"react": "^18"}, '
        '"devDependencies": {"jest": "^29"}}'
    )
    manifests = parse_manifests({"package.json": content}, notes)
    assert len(manifests) == 1
    m = manifests[0]
    assert m.kind == "package.json"
    assert m.name == "x"
    assert m.scripts == {"build": "tsc"}
    assert set(m.dependencies) == {"react", "jest"}
    assert notes == []


def test_parse_package_json_malformed_is_noted_not_raised() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"package.json": "{not valid json"}, notes)
    assert manifests == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_pyproject_toml_valid() -> None:
    notes: list[str] = []
    content = (
        "[project]\n"
        'name = "pkg"\n'
        'description = "desc"\n'
        'version = "0.1.0"\n'
        'dependencies = ["click"]\n'
        "\n"
        "[project.scripts]\n"
        'pkg = "pkg.cli:main"\n'
    )
    manifests = parse_manifests({"pyproject.toml": content}, notes)
    assert len(manifests) == 1
    m = manifests[0]
    assert m.name == "pkg"
    assert m.dependencies == ["click"]
    assert m.scripts == {"pkg": "pkg.cli:main"}


def test_parse_pyproject_toml_malformed_is_noted_not_raised() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"pyproject.toml": "not = [valid toml"}, notes)
    assert manifests == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_go_mod_valid() -> None:
    notes: list[str] = []
    content = "module example.com/foo\n\nrequire (\n\tgithub.com/x/y v1.0.0\n)\n"
    manifests = parse_manifests({"go.mod": content}, notes)
    assert len(manifests) == 1
    m = manifests[0]
    assert m.name == "example.com/foo"
    assert m.dependencies == ["github.com/x/y"]


def test_parse_go_mod_missing_module_line_is_noted() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"go.mod": "require github.com/x/y v1.0.0\n"}, notes)
    assert manifests == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_manifests_skips_unrecognized_filenames() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"random.txt": "hello"}, notes)
    assert manifests == []
    assert notes == []
