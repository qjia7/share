from util import *

args = ''
root_dir = ''     # e.g., /workspace/project/chromium-linux
src_dir = ''      # e.g., /workspace/project/chromium-linux/src
build_dir = ''    # e.g., /workspace/project/chromium-linux/src/out/Release
gen_mk = ''
target_os = ''
target_arch = ''
target_module = ''
# From this rev, do not append --target-arch to envsetup.sh, instead, use android_gyp -Dtarget_arch.
# From rev 252166, envsetup.sh --target-arch would report an error.
rev_envsetup = 252034

# Form this rev, envsetup would no longer set OS=android, we need to define it using GYP_DEFINES='OS=android'
rev_gyp_defines = 260548

# From this rev, android_gyp is no longer supported. Use gyp_chromium instead.
rev_no_android_gyp = 262292


def has_build_dir():
    if not os.path.exists(build_dir):
        warning(build_dir + ' directory doesn\'t exist. Will create the directory for you and perform a clean build')
        os.makedirs(build_dir)
        return False

    return True


def get_target_os():
    return root_dir[root_dir.rfind('-') + 1:]

###########################################################


def check():
    # System sanity check
    if not is_windows() and not is_linux():
        error('Current host system is not supported')

# override format_epilog to make it format better
argparse.format_epilog = lambda self, formatter: self.epilog


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to update, build and run Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  update:
  python %(prog)s -u 'sync --force'
  python %(prog)s -u runhooks
  python %(prog)s -u fetch

  build:
  python %(prog)s -b -c -v
  python %(prog)s -b --target-module webview // out/Release/lib/libstandalonelibwebviewchromium.so->Release/android_webview_apk/libs/x86/libstandalonelibwebviewchromium.so
  python %(prog)s -b --target-module chrome

  run:
  python %(prog)s -r release
  python %(prog)s -r release -g
  python %(prog)s -r debug
  python %(prog)s -r release -o=--enable-logging=stderr
  python %(prog)s -r release -o--enable-logging=stderr
  python %(prog)s -r release '-o --enable-logging=stderr'
  python %(prog)s -r release --run-debug-renderer
  python %(prog)s -p android -r release --run-option 'http://browsermark.rightware.com'

  python %(prog)s --owner

  update & build & run
  python %(prog)s -u sync -b
  python %(prog)s -b

''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupBuild = parser.add_argument_group('build')
    groupBuild.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    groupBuild.add_argument('--gen-mk', dest='gen_mk', help='generate makefile', action='store_true')
    groupBuild.add_argument('-v', '--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')

    groupRun = parser.add_argument_group('run')
    groupRun.add_argument('-r', '--run', dest='run', help='run', action='store_true')
    groupRun.add_argument('-o', '--run-option', dest='run_option', help='option to run')
    groupRun.add_argument('-g', '--run-gpu', dest='run_GPU', help='enable GPU acceleration', action='store_true')
    groupRun.add_argument('--run-debug-renderer', dest='run_debug_renderer', help='run gdb before renderer starts', action='store_true')

    # Other options
    #dir: <arch>-<target-os>/out/<type>, example: x86-linux/out/Release
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64'], default='x86')
    #parser.add_argument('--target-os', dest='target_os', help='target os', choices=['linux', 'android'], default='linux')
    parser.add_argument('--type', dest='type', help='type', choices=['release', 'debug'], default='release')
    parser.add_argument('--target-module', dest='target_module', help='target module to build', choices=['chrome', 'webview', 'content_shell'])

    parser.add_argument('--owner', dest='owner', help='find owner for latest commit', action='store_true')
    parser.add_argument('-d', '--root-dir', dest='root_dir', help='set root directory')
    parser.add_argument('--layout-test', dest='layout_test', help='cases to run against')
    parser.add_argument('-i', '--install', dest='install', help='install chrome for android', choices=['release', 'debug'])
    parser.add_argument('--log-file', dest='log_file', help='log file to record log', default='')
    parser.add_argument('--rev', dest='rev', type=int, help='revision', default=0)

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global root_dir, src_dir, build_dir, target_os, target_module, target_arch, gen_mk

    if args.root_dir:
        root_dir = args.root_dir
    else:
        root_dir = get_symbolic_link_dir()

    target_os = get_target_os()
    target_arch = args.target_arch

    src_dir = root_dir + '/src'
    build_dir = src_dir + '/out/' + args.type.capitalize()

    os.putenv('http_proxy', '127.0.0.1:8118')
    os.putenv('https_proxy', '127.0.0.1:8118')

    if is_windows():
        path = os.getenv('PATH')
        p = re.compile('depot_tools')
        if not p.search(path):
            path = 'd:\user\ygu5\project\chromium\depot_tools;' + path
            os.putenv('PATH', path)

    os.putenv('GYP_GENERATORS', 'ninja')
    if target_os == 'windows':
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        os.putenv('GYP_MSVS_VERSION', '2010e')
        os.putenv('GYP_MSVS_OVERRIDE_PATH', 'd:/user/ygu5/project/chromium/win_toolchain')
        os.putenv('WDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/WDK')
        os.putenv('DXSDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/DXSDK')
        os.putenv('WindowsSDKDir', 'd:/user/ygu5/project/chromium/win_toolchain/win8sdk')
    elif target_os == 'linux':
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0')
        os.putenv('CHROME_DEVEL_SANDBOX', '/usr/local/sbin/chrome-devel-sandbox')
    elif target_os == 'android':
        if args.rev < rev_envsetup:
            backup_dir(src_dir)
            shell_source('build/android/envsetup.sh --target-arch=' + target_arch, use_bash=True)
            restore_dir()
            if not os.getenv('ANDROID_SDK_ROOT'):
                error('Environment is not well set')

        if args.rev < rev_gyp_defines:
            os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 enable_svg=0')
        else:
            os.putenv('GYP_DEFINES', 'OS=android werror= disable_nacl=1 enable_svg=0')

    if not args.target_module:
        if target_os == 'linux':
            target_module = 'chrome'
        elif target_os == 'android':
            target_module = 'webview'
    else:
        target_module = args.target_module

    gen_mk = args.gen_mk
    if not has_build_dir():
        gen_mk = True


def update():
    if not args.update:
        return()

    # 'third_party/skia/src' is not on master
    repos = ['./', 'third_party/WebKit']
    for repo in repos:
        is_master = False
        backup_dir(src_dir + '/' + repo)
        branches = commands.getoutput('git branch').split('\n')
        for branch in branches:
            if branch == '* master':
                is_master = True

        if not is_master:
            error('Repo ' + repo + ' is not on master')

        restore_dir()

    backup_dir(root_dir)

    if host_os == 'Linux' and not has_process('privoxy'):
        execute('sudo privoxy /etc/privoxy/config')

    cmd = 'gclient ' + args.update
    if target_os == 'android':
        if args.rev < rev_envsetup:
            cmd = 'source src/build/android/envsetup.sh --target-arch=' + target_arch + ' && ' + cmd
        else:
            cmd = 'source src/build/android/envsetup.sh && ' + cmd
    result = execute(bashify(cmd), show_progress=True)

    if host_os == 'Linux':
        execute('sudo killall privoxy')

    if result[0]:
        error('Fail to execute command: ' + cmd, error_code=result[0])

    restore_dir()


def gen_makefile():
    if not gen_mk:
        return

    backup_dir(src_dir)
    if target_os == 'android':

        if target_arch == 'x86':
            target_arch_temp = 'ia32'
        else:
            target_arch_temp = target_arch

        # We can't omit this step as android_gyp is a built-in command, instead of environmental variable.
        if args.rev < rev_envsetup:
            cmd = bashify('source build/android/envsetup.sh --target-arch=' + target_arch + ' && android_gyp -Dwerror= -Duse_goma=0')
        elif args.rev < rev_gyp_defines:
            cmd = bashify('source build/android/envsetup.sh && android_gyp -Dwerror= -Duse_goma=0 -Dtarget_arch=' + target_arch_temp)
        else:
            cmd = bashify('source build/android/envsetup.sh && build/gyp_chromium -Dwerror= -Duse_goma=0 -Dtarget_arch=' + target_arch_temp)
    else:
        cmd = 'build/gyp_chromium -Dwerror='

    result = execute(cmd, interactive=True)
    if result[0]:
        error('Fail to execute command: ' + cmd, error_code=result[0])

    restore_dir()


def build():
    if not args.build:
        return()

    backup_dir(src_dir)

    print '== Build Environment =='
    print 'Directory of root: ' + root_dir
    print 'Build type: ' + args.type
    print 'Build system: Ninja'
    print 'Need clean build: ' + str(gen_mk)
    print 'Host OS: ' + host_os
    print 'Target OS: ' + target_os.capitalize()
    print '======================='

    ninja_cmd = 'ninja -j16'

    if args.build_verbose:
        ninja_cmd += ' -v'

    ninja_cmd += ' -C ' + build_dir

    if target_module == 'webview':
        ninja_cmd += ' android_webview_apk libwebviewchromium'
    elif target_module == 'content_shell' and target_os == 'android':
        ninja_cmd += ' content_shell_apk'
    else:
        ninja_cmd += ' ' + target_module

    result = execute(ninja_cmd, log_file=args.log_file, show_progress=True)
    if result[0]:
        error('Fail to execute command: ' + ninja_cmd, error_code=result[0])

    restore_dir()


def install():
    if not args.install:
        return

    if not target_os == 'android':
        return

    backup_dir(src_dir)
    execute('python build/android/adb_install_apk.py --apk ContentShell.apk --' + args.install)
    restore_dir()


def run():
    if not args.run:
        return()

    if target_os == 'linux':
        option = ' --flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + root_dir + '/user-data'

        if args.run_GPU:
            option += ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

        if args.run_debug_renderer:
            if args.type.upper() == 'RELEASE':
                warning('Debugger should run with debug version. Switch to it automatically')
                args.type = 'debug'
            option = option + ' --renderer-cmd-prefix="xterm -title renderer -e gdb --args"'

        cmd = build_dir + '/chrome ' + option
    else:
        cmd = root_dir + '/src/build/android/adb_run_content_shell'

    if args.run_option:
        cmd += ' ' + args.run_option

    execute(cmd)


def find_owner():
    if not args.owner:
        return()

    backup_dir(src_dir)
    files = commands.getoutput('git diff --name-only HEAD origin/master').split('\n')
    owner_file_map = {}  # map from OWNERS file to list of modified files
    for file in files:
        dir = os.path.dirname(file)
        while not os.path.exists(dir + '/OWNERS'):
            dir = os.path.dirname(dir)

        owner_file = dir + '/OWNERS'
        if owner_file in owner_file_map:
            owner_file_map[owner_file].append(file)
        else:
            owner_file_map[owner_file] = [file]

    for owner_file in owner_file_map:
        owner = commands.getoutput('cat ' + dir + '/OWNERS')
        print '--------------------------------------------------'
        print '[Modified Files]'
        for modified_file in owner_file_map[owner_file]:
            print modified_file
        print '[OWNERS File]'
        print owner

    restore_dir()


def layout_test():
    if not args.layout_test:
        return()

    backup_dir(src_dir + '/out/Release')
    if os.path.isdir('content_shell'):
        execute('rm -rf content_shell_dir')
        execute('mv content_shell content_shell_dir')
    restore_dir()

    backup_dir(src_dir)
    execute('ninja -C out/Release content_shell')
    execute('webkit/tools/layout_tests/run_webkit_tests.sh ' + args.layout_test)
    restore_dir()

if __name__ == '__main__':
    check()
    handle_option()
    setup()
    update()
    gen_makefile()
    build()
    install()
    run()
    find_owner()
    layout_test()
