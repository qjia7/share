#!/usr/bin/env python

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import fileinput

dir_root = ''
dir_chromium = ''
dir_out = ''
dir_script = sys.path[0]
dir_backup = 'backup'
target_archs = []
target_devices = []
target_modules = []
devices = []
devices_name = []
chromium_version = ''
ip = '192.168.42.1'

patches_init = {
    '.repo/manifests': ['0001-Replace-webview-and-chromium_org.patch'],
}
patches_init2 = {
    'manifests': ['0001-Replace-webview-and-chromium_org.patch'],
}

patches_baytrail_disable_2nd_arch = {
    'device/intel/baytrail_64': ['0002-baytrail_64-Disable-2nd-arch.patch'],
}

patches_generic_disable_2nd_arch = {
    'build': ['0001-generic_x86_64-Disable-2nd-arch.patch']
}

patches_build = {
    'frameworks/webview': ['0001-Change-drawGLFunctor-to-64-bit.patch'],
    'device/intel/baytrail': ['0001-Disable-prebuilding-webviewchromium.patch'],
    'packages/apps/Browser': [
        '0001-Make-browser-preference-fragment-valid.patch',
        '0002-Fix-a-crash-when-creating-an-incognito-tab-on-tablet.patch',
    ],
}


def handle_option():
    global args

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s all -b --disable-2nd-arch --patch
  python %(prog)s -b --build-skip-mk --disable-2nd-arch
  python %(prog)s -b --disable-2nd-arch  --build-skip-mk --target-module libwebviewchromium --build-no-dep
''')

    parser.add_argument('--init', dest='init', help='init', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync code for android, chromium and intel', choices=['all', 'aosp', 'chromium'])
    parser.add_argument('--patch', dest='patch', help='patch', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    parser.add_argument('--build-skip-mk', dest='build_skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--build-no-dep', dest='build_no_dep', help='use mmma or mmm', action='store_true')
    parser.add_argument('--disable-2nd-arch', dest='disable_2nd_arch', help='disable 2nd arch, only effective for baytrail', action='store_true')
    parser.add_argument('--burn-image', dest='burn_image', help='burn live image')
    parser.add_argument('--flash-image', dest='flash_image', help='flash the boot and system', action='store_true')
    parser.add_argument('--backup', dest='backup', help='backup output to both local and samba server', action='store_true')
    parser.add_argument('--start-emu', dest='start_emu', help='start the emulator. Copy http://ubuntu-ygu5-02.sh.intel.com/aosp-stable/sdcard.img to dir_root and rename it as sdcard-<arch>.img', action='store_true')
    parser.add_argument('--analyze', dest='analyze', help='analyze tombstone or trace file for libwebviewchromium.so')
    parser.add_argument('--push', dest='push', help='push updates to system', action='store_true')
    parser.add_argument('--remove-out', dest='remove_out', help='remove out dir before build', action='store_true')
    parser.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
    parser.add_argument('--hack-app-process', dest='hack_app_process', help='hack app_process', action='store_true')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'all'], default='x86_64')
    parser.add_argument('--target-device', dest='target_device', help='target device', choices=['baytrail', 'generic', 'all'], default='baytrail')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=['webview', 'libwebviewchromium', 'system', 'all'], default='system')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_chromium, dir_out, target_archs, target_devices, target_modules, chromium_version, devices, devices_name

    # Ensure device is connected if available
    connect_device()

    # Set path
    path = os.getenv('PATH')
    path += ':/usr/bin:/usr/sbin'
    if args.extra_path:
        path += ':' + args.extra_path
    setenv('PATH', path)
    for cmd in ['adb', 'git', 'gclient']:
        result = execute('which ' + cmd, show_command=False)
        if result[0]:
            error('Could not find ' + cmd + ', and you may use --extra-path to designate it')

    # Set proxy
    if os.path.exists('/usr/sbin/privoxy'):
        http_proxy = '127.0.0.1:8118'
        https_proxy = '127.0.0.1:8118'
    else:
        http_proxy = 'proxy-shz.intel.com:911'
        https_proxy = 'proxy-shz.intel.com:911'
    setenv('http_proxy', http_proxy)
    setenv('https_proxy', https_proxy)
    setenv('no_proxy', 'intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,127.0.0.0/8,134.134.0.0/16,172.16.0.0/20,192.168.42.0/16')

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

    if os.path.exists(dir_chromium + '/src'):
        chromium_version = 'cr36'
    else:
        chromium_version = 'cr30'

    (devices, devices_name) = setup_device()

    os.chdir(dir_root)


def init():
    if not args.init:
        return()

    execute('curl --noproxy intel.com http://android.intel.com/repo >./repo')
    execute('chmod +x ./repo')
    execute('./repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/private/topic/aosp_stable/master')
    patch(patches_init, force=True)
    execute('./repo sync -c -j16')
    patch(patches_init2, force=True)
    execute('./repo start x64 --all')

    upstream_chromium = 'external/chromium_org/src'
    if not os.path.exists(upstream_chromium):
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

    if args.remove_out:
        execute('rm -rf out')

    for arch, device, module in [(arch, device, module) for arch in target_archs for device in target_devices for module in target_modules]:
        _patch_cond(args.disable_2nd_arch and device == 'baytrail', patches_baytrail_disable_2nd_arch)
        _patch_cond(args.disable_2nd_arch and device == 'generic', patches_generic_disable_2nd_arch)

        combo = _get_combo(arch, device)
        if not args.build_skip_mk:
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86'
            if arch == 'x86_64':
                cmd += ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86_64'
            cmd = bashify(cmd)
            execute(cmd, interactive=True)

        if module == 'system':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && make'
        elif module == 'webview' or module == 'libwebviewchromium':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && '
            if args.build_no_dep:
                cmd += 'mmm '
            else:
                cmd += 'mmma '

            if module == 'webview':
                cmd += 'frameworks/webview'
            elif module == 'libwebviewchromium':
                cmd += 'external/chromium_org'

        if args.build_showcommands:
            cmd += ' showcommands'
        cmd += ' -j16 2>&1 |tee log.txt'
        cmd = bashify(cmd)
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


def flash_image():
    if not args.flash_image:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices) > 1 or target_devices[0] != 'baytrail':
        error('Only baytrail can burn the image')

    arch = target_archs[0]
    device = target_devices[0]

    # This command would not return so we have to use timeout here
    execute('timeout 5s adb reboot bootloader')
    sleep_sec = 3
    for i in range(0, 60):
        if not _device_connected(cmd='fastboot devices'):
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            continue

        android_product_out = dir_out + '/target/product/' + _get_product(arch, device)
        cmd = 'fastboot -t %s oem unlock' % ip
        execute(cmd)
        cmd = 'ANDROID_PRODUCT_OUT=%s fastboot -t %s flashall' % (android_product_out, ip)
        execute(cmd, interactive=True)
        # This command would not return so we have to use timeout here
        cmd = 'timeout 10s fastboot -t %s reboot' % ip
        execute(cmd)

        # Wait until system is up
        while not _device_connected():
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            connect_device()

        break


def start_emu():
    if not args.start_emu:
        return

    for arch in target_archs:
        combo = _get_combo(arch, 'generic')
        #backup_dir('/workspace/service/www/aosp-stable/temp/20140414-x86_64-generic-system-cr30/out')
        #cmd = 'host/linux-x86/bin/emulator64-x86 -kernel ../prebuilts/qemu-kernel/x86_64/kernel-qemu -sdcard /workspace/service/www/aosp-stable/sdcard.img -gpu off -system target/product/generic_x86_64/system.img -ramdisk target/product/generic_x86_64/ramdisk.img -skin HVGA -skindir ../sdk/emulator/skins -sysdir target/product/generic_x86_64 -datadir target/product/generic_x86_64 -data target/product/generic_x86_64/userdata-qemu.img -initdata target/product/generic_x86_64/userdata.img -memory 256 -verbose'

        cmd = bashify('. build/envsetup.sh && lunch ' + combo + ' && emulator -sdcard sdcard-' + arch + '.img')
        execute(cmd, interactive=True)
        #restore_dir()


def analyze():
    if not args.analyze:
        return

    count_line_max = 1000
    count_valid_max = 30

    execute('adb connect ' + ip)
    if args.analyze == 'tombstone':
        result = execute('adb shell \ls /data/tombstones', return_output=True)
        files = result[1].split('\n')
        result = execute('adb shell cat /data/tombstones/' + files[-2].strip(), return_output=True)
        lines = result[1].split('\n')
    elif args.analyze == 'anr':
        result = execute('adb shell cat /data/anr/traces.txt', return_output=True)
        lines = result[1].split('\n')

    pattern = re.compile('pc (.*)  .*lib(webviewchromium|art|c)')
    count_line = 0
    count_valid = 0
    for line in lines:
        count_line += 1
        if count_line > count_line_max:
            return
        match = pattern.search(line)
        if match:
            print line
            cmd = 'prebuilts/gcc/linux-x86/x86/x86_64-linux-android-4.8/bin/x86_64-linux-android-addr2line -C -e out/target/product/baytrail_64/symbols/system/lib64/lib%s.so -f %s' % (match.group(2), match.group(1))
            result = execute(cmd, return_output=True, show_command=False)
            print result[1]

            count_valid += 1
            if count_valid > count_valid_max:
                return


def push():
    if not args.push:
        return

    if args.target_module == 'all':
        modules = ['libwebviewchromium', 'webview']
    else:
        modules = args.target_module.split(',')

    cmd = 'adb root && adb remount'

    for module in modules:
        if module == 'libwebviewchromium':
            cmd += ' && adb push out/target/product/baytrail_64/obj/lib/libwebviewchromium.so /system/lib64'
        elif module == 'webview':
            cmd += ' && adb push out/target/product/baytrail_64/system/framework/webviewchromium.jar /system/framework'

    if len(modules) > 0:
        cmd += ' && adb shell stop && adb shell start'

    result = execute(cmd)
    if result[0]:
        error('Failed to push binaries to system')


def hack_app_process():
    if not args.hack_app_process:
        return

    for device in devices:
        if not execute_adb("test -d /system/lib64", device=device):
            continue

        for file in ['am', 'pm']:
            execute('adb -s ' + device + ' pull /system/bin/' + file + ' /tmp/' + file)
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                execute('adb -s ' + device + ' root && adb -s ' + device + ' remount && adb -s ' + device + ' push /tmp/' + file + ' /system/bin/')


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


# All valid combination:
# 1. x86_64, baytrail, webview
# 2. x86_64, baytrail, system
# 3. x86, baytrail, system
# 4. x86_64, generic, system
# 5. x86, generic, system
# (x86_64, generic, webview) is same as 1
# (x86, baytrail, webview) is included in 1
# (x86, generic, webview) is included in 1

def _backup_one(arch, device, module):
    product = _get_product(arch, device)

    if module == 'webview':
        if arch == 'x86_64':
            libs = ['lib64', 'lib']
        elif arch == 'x86':
            libs = ['lib']

        backup_files = [
            'out/target/product/' + product + '/system/framework/webviewchromium.jar',
            'out/target/product/' + product + '/system/framework/webview/paks',
        ]

        for lib in libs:
            backup_files.append('out/target/product/' + product + '/system/' + lib + '/libwebviewchromium_plat_support.so')
            backup_files.append('out/target/product/' + product + '/system/' + lib + '/libwebviewchromium.so')
            # binary with symbol is just too big, disable them temporarily.
            #backup_files.append('out/target/product/' + product + '/symbols/system/' + lib + '/libwebviewchromium_plat_support.so')
            #backup_files.append('out/target/product/' + product + '/symbols/system/' + lib + '/libwebviewchromium.so')

    else:  # module == 'system'
        if device == 'baytrail':
            backup_files = [
                'out/target/product/' + product + '/live.img'
            ]

        elif device == 'generic':
            if arch == 'x86_64':
                backup_files = [
                    'out/host/linux-x86/bin/emulator64-x86',
                    'out/host/linux-x86/lib',
                    'out/host/linux-x86/usr/share/pc-bios',
                    'out/target/product/generic_x86_64/system/build.prop',
                    'out/target/product/generic_x86_64/cache.img'
                    'out/target/product/generic_x86_64/userdata.img',
                    'out/target/product/generic_x86_64/userdata-qemu.img',
                    'out/target/product/generic_x86_64/ramdisk.img',
                    'out/target/product/generic_x86_64/system.img',
                    'out/target/product/generic_x86_64/hardware-qemu.ini',
                    'prebuilts/qemu-kernel/x86_64/kernel-qemu',
                    'sdk/emulator/skins',
                ]
            elif arch == 'x86':
                pass

    time = get_datetime()
    name = time + '-' + arch + '-' + device + '-' + module + '-' + chromium_version
    dir_backup_one = dir_backup + '/' + name
    if not os.path.exists(dir_backup_one):
        os.makedirs(dir_backup_one)
    backup_dir(dir_backup_one)
    for backup_file in backup_files:
        dir_backup_relative = os.path.split(backup_file)[0]
        if not os.path.exists(dir_backup_relative):
            os.makedirs(dir_backup_relative)
        execute('cp -rf ' + dir_root + '/' + backup_file + ' ' + dir_backup_relative)
    restore_dir()

    backup_dir(dir_backup)
    name_tar = name + '.tar.gz'
    execute('tar zcf ' + name_tar + ' ' + name)
    backup_smb('//ubuntu-ygu5-02.sh.intel.com/aosp-stable', 'temp', name_tar)
    restore_dir()


def _ensure_exist(file):
    if not os.path.exists(file):
        execute('mv -f %s.bk %s' % (file, file))


def _ensure_nonexist(file):
    if os.path.exists(file):
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


# Check if device is connected in bootloader or system
def _device_connected(ip='192.168.42.1', cmd='adb devices'):
    result = execute(cmd, return_output=True, show_command=False)
    if re.search(ip, result[1]):
        return True
    else:
        return False


if __name__ == "__main__":
    handle_option()
    setup()
    init()
    sync()
    patch(patches_build)
    build()
    backup()
    burn_image()
    flash_image()
    start_emu()
    analyze()
    push()
    hack_app_process()
