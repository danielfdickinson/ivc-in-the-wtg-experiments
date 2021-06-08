#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
from typing import Collection, Mapping
import openstack
from getpass import getpass
import configparser
import collections
import munch


def get_named_resource(method, res_type_name, name):
    print(
        "    Getting {res_type} named {res_name}".format(
            res_type=res_type_name, res_name=name
        )
    )
    value = method(name)
    if value is None:
        print(
            "    ** Failed to find {res_type} named {res_name}.".format(
                res_type=res_type_name, res_name=name
            ),
            file=sys.stderr,
        )
    return value


def get_named_resource_list(
    method, res_type_name, name_list_str, sep=":", error_if_not_found=True
):
    result_names = []
    result_objects = []
    name_list = name_list_str.split(sep)
    if "" in name_list:
        print(
            "    ** Empty {res_type_name}. Invalid config.".format(
                res_type_name=res_type_name
            ),
            file=sys.stderr,
        )
        result_names = None
        result_objects = None
    else:
        for named_item in name_list:
            item_munch = get_named_resource(method, res_type_name, named_item)
            if item_munch is not None:
                result_names.append(named_item)
                result_objects.append(item_munch)
            else:
                if error_if_not_found:
                    result_names = None
                    result_objects = None
                    break
                # else we just ignore the missing resource
    return result_names, result_objects


def map_or_list_contains_None(maplist):
    if maplist is None:
        return True
    elif isinstance(maplist, munch.Munch):
        return False
    elif isinstance(maplist, collections.abc.Mapping):
        for key, value in maplist.items():
            if map_or_list_contains_None(value):
                return True
    elif isinstance(maplist, list):
        for value in maplist:
            if map_or_list_contains_None(value):
                return True
    else:
        return False


passwords = {}
servers_created = {}
servers_deleted = []

config = configparser.ConfigParser(
    defaults={
        "delete_if_exists": "no",
        "remember_password": "yes",
        "userdata": "userdata-instances-no-templates.yaml",
        "security_groups": "default",
        "config_drive": "no",
    }
)

readfile = config.read("instances-no-templates.ini")

if len(readfile) < 1:
    print("Failed to read config file. Bailing...", file=sys.stderr)
    sys.exit(1)

print("Creating {num_servers} servers".format(num_servers=(len(config.sections()))))

for section in config.sections():
    resources = {}
    sectmap = config[section]
    print("Processing server {server_name}".format(server_name=sectmap["server_name"]))
    username = sectmap["username"]
    remember_password = sectmap.getboolean("remember_password")
    delete_if_exists = sectmap.getboolean("delete_if_exists")
    config_drive = sectmap.getboolean("config_drive")

    password = passwords.get(username)
    if password is None:
        password = getpass(
            "Enter password for user {username}: ".format(username=username)
        )
        if remember_password:
            passwords[username] = password

    conn = openstack.connect(
        cloud=sectmap["cloud"], username=username, password=password
    )
    server = conn.get_server(sectmap["server_name"], bare=True)

    resources["image"] = get_named_resource(
        conn.get_image, "boot image", sectmap["image"]
    )

    resources["flavor"] = get_named_resource(
        conn.get_flavor, "instance flavor", sectmap["flavor"]
    )

    resources["network"] = get_named_resource(
        conn.get_network, "primary network", sectmap["network"]
    )

    resources["security_groups"], __ = get_named_resource_list(
        conn.get_security_group, "security group", sectmap["security_groups"]
    )

    if (sectmap.get("volumes") is not None) and (sectmap.get("volumes") != ""):
        __, resources["volumes"] = get_named_resource_list(
            conn.get_volume, "volume", sectmap["volumes"]
        )

    if (sectmap.get("secondary_network") is not None) and (
        sectmap.get("secondary_network") != ""
    ):
        secondary_network = get_named_resource(
            conn.get_network, "secondary network", sectmap["secondary_network"]
        )
        if secondary_network is None:
            print(
                "  ** Skipping to next server due to missing resource",
                file=sys.stderr,
            )
            continue
        resources["network"] = [resources["network"], secondary_network]

    if map_or_list_contains_None(resources):
        print(
            "  ** Skipping to next server due to missing resource",
            file=sys.stderr,
        )
        continue

    print("    Getting userdata for instance")

    try:
        userdatafile = open(sectmap["userdata"], "r")
        userdata = userdatafile.read()
        userdatafile.close()
    except FileNotFoundError:
        print(
            "    ** Unable to find userdata file {userdata_file}. Skipping to next server.".format(
                sectmap["userdata"]
            ),
            file=sys.stderr,
        )
        continue
    except IOError as e:
        print(
            "    ** Unable to read userdata file {userdata_file}. Skipping to next server.".format(
                sectmap["userdata"]
            ),
            file=sys.stderr,
        )
        print("Error was {msg}".format(msg=e.strerror), file=sys.stderr)
        continue

    if server is not None:
        if delete_if_exists:
            print(
                "  Deleting existing server {server_name}, per delete_if_exists".format(
                    server_name=sectmap["server_name"]
                )
            )

            if conn.delete_server(server, True, 600):
                print(
                    "  Server {server_name} successfully deleted".format(
                        server_name=sectmap["server_name"]
                    )
                )
                servers_deleted.append(sectmap["server_name"])
            else:
                print(
                    "Weird. Server {server_name} doesn't exist after all. Bailing...".format(
                        server_name=sectmap["server_name"]
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print(
                "  Server {server_name} exists and delete_if_exists is False. Skipping to next server".format(
                    server_name=sectmap["server_name"]
                )
            )
            continue

    print(
        "    Creating server {server_name}".format(server_name=sectmap["server_name"])
    )
    server = conn.create_server(
        sectmap["server_name"],
        image=resources["image"],
        flavor=resources["flavor"],
        network=resources["network"],
        security_groups=resources["security_groups"],
        volumes=resources.get("volumes"),
        config_drive=config_drive,
        userdata=userdata,
        wait=True,
        timeout=600,
    )

    if server is not None:
        assigned_ip = server.accessIPv4
        if (server.accessIPv4 is None) or (server.accessIPv4 == ""):
            if server.addresses.get(sectmap["network"]) is not None:
                assigned_ip = server.addresses.get(sectmap["network"])[0]["addr"]
        print(
            "Created server {server_name} with ip '{ip}'.".format(
                server_name=server.name, ip=assigned_ip
            )
        )
        servers_created[server.name] = assigned_ip

if len(servers_deleted) < 1:
    print("No servers deleted")
else:
    print("Successfully deleted the following servers:")
    for server_name in servers_deleted:
        print(server_name)
print("Successfully created the following servers:")
for server_name, assigned_ip in servers_created.items():
    print(
        "{server_name}: {assigned_ip}".format(
            server_name=server_name, assigned_ip=assigned_ip
        )
    )
