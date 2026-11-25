from __future__ import annotations

from pathlib import Path

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


def test_parse_package_json_non_object_is_noted_not_raised() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"package.json": "[1, 2, 3]"}, notes)
    assert manifests == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_pyproject_toml_non_table_project_does_not_raise() -> None:
    notes: list[str] = []
    manifests = parse_manifests({"pyproject.toml": 'project = "oops"\n'}, notes)
    assert len(manifests) == 1
    assert manifests[0].name is None
    assert manifests[0].dependencies == []


def _parse_fixture(fixtures_dir: Path, repo: str, filename: str) -> list:
    notes: list[str] = []
    content = (fixtures_dir / repo / filename).read_text(encoding="utf-8")
    manifests = parse_manifests({filename: content}, notes)
    assert notes == []
    return manifests


def test_parse_cargo_toml_fixture(fixtures_dir: Path) -> None:
    [m] = _parse_fixture(fixtures_dir, "rust_repo", "Cargo.toml")
    assert m.kind == "Cargo.toml"
    assert m.name == "samplers"
    assert m.version == "0.2.0"
    assert m.description == "A sample Rust crate"
    assert m.dependencies == ["serde", "clap", "assert_cmd"]
    assert m.scripts == {}


def test_parse_cargo_toml_workspace_without_package() -> None:
    notes: list[str] = []
    content = '[workspace]\nmembers = ["a", "b"]\n'
    [m] = parse_manifests({"Cargo.toml": content}, notes)
    assert m.name is None
    assert m.dependencies == []


def test_parse_cargo_toml_malformed_is_noted_not_raised() -> None:
    notes: list[str] = []
    assert parse_manifests({"Cargo.toml": "[package\nname = "}, notes) == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_composer_json_fixture(fixtures_dir: Path) -> None:
    [m] = _parse_fixture(fixtures_dir, "php_repo", "composer.json")
    assert m.kind == "composer.json"
    assert m.name == "acme/samplephp"
    assert m.version == "1.4.0"
    assert m.description == "A sample PHP package"
    assert m.dependencies == ["php", "guzzlehttp/guzzle", "phpunit/phpunit"]
    assert m.scripts == {"test": "phpunit", "check": "@lint && @test"}


def test_parse_composer_json_malformed_is_noted_not_raised() -> None:
    notes: list[str] = []
    assert parse_manifests({"composer.json": '{"name": '}, notes) == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_pubspec_yaml_fixture(fixtures_dir: Path) -> None:
    [m] = _parse_fixture(fixtures_dir, "dart_repo", "pubspec.yaml")
    assert m.kind == "pubspec.yaml"
    assert m.name == "sampledart"
    assert m.version == "1.0.0+3"
    assert m.description == "A sample Dart package."
    assert m.dependencies == ["http", "path", "test"]


def test_parse_pubspec_yaml_unquoted_numeric_version_is_a_string() -> None:
    notes: list[str] = []
    [m] = parse_manifests({"pubspec.yaml": "name: x\nversion: 1.0\n"}, notes)
    assert m.version == "1.0"


def test_parse_pubspec_yaml_malformed_is_noted_not_raised() -> None:
    notes: list[str] = []
    assert parse_manifests({"pubspec.yaml": "name: [unclosed\n"}, notes) == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_pubspec_yaml_non_mapping_is_noted_not_raised() -> None:
    notes: list[str] = []
    assert parse_manifests({"pubspec.yaml": "- just\n- a list\n"}, notes) == []
    assert any("malformed manifest" in n for n in notes)


def test_parse_gemfile_fixture(fixtures_dir: Path) -> None:
    [m] = _parse_fixture(fixtures_dir, "ruby_repo", "Gemfile")
    assert m.kind == "Gemfile"
    assert m.name is None
    assert m.dependencies == ["rails", "puma", "rspec-rails"]


def test_parse_manifests_finds_nested_manifest_by_filename() -> None:
    notes: list[str] = []
    [m] = parse_manifests({"crates/core/Cargo.toml": '[package]\nname = "core"\n'}, notes)
    assert m.path == "crates/core/Cargo.toml"
    assert m.name == "core"
