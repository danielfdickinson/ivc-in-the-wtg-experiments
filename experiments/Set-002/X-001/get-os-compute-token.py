from getpass import getpass
import openstack

os_pass = getpass("Enter your password: ")

conn = openstack.connect(cloud='ovh', password=os_pass)
print("Your token is: ")
print(conn.authorize())
