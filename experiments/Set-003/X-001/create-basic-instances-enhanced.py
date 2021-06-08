#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import openstack
from getpass import getpass
import configparser


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


passwords = {}

config = configparser.ConfigParser(
    defaults={
        "delete_if_exists": "no",
        "remember_password": "yes",
        "userdata": "userdata-basic-instance.yaml",
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

    if (image is None) or (flavor is None) or (network is None):
        print("  ** Skipping to next server due to missing resource", file=sys.stderr)
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
        wait=True,
        timeout=600,
    )

    if server is not None:
        print(
            "Created server {server_name} with ip {ip}.".format(
                server_name=server.name, ip=server.accessIPv4
            )
        )
