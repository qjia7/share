# TODO:
# Update rev_commit once all builds are finished for a rev, which would free some memory.
# From 245002, may need to manually execute "gclient sync -f" with hook to check out gn related code.

# Build speed
# android_content_shell: 25/hour
# linux_chrome: 30/hour

# build:
# linux-x86-chrome: rev.tar.gz, rev.FAIL, rev.NULL
# android-x86-content_shell: rev.apk, rev.FAIL, rev.NULL. Finished: 235194-238638

# Build master: host all the builds.
# Build slave: ssh-keygen && ssh-add ~/.ssh/id_rsa && cat ~/.ssh/id_rsa.pub | ssh ubuntu-ygu5-02 cat - >>~/.ssh/authorized_keys

# Chromium revision can be checked at https://src.chromium.org/viewvc/chrome?view=revision&revision=xxxxxx

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
from common import *

import time
import os as OS
import fileinput
import random
import select

rev_commit = {}

# os -> [build, fetch_time, rev_min, rev_max, rev_git_max]
# build -> [[arch, module, rev_next], [arch, module, rev_next]]
# Example: {'android': [[['x86', 'webview', 100000], ['x86', 'content_shell', 200000]], 20140115, 10000, 999999, 150000]}

os_info = {}
OS_INFO_INDEX_BUILD = 0
OS_INFO_INDEX_TIME = 1
OS_INFO_INDEX_REV_MIN = 2
OS_INFO_INDEX_REV_MAX = 3
OS_INFO_INDEX_REV_GIT = 4

OS_INFO_INDEX_BUILD_ARCH = 0
OS_INFO_INDEX_BUILD_MODULE = 1
OS_INFO_INDEX_BUILD_REV_NEXT = 2

# build_next = [os, arch, module, rev_next, index_next]
BUILD_NEXT_INDEX_OS = 0
BUILD_NEXT_INDEX_ARCH = 1
BUILD_NEXT_INDEX_MODULE = 2
BUILD_NEXT_INDEX_REV_NEXT = 3
BUILD_NEXT_INDEX_INDEX_NEXT = 4

DRYRUN = False

fail_number_max = 3

build_every = 1

time_sleep_default = 300

expectfail_list = [
    233707, 236662, 234213, 234223, 234517, 234689, 235193, 235194, 237586,
    241661, 241848,
]

run_chromium_script = 'python ../chromium.py'

################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to build automatically',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --root password
  python %(prog)s -b -r 217377-225138
  python %(prog)s -b --os linux --module chrome -r 233137-242710 --build-every 5
  python %(prog)s -b --os android --module content_shell --keep_out

''')
    parser.add_argument('--os', dest='os', help='os', choices=os_all + ['all'], default='all')
    parser.add_argument('--arch', dest='arch', help='arch', choices=arch_all + ['all'], default='all')
    parser.add_argument('--module', dest='module', help='module', choices=module_all + ['all'], default='all')
    parser.add_argument('-r', '--rev', dest='rev', help='revisions to build. E.g., 233137, 217377-225138')
    parser.add_argument('--root', dest='root_pwd', help='root password')
    parser.add_argument('--build-every', dest='build_every', help='build every number')
    parser.add_argument('--keep-out', dest='keep_out', help='do not remove out dir after failure', action='store_true')
    parser.add_argument('--slave-only', dest='slave_only', help='only do things at slave machine, for sake of test', action='store_true')
    parser.add_argument('--fail-number-max', dest='fail_number_max', help='maximum failure number', type=int)

    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--clean-lock', dest='clean_lock', help='clean all lock files', action='store_true')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)


def setup():
    global os_info, build_every, fail_number_max

    if not args.slave_only:
        result = execute(remotify_cmd('ls ' + dir_out_server), show_command=False)
        if result[0]:
            error('Can not connect to build server')

    if args.fail_number_max:
        fail_number_max = args.fail_number_max

    backup_dir(get_symbolic_link_dir())
    # Packages is split by white space so that you may easily install them all
    ensure_package('libnss3-dev ant libcups2-dev libcap-dev libxtst-dev libasound2-dev libxss-dev')

    OS.putenv('JAVA_HOME', '/usr/lib/jvm/jdk1.6.0_45')

    if args.os == 'all':
        arg_os = os_all
    else:
        arg_os = args.os.split(',')

    if args.arch == 'all':
        arg_arch = arch_all
    else:
        arg_arch = args.arch.split(',')

    if args.module == 'all':
        arg_module = module_all
    else:
        arg_module = args.module.split(',')

    for os, arch, module in [(os, arch, module) for os in arg_os for arch in arg_arch for module in arg_module]:
        if not (os, arch, module) in comb_valid:
            continue

        if not os in os_info:
            os_info[os] = [[], 0, 0, 0, 0]
            if args.rev:
                revs = [int(x) for x in args.rev.split('-')]
                if len(revs) > 1:
                    rev_min = revs[0]
                    rev_max = revs[1]
                else:
                    rev_min = revs[0]
                    rev_max = revs[0]

                os_info[os][OS_INFO_INDEX_REV_MIN] = rev_min
                os_info[os][OS_INFO_INDEX_REV_MAX] = rev_max
            else:
                os_info[os][OS_INFO_INDEX_REV_MIN] = rev_default[0]
                os_info[os][OS_INFO_INDEX_REV_MAX] = rev_default[1]

        os_info[os][OS_INFO_INDEX_BUILD].append([arch, module, os_info[os][OS_INFO_INDEX_REV_MIN]])

    update_git_info(fetch=False)

    if not OS.path.exists(dir_log):
        OS.mkdir(dir_log)

    if not OS.path.exists(dir_out):
        OS.mkdir(dir_out)

    for os in os_info:
        for build in os_info[os][OS_INFO_INDEX_BUILD]:
            arch = build[OS_INFO_INDEX_BUILD_ARCH]
            module = build[OS_INFO_INDEX_BUILD_MODULE]
            dir_comb_slave = dir_out + '/' + get_comb_name(os, arch, module)
            dir_comb_server = dir_out_server + '/' + get_comb_name(os, arch, module)
            # Make dir_comb for slave
            if not OS.path.exists(dir_comb_slave):
                OS.mkdir(dir_comb_slave)
            # Make dir_comb for server

            result = execute(remotify_cmd('ls ' + dir_comb_server))
            if result[0]:
                execute(remotify_cmd('mkdir -p ' + dir_comb_server))

    if args.build_every:
        build_every = int(args.build_every)

    restore_dir()


def build():
    if not args.build:
        return

    fail_number = 0
    need_sleep = False
    while True:
        build_next = get_build_next()
        os_next = build_next[BUILD_NEXT_INDEX_OS]
        rev_next = build_next[BUILD_NEXT_INDEX_REV_NEXT]
        index_next = build_next[BUILD_NEXT_INDEX_INDEX_NEXT]
        if rev_next in rev_commit:
            os_info[os_next][OS_INFO_INDEX_BUILD][index_next][OS_INFO_INDEX_BUILD_REV_NEXT] = rev_next + 1
            result = build_one(build_next)
            if result:
                fail_number += 1
                if fail_number >= fail_number_max:
                    error('You have reached maximum failure number')
            else:
                fail_number = 0
        else:
            os = build_next[BUILD_NEXT_INDEX_OS]
            rev_max = os_info[os][OS_INFO_INDEX_REV_MAX]
            if rev_next > rev_max:
                return

            time_fetch = os_info[os][OS_INFO_INDEX_TIME]
            time_diff = get_time() - time_fetch

            if time_diff < time_sleep_default:
                time_sleep = time_sleep_default - time_diff
            else:
                time_sleep = time_sleep_default

            if need_sleep:
                info('Sleeping ' + str(time_sleep) + ' seconds...')
                time.sleep(time_sleep)
            else:
                need_sleep = True
            update_git_info(fetch=True)

        # Allow pause
        seconds = 3
        info('You have ' + str(seconds) + ' seconds to type "enter" to pause')
        i, o, e = select.select([sys.stdin], [], [], seconds)
        if i:
            info('Please type "r" to resume')
            while True:
                input = raw_input()
                if input == 'r':
                    break


def patch_func(name):
    func_name = 'patch_' + name
    info(func_name)
    globals()[func_name]()


# Patch the problem disable_nacl=1
def patch_src_disable_nacl():
    backup_dir('src/build')

    for line in fileinput.input('all.gyp', inplace=1):
        if re.search('native_client_sdk_untrusted', line):
            continue
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()
    restore_dir()


# Fix the issue using the same way introduced by @237081
def patch_src_basename():
    backup_dir('src/chrome')

    file_browser = 'browser/component_updater/test/update_manifest_unittest.cc'
    file_browser_new = file_browser.replace('update_manifest_unittest', 'component_update_manifest_unittest')
    file_common = 'common/extensions/update_manifest_unittest.cc'

    if not OS.path.exists(file_browser) or not OS.path.exists(file_common):
        return

    gypi_file = 'chrome_tests_unit.gypi'
    for line in fileinput.input(gypi_file, inplace=1):
        if re.search(file_browser, line):
            line = line.replace(file_browser, file_browser_new)
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()

    execute('mv ' + file_browser + ' ' + file_browser_new)

    restore_dir()


# Patch the problem of __int128 in openssl
def patch_openssl_int128():
    backup_dir('src/third_party/openssl')
    execute('git reset --hard 08086bd0f0dfbc08d121ccc6fbd27de9eaed55c7')
    restore_dir()


# Patch the problem of -mfpu=neon in libyuv
def patch_libyuv_neon():
    backup_dir('src/third_party/libyuv')
    execute('git reset --hard dd4995805827539ee2c5b4b65c7514e62df2d358')
    restore_dir()


def patch_libvpx_neon():
    backup_dir('src/third_party/libvpx')
    file = 'libvpx.gyp'
    old = '\'OS=="android"\', {'
    new = '\'OS=="android" and ((target_arch=="arm" or target_arch=="armv7") and arm_neon==0)\', {'
    need_change = True
    for line in fileinput.input(file, inplace=1):
        if need_change and re.search(old, line):
            line = line.replace(old, new)
            need_change = False
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()
    restore_dir()


def patch_opus_celt():
    backup_dir('src/third_party/opus/src')
    result = execute('git reset --hard e3ea049fcaee2247e45f0ce793d4313babb4ef69')
    if result[0]:
        error('Fail to patch')
    restore_dir()


def patch_src_sampling():
    backup_dir('src')
    result = execute('git revert -n 462ceb0a79acbd01421795bf2391643ca6d73f78')
    if result[0]:
        error('Fail to patch')
    restore_dir()


# Patch the code to solve some build error problem in upstream
def patch_after_sync(os, arch, module, rev):
    dir_repo = dir_project + '/chromium-' + os
    backup_dir(dir_repo)

    if rev >= 233687 and rev < 233690:
        patch_func('opus_celt')

    if rev >= 234913 and rev < 234919:
        patch_func('openssl_int128')

    if rev >= 235053 and rev < 235114:
        patch_func('src_disable_nacl')

    if rev >= 235193 and rev < 235196:
        patch_func('webrtc')

    if rev >= 236727 and rev < 237081:
        patch_func('src_basename')

    if rev >= 242671 and rev < 242679:
        patch_func('src_sampling')

    if rev >= 244572 and rev < 244600:
        patch_func('libyuv_neon')

    if rev >= 247840 and rev < 248040:
        patch_func('libvpx_neon')

    restore_dir()


def patch_before_build(os, arch, module, rev):
    dir_repo = dir_project + '/chromium-' + os

    # For 7c849b3d759fa9fedd7d4aea73577d643465918d (rev 253545)
    # http://comments.gmane.org/gmane.comp.web.chromium.devel/50482
    execute('rm -f ' + dir_repo + '/src/out/Release/gen/templates/org/chromium/base/ActivityState.java')


def move_to_server(file, os, arch, module):
    dir_comb_server = dir_out_server + '/' + get_comb_name(os, arch, module)
    execute('scp ' + file + ' gyagp@' + server + ':' + dir_comb_server)
    execute('rm -f ' + file)


def build_one(build_next):
    (os, arch, module, rev, index) = build_next

    info('Begin to build ' + get_comb_name(os, arch, module) + '@' + str(rev) + '...')
    dir_comb = dir_out + '/' + get_comb_name(os, arch, module)
    if rev in expectfail_list:
        file_final = dir_comb + '/' + str(rev) + '.EXPECTFAIL'
        execute('touch ' + file_final)
        move_to_server(file_final, os, arch, module)
        return 0

    file_log = dir_log + '/' + get_comb_name(os, arch, module) + '@' + str(rev) + '.log'

    if not args.slave_only:
        file_lock = dir_out_server + '/' + get_comb_name(os, arch, module) + '/' + str(rev) + '.LOCK'
        execute(remotify_cmd('touch ' + file_lock))

    commit = rev_commit[rev]
    dir_repo = dir_project + '/chromium-' + os

    cmd_sync = run_chromium_script + ' -u "sync -f -n -j16 --revision src@' + commit + '"' + ' -d ' + dir_repo
    result = execute(cmd_sync, dryrun=DRYRUN, show_progress=True)
    if result[0]:
        execute(remotify_cmd('rm -f ' + file_lock))
        error('Sync failed', error_code=result[0])

    patch_after_sync(os, arch, module, rev)

    cmd_gen_mk = run_chromium_script + ' --gen-mk --target-arch ' + arch + ' --target-module ' + module + ' -d ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_gen_mk, dryrun=DRYRUN, show_progress=True)
    if result[0]:
        # Run hook to retry. E.g., for revision >=252065, we have to run with hook to update gn tool.
        cmd_sync_hook = cmd_sync.replace('-n ', '')
        execute(cmd_sync_hook, dryrun=DRYRUN, show_progress=True)
        result = execute(cmd_gen_mk, dryrun=DRYRUN)
        if result[0]:
            execute(remotify_cmd('rm -f ' + file_lock))
            error('Failed to generate makefile')

    patch_before_build(os, arch, module, rev)

    cmd_build = run_chromium_script + ' -b --target-arch ' + arch + ' --target-module ' + module + ' -d ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_build, dryrun=DRYRUN, show_progress=True)

    # Retry here
    if result[0]:
        if os == 'android':
            execute('sudo ' + dir_repo + '/src/build/install-build-deps-android.sh', dryrun=DRYRUN)
        if result[0] and not args.keep_out:
            execute('rm -rf ' + dir_repo + '/src/out', dryrun=DRYRUN)

        result = execute(cmd_build, dryrun=DRYRUN)

    # Handle result, either success or failure. TODO: Need to handle other comb.
    if os == 'android' and module == 'content_shell':
        if result[0]:
            file_final = dir_comb + '/' + str(rev) + '.FAIL'
            execute('touch ' + file_final)
        else:
            file_final = dir_comb + '/' + str(rev) + '.apk'
            execute('cp ' + dir_repo + '/src/out/Release/apks/ContentShell.apk ' + file_final, dryrun=DRYRUN)
            execute('rm -f ' + file_log)
    elif os == 'android' and module == 'webview':
        if result[0]:
            file_final = dir_comb + '/' + str(rev) + '.FAIL'
            execute('touch ' + file_final)
        else:
            file_final = dir_comb + '/' + str(rev) + '.apk'
            execute('cp ' + dir_repo + '/src/out/Release/apks/AndroidWebView.apk ' + file_final, dryrun=DRYRUN)
            execute('rm -f ' + file_log)
    elif os == 'linux' and module == 'chrome':
        dest_dir = dir_comb + '/' + str(rev)
        if result[0]:
            file_final = dest_dir + '.FAIL'
            execute('touch ' + file_final)
        else:
            OS.mkdir(dest_dir)
            src_dir = dir_repo + '/src/out/Release'
            config_file = dir_repo + '/src/chrome/tools/build/' + os + '/FILES.cfg'
            file = open(config_file)
            lines = file.readlines()
            file.close()
            pattern = re.compile("'filename': '(.*)'")
            files = []
            for line in lines:
                match = pattern.search(line)
                if match and OS.path.exists(src_dir + '/' + match.group(1)):
                    files.append(match.group(1))

            # This file is not included in FILES.cfg. Bug?
            files.append('lib/*.so')

            for file_name in files:
                dest_dir_temp = OS.path.dirname(dest_dir + '/' + file_name)
                if not OS.path.exists(dest_dir_temp):
                    execute('mkdir -p ' + dest_dir_temp)

                # Some are just dir, so we need -r option
                execute('cp -rf ' + src_dir + '/' + file_name + ' ' + dest_dir_temp)

            backup_dir(dir_comb)
            # It's strange some builds have full debug info
            #size = int(OS.path.getsize(str(rev) + '/chrome'))
            #if size > 300000000:
            #    execute('strip ' + str(rev) + '/chrome')
            execute('tar zcf ' + str(rev) + '.tar.gz ' + str(rev))
            execute('rm -rf ' + str(rev))
            execute('rm -f ' + file_log)
            restore_dir()

            file_final = dir_comb + '/' + str(rev) + '.tar.gz'

    if not args.slave_only:
        move_to_server(file_final, os, arch, module)
        execute(remotify_cmd('rm -f ' + file_lock))

    return result[0]


def rev_is_built(os, arch, module, rev):
    # Skip the revision marked as built
    if not args.slave_only:
        rev_min = comb_valid[(os, arch, module)][COMB_VALID_INDEX_REV_MIN]
        rev_max = comb_valid[(os, arch, module)][COMB_VALID_INDEX_REV_MAX]
        if rev >= rev_min and rev <= rev_max:
            return True

    # Check if file exists or not
    if args.slave_only:
        cmd = 'ls ' + dir_out + '/' + get_comb_name(os, arch, module) + '/' + str(rev) + '*'
    else:
        cmd = remotify_cmd('ls ' + dir_out_server + '/' + get_comb_name(os, arch, module) + '/' + str(rev) + '*')

    result = execute(cmd, show_command=True)
    if result[0] == 0:
        return True

    # Check again to avoid conflict among parallel build machines
    second = random.randint(1, 10)
    info('sleep ' + str(second) + ' seconds and check again')
    time.sleep(second)
    result = execute(cmd, show_command=False)
    if result[0] == 0:
        return True

    return False


def get_rev_next(os, index):
    arch = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_ARCH]
    module = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_MODULE]
    rev_next = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_REV_NEXT]
    rev_max = os_info[os][OS_INFO_INDEX_REV_MAX]
    rev_git = os_info[os][OS_INFO_INDEX_REV_GIT]
    for rev in range(rev_next, rev_max + 1):
        if rev > rev_git:
            return rev

        if not rev % build_every == 0:
            continue

        if rev_is_built(os, arch, module, rev):
            info(str(rev) + ' has been built')
            os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_REV_NEXT] = rev + 1
            continue

        # Does not exist from here

        if rev in rev_commit:
            return rev

        # Handle invalid revision number here. TODO: Need to handle other comb.
        dir_comb = dir_out + '/' + get_comb_name(os, arch, module)
        file_final = dir_comb + '/' + str(rev) + '.NULL'
        info(str(rev) + ' does not exist')
        execute('touch ' + file_final)
        if not args.slave_only:
            move_to_server(file_final, os, arch, module)
    return rev_max + 1


# Get the smallest revision from all targeted builds
def get_build_next():
    is_base = True
    for os in os_info:
        for index, comb in enumerate(os_info[os][OS_INFO_INDEX_BUILD]):
            arch = comb[0]
            module = comb[1]
            rev_next_temp = get_rev_next(os, index)

            if is_base or rev_next_temp < rev_next:
                os_next = os
                arch_next = arch
                module_next = module
                rev_next = rev_next_temp
                index_next = index

            if is_base:
                is_base = False

    build_next = [os_next, arch_next, module_next, rev_next, index_next]
    return build_next


def ensure_package(packages):
    package_list = packages.split(' ')
    for package in package_list:
        result = execute('dpkg -l ' + package, show_command=False)
        if result[0]:
            error('You need to install package: ' + package)


def get_time():
    return int(time.time())


def update_git_info_one(os):
    global rev_commit
    backup_dir(dir_root + '/project/chromium-' + os + '/src')
    execute('git log origin master >git_log')
    file = open('git_log')
    lines = file.readlines()
    file.close()

    is_max_rev = True
    pattern_commit = re.compile('^commit (.*)')
    pattern_rev = re.compile('git-svn-id: .*@(.*) (.*)')
    for line in lines:
        match = pattern_commit.search(line)
        if match:
            commit = match.group(1)

        match = pattern_rev.search(line)
        if match:
            rev = int(match.group(1))

            if is_max_rev:
                is_max_rev = False
                if rev <= os_info[os][OS_INFO_INDEX_REV_GIT]:
                    return
                else:
                    rev_git_old = os_info[os][OS_INFO_INDEX_REV_GIT]
                    os_info[os][OS_INFO_INDEX_REV_GIT] = rev

            if rev <= rev_git_old:
                return
            elif rev < os_info[os][OS_INFO_INDEX_REV_MIN]:
                return
            elif rev > os_info[os][OS_INFO_INDEX_REV_MAX]:
                continue
            else:
                rev_commit[rev] = commit

    restore_dir()


def update_git_info(fetch=True):
    for os in os_info:
        if fetch:
            dir_repo = dir_project + '/chromium-' + os
            execute(run_chromium_script + ' -u "fetch" --root-dir ' + dir_repo, dryrun=DRYRUN)
            os_info[os][OS_INFO_INDEX_TIME] = get_time()
        update_git_info_one(os)


# Patch command if it needs to run on build server
def remotify_cmd(cmd):
    return 'ssh gyagp@' + server + ' ' + cmd


def clean_lock():
    if not args.clean_lock:
        return

    for os in os_info:
        for comb in os_info[os][OS_INFO_INDEX_BUILD]:
            arch = comb[0]
            module = comb[1]

            if args.slave_only:
                cmd = 'rm ' + dir_out + '/' + get_comb_name(os, arch, module) + '/*.LOCK'
            else:
                cmd = remotify_cmd('rm ' + dir_out_server + '/' + get_comb_name(os, arch, module) + '/*.LOCK')

            execute(cmd)


################################################################################


if __name__ == '__main__':
    handle_option()
    setup()
    clean_lock()
    build()
