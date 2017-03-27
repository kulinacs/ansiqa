import argparse
import ansiqa.stats as get_stats
import yaml
from tabulate import tabulate


def stats(args):
    if args.rolename is None:
        roles = get_stats.scan()
    else:
        roles = []
        for rolename in args.rolename:
            roles.extend(get_stats.scan(rolename))
    if args.dump_vars:
        vars_dict = get_stats.dump_vars(roles)
        if vars_dict:
            print('---\n' + yaml.dump(vars_dict, default_flow_style=False),
                  end='')
        else:
            print('---')
    elif args.dump_defaults:
        defaults_dict = get_stats.dump_defaults(roles)
        if defaults_dict:
            print('---\n' + yaml.dump(defaults_dict, default_flow_style=False),
                  end='')
        else:
            print('---')
    else:
        headers = ['name', 'tasks', 'vars', 'defaults', 'README', 'meta']
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
                           str(role['meta'] is not None)])
        print(tabulate(values, headers, tablefmt="plain"))


def main():
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
    stats_parser.set_defaults(func=stats)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
