#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins.html
#
# Check plug-in for the <<<ssh_keys>>> section of the agent plug-in "sshkeys":
# compares the authorized_keys of each user against a list of allowed keys.

import re
from collections.abc import Mapping
from typing import Any

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    StringTable,
)

# user -> entries of ~/.ssh/authorized_keys (without empty lines and comments)
Section = dict[str, list[str]]

# Key types as written in authorized_keys, e.g. ssh-ed25519, ssh-rsa,
# ecdsa-sha2-nistp256, sk-ssh-ed25519@openssh.com
_KEY_TYPE = re.compile(r"^(ssh-|ecdsa-sha2-|sk-)")


def parse_ssh_keys(string_table: StringTable) -> Section:
    # The agent prints one line per user, its keys separated by ";".
    section: Section = {}
    for line in string_table:
        if not line:
            continue
        entries = (e.strip() for e in " ".join(line[1:]).split(";"))
        section[line[0]] = [e for e in entries if e and not e.startswith("#")]
    return section


def _normalize_key(text: str) -> str | None:
    # Reduce a key line to "<type> <base64>", ignoring options and comment.
    tokens = text.split()
    for index, token in enumerate(tokens[:-1]):
        if _KEY_TYPE.match(token):
            return f"{token} {tokens[index + 1]}"
    return None


def _short_name(entry: str) -> str:
    # Comment of the key if present, otherwise a shortened key.
    tokens = entry.split()
    for index, token in enumerate(tokens[:-1]):
        if _KEY_TYPE.match(token):
            comment = " ".join(tokens[index + 2:])
            return comment or f"{token} {tokens[index + 1][:20]}..."
    return entry[:40]


def _allowed_keys(params: Mapping[str, Any]) -> dict[str, str]:
    # Rules created with version 1.x store (key, label) tuples, until they are
    # migrated by the GUI or cmk-update-config.
    allowed = {}
    for entry in params["sshkeys"]:
        if isinstance(entry, Mapping):
            key, label = entry["key"], entry["label"]
        else:
            key, label = entry[0], entry[1]
        allowed[_normalize_key(key) or key.strip()] = label
    return allowed


def discover_ssh_keys(section: Section) -> DiscoveryResult:
    for user in section:
        yield Service(item=user)


def check_ssh_keys(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    if item not in section:
        return
    keys = section[item]
    if not keys:
        yield Result(state=State.OK, summary="No authorized keys")
        return
    if params.get("sshkeys") is None:
        yield Result(state=State.WARN, summary="User has authorized keys, but no config found")
        return

    allowed = _allowed_keys(params)
    labels = []
    denied = []
    for key in keys:
        label = allowed.get(_normalize_key(key) or "")
        if label is None:
            denied.append(key)
        else:
            labels.append(label)

    if not denied:
        yield Result(state=State.OK, summary=f"Authorized keys: {', '.join(dict.fromkeys(labels))}")
        return
    yield Result(
        state=State.CRIT,
        summary=f"{len(denied)} of {len(keys)} key(s) not allowed",
        details="Not allowed:\n" + "\n".join(_short_name(k) for k in denied),
    )


agent_section_ssh_keys = AgentSection(
    name="ssh_keys",
    parse_function=parse_ssh_keys,
)

check_plugin_ssh_keys = CheckPlugin(
    name="ssh_keys",
    service_name="SSH-Keys %s",
    discovery_function=discover_ssh_keys,
    check_function=check_ssh_keys,
    check_ruleset_name="ssh_keys",
    check_default_parameters={},
)
