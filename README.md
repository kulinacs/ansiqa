AnsiQA
======

A utility for managing Ansible Roles. Designed to be run inside the `roles` directory.

Inspired by [ansigenome](https://github.com/nickjj/ansigenome/)

Host Depends
------------

depends functionality requires on graphviz to be installed.

Features
--------

### Stats

`ansiqa stats`

Prints stats about roles. With no arguments, `stats` will print the following for each:

* Number of tasks
* Number of variables set
* Number of defaults set
* If a README.* file is present
* If meta/main.yml is present
* If extras/main.yml is present (used by Ansiqa to generate READMEs)

### Meta

`ansiqa meta`

Generate base meta files for roles from values in the AnsiQA config file.

### Extra

`ansiqa extra`

Generate base extra files for roles from values in the AnsiQA config file, stored in `extra/main.yml`. These values are used by AnsiQA to generate READMEs.

### Docs

`ansiqa docs`

Generate a README by filling a Jinja2 template. The readme template must end in .j2, and can be put in the following places:

* Specified in the AnsiQA config file, by the root level token `template`
* Found in the current working directory, matching the README.*.j2 glob
* Found in the user's home directory, matching the README.*.j2 glob

This template is fed a role dictionary, which contains the following tokens

```
'name': the role name
'path': the role absolute path
'defaults': the defaults provided by the role, formatted as yaml
'files': a list of files by the role
'handlers': a list of handlers provided by the role
'meta': a dict containing the values in meta/main.yml
'tasks': a list of tasks provided by the role
'templates': a list of templates provided by the role
'tests': a boolean value, if the tests directory exists
'vars': the variables provided by the role, formatted as yaml
'extra': a dict containing the values in extra/main.yml
```

### Depends

`ansiqa depends`

Dependency introspection. With no arguments, `depends` prints the number of dependencies each role has, the number of times each role is depended on, and the "dependency depth" of each role (how long the longest dependency chain is.)

With the `--graph` flag, ansiqa generates a GraphViz graph to visualize the dependency tree.


Configuration
-------------
The configuration file should be a yaml file named `.ansiqa` and be located either in the current working directory or in the user's home directory. It can have the following root level tokens

```
meta: A dict containing the default values for the meta/main.yml
extra: A dict containing the default values for the extra/main.yml
template: A string containing the path to the README template, first checking the current working directory for the path, then the home directory, and finally checking it as an absolute path.
```
