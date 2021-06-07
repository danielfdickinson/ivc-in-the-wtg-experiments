# -*- encoding: utf-8 -*-

import ovh

# create a client
client = ovh.Client()

credentials = client.get('/me/api/credential', status='validated')
for credential_id in credentials:
  client.delete('/me/api/credential/'+str(credential_id))
