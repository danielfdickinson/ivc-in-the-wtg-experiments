# -*- encoding: utf-8 -*-

import ovh

# create a client using configuration
client = ovh.Client()

ck = client.new_consumer_key_request()
ck.add_recursive_rules(ovh.API_READ_WRITE, "/domain")
ck.add_recursive_rules(ovh.API_READ_WRITE, "/ip")

# Request token
validation = ck.request()

print("Please visit %s to authenticate" % validation['validationUrl'])
input("and press Enter to continue...")

# Print nice welcome message
print("Btw, your 'consumerKey' is '%s'" % validation['consumerKey'])
