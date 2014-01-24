#!/usr/bin/env python

from util import *

root_dir = ''
webviewchromium_dir = ''
repos = []
android_target_arch = ''
chromium_target_arch = ''

patches = [
    # stage 1
    'git fetch https://aia-review.intel.com/platform/bionic refs/changes/92/4592/2 && git checkout FETCH_HEAD',  # upstream change
    'git fetch https://aia-review.intel.com/platform/system/core refs/changes/03/3203/2 && git checkout FETCH_HEAD',  # revert our change, redefinition error
    'git fetch https://aia-review.intel.com/platform/frameworks/base refs/changes/93/4593/2 && git checkout FETCH_HEAD',  # sync with upstream

    'git fetch https://aia-review.intel.com/platform/bootable/iago refs/changes/83/4583/2 && git checkout FETCH_HEAD',  # no upstream code, necessary change
    'git fetch https://aia-review.intel.com/platform/bootable/userfastboot refs/changes/04/4804/1 && git checkout FETCH_HEAD',  # no upstream code, necessary change

    'git fetch https://aia-review.intel.com/platform/frameworks/av refs/changes/94/4594/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary
    'git fetch https://aia-review.intel.com/platform/system/netd refs/changes/86/4586/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary
    'git fetch https://aia-review.intel.com/platform/system/vold refs/changes/89/4589/1 && git checkout FETCH_HEAD',  # upstream has no change, but necessary

    # stage 2
    # kernel: Give more memory range out for 2G- trick
    'git fetch https://aia-review.intel.com/kernel/intel-uefi refs/changes/59/4459/1 && git checkout FETCH_HEAD',

    'git fetch https://aia-review.intel.com/platform/build refs/changes/81/4181/1 && git checkout FETCH_HEAD',  # Enable build for Chromium WebView
    'git fetch https://aia-review.intel.com/platform/build refs/changes/21/3921/1 && git checkout FETCH_HEAD',  # force to build v8 host tools with m64
    'git fetch https://aia-review.intel.com/platform/build refs/changes/93/4393/1 && git checkout FETCH_HEAD',  # Set the code range size as the correct value on Android, 64bit: gold has default alignment as 2M for PT_LOAD segment for 64bit
    # chromium_org
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/95/2395/2 && git checkout FETCH_HEAD',  # build/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/94/3194/5 && git checkout FETCH_HEAD',  # build/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/92/4792/1 && git checkout FETCH_HEAD',  # base/android/jni_generator/ upstream r226503
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/93/4793/1 && git checkout FETCH_HEAD',  # base/android/jni_generator/ upstream r232858
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/56/4556/2 && git checkout FETCH_HEAD',  # base/android/jni_generator/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/94/4794/1 && git checkout FETCH_HEAD',  # base/ upstream r234212
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/95/4795/1 && git checkout FETCH_HEAD',  # base/ upstream r235725
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/57/4557/2 && git checkout FETCH_HEAD',  # base/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/96/4796/1 && git checkout FETCH_HEAD',  # net/ upstream r234285
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/58/4558/2 && git checkout FETCH_HEAD',  # net/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/97/4797/2 && git checkout FETCH_HEAD',  # ui/ upstream r234312
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/98/4798/1 && git checkout FETCH_HEAD',  # android_webview/ upstream r237788
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/60/4560/3 && git checkout FETCH_HEAD',  # android_webview/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/02/4802/4 && git checkout FETCH_HEAD',  # content/ upstream r235815
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/61/4561/6 && git checkout FETCH_HEAD',  # content/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/01/4801/2 && git checkout FETCH_HEAD',  # chrome/ upstream r236536
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/62/4562/2 && git checkout FETCH_HEAD',  # chrome/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/63/4563/1 && git checkout FETCH_HEAD',  # components/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/00/4800/1 && git checkout FETCH_HEAD',  # testing/android/native_test/ upstream r234513
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/99/4799/1 && git checkout FETCH_HEAD',  # sync/ upstream r234804
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/66/4566/1 && git checkout FETCH_HEAD',  # sandbox/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/77/4577/1 && git checkout FETCH_HEAD',  # media/ upstream r234278
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/57/3357/3 && git checkout FETCH_HEAD',  # media/
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/29/3929/2 && git checkout FETCH_HEAD',  # import x86_64.mk files
    # third_party
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/third_party/icu refs/changes/27/3027/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/third_party/openssl refs/changes/28/3028/1 && git checkout FETCH_HEAD',
    # v8
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/v8 refs/changes/29/3029/4 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/v8 refs/changes/27/4227/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/external/chromium_org/v8 refs/changes/78/4578/1 && git checkout FETCH_HEAD',
    # misc
    'git fetch https://aia-review.intel.com/platform/external/webrtc refs/changes/10/4910/1 && git checkout FETCH_HEAD',
    'git fetch https://aia-review.intel.com/platform/frameworks/webview refs/changes/23/3523/3 && git checkout FETCH_HEAD',
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
    group_other.add_argument('-m', '--module', dest='module', help='modules, split with ","', choices=modules_common + modules_system.values() + ['all'], default='webviewchromium')
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


def sync(force=False):
    if not args.sync and not force:
        return

    execute('repo init -u ssh://aia-review.intel.com/platform/manifest -b topic/64-bit/master')
    command = 'repo sync -c -j16'
    if args.sync_local:
        command += ' -l'
    result = execute(command, show_progress=True)
    if result[0]:
        error('sync failed', error_code=result[0])


def patch(force=False):
    if not args.patch and not force:
        return

    backup_dir(webviewchromium_dir)
    execute('find -name "*linux-x86_64.mk" | xargs rm -f')
    restore_dir()

    for patch in patches:
        pattern = re.compile('aia-review\.intel\.com/(.*) (.*) &&')
        match = pattern.search(patch)
        path = match.group(1)

        # Handle repos like platform/build, device/intel/haswell
        repo = path
        if re.search('^platform', repo):
            repo = repo.replace('platform/', '')

        repo = repo.replace('kernel/intel-uefi', 'linux/kernel-uefi')

        change = match.group(2)
        backup_dir(root_dir + '/' + repo)

        cmd_fetch = 'git fetch ssh://aia-review.intel.com/' + path + ' ' + change
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
        execute('git reset --hard aia/topic/64-bit/master', show_command=False)
        info(repo + ' is reset to aia/topic/64-bit/master')
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
            command = '. ' + root_dir + '/build/envsetup.sh && lunch ' + combo + ' && '

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
    mk64()
    build()
    git_status()
    dep()
    test_build()
    scan()
    burn_live()
