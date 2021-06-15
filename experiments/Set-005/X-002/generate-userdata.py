import base64
import gzip
import os
import sys

import configparser
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined
from jinja2.exceptions import UndefinedError
from jinja2.runtime import to_string


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

    config = configparser.ConfigParser(defaults=defaults, interpolation=None)

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


def get_file_data(config, section, userdata_vars):
    verbatim_files_dirs = config[section]["verbatim_files_dirs"].split(":")

    userdata_vars["files_to_write"] = []
    userdata_vars["write_files"] = {}
    for verbatim_files_dir in verbatim_files_dirs:
        for verbatim_dirpath, __, verbatim_filenames in os.walk(verbatim_files_dir):
            for verbatim_filename in verbatim_filenames:
                local_path = os.path.join(verbatim_dirpath, verbatim_filename)
                target_path = os.path.join(
                    verbatim_dirpath.removeprefix(verbatim_files_dir), verbatim_filename
                )
                local_path_size = os.path.getsize(local_path)
                if local_path_size > 10240:
                    print("  Error: Files greater than 10k can't be part of userdata")
                    return None
                target_file = open(local_path, "rb")
                target_base_content = target_file.read()
                target_file.close()
                target_base_len = len(target_base_content)
                target_gz_content = gzip.compress(target_base_content)
                target_gz_len = len(target_gz_content)
                target_gzipped = target_gz_len < target_base_len
                target_var_name = (
                    target_path.replace("/", "-").replace(".", "-").removeprefix("-")
                )
                userdata_vars["write_files"][target_var_name] = {}
                userdata_vars["write_files"][target_var_name]["path"] = target_path
                if userdata_vars.get(target_var_name + "-permissions"):
                    userdata_vars["write_files"][target_var_name]["permissions"] = (
                        '"' + userdata_vars[target_var_name + "-permissions"] + '"'
                    )
                else:
                    userdata_vars["write_files"][target_var_name]["permissions"] = ""
                if userdata_vars.get(target_var_name + "-owner"):
                    userdata_vars["write_files"][target_var_name]["owner"] = (
                        '"' + userdata_vars[target_var_name + "-owner"] + '"'
                    )
                else:
                    userdata_vars["write_files"][target_var_name]["owner"] = ""
                if userdata_vars.get(target_var_name + "-append"):
                    userdata_vars["write_files"][target_var_name][
                        "append"
                    ] = userdata_vars[target_var_name + "-append"]
                else:
                    userdata_vars["write_files"][target_var_name]["append"] = False
                if target_gzipped:
                    userdata_vars["write_files"][target_var_name][
                        "content"
                    ] = base64.b64encode(target_gz_content).decode("utf-8")
                    userdata_vars["write_files"][target_var_name]["encoding"] = "gz+b64"
                else:
                    userdata_vars["write_files"][target_var_name][
                        "content"
                    ] = base64.b64encode(target_base_content).decode("utf-8")
                    userdata_vars["write_files"][target_var_name]["encoding"] = "b64"
                userdata_vars["files_to_write"].append(target_var_name)
    return userdata_vars


def copy_userdata_vars(userdata_vars):
    new_dict = {}
    for key, val in userdata_vars.items():
        new_dict[key] = val
    return new_dict


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
                userdata_vars = config[config.default_section]

            userdatafile = config[section]["userdata"]
            userdata_vars = get_file_data(
                config, section, copy_userdata_vars(userdata_vars)
            )

            if userdata_vars is None:
                continue

            print(
                "    Userdata for server {server_name}:".format(server_name=server_name)
            )
            try:
                userdata = apply_userdata_template(
                    userdatafile, userdata_vars, server_name
                )

                if len(userdata) > 16384:
                    print("  Error: userdata is >16k")
                    continue

                print(userdata)
            except UndefinedError as ue:
                print("    Error: {msg}".format(msg=ue.message))
                continue
        else:
            continue


if __name__ == "__main__":
    main()