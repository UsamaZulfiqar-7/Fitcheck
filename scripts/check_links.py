"""Check that every free-resource link used in the lessons still opens (needs internet).

    python scripts/check_links.py
"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.learning_content import CURATED  # noqa: E402


def main() -> None:
    bad = 0
    for path in CURATED.values():
        for res in path["resources"]:
            req = urllib.request.Request(res["url"], headers={"User-Agent": "Mozilla/5.0 FitCheck-link-check"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    status = resp.status
            except Exception as exc:
                status = f"ERROR {type(exc).__name__}"
                bad += 1
            print(f"{status!s:>10}  {path['skill']:<18} {res['url']}")
    print("\nAll links reachable." if not bad else f"\n{bad} link(s) failed - open them in a browser and update core/content/*.py if needed.")


if __name__ == "__main__":
    main()
