import argparse
from ansiqa import load
import yaml
from tabulate import tabulate
from termcolor import colored
import os


def load_config():
    '''Load and set defaults for the running configuration'''
    config = {}
    user_config_file = os.path.join(os.path.expanduser('~'), '.ansiqa.yml')
    cwd_config_file = os.path.join(os.getcwd(), '.ansiqa.yml')
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            config.update(yaml.safe_load(f))
    if os.path.exists(cwd_config_file):
        with open(cwd_config_file) as f:
            config.update(yaml.safe_load(f))
    if 'meta' not in config:
        config['meta'] = {}
    if 'extra' not in config:
        config['extra'] = {}
    return config


def _get_roles(args):
    '''Returns the selected roles'''
    if args.rolename is None:
        roles = load.scan()
    else:
        roles = []
        for rolename in args.rolename:
            roles.extend(load.scan(rolename))
    return roles


def stats(args, conf):
    '''Print stats about the selected roles'''
    roles = _get_roles(args)

    # Print variables if selected
    if args.dump_vars:
        vars_dict = load.dump_vars(roles)
        if vars_dict:
            print('---\n' + yaml.dump(vars_dict, default_flow_style=False),
                  end='')
        else:
            print('---')

    # Print defaults if selected
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

    # Print general stats if no option selected
    else:
        headers = ['name', 'tasks', 'vars', 'defaults', 'README', 'meta',
                   'extra']
        values = []
        for role in roles:
            varsnum = len(role['vars'].keys())
            defaultsnum = len(role['defaults'].keys())
            if len(role['readme']) > 0:
                readme = colored('ok', 'green')
            else:
                readme = colored('none', 'red')
            if role['meta']:
                meta = colored('ok', 'green')
            else:
                meta = colored('none', 'red')
            if role['extra']:
                extra = colored('ok', 'green')
            else:
                extra = colored('none', 'red')
            values.append([role['name'], len(role['tasks']), varsnum,
                           defaultsnum, readme, meta, extra])
        print(tabulate(values, headers, tablefmt="plain"))


def __augment_dict(old, update):
    '''Augment values in a dictionary, adding new values but not changing old values'''
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
    '''Replace values in a dictionary, changing old values but not adding new values'''
    for key in old:
        try:
            if isinstance(old[key], dict) and isinstance(update[key], dict):
                __replace_dict(old[key], update[key])
            else:
                old[key] = update[key]
        except (KeyError):
            pass


def meta(args, conf):
    '''Generate meta data for selected roles'''
    roles = _get_roles(args)
    values = []
    for role in roles:
        metadir = os.path.join(role['path'], args.key)
        metafile = os.path.join(metadir, 'main.yml')
        old_dict = dict(role[args.key])
        if args.augment:
            __augment_dict(role[args.key], conf[args.key])
        elif args.replace:
            __replace_dict(role[args.key], conf[args.key])
        else:
            role[args.key].update(conf[args.key])
        if not args.check:
            if not os.path.exists(metadir):
                os.makedirs(metadir)
            with open(metafile, 'w') as f:
                f.write('---\n')
                f.write(yaml.dump(role[args.key], default_flow_style=False))
        if (old_dict == role[args.key]):
            values.append([role['name'], colored('ok', 'green')])
        else:
            values.append([role['name'], colored('changed', 'yellow')])
    print(tabulate(values, tablefmt="plain"))


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
    meta_parser.add_argument('-C', '--check', default=False,
                             action='store_true', help='Don\'t change'
                             'values, just show what would change')
    meta_options = meta_parser.add_mutually_exclusive_group()
    meta_options.add_argument('--augment', default=False,
                              action='store_true', help='Only add value,'
                              ' don\'t change existing')
    meta_options.add_argument('--replace', default=False,
                              action='store_true', help='Only change'
                              ' existing values, don\'t add any')
    meta_parser.set_defaults(func=meta, key='meta')

    # Extra parser
    extra_parser = subparsers.add_parser('extra', help='Generate extra meta')
    extra_parser.add_argument('-r', '--rolename', type=str, nargs='*',
                              help='specific role(s) to operate on')
    extra_parser.add_argument('-C', '--check', default=False,
                              action='store_true', help='Don\'t change'
                              'values, just show what would change')
    extra_options = extra_parser.add_mutually_exclusive_group()
    extra_options.add_argument('--augment', default=False,
                               action='store_true', help='Only add value,'
                               ' don\'t change existing')
    extra_options.add_argument('--replace', default=False,
                               action='store_true', help='Only change'
                               ' existing values, don\'t add any')
    extra_parser.set_defaults(func=meta, key='extra')

    # Parse args
    args = parser.parse_args()
    args.func(args, conf)

if __name__ == '__main__':
    main()
