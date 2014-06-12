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
target_devices_type = []
target_modules = []
devices = []
devices_name = []
devices_type = []
chromium_version = ''
ip = '192.168.42.1'
timestamp = ''
use_upstream_chromium = False

patches_init = {
    '.repo/manifests': ['0001-Replace-webview-and-chromium_org.patch'],
}
patches_init2 = {
    'manifests': ['0001-Replace-webview-and-chromium_org.patch'],
}

patches_build = {}

patches_build_common = {
    # Emulator
    'build/core': ['0001-Emulator-Remove-opengl-from-blacklist-to-enable-gpu.patch'],
    'device/generic/goldfish': ['0001-Emulator-Make-the-size-of-cb_handle_t-same-for-32-64.patch'],
    'frameworks/base': ['0001-Emulator-Enable-HWUI.patch'],
}

patches_build_upstream_chromium = {
    'frameworks/webview': ['0001-Change-drawGLFunctor-to-64-bit.patch'],
    'external/chromium-libpac': ['0001-libpac-Change-v8-path-and-v8-tools-module-name.patch'],
}

patches_build_aosp_chromium = {
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
  python %(prog)s --target-device generic --backup --backup-skip-server --time-fixed
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
    parser.add_argument('--file-image', dest='file_image', help='image tgz file')
    parser.add_argument('--backup', dest='backup', help='backup output to both local and samba server', action='store_true')
    parser.add_argument('--backup-skip-server', dest='backup_skip_server', help='only local backup', action='store_true')
    parser.add_argument('--start-emu', dest='start_emu', help='start the emulator. Copy http://ubuntu-ygu5-02.sh.intel.com/aosp-stable/sdcard.img to dir_root and rename it as sdcard-<arch>.img', action='store_true')
    parser.add_argument('--dir-emu', dest='dir_emu', help='emulator dir')
    parser.add_argument('--analyze', dest='analyze', help='analyze tombstone or ANR file')
    parser.add_argument('--push', dest='push', help='push updates to system', action='store_true')
    parser.add_argument('--remove-out', dest='remove_out', help='remove out dir before build', action='store_true')
    parser.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
    parser.add_argument('--hack-app-process', dest='hack_app_process', help='hack app_process', action='store_true')
    parser.add_argument('--time-fixed', dest='time_fixed', help='fix the time for test sake. We may run multiple tests and results are in same dir', action='store_true')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'all'], default='x86_64')
    parser.add_argument('--target-device-type', dest='target_device_type', help='target device', choices=['baytrail', 'generic', 'all'], default='baytrail')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=['libwebviewchromium', 'webview', 'browser', 'system', 'all'], default='system')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_chromium, dir_out, target_archs, target_devices_type, target_modules, chromium_version, devices, devices_name, devices_type, timestamp, use_upstream_chromium, patches_build

    if args.time_fixed:
        timestamp = get_datetime(format='%Y%m%d')
    else:
        timestamp = get_datetime()

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

    if args.target_device_type == 'all':
        target_devices_type = ['baytrail', 'generic']
    else:
        target_devices_type = args.target_device_type.split(',')

    if args.target_module == 'all':
        target_modules = ['system']
    else:
        target_modules = args.target_module.split(',')

    if os.path.exists(dir_chromium + '/src'):
        chromium_version = 'cr36'
    else:
        chromium_version = 'cr30'

    (devices, devices_name, devices_type) = setup_device()

    os.chdir(dir_root)

    if os.path.exists('external/chromium_org/src'):
        use_upstream_chromium = True

    if use_upstream_chromium:
        patches_build = dict(patches_build_common, **patches_build_upstream_chromium)
    else:
        patches_build = dict(patches_build_common, **patches_build_aosp_chromium)


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

    if (args.sync == 'all' or args.sync == 'chromium') and os.path.exists(dir_chromium + '/src'):
        info('Syncing chromium...')
        _sync_repo(dir_chromium, 'GYP_DEFINES="OS=android werror= disable_nacl=1 enable_svg=0" gclient sync -f -n -j16')


def patch(patches, force=False):
    if not args.patch and not force:
        return

    for dir_repo in patches:
        if not os.path.exists(dir_repo):
            continue

        for patch in patches[dir_repo]:
            path_patch = dir_script + '/patches/' + patch
            if _patch_applied(dir_repo, path_patch):
                info('Patch ' + patch + ' was applied before, so is just skipped here')
            else:
                backup_dir(dir_repo)
                cmd = 'git am ' + path_patch
                result = execute(cmd, show_progress=True)
                restore_dir()
                if result[0]:
                    error('Fail to apply patch ' + patch, error_code=result[0])


def build():
    if not args.build:
        return

    if args.remove_out:
        execute('rm -rf out')

    for arch, device_type, module in [(arch, device_type, module) for arch in target_archs for device_type in target_devices_type for module in target_modules]:
        combo = _get_combo(arch, device_type)
        if not args.build_skip_mk and os.path.exists(dir_root + '/external/chromium_org/src'):
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86'
            if arch == 'x86_64':
                cmd += ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86_64'
            cmd = bashify(cmd)
            execute(cmd, interactive=True)

        if module == 'system':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && make dist'
        elif module == 'browser' or module == 'webview' or module == 'libwebviewchromium':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && '
            if args.build_no_dep:
                cmd += 'mmm '
            else:
                cmd += 'mmma '

            if module == 'browser':
                cmd += 'packages/apps/Browser'
            elif module == 'webview':
                cmd += 'frameworks/webview'
            elif module == 'libwebviewchromium':
                cmd += 'external/chromium_org'

        if args.build_showcommands:
            cmd += ' showcommands'
        cmd += ' -j16 2>&1 |tee log.txt'
        cmd = bashify(cmd)
        result = execute(cmd, interactive=True)
        if result[0]:
            error('Failed to build %s %s %s' % (arch, device_type, module))

        if module == 'system' and device_type == 'generic':
            cmd = bashify('. build/envsetup.sh && lunch ' + combo + ' && external/qemu/android-rebuild.sh')
            result = execute(cmd, interactive=True)
            if result[0]:
                error('Failed to build %s emulator' % arch)


def backup():
    if not args.backup:
        return

    for arch, device_type, module in [(arch, device_type, module) for arch in target_archs for device_type in target_devices_type for module in target_modules]:
        _backup_one(arch, device_type, module)


def burn_image():
    if not args.burn_image:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail can burn the image')

    connect_device()

    arch = target_archs[0]
    device_type = target_devices_type[0]
    img = dir_out + '/target/product/' + get_product(arch, device_type) + '/live.img'
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

    connect_device()

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail can burn the image')

    arch = target_archs[0]
    device_type = target_devices_type[0]
    path_fastboot = dir_linux + '/fastboot'

    if args.file_image:
        file_image = args.file_image
    else:
        file_image = 'out/dist/aosp_%s-om-factory.tgz' % get_product(arch, device_type)

    dir_extract = '/tmp/' + get_datetime()
    execute('mkdir ' + dir_extract)
    execute('tar xvf ' + file_image + ' -C ' + dir_extract, interactive=True)
    backup_dir(dir_extract)

    # Hack flash-all.sh to skip sleep and use our own fastboot
    for line in fileinput.input('flash-all.sh', inplace=1):
        if re.search('sleep', line):
            line = line.replace('sleep', '#sleep')
        elif re.match('fastboot', line):
            line = dir_linux + '/' + line
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()

    # Hack gpt.ini for fast userdata erasion
    file_gpt = 'aosp_%s-OM-gpt.ini' % get_product(arch, device_type)
    for line in fileinput.input(file_gpt, inplace=1):
        if re.search('len = -1', line):
            line = line.replace('-1', '2000')
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()

    # This command would not return so we have to use timeout here
    execute('timeout 5s ' + adb(cmd='reboot bootloader'))
    sleep_sec = 3
    for i in range(0, 60):
        if not device_connected(mode='bootloader'):
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            continue
        else:
            break

    execute('./flash-all.sh -t ' + ip, interactive=True, dryrun=False)
    restore_dir()
    execute('rm -rf ' + dir_extract)

    # This command would not return so we have to use timeout here
    cmd = 'timeout 10s %s -t %s reboot' % (path_fastboot, ip)
    execute(cmd)

    # Wait until system is up
    while not device_connected():
        info('Sleeping %s seconds' % str(sleep_sec))
        time.sleep(sleep_sec)
        connect_device()

    # It will take about 45s to boot to GUI
    info('Sleeping 60 seconds until system fully boots up..')
    time.sleep(60)

    # After system boots up, it will show guide screen and never lock or turn off screen.
    set_screen_lock_none()


def start_emu():
    if not args.start_emu:
        return

    for arch in target_archs:
        product = get_product(arch, 'generic')
        if args.dir_emu:
            dir_backup = args.dir_emu
        else:
            result = execute('ls -t -d --group-directories-first backup/*generic*', return_output=True)
            dir_backup = dir_root + '/' + result[1].split('\n')[0]
        backup_dir(dir_backup)

        if not os.path.exists(dir_root + '/sdcard-%s.img' % arch):
            error('Please put sdcard.img into ' + dir_root)

        if not os.path.exists('system-images/aosp_%(arch)s/userdata-qemu.img' % {'arch': arch}):
            execute('cp system-images/aosp_%(arch)s/userdata.img system-images/aosp_%(arch)s/userdata-qemu.img' % {'arch': arch})

        if arch == 'x86_64':
            gpu_type = 'on'
            file_emu = 'emulator64-x86'
        else:
            gpu_type = 'off'
            file_emu = 'emulator-x86'

        cmd = '''
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:%(dir_backup)s/emulator-linux/lib \
%(dir_backup)s/emulator-linux/%(file_emu)s -verbose -show-kernel -no-snapshot -gpu %(gpu_type)s -memory 512 \
-skin HVGA \
-skindir %(dir_backup)s/platforms/skins \
-kernel %(dir_backup)s/system-images/aosp_%(arch)s/kernel-qemu \
-ramdisk %(dir_backup)s/system-images/aosp_%(arch)s/ramdisk.img \
-sysdir %(dir_backup)s/system-images/aosp_%(arch)s \
-system %(dir_backup)s/system-images/aosp_%(arch)s/system.img \
-datadir %(dir_backup)s/system-images/aosp_%(arch)s \
-data %(dir_backup)s/system-images/aosp_%(arch)s/userdata-qemu.img \
-cache %(dir_backup)s/system-images/aosp_%(arch)s/cache.img \
-initdata %(dir_backup)s/system-images/aosp_%(arch)s/userdata.img \
-sdcard %(dir_root)s/sdcard-%(arch)s.img \
''' % {'dir_root': dir_root, 'dir_backup': dir_backup, 'product': product, 'arch': arch, 'gpu_type': gpu_type, 'file_emu': file_emu}

        execute(cmd, interactive=True)
        restore_dir()


def analyze():
    if not args.analyze:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    arch = target_archs[0]
    connect_device()
    analyze_issue(dir_aosp=dir_root, arch=arch, type=args.analyze)


def push():
    if not args.push:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    arch = target_archs[0]
    device_type = target_devices_type[0]

    connect_device()

    if args.target_module == 'all':
        modules = ['libwebviewchromium', 'webview']
    else:
        modules = args.target_module.split(',')

    cmd = adb(cmd='root') + ' && ' + adb(cmd='remount') + ' && ' + adb(cmd='push out/target/product/%s' % get_product(arch, device_type))

    for module in modules:
        if module == 'browser':
            cmd += '/system/app/Browser.apk /system/app'
        if module == 'libwebviewchromium':
            cmd += '/obj/lib/libwebviewchromium.so /system/lib64'
        elif module == 'webview':
            cmd += '/system/framework/webviewchromium.jar /system/framework'

    result = execute(cmd)
    if result[0]:
        error('Failed to push binaries to system')

    if len(modules) == 1 and modules[0] == 'browser':
        pass
    elif len(modules) > 0:
        cmd = adb(cmd='shell stop') + ' && ' + adb(cmd='shell start')
        execute(cmd)


def hack_app_process():
    if not args.hack_app_process:
        return

    for device in devices:
        connect_device(device)
        if not execute_adb_shell("test -d /system/lib64", device=device):
            continue

        for file in ['am', 'pm']:
            cmd = adb('pull /system/bin/' + file + ' /tmp/' + file)
            execute(cmd)
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount', device=device) + ' && ' + adb('push /tmp/' + file + ' /system/bin/')
                execute(cmd)


def _sync_repo(dir, cmd):
    backup_dir(dir)
    result = execute(cmd, interactive=True)
    if result[0]:
        error('Failed to sync ' + dir)
    restore_dir()


def _get_combo(arch, device_type):
    combo_prefix = 'aosp_'
    combo_suffix = '-eng'

    if device_type == 'generic':
        combo = combo_prefix + arch + combo_suffix
    elif device_type == 'baytrail':
        if arch == 'x86_64':
            combo = combo_prefix + device_type + '_64p' + combo_suffix
        elif arch == 'x86':
            combo = combo_prefix + device_type + combo_suffix

    return combo


# All valid combination:
# 1. x86_64, baytrail, webview
# 2. x86_64, baytrail, system
# 3. x86, baytrail, system
# 4. x86_64, generic, system
# 5. x86, generic, system
# (x86_64, generic, webview) is same as 1
# (x86, baytrail, webview) is included in 1
# (x86, generic, webview) is included in 1

def _backup_one(arch, device_type, module):
    product = get_product(arch, device_type)

    if module == 'webview':
        if arch == 'x86_64':
            libs = ['lib64', 'lib']
        elif arch == 'x86':
            libs = ['lib']

        backup_files = {
            'out/target/product/' + product + '/system/framework': 'out/target/product/' + product + '/system/framework/webviewchromium.jar',
            'out/target/product/' + product + '/system/framework/webview': 'out/target/product/' + product + '/system/framework/webview/paks',
        }

        for lib in libs:
            backup_files['out/target/product/' + product + '/system/' + lib] = [
                'out/target/product/' + product + '/system/' + lib + '/libwebviewchromium_plat_support.so',
                'out/target/product/' + product + '/system/' + lib + '/libwebviewchromium.so'
            ]

    else:  # module == 'system'
        if device_type == 'baytrail':
            backup_files = {
                '.': [
                    'out/dist/aosp_%s-om-factory.tgz' % get_product(arch, device_type),
                ],
            }
        elif device_type == 'generic':
            backup_files = {
                'platforms': 'development/tools/emulator/skins',
                'emulator-linux': 'external/qemu/objs/*',
                'system-images/aosp_%s/system' % arch: 'out/target/product/generic_%s/system/*' % arch,
                'system-images/aosp_%s' % arch: [
                    'out/target/product/generic_%s/cache.img' % arch,
                    'out/target/product/generic_%s/userdata.img' % arch,
                    'out/target/product/generic_%s/ramdisk.img' % arch,
                    'out/target/product/generic_%s/system.img' % arch,
                    'prebuilts/qemu-kernel/%s/kernel-qemu' % arch,
                ],
            }

    name = timestamp + '-' + arch + '-' + device_type + '-' + module + '-' + chromium_version
    dir_backup_one = dir_backup + '/' + name
    if not os.path.exists(dir_backup_one):
        os.makedirs(dir_backup_one)
    backup_dir(dir_backup_one)
    info('Begin to backup to ' + dir_backup_one)
    for dir_dest in backup_files:
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)

        if isinstance(backup_files[dir_dest], str):
            files = [backup_files[dir_dest]]
        else:
            files = backup_files[dir_dest]

        for file in files:
            execute('cp -rf ' + dir_root + '/' + file + ' ' + dir_dest)
    restore_dir()

    if not args.backup_skip_server:
        backup_dir(dir_backup)
        name_tar = name + '-' + host_name + '.tar.gz'
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
    result = execute('git show -s --pretty="format:%s" --max-count=' + str(count) + ' |grep "%s"' % title.replace('"', '\\"'), show_command=False)
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
    flash_image()
    start_emu()
    analyze()
    push()
    hack_app_process()
