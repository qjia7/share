from util import *


def handle_option():
    pass


def setup():
    pass


def cleanup():
    # cache for old package
    execute('sudo apt-get autoclean')
    # cache for all package
    execute('sudo apt-get clean')
    # orphan package
    execute('sudo apt-get -y autoremove', interactive=True)

    # ~/.debug, ~/.flasher ~/.cache

    cmd_kernel = "dpkg -l linux-* | awk '/^ii/{ print $2}' | grep -v -e `uname -r | cut -f1,2 -d'-'` | grep -e [0-9] | grep -E '(image|headers)' | xargs sudo apt-get"
    cmd_kernel_dryrun = cmd_kernel + ' --dry-run remove'
    cmd_kernel += ' -y purge'
    execute(cmd_kernel_dryrun, interactive=True)

    sys.stdout.write('Are you sure to remove above kernels? [yes/no]: ')
    choice = raw_input().lower()
    if choice in ['yes', 'y']:
        execute(cmd_kernel, interactive=True)

if __name__ == "__main__":
    handle_option()
    setup()
    cleanup()
