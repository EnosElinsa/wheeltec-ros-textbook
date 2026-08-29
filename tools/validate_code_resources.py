"""Validate the textbook's consumer-level code-resource mapping."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
LEGACY_NUMBERED_COMPONENT = re.compile(r"^\d{4}(?:-|$)")
ANCHOR_PATTERN = r"(?:\{#%s\}|<a\s+id=[\"']%s[\"'])"
MODES = {"static_read", "build", "run", "hardware"}
DEPENDENCY_KINDS = {"system", "project-resource", "runtime-asset", "toolchain"}
VERIFICATION_LEVELS = {
    "static_reviewed",
    "build_verified",
    "runtime_verified",
    "hardware_verified",
}
MODE_VERIFICATION_LEVELS = {
    "static_read": VERIFICATION_LEVELS,
    "build": {"build_verified", "runtime_verified", "hardware_verified"},
    "run": {"runtime_verified", "hardware_verified"},
    "hardware": {"hardware_verified"},
}
FORBIDDEN_VALUES = ("example_only", "schema-example", "/tree/main/", "/blob/main/")
APPENDIX_FORBIDDEN = (
    "/tree/main/",
    "G-archive",
    "R-archive",
    "baseline-",
    "release",
    "catalog",
    "docs/superpowers",
    "C:\\",
    "归档整理",
    "构建这个代码库",
)
APPENDIX_CATEGORIES = (
    "ROS 2 基础与启动",
    "ROS 2 导航",
    "ROS 1 维护",
    "视觉与应用",
    "STM32 外设实验",
    "STM32 控制",
    "R680 固件",
)

MAP_KEYS = {"source_repository", "source_revision", "resources"}
RESOURCE_KEYS = {"id", "repository_path", "consumers", "compatibility", "dependencies", "verification"}
CONSUMER_KEYS = {"page", "anchor", "files", "file_manifest", "role", "mode", "commands", "acceptance", "boundaries"}
DEPENDENCY_KEYS = {"kind", "path", "provider", "verification"}
VERIFICATION_KEYS = {"level", "source_commit", "environment", "command", "result", "evidence_path", "verified_at"}
COMPATIBILITY_KEYS = {"ros_distribution", "platform", "hardware"}
APPROVED_SOURCE_ROOTS = {"applications", "chassis", "examples", "platform", "r680", "ros1", "ros2", "stm32"}
FORBIDDEN_SOURCE_ROOTS = {"docs", "tools", "catalog", "config", "tests", "archives", "releases", "release"}


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
    file_manifest: str = ""


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


def _schema_error(location: str, message: str) -> ValueError:
    return ValueError(f"{location} {message}")


def _require_mapping(data: Any, location: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise _schema_error(location, "must be a mapping")
    for key in keys:
        if key not in data:
            raise _schema_error(location, f"missing required key: {key}")
    unknown = set(data) - keys
    if unknown:
        raise _schema_error(location, f"unknown key: {sorted(unknown)[0]}")
    return data


def _require_string(value: Any, location: str) -> str:
    if not isinstance(value, str):
        raise _schema_error(location, "must be a string")
    return value


def _require_string_list(value: Any, location: str) -> list[str]:
    if not isinstance(value, list):
        raise _schema_error(location, "must be a list")
    return [_require_string(item, f"{location}[{index}]") for index, item in enumerate(value)]


def _consumer(data: Any) -> Consumer:
    if not isinstance(data, dict):
        raise _schema_error("consumer", "must be a mapping")
    row = dict(data)
    row.setdefault("file_manifest", "")
    unknown = set(row) - CONSUMER_KEYS
    if unknown:
        raise _schema_error("consumer", f"unknown key: {sorted(unknown)[0]}")
    for key in CONSUMER_KEYS - {"file_manifest"}:
        if key not in row:
            raise _schema_error("consumer", f"missing required key: {key}")
    return Consumer(
        page=_require_string(row["page"], "consumer.page"),
        anchor=_require_string(row["anchor"], "consumer.anchor"),
        files=_require_string_list(row["files"], "consumer.files"),
        file_manifest=_require_string(row["file_manifest"], "consumer.file_manifest"),
        role=_require_string(row["role"], "consumer.role"),
        mode=_require_string(row["mode"], "consumer.mode"),
        commands=_require_string_list(row["commands"], "consumer.commands"),
        acceptance=_require_string_list(row["acceptance"], "consumer.acceptance"),
        boundaries=_require_string_list(row["boundaries"], "consumer.boundaries"),
    )


def _dependency(data: Any) -> Dependency:
    row = _require_mapping(data, "dependency", DEPENDENCY_KEYS)
    return Dependency(
        kind=_require_string(row["kind"], "dependency.kind"),
        path=_require_string(row["path"], "dependency.path"),
        provider=_require_string(row["provider"], "dependency.provider"),
        verification=_require_string(row["verification"], "dependency.verification"),
    )


def _verification(data: Any) -> Verification:
    row = _require_mapping(data, "verification", VERIFICATION_KEYS)
    return Verification(**{key: _require_string(row[key], f"verification.{key}") for key in Verification.__dataclass_fields__})


def _resource(data: Any) -> CodeResource:
    row = _require_mapping(data, "resource", RESOURCE_KEYS)
    compatibility = _require_mapping(row["compatibility"], "resource.compatibility", COMPATIBILITY_KEYS)
    consumers = row["consumers"]
    dependencies = row["dependencies"]
    if not isinstance(consumers, list):
        raise _schema_error("resources[0].consumers", "must be a list")
    if not isinstance(dependencies, list):
        raise _schema_error("resource.dependencies", "must be a list")
    return CodeResource(
        id=_require_string(row["id"], "resource.id"),
        repository_path=_require_string(row["repository_path"], "resource.repository_path"),
        consumers=[_consumer(item) for item in consumers],
        compatibility={key: _require_string(value, f"resource.compatibility.{key}") for key, value in compatibility.items()},
        dependencies=[_dependency(item) for item in dependencies],
        verification=_verification(row["verification"]),
    )


def load_code_resources(path: Path) -> CodeResourceMap:
    """Load ``metadata/code-resources.yml`` without touching either repository."""
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid YAML: {error}") from error
    raw = _require_mapping(loaded, "mapping", MAP_KEYS)
    resources = raw["resources"]
    if not isinstance(resources, list):
        raise _schema_error("resources", "must be a list")
    return CodeResourceMap(
        source_repository=_require_string(raw["source_repository"], "source_repository"),
        source_revision=_require_string(raw["source_revision"], "source_revision"),
        resources=[_resource(item) for item in resources],
        raw=raw,
    )


def immutable_tree_url(repository: str, revision: str, path: str) -> str:
    """Return the GitHub tree URL pinned to a full commit SHA."""
    if not REVISION_PATTERN.fullmatch(revision):
        raise ValueError("source revision must be a 40-character lowercase commit SHA")
    return f"https://github.com/{repository}/tree/{revision}/{path.strip('/')}"


def clone_source_revision(repository: str, revision: str, destination: Path) -> None:
    """Clone a source repository into an isolated destination at one immutable SHA."""
    if not REVISION_PATTERN.fullmatch(revision):
        raise ValueError("source revision must be a 40-character lowercase commit SHA")
    destination = Path(destination)
    if destination.exists():
        raise ValueError(f"clone destination already exists: {destination}")
    url = repository if "://" in repository or Path(repository).exists() else f"https://github.com/{repository}.git"
    try:
        subprocess.run(["git", "clone", "--no-checkout", url, str(destination)], check=True)
    except Exception:
        if destination.is_dir():
            shutil.rmtree(destination, ignore_errors=True)
        raise
    try:
        subprocess.run(["git", "-C", str(destination), "checkout", "--detach", revision], check=True)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def validate_public_source_tree(source_root: Path) -> list[str]:
    """Ensure a checked-out public source tree contains code roots only."""
    root = Path(source_root)
    errors: list[str] = []
    if not root.is_dir():
        return [f"source root does not exist: {root}"]
    git_dir = root / ".git"
    if git_dir.exists():
        try:
            entries = subprocess.check_output(
                ["git", "-C", str(root), "ls-tree", "--name-only", "HEAD"], text=True
            ).splitlines()
        except subprocess.CalledProcessError as error:
            return [f"cannot inspect source tree: {error}"]
    else:
        entries = [entry.name for entry in root.iterdir()]
    for name in entries:
        if name == ".git" or name.startswith("."):
            continue
        entry = root / name
        if not entry.is_dir() or name not in APPROVED_SOURCE_ROOTS:
            if name in FORBIDDEN_SOURCE_ROOTS:
                errors.append(f"forbidden public source root: {name}")
            else:
                errors.append(f"unapproved public source root: {name}")
    return errors


def run_code_resource_validation(textbook_root: Path, source_root: Path) -> int:
    """Run mapping and Appendix D checks without writing to the source checkout."""
    textbook_root = Path(textbook_root).resolve()
    source_root = Path(source_root).resolve()
    try:
        integrity_errors = validate_public_source_tree(source_root)
        if integrity_errors:
            for error in integrity_errors:
                print(error)
            return 1
        mapping = load_code_resources(textbook_root / "metadata/code-resources.yml")
        errors = validate_code_resource_map(mapping, source_root, textbook_root)
        appendix = (textbook_root / "docs/appendices/d-public-source-reference.md").read_text(encoding="utf-8")
        validate_appendix_matches_mapping(appendix, mapping)
    except (OSError, ValueError) as error:
        print(f"code resource validation failed: {error}")
        return 1
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"code resource validation passed: {len(mapping.resources)} resources")
    return 0


def _legacy_numbered_path_error(path: str) -> str | None:
    for component in PurePosixPath(path).parts:
        if LEGACY_NUMBERED_COMPONENT.match(component):
            return f"legacy numbered path component is not allowed: {component}"
    return None


def _appendix_category(resource: CodeResource) -> str:
    resource_id = resource.id
    if resource_id.startswith("examples.ros2.") or resource_id.startswith("ros2.robot."):
        return "ROS 2 基础与启动"
    if resource_id.startswith("ros2.navigation."):
        return "ROS 2 导航"
    if resource_id.startswith("ros1."):
        return "ROS 1 维护"
    if resource_id.startswith("applications."):
        return "视觉与应用"
    if resource_id.startswith("stm32.labs."):
        return "STM32 外设实验"
    if resource_id.startswith("stm32.control."):
        return "STM32 控制"
    if resource_id.startswith("r680.firmware."):
        return "R680 固件"
    raise ValueError(f"resource has no reader-facing Appendix D category: {resource.id}")


def _consumer_link(consumer: Consumer) -> str:
    relative = consumer.page.removeprefix("docs/")
    target = relative if relative.startswith("appendices/") else "../" + relative
    if target.startswith("appendices/"):
        target = target.removeprefix("appendices/")
    return f"[{consumer.role}]({target}#{consumer.anchor})"


def _resource_title(resource: CodeResource) -> str:
    roles = list(dict.fromkeys(consumer.role for consumer in resource.consumers))
    return " / ".join(roles)


def render_appendix(mapping: CodeResourceMap) -> str:
    """Render the reader-facing Appendix D deterministically from the mapping."""
    if not mapping.resources:
        raise ValueError("Appendix D requires at least one selected code resource")
    grouped: dict[str, list[CodeResource]] = {category: [] for category in APPENDIX_CATEGORIES}
    for resource in mapping.resources:
        path_error = _legacy_numbered_path_error(resource.repository_path)
        if path_error:
            raise ValueError(path_error)
        grouped[_appendix_category(resource)].append(resource)

    lines = [
        "---",
        "status: complete",
        "---",
        "",
        "# D. 教材代码资源",
        "",
        "本附录是教材使用的代码资源索引。教材正文中的代码入口是主要使用位置；本页用于按用途集中查找同一批资源，不替代正文给出的文件范围、验收方法和安全边界。",
        "",
        f"所有源码链接固定到提交 `{mapping.source_revision}`。同名目录或后续版本不能自动替代本页所列资源。",
    ]
    for category in APPENDIX_CATEGORIES:
        resources = sorted(grouped[category], key=lambda item: item.repository_path)
        if not resources:
            continue
        lines.extend(("", f"## {category}"))
        for resource in resources:
            files = sorted({file for consumer in resource.consumers for file in consumer.files})
            consumers = sorted(resource.consumers, key=lambda item: (item.page, item.anchor, item.role))
            modes = "、".join(sorted({consumer.mode for consumer in consumers}))
            boundaries = "；".join(
                dict.fromkeys(boundary for consumer in consumers for boundary in consumer.boundaries)
            )
            lines.extend(
                (
                    "",
                    f"### {_resource_title(resource)}",
                    "",
                    f"- 代码目录：[`{resource.repository_path}`]({immutable_tree_url(mapping.source_repository, mapping.source_revision, resource.repository_path)})",
                    f"- 正文入口：{'；'.join(_consumer_link(consumer) for consumer in consumers)}",
                    f"- 关键文件：{'、'.join(f'`{file}`' for file in files)}",
                    f"- 核验状态：`{resource.verification.level}`；使用方式：`{modes}`。",
                    f"- 使用边界：{boundaries}",
                )
            )
    rendered = "\n".join(lines) + "\n"
    forbidden = [value for value in APPENDIX_FORBIDDEN if value in rendered]
    if forbidden:
        raise ValueError("rendered Appendix D contains forbidden text: " + ", ".join(forbidden))
    return rendered


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
    if consumer.file_manifest and (not _is_relative(consumer.file_manifest) or not consumer.file_manifest.startswith("metadata/code-resource-manifests/")):
        errors.append(f"{prefix}: file_manifest must be under metadata/code-resource-manifests/")
    if consumer.mode not in MODES:
        errors.append(f"{prefix}: mode must be one of {sorted(MODES)}")
        return errors
    page = source_root / consumer.page
    if consumer.page and not page.is_file():
        errors.append(f"{prefix}: consumer page does not exist: {consumer.page}")
    elif consumer.anchor and not re.search(ANCHOR_PATTERN % (re.escape(consumer.anchor), re.escape(consumer.anchor)), page.read_text(encoding="utf-8")):
        errors.append(f"{prefix}: consumer anchor does not exist: {consumer.page}#{consumer.anchor}")
    if consumer.mode in {"build", "run", "hardware"} and not any(command.strip() for command in consumer.commands):
        errors.append(f"{prefix}: {consumer.mode} mode requires commands")
    return errors


def validate_code_resource_map(
    mapping: CodeResourceMap, source_root: Path, textbook_root: Path | None = None
) -> list[str]:
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
    content_root = (textbook_root or source_root).resolve()
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
            legacy_error = _legacy_numbered_path_error(resource.repository_path)
            if legacy_error:
                errors.append(f"{prefix}: {legacy_error}")
            package_root = root / resource.repository_path
            if not package_root.is_dir():
                errors.append(f"{prefix}: repository path does not exist: {resource.repository_path}")
        if not resource.consumers:
            errors.append(f"{prefix}: at least one formal consumer is required")
        for consumer_index, consumer in enumerate(resource.consumers):
            consumer_prefix = f"{prefix}.consumers[{consumer_index}]"
            errors.extend(_validate_consumer(consumer, content_root, consumer_prefix))
            for file_path in consumer.files:
                if _is_relative(file_path) and not (package_root / file_path).is_file():
                    errors.append(f"{consumer_prefix}: source file does not exist: {file_path}")
            if consumer.file_manifest:
                manifest_path = content_root / consumer.file_manifest
                if not manifest_path.is_file():
                    errors.append(f"{consumer_prefix}: file_manifest does not exist: {consumer.file_manifest}")
                else:
                    expected = sorted(path.relative_to(package_root).as_posix() for path in package_root.rglob("*") if path.is_file())
                    actual = [line.strip().lstrip("\ufeff") for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                    if actual != expected:
                        errors.append(f"{consumer_prefix}: file_manifest does not match resource tree")
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
        for consumer_index, consumer in enumerate(resource.consumers):
            if consumer.mode in MODE_VERIFICATION_LEVELS and verification.level not in MODE_VERIFICATION_LEVELS[consumer.mode]:
                errors.append(
                    f"{prefix}.consumers[{consumer_index}]: {consumer.mode} mode requires verification level "
                    f"{sorted(MODE_VERIFICATION_LEVELS[consumer.mode])}"
                )
        evidence = verification.evidence_path
        if evidence and (not _is_relative(evidence) or not evidence.startswith("docs/superpowers/audits/")):
            errors.append(f"{prefix}: evidence_path must be under docs/superpowers/audits/")
        elif evidence:
            evidence_file = content_root / evidence
            if not evidence_file.is_file() or evidence_file.stat().st_size == 0:
                errors.append(f"{prefix}: evidence_path must be an existing non-empty file: {evidence}")
    return errors


def validate_appendix_matches_mapping(appendix: str, mapping: CodeResourceMap) -> None:
    """Require exact deterministic parity with the selected consumer mapping."""
    expected = render_appendix(mapping)
    if appendix != expected:
        raise ValueError("appendix does not exactly match the deterministic code-resource rendering")
