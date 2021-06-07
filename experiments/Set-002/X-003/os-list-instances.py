import openstack
from getpass import getpass

username = input("Enter your username: ")
password = getpass("Enter your password: ")

conn = openstack.connect(cloud='ovh', username=username, password=password)

servers = conn.list_servers()

for server in servers:
    print(server.name)
