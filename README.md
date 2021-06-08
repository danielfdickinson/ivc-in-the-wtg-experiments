# Infrastructure Via Code in the Wild Tech "Garden" — Experiments

Code for the Infrastructure Via Code Experimental Learning Project at https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/

## What Is In the Repo?

### /experiments

#### Set-001

Source code of scripts described in [Tokens for OVH v1](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/tokens-for-ovh-v1/).

You would obviously need to modify the ``ovh.conf`` in the directory containing the script to contain usable credentials.

#### Set-002

Source code of scripts described in [First Steps With the OpenStack SDK](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/first-steps-with-openstacksdk/).

You would obviously need to modify the ``clouds.yaml`` in the directory containing to script to contain correct data for the required parameters.
Also, for X-005 you will need to replace the ``basic-instance.ini`` configuration with details that work for your environment. Finally, you would need to adjust ``userdata-basic-instance.yaml`` with the userdata suitable for your instances (or modify the config to use multiple userdata files, if you could use the same userdata for all).
