#!/usr/bin/env python

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import os as OS

dir_root = ''
dir_chromium = ''
dir_out = ''
dir_script = sys.path[0]
dir_backup = '/workspace/service/www/aosp-stable/temp'
target_archs = []
target_devices = []
target_modules = []
chromium_version = ''

patches_init = {
    '.repo/manifests': ['0001-Replace-webview-and-chromium_org.patch'],
}

patches_disable_2nd_arch = {
    'device/intel/baytrail_64': ['0001-baytrail_64-Disable-2nd-arch.patch'],
}

patches_disable_libpac = {
    'external/chromium-libpac': ['0001-Disable-libpac.patch'],
}

patches_build = {
    'build': [
        '0001-build-Make-v8-and-icu-host-tool-64-bit.patch',
        '0002-build-Remove-webview-and-chromium_org-from-blacklist.patch',
    ],
    'external/chromium_org/src/': ['0001-Fix-sandbox.patch'],
}


def handle_option():
    global args

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s all -b
  python %(prog)s -b --build-skip-mk --disable-2nd-arch
''')

    parser.add_argument('--init', dest='init', help='init', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync code for android, chromium and intel', choices=['all', 'aosp', 'chromium'])
    parser.add_argument('--patch', dest='patch', help='patch', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    parser.add_argument('--build-skip-mk', dest='build_skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--disable-2nd-arch', dest='disable_2nd_arch', help='disable 2nd arch, only effective for baytrail', action='store_true')
    parser.add_argument('--burn-image', dest='burn_image', help='burn live image')
    parser.add_argument('--backup', dest='backup', help='backup output', action='store_true')
    parser.add_argument('--start-emu', dest='start_emu', help='start the emulator. Copy http://ubuntu-ygu5-02.sh.intel.com/aosp-stable/sdcard.img to dir_root and rename it as sdcard-<arch>.img', action='store_true')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'all'], default='x86_64')
    parser.add_argument('--target-device', dest='target_device', help='target device', choices=['baytrail', 'generic', 'all'], default='baytrail')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=['webview', 'system', 'all'], default='system')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_chromium, dir_out, target_archs, target_devices, target_modules, chromium_version

    dir_root = os.path.abspath(os.getcwd())
    dir_chromium = dir_root + '/external/chromium_org'
    dir_out = dir_root + '/out'

    if args.target_arch == 'all':
        target_archs = ['x86_64', 'x86']
    else:
        target_archs = args.target_arch.split(',')

    if args.target_device == 'all':
        target_devices = ['baytrail', 'generic']
    else:
        target_devices = args.target_device.split(',')

    if args.target_module == 'all':
        target_modules = ['system']
    else:
        target_modules = args.target_module.split(',')

    if OS.path.exists(dir_chromium + '/src'):
        chromium_version = 'cr36'
    else:
        chromium_version = 'cr30'

    OS.chdir(dir_root)


def init():
    if not args.init:
        return()

    execute('curl http://android.intel.com/repo >./repo')
    execute('chmod +x ./repo')
    execute('./repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/private/topic/aosp_stable/master')
    patch(patches_init, force=True)
    execute('./repo sync -c -j16')
    execute('./repo start x64 --all')

    upstream_chromium = 'external/chromium_org/src'
    if not OS.path.exists(upstream_chromium):
        info('Please put upstream Chromium under ' + upstream_chromium)


def sync():
    if not args.sync:
        return()

    if args.sync == 'all' or args.sync == 'aosp':
        info('Syncing aosp...')
        _sync_repo(dir_root, './repo sync -c -j16')

    if args.sync == 'all' or args.sync == 'chromium':
        info('Syncing chromium...')
        _sync_repo(dir_chromium, 'GYP_DEFINES="OS=android werror= disable_nacl=1 enable_svg=0" gclient sync -f -n -j16')


def patch(patches, force=False):
    if not args.patch and not force:
        return

    for dir_repo in patches:
        for patch in patches[dir_repo]:
            path_patch = dir_script + '/patches/' + patch
            if _patch_applied(dir_repo, path_patch):
                info('Patch ' + patch + ' was applied before, so is just skipped here')
            else:
                cmd = 'git am ' + path_patch
                backup_dir(dir_repo)
                result = execute(cmd, show_progress=True)
                restore_dir()
                if result[0]:
                    error('Fail to apply patch ' + patch, error_code=result[0])


def build():
    if not args.build:
        return

    _patch_cond(args.disable_2nd_arch, patches_disable_2nd_arch)

    for arch, device, module in [(arch, device, module) for arch in target_archs for device in target_devices for module in target_modules]:
        #if chromium_version == 'cr36' and arch == 'x86_64' and device == 'baytrail' and module == 'system':
        #    _ensure_nonexist('external/chromium-libpac/Android.mk')
        #    _ensure_nonexist('external/v8/Android.mk')
        #else:
        #    _ensure_exist('external/chromium-libpac/Android.mk')
        #    _ensure_exist('external/v8/Android.mk')

        _patch_cond(arch == 'x86_64' and device == 'baytrail', patches_disable_libpac)

        combo = _get_combo(arch, device)
        if not args.build_skip_mk:
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86'
            if arch == 'x86_64':
                cmd += ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86_64'
            execute(cmd, interactive=True)

        if module == 'system':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && make'
        elif module == 'webview':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && mmma frameworks/webview'

        if args.build_showcommands:
            cmd += ' showcommands'
        cmd += ' -j16 2>&1 |tee log.txt'
        result = execute(cmd, interactive=True)
        if result[0]:
            error('Failed to build %s %s %s' % (arch, device, module))


def backup():
    if not args.backup:
        return

    for arch, device, module in [(arch, device, module) for arch in target_archs for device in target_devices for module in target_modules]:
        _backup_one(arch, device, module)


def burn_image():
    if not args.burn_image:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices) > 1 or target_devices[0] != 'baytrail':
        error('Only baytrail can burn the image')

    arch = target_archs[0]
    device = target_devices[0]
    img = dir_out + '/target/product/' + _get_product(arch, device) + '/live.img'
    if not os.path.exists(img):
        error('Could not find the live image to burn')

    sys.stdout.write('Are you sure to burn live image to ' + args.burn_image + '? [yes/no]: ')
    choice = raw_input().lower()
    if choice not in ['yes', 'y']:
        return

    execute('sudo dd if=' + img + ' of=' + args.burn_image + ' && sync', interactive=True)


def start_emu():
    if not args.start_emu:
        return

    for arch in target_archs:
        combo = _get_combo(arch, 'generic')
        cmd = '. build/envsetup.sh && lunch ' + combo + ' && emulator -sdcard /workspace/gytemp/sdcard-' + arch + '.img'
        execute(cmd, interactive=True)


def _sync_repo(dir, cmd):
    backup_dir(dir)
    result = execute(cmd, interactive=True)
    if result[0]:
        error('Failed to sync ' + dir)
    restore_dir()


def _get_combo(arch, device):
    combo_prefix = 'aosp_'
    combo_suffix = '-eng'

    if device == 'generic':
        combo = combo_prefix + arch + combo_suffix
    elif device == 'baytrail':
        if arch == 'x86_64':
            combo = combo_prefix + device + '_64' + combo_suffix
        elif arch == 'x86':
            combo = combo_prefix + device + combo_suffix

    return combo


def _get_product(arch, device):
    if device == 'generic':
        product = device + '_' + arch
    elif device == 'baytrail':
        if arch == 'x86_64':
            product = device + '_64'
        elif arch == 'x86':
            product = device

    return product


def _backup_one(arch, device, module):
    if arch == 'x86_64':
        libs = ['lib64', 'lib']
    elif arch == 'x86':
        libs = ['lib']

    product = _get_product(arch, device)

    backup_files = [
        'target/product/' + product + '/system/framework/webviewchromium.jar',
        'target/product/' + product + '/system/framework/webview/paks/*.pak',
    ]

    for lib in libs:
        backup_files.append('target/product/' + product + '/system/' + lib + '/libwebviewchromium_plat_support.so')
        backup_files.append('target/product/' + product + '/system/' + lib + '/libwebviewchromium.so')
        # binary with symbol is just too big, disable them temporarily.
        #backup_files.append('target/product/' + product + '/symbols/system/' + lib + '/libwebviewchromium_plat_support.so')
        #backup_files.append('target/product/' + product + '/symbols/system/' + lib + '/libwebviewchromium.so')

    if module == 'system':
        if device == 'baytrail':
            backup_files += [
                'target/product/' + product + '/live.img'
            ]
        elif device == 'generic':
            # TODO: Add emulator files
            backup_files += [
                'host/linux-x86/bin/emulator*'
            ]

    time = get_datetime()
    name = time + '-' + arch + '-' + device + '-' + module + '-' + chromium_version
    dir_backup_one = dir_backup + '/' + name
    if not OS.path.exists(dir_backup_one):
        OS.makedirs(dir_backup_one)
    backup_dir(dir_backup_one)
    for backup_file in backup_files:
        dir_backup_relative = os.path.split(backup_file)[0]
        if not OS.path.exists(dir_backup_relative):
            OS.makedirs(dir_backup_relative)
        execute('cp ' + dir_out + '/' + backup_file + ' ' + dir_backup_relative)
    restore_dir()

    backup_dir(dir_backup)
    execute('tar zcf ' + name + '.tar.gz ' + name)
    restore_dir()


def _ensure_exist(file):
    if not OS.path.exists(file):
        execute('mv -f %s.bk %s' % (file, file))


def _ensure_nonexist(file):
    if OS.path.exists(file):
        execute('mv -f %s %s.bk' % (file, file))


# repo: repo path
# path_patch: Full path of patch
# count: Recent commit count to check
def _patch_applied(dir_repo, path_patch, count=30):
    file = open(path_patch)
    lines = file.readlines()
    file.close()

    pattern = re.compile('Subject: \[PATCH.*\] (.*)')
    match = pattern.search(lines[3])
    title = match.group(1)
    backup_dir(dir_repo)
    result = execute('git show -s --pretty="format:%s" --max-count=' + str(count) + ' |grep "%s"' % title, show_command=False)
    restore_dir()
    if result[0]:
        return False
    else:
        return True


def _patch_cond(cond_true, patches):
    if cond_true:
        patch(patches, force=True)
    else:
        _patch_remove(patches)


def _patch_remove(patches):
    dir_repo = patches.keys()[0]
    path_patch = dir_script + '/patches/' + patches.values()[0][0]

    if not _patch_applied(dir_repo, path_patch):
        return

    if not _patch_applied(dir_repo, path_patch, count=1):
        error('Can not revert the patch to enable 2nd arch')

    backup_dir(dir_repo)
    execute('git reset --hard HEAD^')
    restore_dir()


if __name__ == "__main__":
    handle_option()
    setup()
    init()
    sync()
    patch(patches_build)
    build()
    backup()
    burn_image()
    start_emu()
