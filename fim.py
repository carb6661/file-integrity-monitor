"""Small, dependency-free file integrity monitoring utility.

The tool snapshots SHA-256 digests under a directory and later reports files
that were added, removed, or changed.  It is intended for local, authorized
integrity checks and for learning about cryptographic hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

MANIFEST_VERSION = 1


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of *path* without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path, excludes: Iterable[Path] = ()) -> Iterable[Path]:
    """Yield regular files below root, excluding exact resolved paths."""
    excluded = {item.resolve() for item in excludes}
    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories[:] = [
            directory
            for directory in directories
            if not (current_path / directory).is_symlink()
        ]
        for filename in filenames:
            candidate = current_path / filename
            if candidate.is_file() and not candidate.is_symlink() and candidate.resolve() not in excluded:
                yield candidate


def build_manifest(root: Path, manifest_path: Path) -> Dict[str, object]:
    """Build a deterministic manifest for files under root."""
    root = root.resolve()
    files = {
        file.relative_to(root).as_posix(): sha256_file(file)
        for file in sorted(iter_files(root, [manifest_path]), key=lambda item: item.as_posix())
    }
    return {
        "version": MANIFEST_VERSION,
        "algorithm": "sha256",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": files,
    }


def write_manifest(manifest: Dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(source: Path) -> Dict[str, object]:
    try:
        manifest = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取清单：{error}") from error
    if manifest.get("version") != MANIFEST_VERSION or manifest.get("algorithm") != "sha256":
        raise ValueError("不支持的清单版本或摘要算法")
    if not isinstance(manifest.get("files"), dict):
        raise ValueError("清单缺少 files 对象")
    return manifest


def compare(expected: Dict[str, str], actual: Dict[str, str]) -> Tuple[list[str], list[str], list[str]]:
    """Return (added, removed, modified) file-name lists."""
    added = sorted(set(actual) - set(expected))
    removed = sorted(set(expected) - set(actual))
    modified = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    return added, removed, modified


def snapshot_command(args: argparse.Namespace) -> int:
    root, output = Path(args.directory), Path(args.output)
    if not root.is_dir():
        raise ValueError(f"目录不存在：{root}")
    manifest = build_manifest(root, output)
    write_manifest(manifest, output)
    print(f"已写入 {len(manifest['files'])} 个文件的清单：{output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    root, manifest_file = Path(args.directory), Path(args.manifest)
    if not root.is_dir():
        raise ValueError(f"目录不存在：{root}")
    manifest = load_manifest(manifest_file)
    actual = build_manifest(root, manifest_file)["files"]
    added, removed, modified = compare(manifest["files"], actual)
    if not any((added, removed, modified)):
        print("完整性检查通过：未发现变化。")
        return 0
    for label, files in (("新增", added), ("删除", removed), ("修改", modified)):
        for file in files:
            print(f"[{label}] {file}")
    print(f"完整性检查失败：新增 {len(added)}，删除 {len(removed)}，修改 {len(modified)}。")
    return 1


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description="本地授权目录的 SHA-256 文件完整性监控工具")
    commands = cli.add_subparsers(dest="command", required=True)
    for name, handler in (("snapshot", snapshot_command), ("verify", verify_command)):
        command = commands.add_parser(name)
        command.add_argument("directory", help="要扫描的目录")
        options = ("-m", "--manifest") if name == "verify" else ("-o", "--output")
        command.add_argument(*options, required=True, help="清单文件路径")
        command.set_defaults(handler=handler)
    return cli


def main() -> int:
    try:
        args = parser().parse_args()
        return args.handler(args)
    except ValueError as error:
        print(f"错误：{error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
