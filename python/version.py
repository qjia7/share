from util import *

default_java_file = '/usr/lib/jvm/default-java'
gcc_file = '/usr/bin/gcc'


def handle_option():
    global args

    parser = argparse.ArgumentParser(description='Set up the version of Java',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -v 1.5 -t java
  python %(prog)s -v jdk1.7.0_45 -t java
  python %(prog)s -v java-7-openjdk-amd64 -t java

''')

    parser.add_argument('-v', '--version', dest='version', help='version of java, gcc, etc.', default='')
    parser.add_argument('-t', '--target', dest='target', help='target to set version with', choices=['java', 'gcc'], default='java')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    pass


def version():
    if args.version == '':
        if args.target == 'java':
            get_version_java()
        elif args.target == 'gcc':
            get_version_gcc()
    else:
        if args.target == 'java':
            set_version_java()
        elif args.target == 'gcc':
            set_version_gcc()


def get_version_java():
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
        match = re.match('.*jdk(.*)', default_java_result[1])
        if match:
            default_java = match.group(1)
        else:
            error('default-java is not expected', abort=False)
            default_java = 'NULL'
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


def set_version_java():
    version = args.version

    execute('sudo update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/' + version + '/bin/javac 50000')
    execute('sudo update-alternatives --install /usr/bin/java java /usr/lib/jvm/' + version + '/bin/java 50000')
    execute('sudo update-alternatives --install /usr/bin/javaws javaws /usr/lib/jvm/' + version + '/bin/javaws 50000')
    execute('sudo update-alternatives --install /usr/bin/javap javap /usr/lib/jvm/' + version + '/bin/javap 50000')
    execute('sudo update-alternatives --install /usr/bin/jar jar /usr/lib/jvm/' + version + '/bin/jar 50000')
    execute('sudo update-alternatives --install /usr/bin/jarsigner jarsigner /usr/lib/jvm/' + version + '/bin/jarsigner 50000')
    execute('sudo update-alternatives --install /usr/bin/javadoc javadoc /usr/lib/jvm/' + version + '/bin/javadoc 50000')
    execute('sudo update-alternatives --config javac', interactive=True)
    execute('sudo update-alternatives --config java', interactive=True)
    execute('sudo update-alternatives --config javaws', interactive=True)
    execute('sudo update-alternatives --config javap', interactive=True)
    execute('sudo update-alternatives --config jar', interactive=True)
    execute('sudo update-alternatives --config jarsigner', interactive=True)
    execute('sudo update-alternatives --config javadoc', interactive=True)

    execute('sudo rm -f ' + default_java_file)
    execute('sudo ln -s /usr/lib/jvm/' + version + ' /usr/lib/jvm/default-java')

    get_version_java()


def get_version_gcc():
    gcc_version_result = execute('ls -l ' + gcc_file, show_command=True, return_output=True)
    match = re.match('.+gcc-(.+)', gcc_version_result[1])
    if match:
        gcc_version = match.group(1)
    else:
        error('gcc is not expected', abort=False)
        gcc_version = 'NULL'

    info('gcc version: ' + gcc_version)


def set_version_gcc():
    version = args.set_version
    execute('sudo rm -f /usr/bin/gcc', show_command=True)
    execute('sudo ln -s /usr/bin/gcc-' + version + ' /usr/bin/gcc', show_command=True)
    execute('sudo rm -f /usr/bin/g++', show_command=True)
    execute('sudo ln -s /usr/bin/g++-' + version + ' /usr/bin/g++', show_command=True)
    execute('sudo rm -f /usr/bin/cc', show_command=True)
    execute('sudo ln -s /usr/bin/gcc /usr/bin/cc', show_command=True)

    get_version_gcc()


if __name__ == "__main__":
    handle_option()
    setup()
    version()
