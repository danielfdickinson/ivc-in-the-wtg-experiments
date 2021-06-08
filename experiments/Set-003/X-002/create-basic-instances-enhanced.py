#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
from typing import Collection, Mapping
from getpass import getpass
import configparser
import collections

import openstack
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
        for __, value in maplist.items():
            if map_or_list_contains_None(value):
                return True
    elif isinstance(maplist, list):
        for value in maplist:
            if map_or_list_contains_None(value):
                return True
    else:
        return False


passwords = {}

config = configparser.ConfigParser(
    defaults={
        "delete_if_exists": "no",
        "remember_password": "yes",
        "userdata": "userdata-basic-instance.yaml",
        "security_groups": "default",
    }
)

readfile = config.read("basic-instance.ini")

if len(readfile) < 1:
    print("Failed to read config file. Bailing...", file=sys.stderr)
    sys.exit(1)

print("Creating {num_servers} servers".format(num_servers=(len(config.sections()))))

for section in config.sections():
    sectmap = config[section]
    print("Processing server {server_name}".format(server_name=sectmap["server_name"]))
    username = sectmap["username"]
    remember_password = sectmap.getboolean("remember_password")
    delete_if_exists = sectmap.getboolean("delete_if_exists")

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

    image = get_named_resource(conn.get_image, "boot image", sectmap["image"])
    flavor = get_named_resource(conn.get_flavor, "instance flavor", sectmap["flavor"])
    network = get_named_resource(
        conn.get_network, "primary network", sectmap["network"]
    )

    security_groups, __ = get_named_resource_list(
        conn.get_security_group, "security group", sectmap["security_groups"]
    )

    if (image is None) or (flavor is None) or (network is None):
        print("  ** Skipping to next server due to missing resource", file=sys.stderr)
        continue

    if map_or_list_contains_None(security_groups):
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
        image=image,
        flavor=flavor,
        network=network,
        userdata=userdata,
        security_groups=security_groups,
        wait=True,
        timeout=600,
    )

    if server is not None:
        print(
            "Created server {server_name} with ip {ip}.".format(
                server_name=server.name, ip=server.accessIPv4
            )
        )
