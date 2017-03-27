import os
from glob import glob
import yaml


def scan(path='.'):
    roles = []
    for root, dirs, files in os.walk(path):
        if 'tasks' in dirs or 'handlers' in dirs:
            roles.append(get_role(root, dirs, files))
    return roles


def get_role(role_path, dirs, files):
    role = {'name': os.path.basename(role_path),
            'path': role_path,
            'readme': glob(os.path.join(role_path, 'README.*')),
            'defaults': _get_defaults(role_path),
            'files': _get_files(role_path),
            'handlers': _get_handlers(role_path),
            'meta': _get_meta(role_path),
            'tasks': _get_tasks(role_path),
            'templates': _get_templates(role_path),
            'tests': 'tests' in dirs,
            'vars': _get_vars(role_path)}
    return role


def dump_vars(roles):
    vars_dict = {}
    for role in roles:
        if role['vars'] is not None:
            vars_dict.update(role['vars'])
    return vars_dict


def dump_defaults(roles):
    defaults_dict = {}
    for role in roles:
        if role['defaults'] is not None:
            defaults_dict.update(role['defaults'])
    return defaults_dict


def _get_defaults(role_path):
    defaults_path = os.path.join(role_path, 'defaults', 'main.yml')
    if not os.path.exists(defaults_path):
        defaults = None
    else:
        with open(defaults_path) as defaults_file:
            defaults = yaml.safe_load(defaults_file)
    return defaults


def _get_files(role_path):
    files_path = os.path.join(role_path, 'files')
    files = __list_files(files_path)
    return files


def __list_files(file_path):
    found_files = []
    if os.path.exists(file_path):
        for root, dirs, files in os.walk(file_path):
            found_files.extend([os.path.join(root, filename)
                                for filename in files])
            for dirname in dirs:
                found_files.extend(__list_files(os.path.join(root, dirname)))
    return found_files


def _get_handlers(role_path):
    handlers_path = os.path.join(role_path, 'handlers', 'main.yml')
    if not os.path.exists(handlers_path):
        handlers = []
    else:
        with open(handlers_path) as handlers_file:
            handlers = yaml.safe_load(handlers_file)
    return handlers


def _get_meta(role_path):
    meta_path = os.path.join(role_path, 'meta', 'main.yml')
    if not os.path.exists(meta_path):
        meta = None
    else:
        with open(meta_path) as meta_file:
            meta = yaml.safe_load(meta_file)
    return meta


def _get_tasks(role_path):
    tasks_path = os.path.join(role_path, 'tasks', 'main.yml')
    if not os.path.exists(tasks_path):
        tasks = []
    else:
        with open(tasks_path) as tasks_file:
            tasks = yaml.safe_load(tasks_file)
    return tasks


def _get_templates(role_path):
    templates_path = os.path.join(role_path, 'templates')
    templates = __list_files(templates_path)
    return templates


def _get_vars(role_path):
    vars_path = os.path.join(role_path, 'vars', 'main.yml')
    if not os.path.exists(vars_path):
        vars = None
    else:
        with open(vars_path) as vars_file:
            vars = yaml.safe_load(vars_file)
    return vars
