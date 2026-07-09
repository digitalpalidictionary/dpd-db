#!/usr/bin/env python3
"""
Digital Pāḷi Dictionary — Project Health Check

Fetches open issues, PRs, latest commit, and latest release for each repo
under digitalpalidictionary using gh api. Formats a terminal report.

Usage:
    uv run scripts/project_health_check.py [--full] [--repo REPO_NAME]
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any

ACTIVE_REPOS = [
    "dpd-db",
    "dpd-flutter-app",
    "dpd-pali-courses",
    "digitalpalidictionary.github.io",
    "dpd-audio",
    "dpd_submodules",
    "other-dictionaries",
    "tipitaka-translation-db",
    "dpd-updater-go",
    "dpd-updater",
    "dpd-app",
    "dpd-chrome-extenstion",
    "discussions",
    "sutta_analysis",
]

STALE_DAYS = 30
IST = timezone(timedelta(hours=5, minutes=30))


def gh_jq(path: str, jq: str) -> str | None:
    try:
        r = subprocess.run(
            ["gh", "api", path, "--jq", jq],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def gh(path: str) -> Any:
    try:
        r = subprocess.run(
            ["gh", "api", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def check_auth() -> bool:
    return gh("user") is not None


def days_ago(iso_str: str | None) -> int | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return None


def fmt_age(iso_str: str | None) -> str:
    d = days_ago(iso_str)
    if d is None:
        return "?"
    if d == 0:
        return "today"
    if d == 1:
        return "1d"
    if d < 30:
        return f"{d}d"
    if d < 365:
        return f"{d // 30}mo"
    return f"{d // 365}y"


def is_stale(iso_str: str | None) -> bool:
    d = days_ago(iso_str)
    return d is not None and d >= STALE_DAYS


def scan_repo(repo: str) -> dict[str, Any]:
    owner = "digitalpalidictionary"
    base = f"repos/{owner}/{repo}"

    # GitHub's issues endpoint also returns PRs; filter them out by key absence
    issues_raw: list[Any] = (
        gh(f"{base}/issues?state=open&per_page=100&sort=updated&direction=desc") or []
    )
    issues = [i for i in issues_raw if "pull_request" not in i]

    prs: list[Any] = (
        gh(f"{base}/pulls?state=open&per_page=100&sort=updated&direction=desc") or []
    )

    commit_jq = gh_jq(f"{base}/commits?per_page=1", ".[0].commit.author.date")
    latest_commit = commit_jq.strip('"') if commit_jq else None

    release_jq = gh_jq(f"{base}/releases?per_page=1", ".[0]")
    latest_release: dict[str, Any] | None = (
        json.loads(release_jq) if release_jq and release_jq != "null" else None
    )

    unlabeled = [i for i in issues if not i.get("labels")]
    stale_issues = [i for i in issues if is_stale(i.get("updated_at"))]
    stale_prs = [p for p in prs if is_stale(p.get("updated_at"))]

    return {
        "name": repo,
        "issues": issues,
        "prs": prs,
        "unlabeled": unlabeled,
        "stale_issues": stale_issues,
        "stale_prs": stale_prs,
        "latest_commit": latest_commit,
        "latest_release": latest_release,
    }


def print_report(results: list[dict[str, Any]]) -> None:
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    total_issues = sum(len(r["issues"]) for r in results)
    total_prs = sum(len(r["prs"]) for r in results)
    total_stale_i = sum(len(r["stale_issues"]) for r in results)
    total_stale_p = sum(len(r["stale_prs"]) for r in results)
    total_unlabeled = sum(len(r["unlabeled"]) for r in results)

    sep = "  " + "=" * 57
    thin = "  " + "-" * 57

    print()
    print(f"  DPD Project Health Report  —  {now}")
    print(sep)
    print(
        f"  {len(results)} repos  |  {total_issues} open issues  |  {total_prs} open PRs"
    )
    print(
        f"  {total_stale_i} stale issues (>30d)  |  {total_stale_p} stale PRs  |  {total_unlabeled} unlabeled issues"
    )
    print()

    has_attention = False
    for r in results:
        if not r["unlabeled"] and not r["stale_issues"]:
            continue
        has_attention = True
        print(f"  [{r['name']}]")

        if r["unlabeled"]:
            print(f"    ~ Unlabeled ({len(r['unlabeled'])}):")
            for i in r["unlabeled"][:6]:
                print(
                    f"      #{i['number']}  {i['title'][:58]}  ({fmt_age(i.get('updated_at'))})"
                )
            if len(r["unlabeled"]) > 6:
                print(f"      ... +{len(r['unlabeled']) - 6} more")
            print()

        if r["stale_issues"]:
            shown = {i["number"] for i in r["unlabeled"]}
            stale_only = [i for i in r["stale_issues"] if i["number"] not in shown]
            if stale_only:
                print(f"    ! Stale ({len(stale_only)}):")
                for i in stale_only[:6]:
                    labels = ", ".join(lbl["name"] for lbl in i.get("labels", []))
                    print(
                        f"      #{i['number']}  [{labels}]  {i['title'][:48]}  ({fmt_age(i.get('updated_at'))})"
                    )
                if len(stale_only) > 6:
                    print(f"      ... +{len(stale_only) - 6} more")
                print()

    if not has_attention:
        print("  No issues need attention.")
        print()

    repos_with_prs = [r for r in results if r["prs"]]
    if repos_with_prs:
        print(thin)
        print("  Open PRs:")
        for r in repos_with_prs:
            stale_tag = "  [!]" if r["stale_prs"] else ""
            print(f"    [{r['name']}]{stale_tag}")
            for p in r["prs"]:
                author = (p.get("user") or {}).get("login", "?")
                print(
                    f"      #{p['number']}  {p['title'][:55]}  by {author}  ({fmt_age(p.get('updated_at'))})"
                )
        print()

    print(thin)
    print("  Latest activity per repo:")
    for r in results:
        c_age = fmt_age(r["latest_commit"])
        rel_str = ""
        if r["latest_release"]:
            rel = r["latest_release"]
            rel_str = (
                f"   release: {rel['tag_name']} ({fmt_age(rel.get('published_at'))})"
            )
        print(f"    {r['name']:<38}  commit: {c_age}{rel_str}")

    print()
    print(sep)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DPD Project Health Check")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--full", action="store_true", help="Scan all non-archived org repos"
    )
    group.add_argument("--repo", metavar="REPO_NAME", help="Scan a single named repo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not check_auth():
        print("  ERROR: gh is not available or not authenticated. Run: gh auth login")
        sys.exit(1)

    repos: list[str]
    if args.repo:
        repos = [args.repo]
    elif args.full:
        data = gh(
            "orgs/digitalpalidictionary/repos?per_page=100&sort=updated&direction=desc"
        )
        repos = (
            [r["name"] for r in data if not r.get("archived")] if data else ACTIVE_REPOS
        )
    else:
        repos = ACTIVE_REPOS

    print(f"  Scanning {len(repos)} repos ...")
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(scan_repo, repo): repo for repo in repos}
        for future in as_completed(futures):
            repo_name = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f"  WARNING: {repo_name} raised {exc}")

    results.sort(key=lambda r: r["name"])
    if results:
        print_report(results)
    else:
        print("  Nothing collected.")


if __name__ == "__main__":
    main()
