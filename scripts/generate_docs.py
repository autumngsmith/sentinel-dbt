"""Generate the static dbt docs and remove the local machine path from them.

Runs `dbt docs generate --static`, then replaces the project's absolute path
(which includes the local username) in `target/static_index.html` with the
repo folder name. Nothing in the docs page reads that path, so the docs work
the same. Use this instead of calling `dbt docs generate` directly.

Usage:
    python scripts/generate_docs.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "target" / "static_index.html"


def main():
    dbt = Path(sys.executable).parent / "dbt"
    subprocess.run([str(dbt), "docs", "generate", "--static"], cwd=ROOT, check=True)

    html = DOCS.read_text()
    count = html.count(str(ROOT))
    html = html.replace(str(ROOT), ROOT.name)
    DOCS.write_text(html)
    print(f"Removed {count} local path(s) from {DOCS.relative_to(ROOT)}")

    if str(Path.home()) in html:
        raise SystemExit(f"{DOCS.relative_to(ROOT)} still contains {Path.home()}")


if __name__ == "__main__":
    main()
