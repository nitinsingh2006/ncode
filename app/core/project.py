"""Portable, relative-path `project.ncode` persistence format (format v1)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_FILENAME = "project.ncode"
PROJECT_FORMAT_VERSION = 1


def _relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Project file paths must be relative and may not escape the project")
    return path.as_posix()


@dataclass(frozen=True)
class ProjectFile:
    path: str
    language: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _relative_path(self.path))


@dataclass
class Project:
    name: str
    files: list[ProjectFile] = field(default_factory=list)
    open_tabs: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    run_configuration: dict[str, Any] = field(default_factory=dict)
    database: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": PROJECT_FORMAT_VERSION,
            "name": self.name,
            "files": [{"path": f.path, "language": f.language} for f in self.files],
            "open_tabs": [_relative_path(p) for p in self.open_tabs],
            "settings": self.settings,
            "run_configuration": self.run_configuration,
            "database": self.database,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        if data.get("format_version", PROJECT_FORMAT_VERSION) != PROJECT_FORMAT_VERSION:
            raise ValueError("Unsupported project.ncode format version")
        files = [ProjectFile(item["path"], item.get("language")) for item in data.get("files", [])]
        return cls(
            name=str(data.get("name", "Untitled Project")), files=files,
            open_tabs=[_relative_path(str(p)) for p in data.get("open_tabs", [])],
            settings=dict(data.get("settings", {})),
            run_configuration=dict(data.get("run_configuration", {})),
            database=dict(data.get("database", {})),
        )


def save_project(project: Project, directory: str | Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / PROJECT_FILENAME
    path.write_text(json.dumps(project.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_project(path: str | Path) -> Project:
    path = Path(path)
    if path.is_dir():
        path = path / PROJECT_FILENAME
    with path.open(encoding="utf-8") as handle:
        return Project.from_dict(json.load(handle))
