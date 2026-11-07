"""
ncode — File Tree Widget
Left-sidebar file explorer: open a folder and browse its files.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal as Sig
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFileDialog, QSizePolicy,
    QLineEdit,
)

# Directories to skip when building the tree
_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".eggs", "*.egg-info",
}

_STYLE = """
QWidget#FileTreeRoot {
    background-color: #1e1e2e;
}
QTreeWidget {
    background-color: #181825;
    color: #cdd6f4;
    border: none;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 2px 4px;
    border-radius: 3px;
}
QTreeWidget::item:selected {
    background-color: #313244;
    color: #cdd6f4;
}
QTreeWidget::item:hover {
    background-color: #242436;
}
QTreeWidget::branch {
    background: transparent;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #45475a;
}
QLabel#FolderLabel {
    color: #89b4fa;
    font-size: 12px;
    font-weight: bold;
    padding: 4px 2px;
}
QLineEdit {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}
"""

# File extension → emoji icon
_EXT_ICONS: dict[str, str] = {
    ".py": "🐍", ".js": "🟨", ".ts": "🔷", ".html": "🌐", ".htm": "🌐",
    ".css": "🎨", ".cpp": "⚙", ".cc": "⚙", ".cxx": "⚙", ".c": "🔧",
    ".java": "☕", ".go": "🐹", ".rs": "🦀", ".kt": "🎯", ".swift": "🍎",
    ".rb": "💎", ".php": "🐘", ".sql": "🗄", ".db": "🗄", ".md": "📝",
    ".txt": "📄", ".json": "📋", ".yaml": "📋", ".yml": "📋", ".toml": "📋",
    ".sh": "⚡", ".bash": "⚡", ".lua": "🌙", ".r": "📊", ".dart": "🎯",
    ".cs": "🔷", ".scala": "🔴", ".pl": "🐪", ".hs": "λ",
}


def _file_icon(name: str) -> str:
    ext = Path(name).suffix.lower()
    return _EXT_ICONS.get(ext, "📄")


class FileTreeWidget(QWidget):
    """Left-sidebar file tree. Emits file_opened(str) on double-click."""

    file_opened = Sig(str)   # absolute file path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FileTreeRoot")
        self.setStyleSheet(_STYLE)
        self._root_path: Path | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        # Header row: label
        self._folder_label = QLabel("No folder open")
        self._folder_label.setObjectName("FolderLabel")
        self._folder_label.setWordWrap(True)
        layout.addWidget(self._folder_label)

        # Search / filter
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Filter files…")
        self._search.textChanged.connect(self._filter_tree)
        layout.addWidget(self._search)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._open_btn = QPushButton("📁 Open Folder")
        self._open_btn.setToolTip("Open a project folder")
        self._open_btn.clicked.connect(self._choose_folder)
        btn_row.addWidget(self._open_btn)

        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setToolTip("Refresh tree")
        self._refresh_btn.setFixedWidth(36)
        self._refresh_btn.clicked.connect(self._refresh)
        btn_row.addWidget(self._refresh_btn)

        layout.addLayout(btn_row)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree)

    # ── Public API ─────────────────────────────────────────────────────────────

    def open_folder(self, path: str | Path) -> None:
        """Load the given folder into the tree."""
        self._root_path = Path(path).resolve()
        self._folder_label.setText(f"📂 {self._root_path.name}")
        self._folder_label.setToolTip(str(self._root_path))
        self._search.clear()
        self._populate_tree()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _choose_folder(self) -> None:
        start = str(self._root_path) if self._root_path else str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", start)
        if folder:
            self.open_folder(folder)

    def _refresh(self) -> None:
        if self._root_path:
            self._populate_tree()

    def _populate_tree(self) -> None:
        self._tree.clear()
        if self._root_path is None:
            return
        root_item = QTreeWidgetItem([f"📂 {self._root_path.name}"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(self._root_path))
        root_item.setFont(0, QFont("", -1, QFont.Weight.Bold))
        self._tree.addTopLevelItem(root_item)
        self._fill_dir(root_item, self._root_path, depth=0)
        root_item.setExpanded(True)

    def _fill_dir(self, parent: QTreeWidgetItem, dir_path: Path, depth: int) -> None:
        if depth > 8:   # safety: don't recurse too deep
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        for entry in entries:
            # Skip hidden + blacklisted dirs
            if entry.name.startswith(".") and entry.name != ".env":
                continue
            if entry.is_dir() and entry.name in _SKIP_DIRS:
                continue

            if entry.is_dir():
                item = QTreeWidgetItem([f"📁 {entry.name}"])
                item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                parent.addChild(item)
                self._fill_dir(item, entry, depth + 1)
            else:
                icon = _file_icon(entry.name)
                item = QTreeWidgetItem([f"{icon} {entry.name}"])
                item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                parent.addChild(item)

    def _on_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str and Path(path_str).is_file():
            self.file_opened.emit(path_str)

    def _filter_tree(self, text: str) -> None:
        """Show/hide tree items based on filter text."""
        text = text.strip().lower()

        def _apply(item: QTreeWidgetItem) -> bool:
            """Returns True if item or any child matches."""
            label = item.text(0).lower()
            any_child_visible = False
            for i in range(item.childCount()):
                child_visible = _apply(item.child(i))
                any_child_visible = any_child_visible or child_visible

            if not text:
                visible = True
            else:
                visible = text in label or any_child_visible

            item.setHidden(not visible)
            if any_child_visible:
                item.setExpanded(True)
            return visible

        for i in range(self._tree.topLevelItemCount()):
            _apply(self._tree.topLevelItem(i))
