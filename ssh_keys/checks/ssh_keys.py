#!/usr/bin/env python
# -*- encoding: utf-8; py-ident-offset: 4 -*

def agent_sshkeys_attr(params, hostname, ipaddress):
    args = []
    if "user" in params:
        args += ["-u", params["user"]]
    if "password" in params:
        args += ["-p", passwordstore_get_cmdline("%s", params["password"])]
    args.append(ipaddress)
    return args

special_agent_info["ssh_keys"] = agent_sshkeys_attr
