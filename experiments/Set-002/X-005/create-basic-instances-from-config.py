import sys
import openstack
from getpass import getpass
import configparser

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
    username = sectmap["username"]
    remember_password = sectmap.getboolean("remember_password")
    delete_if_exists = sectmap.getboolean("delete_if_exists")

    password = passwords.get(username)
    if password is None:
        password = getpass(
            "Enter your password for user {username}: ".format(username=username)
        )
        if remember_password:
            passwords[username] = password

    conn = openstack.connect(
        cloud=sectmap["cloud"], username=username, password=password
    )
    server = conn.get_server(sectmap["server_name"], bare=True)

    image = conn.get_image(sectmap["image"])
    if image is None:
        print(
            "Unable to find image {image}. Bailing...".format(image=sectmap["image"]),
            file=sys.stderr,
        )
        sys.exit(1)
    flavor = conn.get_flavor(sectmap["flavor"])
    if flavor is None:
        print(
            "Unable to find flavor {flavor}. Bailing...".format(
                flavor=sectmap["flavor"]
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    network = conn.get_network(sectmap["network"])
    if network is None:
        print(
            "Unable to find network {network}. Bailing...".format(
                image=sectmap["network"]
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    userdatafile = open(sectmap["userdata"], "r")
    userdata = userdatafile.read()
    userdatafile.close()

    if server is not None:
        if delete_if_exists:
            if conn.delete_server(server, True, 600):
                print("Server {server_name} successfully deleted".format(
                    server_name=sectmap["server_name"]
                ))
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
                "Server {server_name} exists and delete_if_exists is False. Skipping to next server".format(
                    server_name=sectmap["server_name"]
            ))
            continue

    server = conn.create_server(
        sectmap['server_name'],
        image=image,
        flavor=flavor,
        network=network,
        userdata=userdata,
        wait=True,
        timeout=600,
    )

    if server is not None:
        print("Created server {server_name} with ip {ip}.".format(server_name=sectmap['server_name'], ip=server.accessIPv4))
