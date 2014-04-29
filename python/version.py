from util import *

default_java_file = '/usr/lib/jvm/default-java'
gcc_file = '/usr/bin/gcc'


def handle_option():
    global args

    parser = argparse.ArgumentParser(description='Set up the version of Java',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -t java -g
  python %(prog)s -t java -s jdk1.7.0_45
  python %(prog)s -t java -s java-7-openjdk-amd64

''')

    parser.add_argument('-g', '--get-version', dest='get_version', help='get version', action='store_true')
    parser.add_argument('-s', '--set-version', dest='set_version', help='set version')
    parser.add_argument('-t', '--target', dest='target', help='target to set version with', choices=['java', 'gcc'], default='java')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(0)


def setup():
    pass


def get_version():
    if not args.get_version:
        return

    if args.target == 'java':
        _get_version_java()
    elif args.target == 'gcc':
        _get_version_gcc()


def set_version():
    if not args.set_version:
        return

    if args.target == 'java':
        _set_version_java()
    elif args.target == 'gcc':
        _set_version_gcc()


def _get_version_java():
    # Output is in stderr
    java_version_result = execute('java -version', show_command=False, return_output=True)
    match = re.match('java version "(.*)"', java_version_result[1])
    java_version = match.group(1)

    java_home_result = os.getenv('JAVA_HOME')
    if java_home_result:
        match = re.match('jdk(.*)', java_home_result)
        if match:
            java_home = match.group(1)
        else:
            error('JAVA_HOME is not expected', abort=False)
            java_home = 'NULL'
    else:
        java_home = 'NULL'

    if os.path.exists(default_java_file):
        default_java_result = execute('ls -l ' + default_java_file, show_command=False, return_output=True)
        default_java = default_java_result[1].split('/')[-1].rstrip('\n')
    else:
        default_java = 'NULL'

    #info(java_version_result)
    #if java_home_result:
    #    info(java_home_result)
    #if default_java_result:
    #    info(default_java_result)

    info('java -v: ' + java_version)
    info('JAVA_HOME: ' + java_home)
    info('default-java: ' + default_java)


def _update_alt_java(version, files):
    for file in files:
        result = execute('sudo update-alternatives --install /usr/bin/%s %s /usr/lib/jvm/%s/bin/%s 50000' % (file, file, version, file))
        if result[0]:
            warning('Failed to install ' + file)
            continue
        result = execute('sudo update-alternatives --set %s /usr/lib/jvm/%s/bin/%s' % (file, version, file), interactive=True)
        if result[0]:
            warning('Failed to set ' + file)


def _set_version_java():
    version = args.set_version
    _update_alt_java(version, ['java', 'javac', 'javaws', 'javap', 'jar', 'jarsigner', 'javadoc'])
    execute('sudo rm -f ' + default_java_file)
    execute('sudo ln -s /usr/lib/jvm/' + version + ' /usr/lib/jvm/default-java')
    _get_version_java()


def _get_version_gcc():
    gcc_version_result = execute('ls -l ' + gcc_file, show_command=True, return_output=True)
    match = re.match('.+gcc-(.+)', gcc_version_result[1])
    if match:
        gcc_version = match.group(1)
    else:
        error('gcc is not expected', abort=False)
        gcc_version = 'NULL'

    info('gcc version: ' + gcc_version)


def _set_version_gcc():
    version = args.set_version
    execute('sudo rm -f /usr/bin/gcc', show_command=True)
    execute('sudo ln -s /usr/bin/gcc-' + version + ' /usr/bin/gcc', show_command=True)
    execute('sudo rm -f /usr/bin/g++', show_command=True)
    execute('sudo ln -s /usr/bin/g++-' + version + ' /usr/bin/g++', show_command=True)
    execute('sudo rm -f /usr/bin/cc', show_command=True)
    execute('sudo ln -s /usr/bin/gcc /usr/bin/cc', show_command=True)

    _get_version_gcc()


if __name__ == "__main__":
    handle_option()
    setup()
    get_version()
    set_version()
