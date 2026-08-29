"""Validate the textbook's consumer-level code-resource mapping."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ANCHOR_PATTERN = r"(?:\{#%s\}|<a\s+id=[\"']%s[\"'])"
MODES = {"static_read", "build", "run", "hardware"}
DEPENDENCY_KINDS = {"system", "project-resource", "runtime-asset", "toolchain"}
VERIFICATION_LEVELS = {
    "static_reviewed",
    "build_verified",
    "runtime_verified",
    "hardware_verified",
}
FORBIDDEN_VALUES = ("example_only", "schema-example", "/tree/main/", "/blob/main/")


@dataclass
class Consumer:
    page: str = ""
    anchor: str = ""
    files: list[str] = field(default_factory=list)
    role: str = ""
    mode: str = ""
    commands: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)


@dataclass
class Dependency:
    kind: str = ""
    path: str = ""
    provider: str = ""
    verification: str = ""


@dataclass
class Verification:
    level: str = ""
    source_commit: str = ""
    environment: str = ""
    command: str = ""
    result: str = ""
    evidence_path: str = ""
    verified_at: str = ""


@dataclass
class CodeResource:
    id: str = ""
    repository_path: str = ""
    consumers: list[Consumer] = field(default_factory=list)
    compatibility: dict[str, str] = field(default_factory=dict)
    dependencies: list[Dependency] = field(default_factory=list)
    verification: Verification = field(default_factory=Verification)


@dataclass
class CodeResourceMap:
    source_repository: str = ""
    source_revision: str = ""
    resources: list[CodeResource] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _consumer(data: Any) -> Consumer:
    row = data if isinstance(data, dict) else {}
    return Consumer(
        page=_as_text(row.get("page")),
        anchor=_as_text(row.get("anchor")),
        files=[_as_text(item) for item in _as_list(row.get("files"))],
        role=_as_text(row.get("role")),
        mode=_as_text(row.get("mode")),
        commands=[_as_text(item) for item in _as_list(row.get("commands"))],
        acceptance=[_as_text(item) for item in _as_list(row.get("acceptance"))],
        boundaries=[_as_text(item) for item in _as_list(row.get("boundaries"))],
    )


def _dependency(data: Any) -> Dependency:
    row = data if isinstance(data, dict) else {}
    return Dependency(
        kind=_as_text(row.get("kind")),
        path=_as_text(row.get("path")),
        provider=_as_text(row.get("provider")),
        verification=_as_text(row.get("verification")),
    )


def _verification(data: Any) -> Verification:
    row = data if isinstance(data, dict) else {}
    return Verification(**{key: _as_text(row.get(key)) for key in Verification.__dataclass_fields__})


def _resource(data: Any) -> CodeResource:
    row = data if isinstance(data, dict) else {}
    compatibility = row.get("compatibility")
    return CodeResource(
        id=_as_text(row.get("id")),
        repository_path=_as_text(row.get("repository_path")),
        consumers=[_consumer(item) for item in _as_list(row.get("consumers"))],
        compatibility={str(key): _as_text(value) for key, value in compatibility.items()}
        if isinstance(compatibility, dict)
        else {},
        dependencies=[_dependency(item) for item in _as_list(row.get("dependencies"))],
        verification=_verification(row.get("verification")),
    )


def load_code_resources(path: Path) -> CodeResourceMap:
    """Load ``metadata/code-resources.yml`` without touching either repository."""
    loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    raw = loaded if isinstance(loaded, dict) else {}
    return CodeResourceMap(
        source_repository=_as_text(raw.get("source_repository")),
        source_revision=_as_text(raw.get("source_revision")),
        resources=[_resource(item) for item in _as_list(raw.get("resources"))],
        raw=raw,
    )


def immutable_tree_url(repository: str, revision: str, path: str) -> str:
    """Return the GitHub tree URL pinned to a full commit SHA."""
    if not REVISION_PATTERN.fullmatch(revision):
        raise ValueError("source revision must be a 40-character lowercase commit SHA")
    return f"https://github.com/{repository}/tree/{revision}/{path.strip('/')}"


def _is_relative(path: str) -> bool:
    candidate = PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for value_item in value for item in _iter_strings(value_item)]
    if isinstance(value, dict):
        return [item for item_value in value.values() for item in _iter_strings(item_value)]
    return []


def _has_build_command(commands: list[str]) -> bool:
    return any("build" in command.lower() for command in commands if command.strip())


def _has_non_build_command(commands: list[str]) -> bool:
    return any("build" not in command.lower() and command.strip() for command in commands)


def _validate_consumer(consumer: Consumer, source_root: Path, prefix: str) -> list[str]:
    errors: list[str] = []
    for name, value in (("page", consumer.page), ("anchor", consumer.anchor), ("role", consumer.role)):
        if not value.strip():
            errors.append(f"{prefix}: {name} is required")
    if not consumer.files or any(not _is_relative(item) for item in consumer.files):
        errors.append(f"{prefix}: files must be non-empty relative paths")
    if not consumer.acceptance or any(not item.strip() for item in consumer.acceptance):
        errors.append(f"{prefix}: acceptance is required")
    if not consumer.boundaries or any(not item.strip() for item in consumer.boundaries):
        errors.append(f"{prefix}: boundaries is required")
    if consumer.mode not in MODES:
        errors.append(f"{prefix}: mode must be one of {sorted(MODES)}")
        return errors
    page = source_root / consumer.page
    if consumer.page and not page.is_file():
        errors.append(f"{prefix}: consumer page does not exist: {consumer.page}")
    elif consumer.anchor and not re.search(ANCHOR_PATTERN % (re.escape(consumer.anchor), re.escape(consumer.anchor)), page.read_text(encoding="utf-8")):
        errors.append(f"{prefix}: consumer anchor does not exist: {consumer.page}#{consumer.anchor}")
    if consumer.mode in {"build", "run", "hardware"} and not _has_build_command(consumer.commands):
        errors.append(f"{prefix}: {consumer.mode} mode requires a build command")
    if consumer.mode in {"run", "hardware"} and not _has_non_build_command(consumer.commands):
        errors.append(f"{prefix}: {consumer.mode} mode requires a startup command after build")
    if consumer.mode == "hardware":
        hardware_evidence = " ".join(consumer.acceptance)
        for required in ("硬件", "接线", "测量", "停止"):
            if required not in hardware_evidence:
                errors.append(f"{prefix}: hardware mode acceptance must record {required}")
    return errors


def validate_code_resource_map(mapping: CodeResourceMap, source_root: Path) -> list[str]:
    """Return every contract violation for a mapping and checked-out source tree."""
    errors: list[str] = []
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", mapping.source_repository):
        errors.append("source_repository must be an owner/repository name")
    if not REVISION_PATTERN.fullmatch(mapping.source_revision):
        errors.append("source_revision must be a 40-character lowercase commit SHA")
    for value in _iter_strings(asdict(mapping)):
        lowered = value.lower()
        for forbidden in FORBIDDEN_VALUES:
            if forbidden in lowered:
                errors.append(f"mapping contains forbidden placeholder or mutable URL: {forbidden}")

    root = source_root.resolve()
    resource_ids: set[str] = set()
    for index, resource in enumerate(mapping.resources):
        prefix = f"resource[{index}]"
        if not resource.id.strip() or resource.id in resource_ids:
            errors.append(f"{prefix}: id must be present and unique")
        resource_ids.add(resource.id)
        if not _is_relative(resource.repository_path):
            errors.append(f"{prefix}: repository_path must be a relative path")
            package_root = root
        else:
            package_root = root / resource.repository_path
            if not package_root.is_dir():
                errors.append(f"{prefix}: repository path does not exist: {resource.repository_path}")
        if not resource.consumers:
            errors.append(f"{prefix}: at least one formal consumer is required")
        for consumer_index, consumer in enumerate(resource.consumers):
            consumer_prefix = f"{prefix}.consumers[{consumer_index}]"
            errors.extend(_validate_consumer(consumer, root, consumer_prefix))
            for file_path in consumer.files:
                if _is_relative(file_path) and not (package_root / file_path).is_file():
                    errors.append(f"{consumer_prefix}: source file does not exist: {file_path}")
        if not resource.dependencies:
            errors.append(f"{prefix}: dependencies must be a non-empty structured list")
        for dependency_index, dependency in enumerate(resource.dependencies):
            dependency_prefix = f"{prefix}.dependencies[{dependency_index}]"
            if dependency.kind not in DEPENDENCY_KINDS:
                errors.append(f"{dependency_prefix}: dependency kind is invalid")
            for name, value in (("path", dependency.path), ("provider", dependency.provider), ("verification", dependency.verification)):
                if not value.strip():
                    errors.append(f"{dependency_prefix}: dependency {name} is required")
        verification = resource.verification
        if verification.level not in VERIFICATION_LEVELS:
            errors.append(f"{prefix}: verification level is invalid")
        for name in Verification.__dataclass_fields__:
            value = getattr(verification, name)
            if not value.strip():
                errors.append(f"{prefix}: verification {name} is required")
        if verification.source_commit and verification.source_commit != mapping.source_revision:
            errors.append(f"{prefix}: verification source_commit must match source_revision")
        evidence = verification.evidence_path
        if evidence and (not _is_relative(evidence) or not evidence.startswith("docs/superpowers/audits/")):
            errors.append(f"{prefix}: evidence_path must be under docs/superpowers/audits/")
        elif evidence and not (root / evidence).is_file():
            errors.append(f"{prefix}: evidence_path does not exist: {evidence}")
    return errors


def validate_appendix_matches_mapping(appendix: str, mapping: CodeResourceMap) -> None:
    """Reject an Appendix D that omits a mapped resource or formal consumer."""
    missing: list[str] = []
    for resource in mapping.resources:
        url = immutable_tree_url(mapping.source_repository, mapping.source_revision, resource.repository_path)
        if url not in appendix:
            missing.append(url)
        for consumer in resource.consumers:
            reference = f"{consumer.page}#{consumer.anchor}"
            if reference not in appendix:
                missing.append(reference)
    if missing:
        raise ValueError("appendix does not match code-resource mapping: " + ", ".join(missing))
