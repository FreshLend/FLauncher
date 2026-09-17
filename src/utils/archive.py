import zipfile
from pathlib import Path


def safe_extract_zip(zip_path, target_dir):
    target_dir = Path(target_dir).resolve()
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            try:
                member_path = (target_dir / member).resolve()
                member_path.relative_to(target_dir)
            except ValueError:
                raise Exception(f"Unsafe path in archive: {member}")
        zf.extractall(target_dir)