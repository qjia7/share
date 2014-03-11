#!/usr/bin/env python

from util import *
import os as OS

dir_root = ''
dir_android = ''
dir_chromium = ''


def handle_option():
    global args

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s master
  python %(prog)s -s android-4.4.2_r1
  python %(prog)s -f all

  python %(prog)s -s android-4.3_r1 -b -f all

''')

    #parser.add_argument('-s', '--sync', dest='sync', help='android or chromium, all for both', choices=['all', 'chromium', 'android'])
    parser.add_argument('--sync-android', dest='sync_android', help='sync android code', action='store_true')
    #parser.add_argument('--sync-chromium', dest='sync_chromium', help='sync chromium code', action='store_true')

    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64'], default='x86_64')

    parser.add_argument('--init', dest='init', help='init', action='store_true')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_android, dir_chromium

    dir_root = os.path.abspath(os.getcwd())
    dir_android = dir_root + '/android'
    dir_chromium = dir_root + "/chromium"

    os.chdir(dir_root)


def hack_manifest():
    backup_dir('android/.repo/manifests')
    execute('rm -f default.xml.bk')
    execute('cp -f default.xml default.xml.bk')
    restore_dir()


def init():
    if not args.init:
        return()

    if not OS.path.exists('chromium'):
        error('Could not find chromium code, please prepare for it first')

    if not OS.path.exists('android'):
        OS.mkdir('android')

    backup_dir('android')
    if host_os == 'Linux' and not has_process('privoxy'):
        execute('sudo privoxy /etc/privoxy/config')
        os.putenv('http_proxy', '127.0.0.1:8118')
        os.putenv('https_proxy', '127.0.0.1:8118')

    cmd = 'repo init -u https://android.googlesource.com/platform/manifest'
    result = execute(cmd, show_progress=True)
    if result[0]:
        error('Failed to repo init for android')

    if host_os == 'Linux':
        execute('sudo killall privoxy')
        os.putenv('http_proxy', '')
        os.putenv('https_proxy', '')
    restore_dir()

    hack_manifest()

    #sync_android(force=True)

    if not OS.path.islink('android/external/chromium_org/src'):
        execute('ln -s ' + dir_chromium + '/src android/external/chromium_org/src')


def sync_android(force=False):
    if not args.sync_android and not force:
        return

    backup_dir('android')
    cmd = 'repo sync -c -j16'
    result = execute(cmd, interactive=True)
    if result[0]:
        error('Failed to sync android')
    restore_dir()


def build():
    if not args.build:
        return

    backup_dir('chromium/src')
    #execute('./android_webview/tools/gyp_webview -Dtarget_arch=' + args.target_arch, show_progress=True)
    restore_dir()

    backup_dir('android')
    execute('. build/envsetup.sh && lunch aosp_' + args.target_arch + '-eng')
    # make -j
    execute('mmm frameworks/webview external/chromium_org -j16')
    restore_dir()




if __name__ == "__main__":
    handle_option()
    setup()
    init()
    build()
