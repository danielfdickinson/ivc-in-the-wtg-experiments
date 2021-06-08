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

#### Set-003

Source code of scripts described in [Completing Bare Bones OpenStack SDK](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/completing-bare-bones-openstacksdk/). As usual you would need to update configuration and userdata to suit your environment.

For ``X-002`` you will notice that the config as written will only create one of the three defined instances, and the other two will fail be skipped due to detected errors. This is an intentional quick test of the new code's error handling.
