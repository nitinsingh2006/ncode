"""Platform-independent Nitin Editor domain model.

This package deliberately has no Qt dependency so it can be reused by desktop,
Android tooling, and tests.
"""

from .languages import LANGUAGES, LANGUAGE_EXTENSIONS, EXTENSION_MAP, detect_language
from .platform import HostPlatform, detect_host_platform
from .project import Project, ProjectFile, load_project, save_project

__all__ = [
    "LANGUAGES", "LANGUAGE_EXTENSIONS", "EXTENSION_MAP", "detect_language",
    "HostPlatform", "detect_host_platform", "Project", "ProjectFile",
    "load_project", "save_project",
]
