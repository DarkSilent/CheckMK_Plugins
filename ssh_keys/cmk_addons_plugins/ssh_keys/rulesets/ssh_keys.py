#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins_rulesets.html
#
# Rule set "SSH-Keys" for the ssh_keys check: list of allowed keys with labels.

from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    FieldSize,
    List,
    String,
    validators,
)
from cmk.rulesets.v1.rule_specs import CheckParameters, HostAndItemCondition, Topic


def _migrate(value: object) -> dict[str, object]:
    # Version 1.x stored the keys as (key, label) tuples.
    if not isinstance(value, dict):
        raise TypeError(value)
    if "sshkeys" not in value:
        return value
    return {
        **value,
        "sshkeys": [
            entry if isinstance(entry, dict) else {"key": entry[0], "label": entry[1]}
            for entry in value["sshkeys"]
        ],
    }


def _parameter_form() -> Dictionary:
    return Dictionary(
        title=Title("Check SSH-Keys (Linux)"),
        migrate=_migrate,
        elements={
            "sshkeys": DictElement(
                parameter_form=List(
                    title=Title("SSH-Keys"),
                    help_text=Help(
                        "Keys that are allowed in authorized_keys. Only the key type and "
                        "the base64 part are compared, options and comments are ignored."
                    ),
                    add_element_label=Label("Add new key"),
                    element_template=Dictionary(
                        elements={
                            "key": DictElement(
                                required=True,
                                parameter_form=String(
                                    title=Title("Key"),
                                    field_size=FieldSize.LARGE,
                                    custom_validate=(validators.LengthInRange(min_value=1),),
                                ),
                            ),
                            "label": DictElement(
                                required=True,
                                parameter_form=String(
                                    title=Title("Label"),
                                    custom_validate=(validators.LengthInRange(min_value=1),),
                                ),
                            ),
                        },
                    ),
                ),
            ),
        },
    )


rule_spec_ssh_keys = CheckParameters(
    name="ssh_keys",
    title=Title("SSH-Keys"),
    topic=Topic.OPERATING_SYSTEM,
    parameter_form=_parameter_form,
    condition=HostAndItemCondition(item_title=Title("Username")),
)
