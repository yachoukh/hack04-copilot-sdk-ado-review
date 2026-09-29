from pathlib import Path


def load_report(base_dir: Path, report_name: str) -> str:
    path = base_dir / report_name
    return path.read_text(encoding="utf-8")


def write_upload(upload_dir: Path, filename: str, data: bytes) -> Path:
    target = upload_dir / filename
    if target.exists():
        target.unlink()
    target.write_bytes(data)
    return target
