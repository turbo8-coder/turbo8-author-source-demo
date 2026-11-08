import hashlib
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

MAX_ZIP = 32 * 1024 * 1024
LEGACY_MAX_ZIP = 8 * 1024 * 1024
MAX_COVER = 128 * 1024
COVER_SIZE = (256, 144)


def cart_info(path):
    if path.stat().st_size > MAX_ZIP:
        raise ValueError(f"{path.name}: ZIP exceeds 32 MiB")
    raw = path.read_bytes()
    if not raw.startswith(b"PK\x03\x04") or len(raw) > MAX_ZIP:
        raise ValueError(f"{path.name}: expected Turbo8 ZIP at most 32 MiB")
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) > 1024 or len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 64 * 1024 * 1024:
            raise ValueError(f"{path.name}: invalid entry count, duplicate entries or expanded ZIP exceeds 64 MiB")
        if "index.json" not in names or "cover.png" not in names:
            raise ValueError(f"{path.name}: missing index.json or cover.png")
        index = json.loads(archive.read("index.json"))
        rules = json.loads((Path(__file__).resolve().parents[1] / "Runtime/display-config.json").read_text())
        default = next(p for p in rules["presets"] if p["id"] == rules["default"])
        resolution = index.get("resolution", default)
        if not isinstance(resolution, dict):
            raise ValueError(f"{path.name}: invalid canvas resolution")
        width, height = resolution.get("width"), resolution.get("height")
        if any(type(n) not in (int, float) or not rules["minDimension"] <= n <= rules["maxDimension"] or n != int(n) for n in (width, height)):
            raise ValueError(f"{path.name}: invalid canvas dimensions")
        if width * height > rules["maxPixels"] or max(width / height, height / width) > rules["maxAspect"]:
            raise ValueError(f"{path.name}: canvas exceeds supported limits")
        cover = archive.read("cover.png")
        if len(cover) > MAX_COVER or cover[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{path.name}: cover must be PNG at most 128 KiB")
        if struct.unpack(">II", cover[16:24]) != COVER_SIZE:
            raise ValueError(f"{path.name}: cover must be 256 x 144")
        scripts = index.get("scripts") if isinstance(index, dict) else None
        if not isinstance(scripts, list) or not scripts or not all(
            isinstance(script, str) and (script if script.endswith(".js") else script + ".js") in names
            for script in scripts
        ) or any(name.startswith("/") or ".." in name for name in names):
            raise ValueError(f"{path.name}: unsafe or incomplete ZIP")
    stem = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")[:40] or "cart"
    identity = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:10]
    return {
        "id": f"{stem}-{identity}",
        "title": str(index.get("name") or path.stem)[:120],
        "source_file": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "cover_bytes": cover,
        "resolution": {"width": int(width), "height": int(height)},
    }


def next_version(previous):
    if not previous:
        return "1.0.0"
    parts = previous.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Cannot advance version {previous!r}")
    return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
