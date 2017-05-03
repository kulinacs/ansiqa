import os
from glob import glob
import ruamel.yaml as yaml


def scan(path=os.getcwd()):
    '''Return a list of roles given a path'''
    roles = []
    for root, dirs, files in os.walk(path):
        if 'tasks' in dirs or 'handlers' in dirs:
            roles.append(get_role(root, dirs, files))
    return roles


def get_role(role_path, dirs, files):
    '''Return a role dict'''
    role = {'name': os.path.basename(role_path),
            'path': role_path,
            'readme': glob(os.path.join(role_path, 'README.*')),
            'defaults': _get_attribute(role_path, 'defaults'),
            'files': _get_listing(role_path, 'files'),
            'handlers': _get_attribute(role_path, 'handlers'),
            'meta': _get_attribute(role_path, 'meta'),
            'tasks': _get_tasks(role_path),
            'templates': _get_listing(role_path, 'templates'),
            'tests': 'tests' in dirs,
            'vars': _get_attribute(role_path, 'vars'),
            'extra': _get_attribute(role_path, 'extra')}
    return role


def dump_vars(roles):
    '''Return a dict of all passed roles vars'''
    vars_dict = {}
    for role in roles:
        if role['vars']:
            vars_dict.update(role['vars'])
    return vars_dict


def dump_defaults(roles):
    '''Return a dict of all passed roles defaults'''
    defaults_dict = {}
    for role in roles:
        if role['defaults']:
            defaults_dict.update(role['defaults'])
    return defaults_dict


def printable(role):
    to_print = ['defaults', 'vars']
    for item in to_print:
        role[item] = yaml.dump(role[item], default_flow_style=False,
                               indent=4, block_seq_indent=2).rstrip('\n')
    return role


def _get_attribute(role_path, attr):
    '''Get a generic Ansible role attribute'''
    attr_path = os.path.join(role_path, attr, 'main.yml')
    if not os.path.isfile(attr_path):
        attr_value = {}
    else:
        with open(attr_path) as attr_file:
            attr_value = yaml.safe_load(attr_file)
        if attr_value is None:
            attr_value = {}
    return attr_value


def _get_listing(role_path, attr):
    '''Get a listing of files in a directory for an Ansible role'''
    files_path = os.path.join(role_path, attr)
    files = __list_files(files_path)
    return files


def __list_files(file_path):
    '''Recursively enumerate all files in a directory'''
    found_files = []
    if os.path.exists(file_path):
        for root, dirs, files in os.walk(file_path):
            found_files.extend([os.path.join(root, filename)
                                for filename in files])
            for dirname in dirs:
                found_files.extend(__list_files(os.path.join(root, dirname)))
    return found_files


def _get_tasks(role_path):
    '''Get a list of all tasks for an Ansible role'''
    tasks_path = os.path.join(role_path, 'tasks', 'main.yml')
    if not os.path.isfile(tasks_path):
        tasks = []
    else:
        with open(tasks_path) as tasks_file:
            tasks = yaml.safe_load(tasks_file)
        if tasks is None:
            tasks = []
    current = 0
    while (current < len(tasks)):
        if 'include' in tasks[current].keys():
            include_tasks_path = os.path.join(role_path, 'tasks',
                                              tasks[current]['include'])
            with open(include_tasks_path) as include_tasks_file:
                include_tasks = yaml.safe_load(include_tasks_file)
            tasks = tasks[:current] + include_tasks + tasks[current+1:]
            current = current + len(include_tasks)
        current += 1
    return tasks
