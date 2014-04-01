#!/usr/bin/env python

# Steps to use this script:
# python gmin-master.py --init
# python gmin-master.py --sync --patch --build


import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import os as OS

dir_root = ''
dir_android = ''
dir_chromium = ''
dir_intel = ''
dir_script = sys.path[0]
target_arch = ''
target_module = ''

patches_init = {
    'intel/.repo/manifests': ['0001-Remove-webview-and-chromium_org.patch'],
}

patches_build = {
    'intel/device/intel/baytrail_64': ['0001-baytrail_64-Disable-2nd-arch.patch'],
    'intel/build': [
        '0001-build-Make-v8-and-icu-host-tool-64-bit.patch',
        '0002-build-Remove-webview-and-chromium_org-from-blacklist.patch'
    ],
    'chromium/src/third_party/icu': ['0001-third_party-icu-x64-support.patch'],
}


def handle_option():
    global args, target_arch

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s master


''')

    parser.add_argument('--init', dest='init', help='init', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync code for android, chromium and intel', choices=['all', 'android', 'chromium', 'intel'])
    parser.add_argument('--patch', dest='patch', help='patch', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    parser.add_argument('--build_skip_mk', dest='build_skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--burn-image', dest='burn_image', help='burn live image')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64'], default='x86_64')
    parser.add_argument('--target-module', dest='target_module', help='target arch', choices=['webview', 'system', 'emulator'], default='webview')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_android, dir_chromium, dir_intel, target_arch, target_module

    dir_root = os.path.abspath(os.getcwd())
    dir_android = dir_root + '/android'
    dir_chromium = dir_root + '/chromium'
    dir_intel = dir_root + '/intel'

    if not OS.path.exists(dir_android):
        error('Please prepare for ' + dir_android)

    if not OS.path.exists(dir_chromium):
        error('Please prepare for ' + dir_chromium)

    if not OS.path.exists(dir_intel):
        error('Please prepare for ' + dir_intel)

    os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 enable_svg=0')

    target_arch = args.target_arch
    target_module = args.target_module

    os.chdir(dir_root)


def init():
    if not args.init:
        return()

    backup_dir(dir_android)
    execute('./repo start x64 --all')
    restore_dir()

    backup_dir(dir_intel)
    execute('./repo start x64 --all')
    restore_dir()

    patch(patches_init, force=True)

    intel_webview = 'intel/frameworks/webview'
    execute('rm -rf ' + intel_webview)
    if not OS.path.islink(intel_webview):
        execute('ln -s %s/frameworks/webview intel/frameworks' % dir_android)

    intel_chromium_org = 'intel/external/chromium_org'
    execute('rm -rf ' + intel_chromium_org)
    if not OS.path.islink(intel_chromium_org):
        execute('ln -s %s/external/chromium_org intel/external' % dir_android)

    android_chromium_org = 'android/external/chromium_org/src'
    execute('rm -rf ' + android_chromium_org)
    if not OS.path.islink(android_chromium_org):
        execute('ln -s %s/src android/external/chromium_org' % dir_chromium)


def sync():
    if not args.sync:
        return()

    if args.sync == 'all' or args.sync == 'android':
        info('Syncing ' + dir_android)
        _sync_repo(dir_android, './repo sync -c -j16')

    if args.sync == 'all' or args.sync == 'chromium':
        info('Syncing ' + dir_chromium)
        _sync_repo(dir_chromium, 'gclient sync -f -n -j16')

    if args.sync == 'all' or args.sync == 'intel':
        info('Syncing ' + dir_intel)
        _sync_repo(dir_intel, './repo sync -c -j16')


def patch(patches, force=False):
    if not args.patch and not force:
        return

    for repo in patches:
        backup_dir(repo)
        for patch in patches[repo]:
            patch_path = dir_script + '/patches/' + patch
            file = open(patch_path)
            lines = file.readlines()
            file.close()

            pattern = re.compile('Subject: \[PATCH.*\] (.*)')
            match = pattern.search(lines[3])
            title = match.group(1)
            result = execute('git show -s --pretty="format:%s" --max-count=30 |grep "' + title + '"', show_command=False)
            if result[0]:
                cmd = 'git am ' + patch_path
                result = execute(cmd, show_progress=True)
                if result[0]:
                    error('Fail to apply patch ' + patch, error_code=result[0])
            else:
                info('Patch ' + patch + ' was applied before, so is just skipped here')
        restore_dir()


def build():
    if not args.build:
        return

    backup_dir(dir_intel)

    if target_module == 'emulator':
        cmd = '. build/envsetup.sh && lunch aosp_' + target_arch + '-eng && make'
    else:
        if not args.build_skip_mk:
            backup_dir(dir_chromium + '/src')
            execute('./android_webview/tools/gyp_webview linux-' + target_arch, show_progress=True)
            restore_dir()

        if target_arch == 'x86_64':
            combo = 'baytrail_64'
        elif target_arch == 'x86':
            combo = 'baytrail'

        cmd = '. build/envsetup.sh && lunch aosp_' + combo + '-eng && '
        if target_module == 'system':
            cmd += 'make'
        else:
            cmd += 'mmma frameworks/webview'

    if args.build_showcommands:
        cmd += ' showcommands'
    cmd += ' -j16 2>&1 |tee log.txt'
    execute(cmd, interactive=True)

    restore_dir()


def burn_image():
    if not args.burn_image:
        return

    img = 'out/target/product/hsb_64/live.img'
    if not os.path.exists(img):
        error('Could not find the live image to burn')

    sys.stdout.write('Are you sure to burn live image to ' + args.burn_image + '? [yes/no]: ')
    choice = raw_input().lower()
    if choice not in ['yes', 'y']:
        return

    execute('sudo dd if=' + img + ' of=' + args.burn_image + ' && sync', interactive=True)


def _sync_repo(dir, cmd):
    backup_dir(dir)
    result = execute(cmd, interactive=True)
    if result[0]:
        error('Failed to sync ' + dir)
    restore_dir()


if __name__ == "__main__":
    handle_option()
    setup()
    init()
    sync()
    patch(patches_build)
    build()
