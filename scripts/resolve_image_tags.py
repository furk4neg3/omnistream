#!/usr/bin/env python3
"""Resolve deterministic OmniStream container image tags.

The output is compatible with GitHub Actions $GITHUB_OUTPUT and is also
readable as simple key=value lines for local verification.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


SERVICES = {
    "query-api": "query_api_image",
    "processing-agent": "processing_agent_image",
    "producer": "producer_image",
}
DEFAULT_NAMESPACE = "omnistream"
DEFAULT_ENV_FILE = ".env.example"
DEFAULT_SHA_LENGTH = 12

IMAGE_COMPONENT_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")


def read_env_value(path: Path, key: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        found_key, value = line.split("=", 1)
        if found_key.strip() == key:
            return value.strip().strip("\"'")
    return None


def git_sha_from_repo() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def resolve_app_version(explicit: str | None, env_file: Path) -> str:
    app_version = (
        explicit
        or os.environ.get("APP_VERSION")
        or read_env_value(env_file, "APP_VERSION")
    )
    if not app_version:
        raise ValueError("APP_VERSION is required or must be present in .env.example")
    if not TAG_RE.fullmatch(app_version):
        raise ValueError(f"APP_VERSION is not a valid Docker tag component: {app_version}")
    return app_version


def resolve_git_sha(explicit: str | None) -> str:
    git_sha = (
        explicit
        or os.environ.get("GITHUB_SHA")
        or os.environ.get("GIT_SHA")
        or git_sha_from_repo()
    )
    if not git_sha:
        raise ValueError("A git SHA is required from --git-sha, GITHUB_SHA, GIT_SHA, or git")
    if not SHA_RE.fullmatch(git_sha):
        raise ValueError(f"Git SHA is not a valid hex commit id: {git_sha}")
    return git_sha.lower()


def normalize_registry(registry: str | None) -> str:
    normalized = (registry or "").strip().rstrip("/")
    if normalized.startswith(("http://", "https://")):
        raise ValueError("OMNISTREAM_IMAGE_REGISTRY must be a registry host, not a URL")
    if "/" in normalized:
        raise ValueError("OMNISTREAM_IMAGE_REGISTRY must not include a namespace path")
    return normalized


def validate_namespace(namespace: str) -> str:
    normalized = namespace.strip().strip("/")
    if not normalized:
        raise ValueError("OMNISTREAM_IMAGE_NAMESPACE must not be empty")
    for component in normalized.split("/"):
        if not IMAGE_COMPONENT_RE.fullmatch(component):
            raise ValueError(
                "OMNISTREAM_IMAGE_NAMESPACE contains an invalid image path "
                f"component: {component}"
            )
    return normalized


def image_ref(registry: str, namespace: str, service: str, tag: str) -> str:
    repository = f"{namespace}/{service}"
    if registry:
        repository = f"{registry}/{repository}"
    return f"{repository}:{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve OmniStream image references for CI build validation."
    )
    parser.add_argument("--app-version", help="Application version for immutable tags.")
    parser.add_argument("--git-sha", help="Git SHA for immutable tags.")
    parser.add_argument(
        "--registry",
        default=os.environ.get("OMNISTREAM_IMAGE_REGISTRY", ""),
        help="Optional future registry host. Leave empty for local/CI validation.",
    )
    parser.add_argument(
        "--namespace",
        default=os.environ.get("OMNISTREAM_IMAGE_NAMESPACE", DEFAULT_NAMESPACE),
        help="Image namespace shared by all OmniStream services.",
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="Env template used as the fallback APP_VERSION source.",
    )
    parser.add_argument(
        "--sha-length",
        type=int,
        default=DEFAULT_SHA_LENGTH,
        help="Number of git SHA characters to include in the image tag.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        app_version = resolve_app_version(args.app_version, Path(args.env_file))
        git_sha = resolve_git_sha(args.git_sha)
        if args.sha_length < 7 or args.sha_length > len(git_sha):
            raise ValueError("--sha-length must be at least 7 and no longer than the git SHA")
        registry = normalize_registry(args.registry)
        namespace = validate_namespace(args.namespace)
        git_sha_short = git_sha[: args.sha_length]
        image_tag = f"{app_version}-{git_sha_short}"
        if not TAG_RE.fullmatch(image_tag):
            raise ValueError(f"Resolved image tag is invalid: {image_tag}")
    except ValueError as exc:
        print(f"error={exc}", file=sys.stderr)
        return 2

    print(f"app_version={app_version}")
    print(f"git_sha={git_sha}")
    print(f"git_sha_short={git_sha_short}")
    print(f"image_tag={image_tag}")
    for service, output_key in SERVICES.items():
        print(f"{output_key}={image_ref(registry, namespace, service, image_tag)}")
        print(f"{output_key}_local={image_ref('', namespace, service, 'local')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
