#!/usr/bin/env python

from util import *

root_dir = ''
webviewchromium_dir = ''
repos = []
android_target_arch = ''
chromium_target_arch = ''

patches = [
    # Below patches is for chromium upstream webview work, no plan to integrate
    # ABT, will try to work on AOSP upstream first.
    #'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/81/166881/1 && git checkout FETCH_HEAD',
    #'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/82/166882/1 && git checkout FETCH_HEAD',
]

patches_merged = [
    # stage 1
    'git fetch https://android.intel.com/a/aosp/platform/bionic refs/changes/00/163200/1 && git checkout FETCH_HEAD',  # upstream change
    'git fetch https://android.intel.com/a/aosp/platform/frameworks/base refs/changes/06/163206/1 && git checkout FETCH_HEAD',  # upstream change
    'git fetch https://android.intel.com/a/aosp/platform/system/core refs/changes/09/163209/1 && git checkout FETCH_HEAD',  # revert our change, redefinition error
    'git fetch https://android.intel.com/a/bsp/platform/bootable/iago refs/changes/12/163212/1 && git checkout FETCH_HEAD',  # no upstream code, necessary change
    'git fetch https://android.intel.com/a/bsp/platform/bootable/userfastboot refs/changes/15/163215/1 && git checkout FETCH_HEAD',  # no upstream code, necessary change
    'git fetch https://android.intel.com/a/aosp/platform/frameworks/av refs/changes/18/163218/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary
    'git fetch https://android.intel.com/a/aosp/platform/system/netd refs/changes/19/163219/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary
    'git fetch https://android.intel.com/a/aosp/platform/system/vold refs/changes/20/163220/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary

    # stage2
    # chromium_org (24)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/81/164381/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/82/164382/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/83/164383/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/84/164384/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/85/164385/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/86/164386/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/87/164387/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/88/164388/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/89/164389/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/90/164390/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/91/164391/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/92/164392/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/93/164393/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/94/164394/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/95/164395/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/96/164396/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/97/164397/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/98/164398/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/99/164399/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/00/164400/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/01/164401/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/02/164402/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/03/164403/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org refs/changes/04/164404/2 && git checkout FETCH_HEAD',

    # v8 (4)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/v8 refs/changes/17/164417/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/v8 refs/changes/18/164418/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/v8 refs/changes/19/164419/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/v8 refs/changes/20/164420/1 && git checkout FETCH_HEAD',

    # third_party/icu (2)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/icu refs/changes/21/164421/1 && git checkout FETCH_HEAD',
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/icu refs/changes/22/164422/1 && git checkout FETCH_HEAD',

    # third_party/WebKit (1)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/WebKit refs/changes/23/164423/1 && git checkout FETCH_HEAD',

    # third_party/angle_dx11 (1)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/angle_dx11 refs/changes/27/164427/1 && git checkout FETCH_HEAD',

    # third_party/openssl (1)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/openssl refs/changes/28/164428/1 && git checkout FETCH_HEAD',

    # third_party/ots (1)
    'git fetch https://android.intel.com/a/aosp/platform/external/chromium_org/third_party/ots refs/changes/29/164429/1 && git checkout FETCH_HEAD',

    # bridge code (1)
    'git fetch https://android.intel.com/a/aosp/platform/frameworks/webview refs/changes/30/164430/1 && git checkout FETCH_HEAD',

    # build (1)
    'git fetch https://android.intel.com/a/aosp/platform/build refs/changes/32/164432/1 && git checkout FETCH_HEAD',

    # stage 3
    # build (1)
    'git fetch https://android.intel.com/a/aosp/platform/build refs/changes/33/164433/1 && git checkout FETCH_HEAD',
]

dirty_repos = [
    # Repos that possible ever patched. This list is not consistent with
    # patches, it will list all patched repos in histroy.
    'bionic',
    'bootable/iago',
    'bootable/userfastboot',
    'build',
    'device/intel/haswell',
    'external/chromium',
    'external/chromium_org',
    'external/chromium_org/third_party/icu',
    'external/chromium_org/third_party/openssl',
    'external/chromium_org/third_party/WebKit',
    'external/chromium_org/third_party/angle_dx11',
    'external/chromium_org/third_party/ots',
    'external/chromium_org/v8',
    'external/webrtc',
    'frameworks/av',
    'frameworks/base',
    'frameworks/native',
    'frameworks/webview',
    'libnativehelper',
    'linux/kernel-uefi',
    'system/core',
    'system/netd',
    'system/vold',
]

combos = ['emu64-eng', 'hsb_64-eng']
modules_common = ['webviewchromium', 'webview', 'browser', 'BrowserTests']
modules_system = {'emu64-eng': 'emu', 'hsb_64-eng': 'droid'}

################################################################################


def _ensure_repos():
    global repos

    if len(repos) > 0:
        return

    backup_dir(webviewchromium_dir)
    r = os.popen('find -name ".git"')
    lines = r.read().split('\n')
    del lines[len(lines) - 1]
    for repo in lines:
        repo = repo.replace('./', '')
        repo = repo.replace('.git', '')
        repos.append(webviewchromium_dir + '/' + repo)

    for repo in dirty_repos:
        if not re.match('external/chromium_org', repo):
            repos.append(root_dir + '/' + repo)

    restore_dir()


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to sync, build Chromium x64',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s --sync-local
  python %(prog)s --mk64
  python %(prog)s -b --build-showcommands --build-onejob
  python %(prog)s --dep
  python %(prog)s -c emu64-eng -b
  python %(prog)s --test-build
  python %(prog)s --scan -m all -c hsb_64-eng
  python %(prog)s --burn-live /dev/sdc
  python %(prog)s --clean -s --patch -b -c hsb_64-eng -m droid
''')
    group_sync = parser.add_argument_group('sync')
    group_sync.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    group_sync.add_argument('--sync-local', dest='sync_local', help='only update working tree, not fetch', action='store_true')

    group_patch = parser.add_argument_group('patch')
    group_patch.add_argument('--patch', dest='patch', help='apply patches from Gerrit', action='store_true')

    group_clean = parser.add_argument_group('clean')
    group_clean.add_argument('--clean', dest='clean', help='clean patches from Gerrit', action='store_true')

    group_mk64 = parser.add_argument_group('mk64')
    group_mk64.add_argument('--mk64', dest='mk64', help='generate mk for x86_64', action='store_true')

    group_build = parser.add_argument_group('build')
    group_build.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    group_build.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    group_build.add_argument('--build-onejob', dest='build_onejob', help='build with one job, and stop once failure happens', action='store_true')

    group_other = parser.add_argument_group('other')
    group_other.add_argument('-c', '--combo', dest='combo', help='combos, split with ","', choices=combos + ['all'], default='hsb_64-eng')
    group_other.add_argument('-m', '--module', dest='module', help='modules, split with ","', choices=modules_common + modules_system.values() + ['all'], default='droid')
    group_other.add_argument('-d', '--root-dir', dest='root_dir', help='set root directory')
    group_other.add_argument('--dep', dest='dep', help='get dep for each module', action='store_true')
    group_other.add_argument('--git-status', dest='git_status', help='git status for repos', action='store_true')
    group_other.add_argument('--scan', dest='scan', help='scan code during build with static analyzer', action='store_true')
    group_other.add_argument('--test-build', dest='test_build', help='build test with all combos and modules', action='store_true')
    group_other.add_argument('--burn-live', dest='burn_live', help='burn live image')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global root_dir, webviewchromium_dir, android_target_arch, chromium_target_arch

    if not args.root_dir:
        root_dir = os.path.abspath(os.getcwd())
    else:
        root_dir = args.root_dir

    webviewchromium_dir = root_dir + '/external/chromium_org'
    os.chdir(root_dir)
    android_target_arch = 'x86_64'
    chromium_target_arch = 'x64'

    _ensure_repos()


def clean(force=False):
    if not args.clean and not force:
        return

    if not force:
        warning('Clean is very dangerous, your local changes will be lost')
        sys.stdout.write('Are you sure to do the cleanup? [yes/no]: ')
        choice = raw_input().lower()
        if choice not in ['yes', 'y']:
            return

    for repo in dirty_repos:
        backup_dir(root_dir + '/' + repo)
        result = execute('git reset --hard umg/abt/topic/64-bit/master', show_command=False)
        if result[0]:
            error('Fail to clean up repo ' + repo)
        else:
            info(repo + ' is reset to umg/abt/topic/64-bit/master')

        restore_dir()


def sync(force=False):
    if not args.sync and not force:
        return

    #execute('./repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/topic/64-bit/master')
    command = './repo sync -c -j16'
    if args.sync_local:
        command += ' -l'
    result = execute(command, show_progress=True)
    if result[0]:
        error('sync failed', error_code=result[0])


def patch(force=False):
    if not args.patch and not force:
        return

    #backup_dir(webviewchromium_dir)
    #execute('find -name "*linux-x86_64.mk" | xargs rm -f')
    #restore_dir()

    type = 'new'

    for patch in patches:
        if re.search('aia-review', patch):
            type = 'old'

        if type == 'old':
            pattern = re.compile('aia-review\.intel\.com/(.*) (.*) &&')
        else:
            pattern = re.compile('android\.intel\.com/a/(.*) (.*) &&')

        match = pattern.search(patch)
        path = match.group(1)

        # Handle repos like platform/build, device/intel/haswell
        repo = path
        if re.search('^aosp/platform', repo):
            repo = repo.replace('aosp/platform/', '')

        if re.search('^bsp/platform', repo):
            repo = repo.replace('bsp/platform/', '')

        if re.search('^platform', repo):
            repo = repo.replace('platform/', '')

        repo = repo.replace('kernel/intel-uefi', 'linux/kernel-uefi')

        change = match.group(2)
        execute('./repo start x64 ' + repo)
        backup_dir(root_dir + '/' + repo)

        cmd_fetch = 'git fetch ssh://'
        if type == 'old':
            cmd_fetch += 'aia-review.intel.com'
        else:
            cmd_fetch += 'android.intel.com/a'
        cmd_fetch += '/' + path + ' ' + change
        result = execute(cmd_fetch, show_command=False)
        if result[0]:
            error('Failed to execute command ' + cmd_fetch, error_code=result[0])

        result = execute('git show FETCH_HEAD |grep Change-Id:', return_output=True, show_command=False)

        pattern = re.compile('Change-Id: (.*)')
        change_id = result[1]
        match = pattern.search(change_id)
        result = execute('git log |grep ' + match.group(1), show_command=False)
        if result[0]:
            result = execute('git cherry-pick FETCH_HEAD', show_command=False)
            if result[0]:
                error('Fail to cherry-pick ' + patch)
            else:
                info('Succeed to cherry-pick ' + patch)
        else:
            warning('Patch has been cherry picked, so it will be skipped: ' + patch)

        restore_dir()


def mk64(force=False):
    if not args.mk64 and not force:
        return

    backup_dir(webviewchromium_dir)

    # Remove all the x64 mk files
    r = os.popen('find -name "*x86_64*.mk" -o -name "*x64*.mk"')
    files = r.read().split('\n')
    del files[len(files) - 1]
    for file in files:
        os.remove(file)

    # Generate raw .mk files
    command = bashify('export CHROME_ANDROID_BUILD_WEBVIEW=1 && . build/android/envsetup.sh --target-arch=' + chromium_target_arch + ' && android_gyp -Dwerror= ')
    execute(command)

    # Generate related x64 files according to raw .mk files
    file = open('GypAndroid.mk')
    lines = file.readlines()
    file.close()

    fw = open('GypAndroid.linux-' + android_target_arch + '.mk', 'w')

    # auto_x64 -> x64: target->target.linux-<android_target_arch>, host->host.linux-<android_target_arch>
    for line in lines:
        pattern = re.compile('\(LOCAL_PATH\)/(.*)')
        match = pattern.search(line)
        if match:
            auto_x64_file = match.group(1)
            x64_file = auto_x64_file.replace('target', 'target.linux-' + android_target_arch)
            x64_file = x64_file.replace('host', 'host.linux-' + android_target_arch)
            command = 'cp -f ' + auto_x64_file + ' ' + x64_file
            execute(command, show_command=False)

            line = line.replace('target', 'target.linux-' + android_target_arch)
            line = line.replace('host', 'host.linux-' + android_target_arch)
        fw.write(line)

    fw.close()

    # Check if x86 version has corresponding <target_arch> version
    # x86 -> x64: x86-><target_arch>, ia32-><target_arch>
    r = os.popen('find -name "*linux-x86.mk"')
    files = r.read().split('\n')
    del files[len(files) - 1]

    for x86_file in files:
        x64_file = x86_file.replace('x86', android_target_arch)
        x64_file = x64_file.replace('ia32', 'x64')
        if not os.path.exists(x64_file):
            print 'x64 version does not exist: ' + x86_file

    info('Number of x86 mk: ' + os.popen('find -name "*linux-x86.mk" |wc -l').read()[:-1])
    info('Number of x64 mk: ' + os.popen('find -name "*linux-' + android_target_arch + '.mk" |wc -l').read()[:-1])

    restore_dir()


def build(force=False):
    if not args.build and not force:
        return

    if args.combo == 'all':
        combos_build = combos
    else:
        combos_build = args.combo.split(',')

    for combo in combos_build:
        if args.module == 'all':
            modules_build = [modules_system[combo]] + modules_common
        else:
            modules_build = args.module.split(',')

        for module in modules_build:
            command = '. ' + root_dir + '/build/envsetup.sh && lunch ' + combo + ' && unset NDK_ROOT && '

            if module == 'emu' or module == 'droid' or module == 'BrowserTests':
                command += 'make ' + module + ' suffix'
            else:
                command += 'mmma '

                if module == 'webviewchromium':
                    command += 'external/chromium_org'
                elif module == 'webview':
                    command += 'frameworks/webview'
                elif module == 'browser':
                    command += 'packages/apps/Browser'

                command += 'suffix'

            suffix = ''
            if args.build_showcommands:
                suffix += ' showcommands'

            if not args.build_onejob:
                suffix += ' -j16 -k'
            suffix += ' 2>&1 |tee ' + root_dir + '/' + combo + '_' + module + '_log'
            command = command.replace('suffix', suffix)
            command = bashify(command)
            execute(command, show_progress=True, show_duration=True)


def git_status():
    if not args.git_status:
        return

    has_change = False
    repos_change = []

    for repo in repos:
        backup_dir(repo)
        result = execute('git status |grep modified', show_command=False)
        if not result[0]:
            has_change = True
            repos_change.append(repo)
            #print result[1]
        restore_dir()

    if has_change:
        info('The following repos have changes: ' + ','.join(repos_change))
    else:
        info('There is no change at all')


def dep():
    if not args.dep:
        return

    backup_dir(webviewchromium_dir)
    libraries = set()

    file = open('GypAndroid.linux-' + android_target_arch + '.mk')
    lines = file.readlines()
    file.close()

    module_prev = ''
    for line in lines:
        pattern = re.compile('\(LOCAL_PATH\)/(.*)')
        match = pattern.search(line)
        if match:
            mk_file = match.group(1)

            fields = mk_file.split('/')
            module = fields[0]
            if module == 'third_party':
                module = fields[1]

            if module == 'skia':
                continue

            if module_prev != module:
                module_prev = module
                #print '[' + module + ']'

            file = open(mk_file)
            lines = file.readlines()
            file.close()

            i = 0
            while (i < len(lines)):
                if re.match('LOCAL_SHARED_LIBRARIES', lines[i]):
                    i += 1
                    while (lines[i].strip()):
                        library = lines[i].strip()
                        index = library.find('\\')
                        if index > 0:
                            library = library[0:index]
                        libraries.add(library)
                        #print library
                        i += 1
                else:
                    i += 1

    s = ''
    for library in libraries:
        if s == '':
            s = library
        else:
            s += ' ' + library
    print 'Shared libraries: ' + s

    restore_dir()


def test_build():
    if not args.test_build:
        return

    combo_orig = args.combo
    args.combo = 'hsb_64-eng'
    module_orig = args.module
    args.module = 'droid'

    execute('rm -rf ' + root_dir + '/out')
    clean(force=True)
    sync(force=True)
    patch(force=True)
    build(force=True)

    args.combo = combo_orig
    args.module = module_orig


def scan():
    if not args.scan:
        return

    if args.module == 'all':
        modules_build = ['webviewchromium', 'webview']
    else:
        modules_build = args.module.split(',')

    for module in modules_build:
        command = '. ' + root_dir + '/build/envsetup.sh && lunch hsb_64-eng && WITH_STATIC_ANALYZER=1 WITHOUT_CLANG=true mmma -B '
        if module == 'webviewchromium':
            command += 'external/chromium_org'
        if module == 'webview':
            command += 'frameworks/webview'
        elif module == 'browser':
            command += 'packages/apps/Browser'

        command += ' -j16' + ' 2>&1 |tee ' + root_dir + '/' + module + '_scan_log'
        command = bashify(command)
        execute(command, show_duration=True)


def burn_live():
    if not args.burn_live:
        return

    img = 'out/target/product/hsb_64/live.img'
    if not os.path.exists(img):
        error('Could not find the live image to burn')

    sys.stdout.write('Are you sure to burn live image to ' + args.burn_live + '? [yes/no]: ')
    choice = raw_input().lower()
    if choice not in ['yes', 'y']:
        return

    execute('sudo dd if=' + img + ' of=' + args.burn_live + ' && sync', interactive=True)


if __name__ == '__main__':
    handle_option()
    setup()
    clean()
    sync()
    patch()
    #mk64()
    build()
    git_status()
    dep()
    test_build()
    scan()
    burn_live()
