"""One-time publish of the three things the GitHub repo holds (besides agent-written files):
the registration app (aut/) and the step definitions needed to run the feature files.

Dry run by default. Pass --publish to commit to the configured repo (a real write).

    python -m scripts.publish_repo_assets [--publish]
"""
import sys

from agent_app.config import ROOT, ServiceError, load_settings
from agent_app.services.github_client import GitHubClient

TEMPLATE = ROOT / "repo_template"
# (local file, path in the repo)
FILES = [
    (ROOT / "aut" / "index.html", "aut/index.html"),
    (ROOT / "aut" / "style.css", "aut/style.css"),
    (ROOT / "aut" / "app.js", "aut/app.js"),
    (ROOT / "aut" / "serve.py", "aut/serve.py"),
    (ROOT / "tests_runtime" / "conftest.py", "tests/conftest.py"),
    (ROOT / "tests_runtime" / "steps" / "registration_steps.py", "tests/steps/registration_steps.py"),
    (TEMPLATE / "test_features.py", "tests/test_features.py"),
    (TEMPLATE / "README.md", "README.md"),
    (TEMPLATE / "requirements.txt", "requirements.txt"),
]
EMPTY = ["tests/__init__.py", "tests/steps/__init__.py"]


def main() -> int:
    publish = "--publish" in sys.argv
    items = [(p.read_text(encoding="utf-8"), dest) for p, dest in FILES] + [("", d) for d in EMPTY]
    for _, dest in items:
        print(("publish " if publish else "would publish ") + dest)
    if not publish:
        print("\nDry run. Re-run with --publish to commit these files.")
        return 0
    try:
        s = load_settings()
        gh = GitHubClient(s.github_token, s.github_repo, s.github_branch)
        for content, dest in items:
            print(f"  {dest}: {gh.push_file(dest, content, f'Add {dest}')}")
    except ServiceError as exc:
        print(f"FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
