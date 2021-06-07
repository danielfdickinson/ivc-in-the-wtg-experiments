# -*- encoding: utf-8 -*-

import ovh

# create a client using configuration
client = ovh.Client()

# Request RO, /me API access
ck = client.new_consumer_key_request()
ck.add_rules(ovh.API_READ_ONLY, "/me/*")
ck.add_rules(ovh.API_READ_ONLY, "/me")

# Request token
validation = ck.request()

print("Please visit %s to authenticate" % validation['validationUrl'])
input("and press Enter to continue...")

# Print nice welcome message
print("Welcome", client.get('/me')['firstname'])
print("Btw, your 'consumerKey' is '%s'" % validation['consumerKey'])
