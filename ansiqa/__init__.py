import os
from ansiqa.scan import get_role


def scan():
    for root, dirs, files in os.walk('.'):
        if 'tasks' in dirs or 'handlers' in dirs:
            role = get_role(root, dirs, files)
            print(role)


def main():
    scan()

if __name__ == '__main__':
    main()
