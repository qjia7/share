from util import *


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to upgrade system',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Examples:
  python %(prog)s
  python %(prog)s -t chrome
  python %(prog)s -t system
''')
    parser.add_argument('-t', '--type', dest='type', help='type to upgrade', default='basic', choices=['basic', 'chrome', 'system'])
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def upgrade():
    if args.type == 'basic':
        setup_http()
        execute('sudo apt-get update && sudo apt-get -y dist-upgrade')
    elif args.type == 'chrome':
        setup_socks()
        execute('sudo tsocks apt-get update && sudo tsocks apt-get -y dist-upgrade')
    elif args.type == 'system':
        setup_http()
        execute('sudo update-manager -d')


def remove(path):
    if os.path.exists(path):
        execute('sudo rm -f ' + path)


def setup_http():
    execute('echo \'Acquire::http::proxy "http://proxy-shz.intel.com:911";\' >apt.conf')
    execute('sudo mv apt.conf /etc/apt/')
    remove('/etc/apt/sources.list.d/google.list')


def setup_socks():
    remove('/etc/apt/apt.conf')
    execute('echo \'deb https://dl.google.com/linux/chrome/deb/ stable main\' >google.list')
    execute('sudo mv google.list /etc/apt/sources.list.d/')


if __name__ == "__main__":
    handle_option()
    upgrade()
