#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins.html
#
# This is the main CMK/server side script for a "Hello World!" Plugin

from .agent_based_api.v1 import *

# Most simple discovery function, basically just checks for the agents
# output containing a section named exactly as the service:

def discover_ssh_keys(section):
    for sector in section:
        yield Service(item=sector[0])

# Thresholds are taken from the default parameters defined in
# ~/local/share/check_mk/web/plugins/wato/helloworld_parameters.py
# respectively overwritten by setup GUI settings.

def check_ssh_keys(item, params, section):
    for sector in section:
        if sector[0] == item:
            if(len(sector[1:]) == 0):
                yield Result(state=State.OK, summary="No authorized keys.")
                return
            if params.get('sshkeys') is None:
                yield Result(state=State.WARN, summary="User has authorized key, but no config found.")
                return
            else:
                keys = ' '.join(sector[1:])
                if ';' in keys:
                    keys = keys.split(';')
                else:
                    keys = [keys]

                keys_valid = True
                valid_keys = []

                for key in keys:
                    valid_key_found = False  # Initialisiere valid_key_found für jeden key

                    for valid_key in params['sshkeys']:
                        if find_key(key.split(' ')) in valid_key[0]:
                            valid_keys.append(valid_key[1])  # Füge valid_key[1] zu valid_keys hinzu
                            valid_key_found = True
                            break

                    if not valid_key_found:
                        keys_valid = False
                        break

                if keys_valid == True:
                    yield Result(state=State.OK, summary=f"Authorized Keys: {', '.join(valid_keys)}")
                else:
                    yield Result(state=State.CRIT, summary="Minimum one key is not allowed to use")
                return

    yield Result(state=State.CRIT, summary=f"Error!")

def find_key(lst):
    start_element = next((x for x in lst if x.startswith("ssh-")), None)

    if start_element is not None:
        start_index = lst.index(start_element)
        return " ".join(lst[start_index:start_index+2])
        #return lst[start_index+1]
    else:
        return ""

# Register the plugin with a unique name and define at least three functions!
# Default parameters can be left empty since defined elsewhere.

register.check_plugin(
    name = "ssh_keys",
    service_name = "SSH-Keys %s",
    discovery_function = discover_ssh_keys,
    check_function = check_ssh_keys,
    check_ruleset_name = "ssh_keys",
    check_default_parameters = { }
)
