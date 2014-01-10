# TODO:
# Update rev_commit once all builds are finished for a rev, which would free some memory.


# Build speed
# android_content_shell: 25/hour
# linux_chrome: 30/hour

from util import *
from common import *

import time
import os as OS

rev_commit = {}

# os -> [build, fetch_time, rev_min, rev_max, rev_git_max]
# build -> [[arch, module, build_next]]
os_info = {}
OS_INFO_INDEX_BUILD = 0
OS_INFO_INDEX_TIME = 1
OS_INFO_INDEX_REV_MIN = 2
OS_INFO_INDEX_REV_MAX = 3
OS_INFO_INDEX_REV_GIT = 4

OS_INFO_INDEX_BUILD_ARCH = 0
OS_INFO_INDEX_BUILD_MODULE = 1
OS_INFO_INDEX_BUILD_NEXT = 2

BUILD_NEXT_INDEX_OS = 0
BUILD_NEXT_INDEX_ARCH = 1
BUILD_NEXT_INDEX_MODULE = 2
BUILD_NEXT_INDEX_REV = 3

DRYRUN = False

fail_number = 0
FAIL_NUMBER_MAX = 3

build_every = 1
################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to build automatically',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --root password
  python %(prog)s -r 217377-225138
  python %(prog)s --os linux --module chrome -r 233137-242710 --build-every 5
  python %(prog)s --os android --module content_shell

''')
    parser.add_argument('--os', dest='os', help='os', choices=os_all + ['all'], default='all')
    parser.add_argument('--arch', dest='arch', help='arch', choices=arch_all + ['all'], default='all')
    parser.add_argument('--module', dest='module', help='module', choices=module_all + ['all'], default='all')
    parser.add_argument('-r', '--rev', dest='rev', help='revisions to build. E.g., 233137, 217377-225138')
    parser.add_argument('--root', dest='root_pwd', help='root password')
    parser.add_argument('--build-every', dest='build_every', help='build every number')
    args = parser.parse_args()


def setup():
    global os_info, build_every

    backup_dir(get_script_dir())
    ensure_package('libnss3-dev')
    ensure_package('ant')
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
            comb_dir = dir_out + '/' + get_comb_name(os, arch, module)
            if not OS.path.exists(comb_dir):
                OS.mkdir(comb_dir)

    if args.build_every:
        build_every = int(args.build_every)

    restore_dir()


def build():
    global fail_number
    while True:
        build_next = get_build_next()
        if build_next[BUILD_NEXT_INDEX_REV] in rev_commit:
            result = build_one(build_next)
            if result:
                fail_number += 1
                if fail_number >= FAIL_NUMBER_MAX:
                    error('You have reached maximum failure number')
        else:
            if args.rev:
                return
            else:
                second = 3600
                info('Sleeping ' + str(second) + ' seconds...')
                time.sleep(second)
                update_git_info(fetch=True)


def build_one(build_next):
    (os, arch, module, rev) = build_next
    log_file = dir_log + '/' + get_comb_name(os, arch, module) + '@' + str(rev) + '.log'

    info('Begin to build ' + get_comb_name(os, arch, module) + '@' + str(rev) + '...')
    commit = rev_commit[rev]
    repo_dir = dir_project + '/chromium-' + os
    result = execute('python chromium.py -u "sync -f -n --revision src@' + commit + '"' + ' -d ' + repo_dir + ' --log-file ' + log_file, dryrun=DRYRUN, show_progress=True)
    if result[0]:
        quit(result[0])

    # Patch the problem disable_nacl=1
    if rev >= 235053 and rev < 235114:
        backup_dir(repo_dir + '/src/build')
        execute('mv all.gyp all.gyp.bk')
        fr = open('all.gyp.bk')
        lines = fr.readlines()
        fr.close()

        fw = open('all.gyp', 'w')
        for line in lines:
            if re.search('native_client_sdk_untrusted', line):
                continue
            fw.write(line)
        fw.close()
        restore_dir()

    command_build = 'python chromium.py -b -c --target-arch ' + arch + ' --target-module ' + module + ' -d ' + repo_dir + ' --log-file ' + log_file
    result = execute(command_build, dryrun=DRYRUN, show_progress=True)

    # Retry here
    if result[0]:
        if os == 'android':
            execute('sudo ' + repo_dir + '/src/build/install-build-deps-android.sh', dryrun=DRYRUN)
            result = execute(command_build, dryrun=DRYRUN)
        if result[0]:
            execute('rm -rf ' + repo_dir + '/src/out', dryrun=DRYRUN)
            result = execute(command_build, dryrun=DRYRUN)

    # Handle result, either success or failure. TODO: Need to handle other comb.
    comb_dir = dir_out + '/' + get_comb_name(os, arch, module)
    if os == 'android' and module == 'content_shell':
        if result[0]:
            execute('touch ' + comb_dir + '/ContentShell@' + str(rev) + '.apk.FAIL')
        else:
            execute('cp ' + repo_dir + '/src/out/Release/apks/ContentShell.apk ' + comb_dir + '/ContentShell@' + str(rev) + '.apk', dryrun=DRYRUN)
            execute('rm -f ' + log_file)
    elif os == 'linux' and module == 'chrome':
        dest_dir = comb_dir + '/' + str(rev)
        if result[0]:
            execute('touch ' + dest_dir + '.FAIL')
        else:
            OS.mkdir(dest_dir)
            src_dir = repo_dir + '/src/out/Release'
            config_file = repo_dir + '/src/chrome/tools/build/' + os + '/FILES.cfg'
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
                print file_name
                if not OS.path.exists(dest_dir_temp):
                    execute('mkdir -p ' + dest_dir_temp)

                # Some are just dir, so we need -r option
                execute('cp -rf ' + src_dir + '/' + file_name + ' ' + dest_dir_temp)

            backup_dir(comb_dir)
            # It's strange some builds have full debug info
            #size = int(OS.path.getsize(str(rev) + '/chrome'))
            #if size > 300000000:
            #    execute('strip ' + str(rev) + '/chrome')
            execute('tar zcf ' + str(rev) + '.tar.gz ' + str(rev))
            execute('rm -rf ' + str(rev))
            restore_dir()

    return result[0]


def get_rev_next(os, index):
    arch = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_ARCH]
    module = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_MODULE]
    rev_next = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_NEXT]
    rev_max = os_info[os][OS_INFO_INDEX_REV_MAX]
    rev_git = os_info[os][OS_INFO_INDEX_REV_GIT]
    for rev in range(rev_next, rev_max + 1):
        if rev > rev_git:
            return rev

        if not rev % build_every == 0:
            continue

        cmd = 'ls ' + dir_out + '/' + get_comb_name(os, arch, module) + '/*' + str(rev) + '*'
        result = execute(cmd, show_command=False)
        if result[0] == 0:
            continue

        # Does not exist from here

        if rev in rev_commit:
            return rev

        # Handle invalid revision number here. TODO: Need to handle other comb.
        if os == 'android' and module == 'content_shell':
            execute('touch ' + dir_out + '/' + get_comb_name(os, arch, module) + '/ContentShell@' + str(rev) + '.apk.NULL')
        elif os == 'linux' and module == 'chrome':
            info(str(rev) + ' does not exist')
            execute('touch ' + dir_out + '/' + get_comb_name(os, arch, module) + '/' + str(rev) + '.NULL')

    return rev_max + 1


def get_build_next():
    is_base = True
    for os in os_info:
        for index, comb in enumerate(os_info[os][OS_INFO_INDEX_BUILD]):
            arch = comb[0]
            module = comb[1]
            rev_next_temp = get_rev_next(os, index)
            os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_NEXT] = rev_next_temp
            if is_base:
                is_base = False
                rev_next = rev_next_temp
                build_next = [os, arch, module, rev_next]
            elif rev_next_temp < rev_next:
                rev_next = rev_next_temp
                build_next = [os, arch, module, rev_next]

    return build_next


def ensure_package(name):
    result = execute('dpkg -l ' + name, show_command=False)
    if result[0]:
        error('You need to install package: ' + name)


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
            repo_dir = dir_project + '/chromium-' + os
            execute('python chromium.py -u "fetch" --root-dir ' + repo_dir, dryrun=DRYRUN)
            os_info[os][OS_INFO_INDEX_TIME] = get_time()
        update_git_info_one(os)


################################################################################


if __name__ == '__main__':
    handle_option()
    setup()
    build()
