"""Language weighting by file extension."""

from __future__ import annotations

from dataclasses import dataclass

from readme_forge.scanner import ScannedFile

MAX_LANGUAGES = 8

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".dart": "Dart",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
}


@dataclass
class LanguageStat:
    name: str
    file_count: int
    weight: float


def detect_languages(files: list[ScannedFile]) -> list[LanguageStat]:
    """Weight languages by their share of recognized code files."""
    counts: dict[str, int] = {}
    for scanned in files:
        language = EXTENSION_LANGUAGES.get(scanned.extension.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return []

    stats = [
        LanguageStat(name=name, file_count=count, weight=round(count / total, 4))
        for name, count in counts.items()
    ]
    stats.sort(key=lambda s: (-s.weight, s.name))
    return stats[:MAX_LANGUAGES]
