"""Load MuJoCo models safely on Windows paths with non-ASCII characters.

MuJoCo's native from_xml_path() often fails on Windows when the path contains
non-ASCII characters (e.g. Chinese folder names like 下载), even if Python
Path.exists() succeeds.

Strategy: if the path is non-ASCII, copy the MJCF + meshes into an ASCII-only
temp directory and load from there. ASCII paths use from_xml_path directly.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import mujoco

_FILE_ATTR_RE = re.compile(r'\bfile="([^"]+)"')
_MESHDIR_RE = re.compile(r'\bmeshdir="([^"]*)"')


def _path_is_ascii(path: Path) -> bool:
    try:
        str(path.resolve()).encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def _meshdir_for(xml_path: Path, xml_text: str) -> Path:
    match = _MESHDIR_RE.search(xml_text)
    if not match:
        return xml_path.parent
    return (xml_path.parent / match.group(1)).resolve()


def stage_mjcf_to_ascii_temp(xml_path: str | Path) -> Path:
    """Copy MJCF + referenced meshes to an ASCII-only temp dir."""
    src_xml = Path(xml_path).resolve()
    if not src_xml.is_file():
        raise FileNotFoundError(src_xml)

    xml_text = src_xml.read_text(encoding="utf-8")
    src_meshdir = _meshdir_for(src_xml, xml_text)

    tmp = Path(tempfile.mkdtemp(prefix="wuji_mjcf_"))
    dst_mesh = tmp / "meshes"
    dst_mesh.mkdir(parents=True, exist_ok=True)

    # Point meshdir at local ASCII folder; keep original file basenames.
    if _MESHDIR_RE.search(xml_text):
        new_xml = _MESHDIR_RE.sub('meshdir="meshes/"', xml_text, count=1)
    else:
        new_xml = xml_text.replace(
            "<compiler",
            '<compiler meshdir="meshes/"',
            1,
        )

    # Normalize file attributes to basenames so meshdir+file resolves cleanly.
    def _basename_file(match: re.Match[str]) -> str:
        return f'file="{Path(match.group(1)).name}"'

    new_xml = _FILE_ATTR_RE.sub(_basename_file, new_xml)
    dst_xml = tmp / src_xml.name
    dst_xml.write_text(new_xml, encoding="utf-8")

    copied: set[str] = set()
    for rel in _FILE_ATTR_RE.findall(xml_text):
        name = Path(rel).name
        if name in copied:
            continue
        src = src_meshdir / rel
        if not src.is_file():
            src = src_meshdir / name
        if not src.is_file():
            src = src_xml.parent / rel
        if not src.is_file():
            continue
        shutil.copy2(src, dst_mesh / name)
        copied.add(name)

    return dst_xml


def load_mjmodel(xml_path: str | Path) -> mujoco.MjModel:
    """Load an MJCF model, resilient to non-ASCII Windows paths."""
    path = Path(xml_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    if _path_is_ascii(path):
        try:
            return mujoco.MjModel.from_xml_path(str(path))
        except ValueError:
            # Rare: path ascii-encodable but native open still fails.
            pass

    staged = stage_mjcf_to_ascii_temp(path)
    return mujoco.MjModel.from_xml_path(str(staged))
