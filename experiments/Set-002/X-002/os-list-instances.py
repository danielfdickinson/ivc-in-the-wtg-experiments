import openstack

conn = openstack.connect(cloud='ovh')

servers = conn.list_servers()

for server in servers:
    print(server.name)
