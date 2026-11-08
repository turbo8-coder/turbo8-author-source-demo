"""Prepare a complete author index and the assets needed by this release."""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from online_cart_metadata import cart_info, next_version


def build(folder, previous, output, tag):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", tag):
        raise ValueError("Invalid release tag")
    old = {item["id"]: item for item in previous.get("cartridges", [])}
    versions = dict(previous.get("last_versions", {}))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for path in sorted(folder.glob("*.zip")):
        info = cart_info(path)
        identity = info["id"]
        prior = old.get(identity)
        if prior and prior["sha256"] == info["sha256"]:
            entries.append(prior)
            continue
        version = next_version(versions.get(identity, prior["version"] if prior else ""))
        asset = f"{identity}-v{version}.zip"
        shutil.copyfile(path, output / asset)
        cover = info.pop("cover_bytes")
        digest = hashlib.sha256(cover).hexdigest()
        (output / f"{digest}.png").write_bytes(cover)
        info.update(version=version, tag=tag, asset=asset, updated_at=now,
                    cover=dict(path=f"covers/{digest}.png", sha256=digest,
                               bytes=len(cover), width=256, height=144))
        versions[identity] = version
        entries.append(info)
    catalog = dict(schema=1, cartridges=entries, last_versions=versions)
    payload = json.dumps(catalog, ensure_ascii=False, indent=2).encode("utf-8")
    if len(payload) > 1024 * 1024 or len(entries) > 5000:
        raise ValueError("Catalog exceeds Turbo8 limits")
    (output / "catalog-v2.json").write_bytes(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    previous = json.loads(args.previous.read_text()) if args.previous else {}
    build(Path("cartridges"), previous, args.output, args.tag)
