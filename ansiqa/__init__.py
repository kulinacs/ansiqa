import argparse
from ansiqa import load
import ruamel.yaml as yaml
from tabulate import tabulate
from termcolor import colored
from glob import glob
from jinja2 import Environment, FileSystemLoader
import os
from copy import deepcopy
import pygraphviz as pgv


class ConfigException(Exception):
    '''Raise if a value is not found in the config file'''
    pass


def load_config():
    '''Load the running configuration'''
    config = {}
    template = None
    user_config_file = os.path.join(os.path.expanduser('~'), '.ansiqa')
    cwd_config_file = os.path.join(os.getcwd(), '.ansiqa')
    if os.path.isfile(user_config_file):
        with open(user_config_file) as f:
            config.update(yaml.safe_load(f))
    if os.path.isfile(cwd_config_file):
        with open(cwd_config_file) as f:
            config.update(yaml.safe_load(f))
    return config


def load_template(config):
    '''
    Attempt to load the template file, first from the file specified by
    the config file, then by the default README.*.j2 glob. First checks
    the current directory, then the home directory, then an absolute path.
    '''
    if 'template' in config:
        if os.path.isfile(os.path.join(os.getcwd(), config['template'])):
            template = os.path.join(os.getcwd(), config['template'])
        elif os.path.isfile(os.path.join(os.path.expanduser('~'),
                                         config['template'])):
            template = join(os.path.expanduser('~'), config['template'])
        elif os.path.isfile(config['template']):
            template = config['template']
        else:
            raise ConfigException('Template file not found')
    else:
        if glob(os.path.join(os.getcwd(), 'README.*.j2')):
            template = glob(os.path.join(os.getcwd(), 'README.*.j2'))[0]
        elif glob(os.path.join(os.path.expanduser('~'), 'README.*.j2')):
            template = glob(os.path.join(os.path.expanduser('~'),
                                         'README.*.j2'))[0]
        else:
            template = None
    return template


def _get_roles(args):
    '''Returns the selected roles'''
    if args.rolename is None:
        roles = load.scan()
    else:
        roles = []
        for rolename in args.rolename:
            roles.extend(load.scan(rolename))
    return roles


def stats(args):
    '''Print stats about the selected roles'''
    roles = _get_roles(args)

    # Print variables if selected
    if args.dump_vars:
        vars_dict = load.dump_vars(roles)
        if vars_dict:
            print('---\n' + yaml.dump(vars_dict, default_flow_style=False,
                                      indent=4, block_seq_indent=2), end='')
        else:
            print('---')

    # Print defaults if selected
    elif args.dump_defaults:
        defaults_dict = load.dump_defaults(roles)
        if defaults_dict:
            print('---\n' + yaml.dump(defaults_dict, default_flow_style=False,
                                      indent=4, block_seq_indent=2), end='')
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
        allroles = {}
        for role in roles:
            allroles[role['name']] = role
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
        values.sort()
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


def meta(args):
    '''Generate meta data for selected roles'''
    roles = _get_roles(args)
    values = []
    if args.key not in args.conf:
        raise ConfigException(args.key + ' not defined in configuration')
    for role in roles:
        metadir = os.path.join(role['path'], args.key)
        metafile = os.path.join(metadir, 'main.yml')
        old_dict = deepcopy(role[args.key])
        if args.augment:
            __augment_dict(role[args.key], args.conf[args.key])
        elif args.replace:
            __replace_dict(role[args.key], args.conf[args.key])
        else:
            role[args.key].update(args.conf[args.key])
        if not args.check:
            if not os.path.exists(metadir):
                os.makedirs(metadir)
            with open(metafile, 'w') as f:
                f.write('---\n')
                f.write(yaml.dump(role[args.key], default_flow_style=False,
                                  indent=4, block_seq_indent=2))
        if (old_dict == role[args.key]):
            values.append([role['name'], colored('ok', 'green')])
        else:
            values.append([role['name'], colored('changed', 'yellow')])
    values.sort()
    print(tabulate(values, tablefmt="plain"))


def docs(args):
    '''Generate documentation for the selected roles'''
    roles = _get_roles(args)
    if args.template is None:
        raise ConfigException('No usable template found')
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(args.template)),
        lstrip_blocks=True,
        trim_blocks=True,
        keep_trailing_newline=True)
    filename_parts = os.path.basename(args.template).split('.')
    filename = filename_parts[0] + '.' + filename_parts[1]
    for role in roles:
        role = load.printable(role)
        readme_template = env.get_template(os.path.basename(args.template))
        if not args.check:
            with open(os.path.join(role['path'], filename), 'w') as f:
                f.write(readme_template.render(role))
        else:
            print(readme_template.render(role), end='')


def _build_tree(roles):
    tree = {}
    for role in roles:
        tree[role['name']] = {'depends': set()}
        try:
            if role['meta']['dependencies'] is not None:
                for dep in role['meta']['dependencies']:
                    if isinstance(dep, dict):
                        dep = dep['role']
                    tree[role['name']]['depends'].add(dep)
        except:
            pass
    return tree


def _depended_on(tree):
    for role in tree:
        tree[role]['depended'] = set()
    for role in tree:
        for dep in tree[role]['depends']:
            tree[dep]['depended'].add(role)


def _dependency_depth(tree):
    def __dependency_depth(role):
        try:
            return tree[role]['depth']
        except (KeyError):
            if len(tree[role]['depends']) == 0:
                tree[role]['depth'] = 0
            else:
                tree[role]['depth'] = max([__dependency_depth(dep) for dep in
                                           tree[role]['depends']]) + 1
            return tree[role]['depth']
    for role in tree:
        __dependency_depth(role)


def depends(args):
    roles = load.scan()
    tree = _build_tree(roles)
    if args.graph is None:
        _depended_on(tree)
        _dependency_depth(tree)
        keys = ['role', 'depends', 'depended', 'depth']
        values = []
        for role in tree:
            values.append([role,
                           len(tree[role]['depends']),
                           len(tree[role]['depended']),
                           tree[role]['depth']])
        values.sort()
        print(tabulate(values, keys, tablefmt="plain"))
    else:
        graph = pgv.AGraph(directed=True)
        graph.node_attr['style'] = 'filled,rounded'
        graph.node_attr['shape'] = 'box'
        graph.node_attr['fontcolor'] = '#000000'

        for role in tree:
            graph.add_node(role)
        for role in tree:
            for dep in tree[role]['depends']:
                graph.add_edge(role, dep)
        if args.graph == '-':
            print(graph, end='')
        else:
            with open(args.graph, 'w') as f:
                f.write(graph.string())


def main():
    conf = load_config()
    template = load_template(conf)

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
                             ' values, just show what would change')
    meta_options = meta_parser.add_mutually_exclusive_group()
    meta_options.add_argument('--augment', default=False,
                              action='store_true', help='Only add value,'
                              ' don\'t change existing')
    meta_options.add_argument('--replace', default=False,
                              action='store_true', help='Only change'
                              ' existing values, don\'t add any')
    meta_parser.set_defaults(func=meta, conf=conf, key='meta')

    # Extra parser
    extra_parser = subparsers.add_parser('extra', help='Generate extra meta')
    extra_parser.add_argument('-r', '--rolename', type=str, nargs='*',
                              help='specific role(s) to operate on')
    extra_parser.add_argument('-C', '--check', default=False,
                              action='store_true', help='Don\'t change'
                              ' values, just show what would change')
    extra_options = extra_parser.add_mutually_exclusive_group()
    extra_options.add_argument('--augment', default=False,
                               action='store_true', help='Only add values,'
                               ' don\'t change existing')
    extra_options.add_argument('--replace', default=False,
                               action='store_true', help='Only change'
                               ' existing values, don\'t add any')
    extra_parser.set_defaults(func=meta, conf=conf, key='extra')

    # Docs parser
    docs_parser = subparsers.add_parser('docs', help='Generate README')
    docs_parser.add_argument('-r', '--rolename', type=str, nargs='*',
                             help='specific role(s) to operate on')
    docs_parser.add_argument('-C', '--check', default=False,
                             action='store_true', help='Don\'t change'
                             ' the README, just print the new README')
    docs_parser.set_defaults(func=docs, conf=conf, template=template)

    # Depends parser
    depends_parser = subparsers.add_parser('depends',
                                           help='Dependecy utilities')
    depends_parser.add_argument('-G', '--graph', default=None,
                                const='-', type=str, nargs='?',
                                help='Generate a graphviz dot file')
    depends_parser.set_defaults(func=depends)

    # Parse args
    try:
        args = parser.parse_args()
        args.func(args)
    except (AttributeError):
        parser.print_help()
        exit(0)

if __name__ == '__main__':
    main()
