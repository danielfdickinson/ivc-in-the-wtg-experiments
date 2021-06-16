import base64
import collections
import gzip
import os
import pathlib
from posixpath import isabs
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

    config = configparser.ConfigParser(defaults=defaults, interpolation=None)

    readfile = config.read(configfile)

    if len(readfile) < 1:
        print("Failed to read config file. Bailing...", file=sys.stderr)
        sys.exit(1)

    return config


def apply_userdata_template(userdatafile, userdata_vars, server_name=""):
    jinja_env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.getcwd(), os.path.dirname(userdatafile))
        ),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
    )
    jinja_template = jinja_env.get_template(os.path.basename(userdatafile))

    if server_name != "":
        userdata_vars["server_name"] = server_name

    return jinja_template.render(userdata_vars)


def get_file_data(config, section, dirlist, userdata_vars, templates=False):
    verbatim_files_dirs = config[section][dirlist].split(":")

    if not "files_to_write" in userdata_vars:
        userdata_vars["files_to_write"] = []
    if not "write_files" in userdata_vars:
        userdata_vars["write_files"] = {}
    for verbatim_files_dir in verbatim_files_dirs:
        verbatim_files_dir = os.path.normpath(verbatim_files_dir)
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
                if templates:
                    target_base_content = bytes(
                        apply_userdata_template(local_path, userdata_vars), "utf-8"
                    )
                else:
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
                orig_path = pathlib.PurePath(target_path)
                if orig_path.is_absolute:
                    if orig_path.drive != "":
                        orig_path = orig_path.relative_to(orig_path.drive)
                posix_path = orig_path.as_posix()
                userdata_vars["write_files"][target_var_name]["path"] = posix_path
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
        if isinstance(val, collections.abc.Mapping):
            val = copy_userdata_vars(val)
        elif isinstance(val, list):
            val = copy_userdata_vars(val)
        new_dict[key] = val
    return new_dict


def main():
    print("Generating userdata")
    config = read_config()
    for section in config.sections():
        if not section.endswith("-userdata-vars"):
            server_name = section

            userdata_vars = {}
            userdata = None

            if (section + "-userdata-vars") in config:
                userdata_vars = copy_userdata_vars(config[section + "-userdata-vars"])
            else:
                userdata_vars = copy_userdata_vars(config[config.default_section])

            userdatafile = config[section]["userdata"]
            if "verbatim_files_dirs" in config[section] and (
                config[section]["verbatim_files_dirs"] != ""
            ):
                userdata_vars = get_file_data(
                    config, section, "verbatim_files_dirs", userdata_vars
                )
            if "template_files_dirs" in config[section] and (
                config[section]["template_files_dirs"] != ""
            ):
                userdata_vars = get_file_data(
                    config,
                    section,
                    "template_files_dirs",
                    userdata_vars,
                    templates=True,
                )
            else:
                if not "files_to_write" in userdata_vars:
                    userdata_vars["files_to_write"] = []
                if not "write_files" in userdata_vars:
                    userdata_vars["write_files"] = {}

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