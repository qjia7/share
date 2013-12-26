# TODO:
# Update rev_commit once all builds are finished for a rev, which would free some memory.

from util import *

import time
import os as OS
import logging


# major -> svn rev, git commit, build. major commit is after build commit.
# To get this, search 'The atomic number' in 'git log origin master chrome/VERSION'
ver_info = {
    34: [241271, '3824512f1312ec4260ad0b8bf372619c7168ef6b', 1751],
    33: [233137, 'eeaecf1bb1c52d4b9b56a620cc5119409d1ecb7b', 1701],
    32: [225138, '6a384c4afe48337237e3da81ccff8658755e2a02', 1652],
    31: [217377, 'c95dd877deb939ec7b064831c2d20d92e93a4775', 1600],
    30: [208581, '88367e9bf6a10b9e024ec99f12755b6f626bbe0c', 1548],
}
VERSION_INFO_INDEX_REV = 0
# revision range for build by default
rev_default = [ver_info[31][VERSION_INFO_INDEX_REV], 999999]
rev_commit = {}

root_dir = '/workspace/project/gyagp/WebCatch'
out_dir = root_dir + '/out'
project_dir = root_dir + '/project'
log_dir = root_dir + '/log'

os_all = ['android', 'linux']
arch_all = ['x86', 'arm']
module_all = ['webview', 'chrome', 'content_shell']

comb_valid = [
    ['android', 'x86', 'content_shell'],
    #['android', 'arm', 'content_shell'],
    #['linux', 'x86', 'chrome']
]

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

LOGGER = logging.getLogger('webcatch')
formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")

#
fail_number = 0
FAIL_NUMBER_MAX = 3
################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description = 'Script to build automatically',
                                     formatter_class = \
                                     argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:
  python %(prog)s --root password
  python %(prog)s -r 217377-225138

''')
    parser.add_argument('--os', dest='os', help='os', choices=os_all + ['all'], default='all')
    parser.add_argument('--arch', dest='arch', help='arch', choices=arch_all + ['all'], default='all')
    parser.add_argument('--module', dest='module', help='module', choices=module_all + ['all'], default='all')
    parser.add_argument('-r', '--rev', dest='rev', help='revisions to build. E.g., 233137, 217377-225138')
    parser.add_argument('--root', dest='root_pwd', help='root password')
    args = parser.parse_args()


def setup():
    global os_info

    backup_dir(get_script_dir())
    ensure_package('libnss3-dev')
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
        if not [os, arch, module] in comb_valid:
            continue

        if not os_info.has_key(os):
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

    LOGGER.setLevel(logging.DEBUG)

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
    log_file = log_dir + '/' + get_comb_name(os, arch, module) + '@' + str(rev) + '.log'
    log = logging.FileHandler(log_file)
    log.setFormatter(formatter)
    LOGGER.addHandler(log)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    LOGGER.addHandler(console)

    LOGGER.info('Begin to build ' + os + ',' + arch + ',' + module + ',' + str(rev) + '...')
    commit = rev_commit[rev]
    repo_dir = project_dir + '/chromium-' + os
    LOGGER.info('Sync to revision ' + str(rev))
    result = execute('python chromium.py -u "sync -f -n --revision src@' + commit +'"' + ' -d ' + repo_dir, catch=True, abort=False, dryrun=DRYRUN)
    if result[0]:
        LOGGER.info(result[1])
        quit(result[0])

    LOGGER.info('')
    command_build = 'python chromium.py -b -c --target-arch ' + arch + ' --target-module ' + module + ' -d ' + repo_dir
    result = execute(command_build, catch=True, abort=False, dryrun=DRYRUN)

    # Retry here
    if result[0]:
        LOGGER.info(result[1])
        if os == 'android':
            pass
            result = execute('sudo ' + repo_dir + '/src/build/install-build-deps-android.sh', catch=True, abort=False, dryrun=DRYRUN)
            if result[0]:
                LOGGER.info(result[1])
            result = execute(command_build, catch=True, abort=False, dryrun=DRYRUN)
        if result[0]:
            LOGGER.info(result[1])
            execute('rm -rf ' + repo_dir + '/src/out', dryrun=DRYRUN)
            result = execute(command_build, catch=True, abort=False, dryrun=DRYRUN)

    # Handle result, either success or failure
    if os == 'android' and module == 'content_shell':
        if result[0]:
            LOGGER.info(result[1])
            execute('touch ' + out_dir + '/' + get_comb_name(os, arch, module) + '/ContentShell@' + str(rev) + '.apk.FAIL')
        else:
            execute('cp ' + repo_dir + '/src/out/Release/apks/ContentShell.apk ' + out_dir + '/' + get_comb_name(os, arch, module) + '/ContentShell@' + str(rev) + '.apk', dryrun=DRYRUN)
            execute('rm -f ' + log_file)

    return result[0]


def get_next_rev(os, index):
    arch = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_ARCH]
    module = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_MODULE]
    rev_next = os_info[os][OS_INFO_INDEX_BUILD][index][OS_INFO_INDEX_BUILD_NEXT]
    rev_max = os_info[os][OS_INFO_INDEX_REV_MAX]
    rev_git = os_info[os][OS_INFO_INDEX_REV_GIT]
    for rev in range(rev_next, rev_max + 1):
        if rev > rev_git:
            return rev

        cmd = 'ls ' + out_dir + '/' + get_comb_name(os, arch, module) + '/*' + str(rev) + '*'
        result = execute(cmd, abort=False, silent=True, catch=True)
        if result[0] == 0:
            continue

        # Does not exist from here

        if rev in rev_commit:
            return rev

        # Handle invalid revision number here
        if os == 'android' and module == 'content_shell':
            execute('touch ' + out_dir + '/' + get_comb_name(os, arch, module) + '/ContentShell@' + str(rev) + '.apk.NULL')

    return rev_max + 1


def get_build_next():
    is_base = True
    for os in os_info:
        for index,comb in enumerate(os_info[os][OS_INFO_INDEX_BUILD]):
            arch = comb[0]
            module = comb[1]
            rev_next_temp = get_next_rev(os, index)
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
    result = execute('dpkg -l ' + name, silent=True, catch=True, abort=False)
    if result[0]:
        error('You need to install package: ' + name)


def get_comb_name(os, arch, module):
    return os + '-' + arch + '-' + module


def get_time():
    return int(time.time())


def update_git_info_one(os):
    global rev_commit
    backup_dir(root_dir + '/project/chromium-' + os + '/src')
    execute('git log origin master >git_log')
    file = open('git_log')
    lines = file.readlines()
    file.close()

    is_max_rev = True
    pattern_commit = re.compile('commit (.*)')
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
            repo_dir = project_dir + '/chromium-' + os
            execute('python chromium.py -u "fetch" --root-dir ' + repo_dir, dryrun=DRYRUN)
            os_info[os][OS_INFO_INDEX_TIME] = get_time()
        update_git_info_one(os)


################################################################################


if __name__ == '__main__':
    handle_option()
    setup()
    build()
