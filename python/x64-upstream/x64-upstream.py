#!/usr/bin/env python

# patch apply again

import sys
sys.path.append(sys.path[0] + '/..')
from util import *

import os as OS

dir_root = ''
dir_src = ''
dir_script = sys.path[0]

patches = {
    'src': [
        '0001-Enable-x64-build.patch',
        '0002-Add-general-compile-options-for-Android-x64.patch',
        '0003-jni-fixes-in-base-for-Android-x64.patch',
        '0004-jni-fixes-in-net-for-Android-x64.patch',
        '0005-jni-fixes-in-android_webview-for-Android-x86.patch',
        '0006-jni-fixes-in-content-for-Android-x64.patch',
        '0007-jni-fixes-in-chrome-for-Android-x64.patch',
        '0008-Add-x86_64-ucontext-structure-for-Android-x64.patch',
        '0009-media-64-support.patch',
        '0010-trivial-fixes-to-suppress-warning-and-type-conversio.patch',
        '0011-suppress-warning-error-in-ppapi.patch',
    ],
    'src/third_party/icu': ['0001-third_party-icu-x64-support.patch'],
    'src/v8': [
        '0001-v8-x64-support.patch',
        '0002-walkaround-for-V8_INT64_C.patch'
    ],
    'src/third_party/libvpx': ['0001-fix-the-target-arch-mistake-for-android-x86-x64.patch'],
    'src/third_party/mesa/src': ['0001-disable-log2.patch'],
}


################################################################################
def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to sync, build upstream x64 Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --clean -s --patch -b
''')

    parser.add_argument('--clean', dest='clean', help='clean patches and local changes', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    parser.add_argument('--patch', dest='patch', help='apply patches', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-clean', dest='build_clean', help='do a clean build', action='store_true')

    parser.add_argument('-d', '--dir_root', dest='dir_root', help='set root directory')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, dir_src

    if not args.dir_root:
        dir_root = get_symbolic_link_dir()
    else:
        dir_root = args.dir_root

    dir_src = dir_root + '/src'
    os.chdir(dir_root)


def clean(force=False):
    if not args.clean and not force:
        return

    if not force:
        warning('Clean is very dangerous, your local changes will be lost')
        sys.stdout.write('Are you sure to do the cleanup? [yes/no]: ')
        choice = raw_input().lower()
        if choice not in ['yes', 'y']:
            return

    cmd = 'gclient revert -n'
    execute(cmd, show_progress=True)


def sync(force=False):
    if not args.sync:
        return

    cmd = 'gclient sync -f -n --revision src@459216a04dd39b744a73876b21266b7ad1ecfdf4'
    result = execute(cmd, show_progress=True)
    if result[0]:
        error('sync failed', error_code=result[0])


def patch(force=False):
    if not args.patch and not force:
        return

    for repo in patches:
        backup_dir(repo)
        for patch in patches[repo]:
            cmd = 'git am ' + dir_script + '/patches/' + patch
            result = execute(cmd, show_progress=True)
            if result[0]:
                warning('Fail to apply patch ' + patch, error_code=result[0])
        restore_dir()


def build(force=False):
    if not args.build and not force:
        return

    set_ndk()

    if args.build_clean:
        backup_dir(dir_src)
        command = bashify('. build/android/envsetup.sh --target-arch=x64 && android_gyp -Dwerror=')
        execute(command)
        restore_dir()

    ninja_cmd = 'ninja -j16 -C src/out/Release android_webview_test_apk android_webview_unittests_apk'
    result = execute(ninja_cmd, show_progress=True)
    if result[0]:
        error('Fail to execute command: ' + ninja_cmd, error_code=result[0])




def set_ndk():
    if not OS.path.exists('ndk'):
        error('Please put ndk under ' + get_symbolic_link_dir())

    if OS.path.exists('src/third_party/android_tools/ndk/toolchains/x86_64-4.8'):
        return

    info('Your ndk is not set well, and script will set it up for you')

    if not OS.path.exists('src/third_party/android_tools/ndk_bk'):
        cmd = 'mv src/third_party/android_tools/ndk src/third_party/android_tools/ndk_bk'
    else:
        cmd = 'rm -rf src/third_party/android_tools/ndk'
    execute(cmd, show_command=False)

    backup_dir('src/third_party/android_tools')
    execute('ln -s ../../../ndk ./', show_command=False)
    restore_dir()

    if not OS.path.exists('ndk/android_tools_ndk.gyp'):
        execute('cp ' + dir_script + '/patches/android_tools_ndk.gyp ndk/')

    if not OS.path.exists('ndk/crazy_linker.gyp'):
        execute('cp ' + dir_script + '/patches/crazy_linker.gyp ndk/')

    if not OS.path.exists('ndk/platforms/android-19/arch-x86_64/usr/include/asm/unistd_64.h'):
        execute('cd ndk; git init; git add .; git commit -a -m \"orig\"; git am ../share/python/x64-upstream/patches/ndk-allinone.patch; cd ..;');

if __name__ == '__main__':
    handle_option()
    setup()

    clean()
    sync()
    patch()

    build()
