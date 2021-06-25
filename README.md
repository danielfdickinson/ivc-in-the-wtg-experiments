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

#### Set-004

Source code of scripts described in [Adding Trivial Templating](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/adding-trivial-templating/). There is the usual note about updating configuration to and userdata to suit your environment.

#### Set-005

Source code of scripts, configs, and files described in [Continuing OpenStack SDK With Templating](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/continuing-openstacksdk-with-templating/). There is the usual note about updating configuration to and userdata to suit your environment. For ``X-002`` and beyond, you will also need to update the additional files to suit your situation. (The additional files are applied verbatim, except compressed and encoded).

##### Set-006

This is the initial copy from Set-005 of source code, configs, and files described in [Completing OpenStackSDK with Templating](https://www.wildtechgarden.ca/projects/experimental-learning/infrastructure-via-code/completing-openstacksdk-with-templating/) final script. Since that project has been halt (see that page for the reasons), this has not been taken beyond some minor modifications.

## That's All Folks

Hopefully you found the referenced website and these files useful.
