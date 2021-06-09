import os
import sys

import configparser
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined
from jinja2.exceptions import UndefinedError


def read_config(
    defaults={
        "delete_if_exists": "no",
        "remember_password": "yes",
        "userdata": "userdata-default.yaml.jinja",  # This can be overridden in the INI file, globally or per-instance
        "security_groups": "default",
        "config_drive": "no",
    },
    configfile="create-instances.ini",
):

    config = configparser.ConfigParser(defaults=defaults)

    readfile = config.read(configfile)

    if len(readfile) < 1:
        print("Failed to read config file. Bailing...", file=sys.stderr)
        sys.exit(1)

    return config


def apply_userdata_template(userdatafile, userdata_vars, server_name):
    jinja_env = Environment(
        loader=FileSystemLoader(os.getcwd()),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
    )
    jinja_template = jinja_env.get_template(userdatafile)

    userdata_vars["server_name"] = server_name

    return jinja_template.render(userdata_vars)


def main():
    print("Generating userdata")
    config = read_config()
    for section in config.sections():
        if not section.endswith("-userdata-vars"):
            server_name = section
            userdata_vars = {}
            if (section + "-userdata-vars") in config:
                userdata_vars = config[section + "-userdata-vars"]
            else:
                userdata_vars = config[configparser.DEFAULTSECT]
            userdatafile = config[section]["userdata"]

            print(
                "    Userdata for server {server_name}:".format(server_name=server_name)
            )
            try:
                userdata = apply_userdata_template(
                    userdatafile, userdata_vars, server_name
                )

                print(userdata)
            except UndefinedError as ue:
                print("    Error: {msg}".format(msg=ue.message))
                continue
        else:
            continue


if __name__ == "__main__":
    main()
