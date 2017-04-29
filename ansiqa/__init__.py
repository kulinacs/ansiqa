import argparse
from ansiqa import load
import yaml
from tabulate import tabulate
import os


def load_config():
    config = {}
    user_config_file = os.path.join(os.path.expanduser('~'), '.ansiqa.yml')
    cwd_config_file = os.path.join(os.getcwd(), '.ansiqa.yml')
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            config.update(yaml.safe_load(f))
    if os.path.exists(cwd_config_file):
        with open(cwd_config_file) as f:
            config.update(yaml.safe_load(f))
    return config


def stats(args, conf):
    if args.rolename is None:
        roles = load.scan()
    else:
        roles = []
        for rolename in args.rolename:
            roles.extend(load.scan(rolename))
    if args.dump_vars:
        vars_dict = load.dump_vars(roles)
        if vars_dict:
            print('---\n' + yaml.dump(vars_dict, default_flow_style=False),
                  end='')
        else:
            print('---')
    elif args.dump_defaults:
        defaults_dict = load.dump_defaults(roles)
        if defaults_dict:
            print('---\n' + yaml.dump(defaults_dict, default_flow_style=False),
                  end='')
        else:
            print('---')
    elif args.list_files:
        for role in roles:
            for filename in role['files']:
                print(filename)
    elif args.list_templates:
        for role in roles:
            for templatename in role['templates']:
                print(templatename)
    else:
        headers = ['name', 'tasks', 'vars', 'defaults', 'README', 'meta',
                   'extra']
        values = []
        for role in roles:
            if role['vars'] is None:
                varsnum = 0
            else:
                varsnum = len(role['vars'].keys())
            if role['defaults'] is None:
                defaultsnum = 0
            else:
                defaultsnum = len(role['defaults'].keys())
            values.append([role['name'], len(role['tasks']), varsnum,
                           defaultsnum, str(len(role['readme']) > 0),
                           str(role['meta'] is not None),
                           str(role['extra'] is not None)])
        print(tabulate(values, headers, tablefmt="plain"))


def __augment_dict(old, update):
    for key in old:
        try:
            if isinstance(old[key], dict) and isinstance(update[key], dict):
                __augment_dict(old[key], update[key])
        except (KeyError):
            pass
    for key in update:
        if key not in old:
            old[key] = update[key]


def __replace_dict(old, update):
    for key in old:
        try:
            if isinstance(old[key], dict) and isinstance(update[key], dict):
                __replace_dict(old[key], update[key])
            else:
                old[key] = update[key]
        except (KeyError):
            pass


def meta(args, conf):
    if args.rolename is None:
        roles = load.scan()
    else:
        roles = []
        for rolename in args.rolename:
            roles.extend(load.scan(rolename))
    for role in roles:
        metadir = os.path.join(role['path'], 'meta')
        metafile = os.path.join(metadir, 'main.yml')
        if role['meta'] is None:
            role['meta'] = {}
        if args.augment:
            __augment_dict(role['meta'], conf['meta'])
        elif args.replace:
            __replace_dict(role['meta'], conf['meta'])
        else:
            role['meta'].update(conf['meta'])
        if not os.path.exists(metadir):
            os.makedirs(metadir)
        with open(metafile, 'w') as f:
            f.write('---\n')
            f.write(yaml.dump(role['meta'], default_flow_style=False))


def extra(args, conf):
    pass


def docs(args, conf):
    pass


def main():
    # Load Conf
    conf = load_config()

    # Parsers
    parser = argparse.ArgumentParser(description='Utilities for managing '
                                     'Ansible Roles')
    subparsers = parser.add_subparsers()

    # Stats Parser
    stats_parser = subparsers.add_parser('stats', help='Role statistics')
    stats_parser.add_argument('-r', '--rolename', type=str, nargs='*',
                              help='specific role(s) to operate on')
    stats_dumpers = stats_parser.add_mutually_exclusive_group()
    stats_dumpers.add_argument('--dump-vars', default=False,
                               action='store_true', help='dump vars as yaml')
    stats_dumpers.add_argument('--dump-defaults', default=False,
                               action='store_true',
                               help='dump defaults as yaml')
    stats_dumpers.add_argument('--list-files', default=False,
                               action='store_true', help='list files')
    stats_dumpers.add_argument('--list-templates', default=False,
                               action='store_true',
                               help='list templates')
    stats_parser.set_defaults(func=stats)

    # Meta parser
    meta_parser = subparsers.add_parser('meta', help='Generate standard meta')
    meta_parser.add_argument('-r', '--rolename', type=str, nargs='*',
                             help='specific role(s) to operate on')
    meta_options = meta_parser.add_mutually_exclusive_group()
    meta_options.add_argument('--augment', default=False,
                              action='store_true', help='Only add value,'
                              ' don\'t change existing')
    meta_options.add_argument('--replace', default=False,
                              action='store_true', help='Only change'
                              ' existing values, don\'t add any')
    meta_parser.set_defaults(func=meta)

    # Extra parser
    extra_parser = subparsers.add_parser('extra', help='Generate extra meta')
    extra_options = extra_parser.add_mutually_exclusive_group()
    extra_options.add_argument('--augment', default=False,
                               action='store_true', help='Only add value,'
                               ' don\'t change existing')
    extra_options.add_argument('--replace', default=False,
                               action='store_true', help='Only change'
                               ' existing values, don\'t add any')
    extra_parser.set_defaults(func=extra)

    # Parse args
    args = parser.parse_args()
    args.func(args, conf)

if __name__ == '__main__':
    main()
