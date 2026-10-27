#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH 
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins.html
#
# This file contains the configuration defaults for our "Hello world!" example
# plus hooks to display and alter these defaults in the setup GUI.

# Import localization:

from cmk.gui.i18n import _

# Import the data structures the GUI uses to pass defaults:

from cmk.gui.valuespec import (
    Dictionary,
    ListOf,
    TextInput,
    Tuple,
    Percentage,
)
from cmk.gui.plugins.wato import (
    CheckParameterRulespecWithItem,
    rulespec_registry,
    RulespecGroupCheckParametersOperatingSystem,
)

def _item_valuespec_sshkeys():
    return TextInput(title="Username")

def _parameter_valuespec_sshkeys_keys():
    return Dictionary(
        title=_("Check SSH-Keys (Linux)"),
        elements=[
            (
                "sshkeys", ListOf(
                    valuespec=Tuple(
                        show_titles=True,
                        orientation="horizontal",
                        elements=[
                            TextInput(title=_("Key"), allow_empty=False, size=100),
                            TextInput(title=_("Label"), allow_empty=False, size=100),
                        ],
                    ),
                    title=_("SSH-Keys"),
                    add_label=_("Add new key"),
                ),
            ),
        ],
    )

rulespec_registry.register(
    CheckParameterRulespecWithItem(
        # as defined in your check in share/check_mk/checks/
        check_group_name = "ssh_keys",
        group = RulespecGroupCheckParametersOperatingSystem,
        match_type = "dict",
	item_spec = _item_valuespec_sshkeys,
        # the function above to issue default parameters
        parameter_valuespec = _parameter_valuespec_sshkeys_keys,
        title=lambda: _("SSH-Keys"),
    ))
