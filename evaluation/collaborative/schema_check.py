#!/usr/bin/env python3
"""Minimal JSON Schema 2020-12 checker for the keyword subset these contracts use.

Standard library only, so the contracts can be tested without adding a
dependency. ``SUPPORTED`` lists every keyword it evaluates; ``unsupported``
reports any other keyword so a schema cannot silently rely on one this checker
ignores. Annotation keywords (``title``, ``$schema``, ``$id``, ``x-*``) are
accepted and ignored. ``$ref`` resolves local ``#/$defs/...`` pointers and
relative file references against the referring file's directory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

SUPPORTED = {
    "type", "const", "enum", "pattern", "minLength", "maxLength", "minimum", "maximum",
    "required", "properties", "additionalProperties", "items", "minItems", "maxItems",
    "uniqueItems", "$ref", "oneOf", "allOf", "if", "then", "else", "$defs",
}
ANNOTATIONS = {"$schema", "$id", "title", "description"}
_TYPES = {
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: type(value) is int,
    "boolean": lambda value: isinstance(value, bool),
    "null": lambda value: value is None,
}
_CACHE: Dict[Path, Any] = {}


def load(path: Path) -> Any:
    """Load and cache one schema file."""
    path = path.resolve()
    if path not in _CACHE:
        _CACHE[path] = json.loads(path.read_text(encoding="utf-8"))
    return _CACHE[path]


def unsupported(schema: Any) -> List[str]:
    """Keywords this checker would not evaluate, anywhere in ``schema``."""
    found: List[str] = []
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key not in SUPPORTED and key not in ANNOTATIONS and not key.startswith("x-"):
                found.append(key)
            if key in ("properties", "$defs"):
                for child in value.values():
                    found.extend(unsupported(child))
            elif key in ("oneOf", "allOf"):
                for child in value:
                    found.extend(unsupported(child))
            elif key in ("items", "if", "then", "else", "additionalProperties"):
                found.extend(unsupported(value))
    return found


def _resolve(ref: str, base: Path) -> Tuple[Any, Path]:
    file_part, _, pointer = ref.partition("#")
    target = (base.parent / file_part).resolve() if file_part else base
    node = load(target)
    for token in [part for part in pointer.split("/") if part]:
        node = node[token.replace("~1", "/").replace("~0", "~")]
    return node, target


def _ecma(pattern: str) -> str:
    """ECMA-262 ``$`` never matches before a trailing newline; Python's does."""
    return re.sub(r"(?<!\\)\$", r"\\Z", pattern)


def _equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    return left == right


def errors(instance: Any, schema: Any, base: Path, where: str = "$") -> List[str]:
    """Return every violation of ``schema`` (defined in file ``base``) by ``instance``."""
    if schema is True:
        return []
    if schema is False:
        return [where + ": rejected"]
    found: List[str] = []
    if "$ref" in schema:
        target, target_base = _resolve(schema["$ref"], base)
        found += errors(instance, target, target_base, where)
    if "type" in schema and not _TYPES[schema["type"]](instance):
        return found + [where + ": expected " + schema["type"]]
    if "const" in schema and not _equal(instance, schema["const"]):
        found.append(where + ": expected constant " + json.dumps(schema["const"]))
    if "enum" in schema and not any(_equal(instance, option) for option in schema["enum"]):
        found.append(where + ": not in enum")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", len(instance)):
            found.append(where + ": length out of range")
        if "pattern" in schema and not re.search(_ecma(schema["pattern"]), instance):
            found.append(where + ": does not match pattern")
    if type(instance) is int:
        if instance < schema.get("minimum", instance) or instance > schema.get("maximum", instance):
            found.append(where + ": out of range")
    if isinstance(instance, dict):
        for name in schema.get("required", []):
            if name not in instance:
                found.append(where + ": missing " + name)
        properties = schema.get("properties", {})
        for name, value in instance.items():
            if name in properties:
                found += errors(value, properties[name], base, where + "." + name)
            elif schema.get("additionalProperties") is False:
                found.append(where + ": unknown field " + name)
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", len(instance)):
            found.append(where + ": item count out of range")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in instance]
            if len(set(encoded)) != len(encoded):
                found.append(where + ": duplicate items")
        if "items" in schema:
            for index, item in enumerate(instance):
                found += errors(item, schema["items"], base, where + "[" + str(index) + "]")
    for child in schema.get("allOf", []):
        found += errors(instance, child, base, where)
    if "oneOf" in schema:
        matches = sum(1 for child in schema["oneOf"] if not errors(instance, child, base, where))
        if matches != 1:
            found.append(where + ": matches " + str(matches) + " oneOf branches, expected 1")
    if "if" in schema:
        branch = "then" if not errors(instance, schema["if"], base, where) else "else"
        if branch in schema:
            found += errors(instance, schema[branch], base, where)
    return found


def validate(instance: Any, schema_path: Path) -> List[str]:
    """Validate ``instance`` against the schema file at ``schema_path``."""
    return errors(instance, load(schema_path), schema_path.resolve())


def schema_at(schema_path: Path, pointer: str) -> Tuple[Any, Path]:
    """Return a sub-schema (e.g. ``#/$defs/receipt``) with its base for ``errors``."""
    return _resolve(pointer, schema_path.resolve())
