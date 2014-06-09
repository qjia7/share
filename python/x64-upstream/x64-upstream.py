#!/usr/bin/env python

import fileinput
import multiprocessing
from multiprocessing import Pool
import sys
sys.path.append(sys.path[0] + '/..')
from util import *

chromium_info = ['e9ff69854e96d7e750242651134110c9ad5b7bed', '273751']
CHROMIUM_INFO_INDEX_HASH = 0
CHROMIUM_INFO_INDEX_REV = 1

patches = {
    'src': [
        '0001-Enlarge-kThreadLocalStorageSize-to-satisfy-test.patch',
    ],
}

dir_script = sys.path[0]
dir_root = ''
dir_src = ''
dir_test = ''
time_stamp = ''
test_type = ''
dir_out_test_type = ''
dir_time = ''
target_arch = ''
target_module = ''
report_name = ''
name_file = sys._getframe().f_code.co_filename

cpu_count = str(multiprocessing.cpu_count() * 2)
devices = []
devices_name = []
devices_type = []

test_command_default = [
    'gtest',
    'instrumentation',
    #'linker',
    #'uiautomator',
    #'monkey',
    #'perf'
]

gtest_suite_default = [
    'android_webview_unittests',
    'base_unittests',
    'cc_unittests',
    'components_unittests',
    'content_unittests',
    'gl_tests',
    'gpu_unittests',
    'ipc_tests',
    'media_unittests',
    'net_unittests',
    'sandbox_linux_unittests',
    'sql_unittests',
    'sync_unit_tests',
    'ui_unittests',
    'webkit_compositor_bindings_unittests',
    'webkit_unit_tests',
    'content_gl_tests',
    'breakpad_unittests',  # Need breakpad
    'unit_tests',  # Need breakpad
    # This is temporarily disabled until we analyze most of failures
    #'content_browsertests',  # Need breakpad
]

instrumentation_suite_default = [
    'ContentShellTest',
    'ChromeShellTest',
    'AndroidWebViewTest',
]

test_suite = {}

# (device_type, target_arch): {}
# device_type can be 'baytrail', 'generic'
test_suite_filter = {
    ('all', 'all'): {},
    ('all', 'x86_64'): {},
    ('all', 'x86'): {},
    ('baytrail', 'all'): {
        'base_unittests': [
            # Confirmed the below case is no longer needed to be filtered
            #'ThreadTest.StartWithOptions_StackSize',
        ],
        'media_unittests': [
            # Status: TODO
            'MediaSourcePlayerTest.A_StarvationDuringEOSDecode',
            'MediaSourcePlayerTest.AV_NoPrefetchForFinishedVideoOnAudioStarvation',
            'AudioAndroidOutputTest.StartOutputStreamCallbacks',  # Crash the system if runs enough time
            'MediaDrmBridgeTest.IsKeySystemSupported_Widevine',
            'MediaDrmBridgeTest.IsSecurityLevelSupported_Widevine',
        ],
        'sandbox_linux_unittests': [
            # Status: Verified with stable image
            'BaselinePolicy.CreateThread',
            'BaselinePolicy.DisallowedCloneFlagCrashes',
            'BrokerProcess.RecvMsgDescriptorLeak',

            # The following cases are due to https://codereview.chromium.org/290143006
            # These are false positive cases and test infrastructure needs to improve to support them.
            'BaselinePolicy.DisallowedKillCrashes',
            'BaselinePolicy.SIGSYS___NR_acct',
            'BaselinePolicy.SIGSYS___NR_chroot',
            'BaselinePolicy.SIGSYS___NR_eventfd',
            'BaselinePolicy.SIGSYS___NR_fanotify_init',
            'BaselinePolicy.SIGSYS___NR_fgetxattr',
            'BaselinePolicy.SIGSYS___NR_getcpu',
            'BaselinePolicy.SIGSYS___NR_getitimer',
            'BaselinePolicy.SIGSYS___NR_init_module',
            'BaselinePolicy.SIGSYS___NR_inotify_init',
            'BaselinePolicy.SIGSYS___NR_io_cancel',
            'BaselinePolicy.SIGSYS___NR_keyctl',
            'BaselinePolicy.SIGSYS___NR_mq_open',
            'BaselinePolicy.SIGSYS___NR_ptrace',
            'BaselinePolicy.SIGSYS___NR_sched_setaffinity',
            'BaselinePolicy.SIGSYS___NR_setpgid',
            'BaselinePolicy.SIGSYS___NR_swapon',
            'BaselinePolicy.SIGSYS___NR_sysinfo',
            'BaselinePolicy.SIGSYS___NR_syslog',
            'BaselinePolicy.SIGSYS___NR_timer_create',
            'BaselinePolicy.SIGSYS___NR_vserver',
            'BaselinePolicy.SocketpairWrongDomain',
        ],
        'ContentShellTest': [
            # Status: TODO
            # Crash
            'JavaBridgeBasicsTest#testCallStaticMethod',
            'JavaBridgeCoercionTest#testPassJavaObject',

            # Status: TODO
            # Fail
            'AddressDetectionTest#testAddressLimits',
            'AddressDetectionTest#testMultipleAddressesInText',
            'AddressDetectionTest#testRealAddresses',
            'AddressDetectionTest#testSpecialChars',
            'AddressDetectionTest#testSplitAddresses',
            'ClickListenerTest#testClickContentOnJSListener1',
            'ClickListenerTest#testClickContentOnJSListener2',
            'ClickListenerTest#testClickContentOnLink',
            'ContentViewLocationTest#testHideWatchResume',
            'ContentViewLocationTest#testWatchHideNewWatchShow',
            'ContentViewLocationTest#testWatchHideShowStop',
            'ContentViewPopupZoomerTest#testPopupZoomerShowsUp',
            'ContentViewScrollingTest#testFling',
            'EmailAddressDetectionTest#testValidEmailAddresses',
            'JavaBridgeBasicsTest#testSameReturnedObjectUsesSameWrapper',
            'PhoneNumberDetectionTest#testInternationalNumberIntents',
            'PhoneNumberDetectionTest#testLocalFRNumbers',
            'PhoneNumberDetectionTest#testLocalUKNumbers',
            'PhoneNumberDetectionTest#testLocalUSNumbers',
            'ScreenOrientationIntegrationTest#testExpectedValues',
            'ScreenOrientationIntegrationTest#testNoChange',
            'ScreenOrientationProviderTest#testBasicValues',
            'ScreenOrientationProviderTest#testLandscape',
            'ScreenOrientationProviderTest#testPortrait',
            'InsertionHandleTest#testDragInsertionHandle',
        ],
        'ChromeShellTest': [
            # Status: Verified with stable image
            # Context menu did not have window focus.
            # If we manually sleep a few seconds after the context menu popup, they will pass.
            'ContextMenuTest#testDismissContextMenuOnBack',
            'ContextMenuTest#testDismissContextMenuOnClick',

            # Status: Verified with stable image (Not important)
            # sync-url is a required parameter for the sync tests
            #
            'SyncTest#testAboutSyncPageDisplaysCurrentSyncStatus',
            'SyncTest#testDisableAndEnableSync',
            'SyncTest#testGetAboutSyncInfoYieldsValidData',

            # Status: Verified with stable image (Not important)
            # Never Panel not opened
            'TranslateInfoBarTest#testTranslateNeverPanel',

            # Status: TODO
            'OAuth2TokenServiceIntegrationTest#testValidateAccountsNoAccountsRegisteredAndNoSignedInUser',  # This would pass if we run it alone
            'OAuth2TokenServiceIntegrationTest#testValidateAccountsOneAccountsRegisteredAndNoSignedInUser',
            'OAuth2TokenServiceIntegrationTest#testValidateAccountsNoAccountsRegisteredButSignedIn',
            'OAuth2TokenServiceIntegrationTest#testValidateAccountsSingleAccountThenAddOne',
            'ProviderBookmarksUriTest#testDeleteBookmark',
            'ProviderBookmarksUriTest#testQueryBookmark',
            'ProviderBookmarksUriTest#testUpdateBookmark',
            'ChromeShellUrlTest#testChromeWelcomePageLoads',
        ],
        'AndroidWebViewTest': [
            # Status: TODO
            'AndroidScrollIntegrationTest#testUiScrollReflectedInJs',
            'AwContentsTest#testCreateAndGcManyTimes',
            'AwSettingsTest#testAllowMixedMode',
            'AwSettingsTest#testFileUrlAccessWithTwoViews',
            'AwSettingsTest#testUserAgentStringDefault',
            'NavigationHistoryTest#testFavicon',
            'NavigationHistoryTest#testNavigateBackToNoncacheableLoginPage',
            'WebViewAsynchronousFindApisTest#testClearFindNext',
            'WebViewAsynchronousFindApisTest#testFindAllDoubleNext',
            'AwSettingsTest#testCacheModeWithTwoViews',
            'AwZoomTest#testZoomControls',
            # Crash
            'AndroidScrollIntegrationTest#testFlingScroll',
            'AndroidScrollIntegrationTest#testJsScrollCanBeAlteredByUi',
            'AndroidScrollIntegrationTest#testJsScrollFromBody',
            'AndroidScrollIntegrationTest#testJsScrollReflectedInUi',
            'AndroidScrollIntegrationTest#testTouchScrollCanBeAlteredByUi',
            # Fail
            'AwContentsClientOnScaleChangedTest#testScaleUp',
            'AwSettingsTest#testLoadWithOverviewModeWithTwoViews',
            'AwSettingsTest#testContentUrlAccessWithTwoViews',
            'CookieManagerStartupTest#testShouldInterceptRequestDeadlock',
        ],
    },
    ('baytrail', 'x86_64'): {
    },
    ('baytrail', 'x86'): {
        'base_unittests': [
            # https://codereview.chromium.org/310323003
            'SafeSPrintfTest.Truncation',
        ],
        'media_unittests': [
            # Status: TODO
            'YUVConvertTest.YUVAtoARGB_MMX_MatchReference',
            'MediaDrmBridgeTest.AddNewKeySystemMapping',
            'MediaDrmBridgeTest.ShouldNotOverwriteExistingKeySystem',
        ],
        'gl_tests': [
            # Status: TODO
            'TextureStorageTest.CorrectPixels',
        ],
        'AndroidWebViewTest': [
            'AwSettingsTest#testLoadWithOverviewModeViewportTagWithTwoViews',
            'AwSettingsTest#testLoadWithOverviewModeWithTwoViews',
        ]
    },
    ('generic', 'all'): {},
    ('generic', 'x86_64'): {},
    ('generic', 'x86'): {},
}


################################################################################


def handle_option():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to sync, build upstream x64 Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --clean -s --patch -b
  python %(prog)s --batch-build
  python %(prog)s --batch-build --sync-upstream
  python %(prog)s --clean -s --sync-upstream --patch
  python %(prog)s --batch-build --test-run
  python %(prog)s --batch-test
  python %(prog)s --test-dryrun --time-fixed
  python %(prog)s --test-to yang.gu@intel.com --test-case 'webkit_compositor_bindings_unittests' --test-run
  python %(prog)s --instrumentation-suite ContentShellTest --test-run --test-command instrumentation --test-formal --test-to yang.gu@intel.com

  crontab -e
  0 1 * * * cd /workspace/project/chromium64-android && python %(prog)s -s --extra-path=/workspace/project/depot_tools
''')

    parser.add_argument('--clean', dest='clean', help='clean patches and local changes', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    parser.add_argument('--sync-upstream', dest='sync_upstream', help='sync with upstream', action='store_true')
    parser.add_argument('--patch', dest='patch', help='apply patches', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-fail', dest='build_fail', help='allow n build failures before it stops', default='0')
    parser.add_argument('--skip-mk', dest='skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('-d', '--dir_root', dest='dir_root', help='set root directory')
    parser.add_argument('--devices', dest='devices', help='device id list separated by ","', default='')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'arm', 'arm64'], default='x86_64')
    parser.add_argument('--target-module', dest='target_module', help='target module to build', choices=['chrome', 'webview', 'content_shell'], default='webview')
    parser.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
    parser.add_argument('--time-fixed', dest='time_fixed', help='fix the time for test sake. We may run multiple tests and results are in same dir', action='store_true')
    parser.add_argument('--just-out', dest='just_out', help='stick to out, instead of out-x86_64/out', action='store_true')

    group_test = parser.add_argument_group('test')
    group_test.add_argument('--test-build', dest='test_build', help='build test', action='store_true')
    group_test.add_argument('--test-run', dest='test_run', help='run test and generate report', action='store_true')
    group_test.add_argument('--test-to', dest='test_to', help='test email receivers that would override the default for test sake')
    group_test.add_argument('--test-formal', dest='test_formal', help='formal test, which would send email and backup to samba server', action='store_true')
    group_test.add_argument('--test-type', dest='test_type', help='test_type', choices=['release', 'debug'], default='release')
    group_test.add_argument('--test-command', dest='test_command', help='test command split by ","')
    group_test.add_argument('--test-drybuild', dest='test_drybuild', help='skip the build of test', action='store_true')
    group_test.add_argument('--test-dryrun', dest='test_dryrun', help='dry run test', action='store_true')
    group_test.add_argument('--test-verbose', dest='test_verbose', help='verbose output for test', action='store_true')
    group_test.add_argument('--test-filter', dest='test_filter', help='filter for test')
    group_test.add_argument('--analyze', dest='analyze', help='analyze test tombstone', action='store_true')
    group_test.add_argument('--gtest-suite', dest='gtest_suite', help='gtest suite')
    group_test.add_argument('--instrumentation-suite', dest='instrumentation_suite', help='instrumentation suite')

    group_batch = parser.add_argument_group('batch')
    group_batch.add_argument('--batch-build', dest='batch_build', help='build batch', action='store_true')
    group_batch.add_argument('--batch-test', dest='batch_test', help='test batch', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, dir_src, test_type, dir_out_test_type, dir_test, dir_time, devices, devices_name, devices_type, target_arch, target_module, report_name, test_suite, time_stamp

    if args.time_fixed:
        time_stamp = get_datetime(format='%Y%m%d')
    else:
        time_stamp = get_datetime()

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

    target_arch = args.target_arch

    if args.dir_root:
        dir_root = args.dir_root
    else:
        dir_root = get_symbolic_link_dir()

    dir_src = dir_root + '/src'
    test_type = args.test_type
    if args.just_out:
        dir_out_test_type = dir_src + '/out/' + test_type.capitalize()
    else:
        dir_out_test_type = dir_src + '/out-' + target_arch + '/out/' + test_type.capitalize()
    dir_test = dir_root + '/test'
    dir_time = dir_test + '/' + time_stamp

    report_name = 'Chromium Tests Report'

    os.environ['GYP_DEFINES'] = 'OS=android werror= disable_nacl=1 enable_svg=0'
    backup_dir(dir_root)
    if not os.path.exists(dir_test):
        os.mkdir(dir_test)

    if args.devices:
        devices_limit = args.devices.split(',')
    else:
        devices_limit = []
    (devices, devices_name, devices_type) = setup_device(devices_limit=devices_limit)

    _hack_app_process()

    target_module = args.target_module

    print '''
========== Configuration Begin ==========
PATH=%(path)s
http_proxy=%(http_proxy)s
https_proxy=%(http_proxy)s
no_proxy=%(no_proxy)s
========== Configuration End ==========
    ''' % {'path': os.getenv('PATH'), 'http_proxy': os.getenv('http_proxy'), 'https_proxy': os.getenv('https_proxy'), 'no_proxy': os.getenv('no_proxy')}

    # Setup test_suite
    for command in _setup_list('test_command'):
        test_suite[command] = []
        for suite in _setup_list(command + '_suite'):
            test_suite[command].append(suite)


def clean(force=False):
    if not args.clean and not force:
        return

    if not force:
        warning('Clean is very dangerous, your local changes will be lost')
        sys.stdout.write('Are you sure to do the cleanup? [yes/no]: ')
        choice = raw_input().lower()
        if choice not in ['yes', 'y']:
            return

    cmd = 'gclient revert -n -j16'
    execute(cmd, interactive=True)
    restore_dir()


def sync(force=False):
    if not args.sync and not force:
        return

    if host_os == 'Linux' and os.path.exists('/usr/sbin/privoxy') and not has_process('privoxy'):
        execute('sudo privoxy /etc/privoxy/config')

    # Judge if the repo is managed or not
    managed = False
    file = open('.gclient')
    lines = file.readlines()
    file.close()
    pattern = re.compile('managed.*(True|False)')
    for line in lines:
        match = pattern.search(line)
        if match and match.group(1) == 'True':
                managed = True

    if not managed:
        backup_dir('src')
        execute('git pull --rebase origin master')
        restore_dir()

    cmd = 'gclient sync -f -n -j16'
    if not args.sync_upstream:
        cmd += ' --revision src@' + chromium_info[CHROMIUM_INFO_INDEX_HASH]
    result = execute(cmd, interactive=True)
    if result[0]:
        error('sync failed', error_code=result[0])

    cmd = 'gclient runhooks'
    result = execute(cmd, interactive=True)
    if result[0]:
        error('sync failed', error_code=result[0])

    if has_process('privoxy'):
        execute('sudo killall privoxy')


def patch(force=False):
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
                    error('Failed to apply patch ' + patch, error_code=result[0])
            else:
                info('Patch ' + patch + ' was applied before, so is just skipped here')
        restore_dir()


def build(force=False):
    if not args.build and not force:
        return

    name_func = get_caller_name()
    timer_start(name_func)

    if not args.skip_mk:
        backup_dir(dir_src)

        if target_arch == 'x86':
            target_arch_temp = 'ia32'
        elif target_arch == 'x86_64':
            target_arch_temp = 'x64'
        elif target_arch == 'arm':
            target_arch_temp = 'arm'
        elif target_arch == 'arm64':
            target_arch_temp = 'arm64'

        command = '. build/android/envsetup.sh && build/gyp_chromium -Dwerror= -Dtarget_arch=' + target_arch_temp
        if not args.just_out:
            command += ' --generator-output out-' + target_arch
        command = bashify(command)

        result = execute(command, interactive=True)
        if result[0]:
            error('Failed to generate makefile')
        restore_dir()

    ninja_cmd = 'ninja -k' + args.build_fail + ' -j' + cpu_count + ' -C ' + dir_out_test_type
    if target_module == 'webview':
        ninja_cmd += ' android_webview_apk'
    elif target_module == 'content_shell':
        ninja_cmd += ' content_shell_apk'
    else:
        ninja_cmd += ' ' + target_module

    ninja_cmd += ' 2>&1 |tee ' + dir_root + '/build.log'
    result = execute(ninja_cmd, show_progress=True)
    if result[0]:
        error('Failed to execute command: ' + ninja_cmd, error_code=result[0])

    timer_end(name_func)


def test_build(force=False):
    if not args.test_build and not force:
        return

    name_func = get_caller_name()
    timer_start(name_func)

    results = {}
    for command in test_suite:
        results[command] = []
        # test command specific build
        _test_build_name(command, 'md5sum forwarder2')

        for suite in test_suite[command]:
            if command == 'gtest':
                if suite in ['breakpad_unittests', 'sandbox_linux_unittests']:
                    name = suite + '_stripped'
                else:
                    name = suite + '_apk'
            elif command == 'instrumentation':
                if suite == 'ContentShellTest':
                    name = 'content_shell_apk content_shell_test_apk'
                elif suite == 'ChromeShellTest':
                    name = 'chrome_shell_apk chrome_shell_test_apk'
                elif suite == 'AndroidWebViewTest':
                    name = 'android_webview_apk android_webview_test_apk'

            result = _test_build_name(command, name)
            if result:
                info('Succeeded to build ' + suite)
                results[command].append('PASS')
            else:
                error('Failed to build ' + suite, abort=False)
                results[command].append('FAIL')

    timer_end(name_func)

    return results


def test_run(force=False):
    if not args.test_run and not force:
        return

    if not os.path.exists(dir_test):
        os.mkdir(dir_test)

    number_device = len(devices)
    if number_device < 1:
        error('Please ensure test device is connected')

    # Build test
    if args.test_drybuild:
        results = {}
        for command in test_suite:
            results[command] = []
            for suite in test_suite[command]:
                results[command].append('PASS')
    else:
        results = test_build(force=True)

    pool = Pool(processes=number_device)
    for index, device in enumerate(devices):
        pool.apply_async(_test_run_device, (index, results))
    pool.close()
    pool.join()


def analyze():
    if not args.analyze:
        return

    analyze_issue(dir_chromium=dir_root, arch='x86_64')


def batch_build(force=False):
    if not args.batch_build and not force:
        return

    clean(force=True)
    sync(force=True)
    patch(force=True)
    build(force=True)


def batch_test(force=False):
    if not args.batch_test and not force:
        return

    batch_build(force=True)
    test_run(force=True)


def _test_build_name(command, name):
    cmd = 'ninja -j' + cpu_count + ' -C ' + dir_out_test_type + ' ' + name
    result = execute(cmd, interactive=True)
    if result[0]:
        return False
    else:
        return True


def _test_run_device(index_device, results):
    timer_start('test_run_' + str(index_device))

    device = devices[index_device]
    device_name = devices_name[index_device]
    device_type = devices_type[index_device]
    dir_device_name = dir_time + '-' + device_name

    connect_device(device)

    if not os.path.exists(dir_device_name):
        os.mkdir(dir_device_name)

    if not args.test_dryrun:
        # Fake /storage/emulated/0
        cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount', device=device) + ' && ' + adb(cmd='shell "mount -o rw,remount rootfs / && chmod 777 /mnt/sdcard && cd /storage/emulated && ln -s legacy 0"', device=device)
        execute(cmd)
        for command in test_suite:
            for index, suite in enumerate(test_suite[command]):
                if results[command][index] == 'FAIL':
                    continue

                # Install packages before running
                if command == 'instrumentation':
                    apks = [suite, suite.replace('Test', '')]
                    for apk in apks:
                        cmd = 'src/build/android/adb_install_apk.py --apk=%s.apk --%s' % (apk, test_type)
                        if not args.just_out:
                            cmd = 'CHROMIUM_OUT_DIR=out-' + target_arch + '/out ' + cmd
                        result = execute(cmd, interactive=True)
                        if result[0]:
                            warning('Failed to install "' + suite + '"')

                    # push test data
                    cmd = adb(cmd='push ', device=device)

                    if suite == 'ContentShellTest':
                        cmd += 'src/content/test/data/android/device_files /storage/emulated/0/content/test/data'
                    elif suite == 'ChromeShellTest':
                        cmd += 'src/chrome/test/data/android/device_files /storage/emulated/0/chrome/test/data'
                    if suite == 'AndroidWebViewTest':
                        cmd += 'src/android_webview/test/data/device_files /storage/emulated/0/chrome/test/data/webview'

                    execute(cmd)

                cmd = 'src/build/android/test_runner.py ' + command
                if not args.just_out:
                    cmd = 'CHROMIUM_OUT_DIR=out-' + target_arch + '/out ' + cmd

                # test command specific cmd
                if command == 'gtest':
                    cmd += ' -s ' + suite + ' -t 60'
                elif command == 'instrumentation':
                    cmd += ' --test-apk ' + suite
                cmd += ' --num_retries 1'

                if args.test_filter:
                    filter_suite = args.test_filter
                else:
                    (filter_suite, count_filter_suite) = _calc_filter(device_type, target_arch, suite)
                cmd += ' -f "' + filter_suite + '"'
                cmd += ' -d ' + device + ' --' + test_type
                if args.test_verbose:
                    cmd += ' -v'
                cmd += ' 2>&1 | tee ' + dir_device_name + '/' + suite + '.log'
                result = execute(cmd, interactive=True)
                if result[0]:
                    warning('Failed to run "' + suite + '"')
                else:
                    info('Succeeded to run "' + suite + '"')

    timer_end('test_run_' + str(index_device))
    # Generate report
    html = _test_gen_report(index_device, results)
    file_html = dir_device_name + '/report.html'
    file_report = open(file_html, 'w')
    file_report.write(html)
    file_report.close()

    if args.test_formal:
        # Backup
        backup_dir(dir_test)
        backup_smb('//ubuntu-ygu5-02.sh.intel.com/chromium64', 'test', time_stamp + '-' + device_name)
        restore_dir()

        # Send mail
        _test_sendmail(index_device, html)


def _test_sendmail(index_device, html):
    device_name = devices_name[index_device]
    if args.test_to:
        to = args.test_to.split(',')
    else:
        to = 'webperf@intel.com'

    send_mail('x64-noreply@intel.com', to, report_name + '-' + time_stamp + '-' + device_name, html, type='html')


def _test_gen_report(index_device, results):
    device_name = devices_name[index_device]
    device_type = devices_type[index_device]
    dir_device_name = dir_time + '-' + device_name

    html_start = '''
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=windows-1252">
    <style type="text/css">
      table {
        border: 2px solid black;
        border-collapse: collapse;
        border-spacing: 0;
        text-align: center;
      }

      table tr td {
        border: 1px solid black;
      }
    </style>
  </head>
  <body>
    <div id="main">
      <div id="content">
        <div>
          <h2 id="Environment">Environment</h2>
          <ul>
            <li>Chromium Revision: ''' + chromium_info[CHROMIUM_INFO_INDEX_REV] + '''</li>
            <li>Target Device: ''' + device_name + '''</li>
            <li>Build Duration: ''' + timer_diff('build') + '''</li>
            <li>Test Build Duration: ''' + timer_diff('test_build') + '''</li>
            <li>Test Run Duration: ''' + timer_diff('test_run_' + str(index_device)) + '''</li>
          </ul>

          <h2>Details</h2>
    '''

    html_end = '''
          <h2>Log</h2>
          <ul>
            <li>http://ubuntu-ygu5-02.sh.intel.com/chromium64/test/''' + time_stamp + '-' + device_name + '''</li>
          </ul>
        </div>
      </div>
    </div>
  </body>
</html>
    '''

    html = html_start
    for command in test_suite:
        html += '''
     <h3>%s</h3>
        ''' % command

        html += '''
      <table>
        <tbody>
          <tr>
            <td> <strong>Test Case Category</strong>  </td>
            <td> <strong>Build Status</strong>  </td>
            <td> <strong>Run Status</strong>  </td>
            <td> <strong>All</strong> </td>
            <td> <strong>Pass</strong> </td>
            <td> <strong>Skip</strong> </td>
            <td> <strong>Fail</strong> </td>
            <td> <strong>Crash</strong> </td>
            <td> <strong>Timeout</strong> </td>
            <td> <strong>Unknown</strong> </td>
          </tr>
        '''

        for index, suite in enumerate(test_suite[command]):
            bs = results[command][index]
            file_log = dir_device_name + '/' + suite + '.log'
            ut_all = ''
            ut_pass = ''
            ut_fail = ''
            ut_crash = ''
            ut_timeout = ''
            ut_unknow = ''

            if bs == 'FAIL' or not os.path.exists(file_log):
                rs = 'FAIL'
            else:
                ut_result = open(dir_device_name + '/' + suite + '.log', 'r')
                lines = ut_result.readlines()
                for line in lines:
                    if 'Main  ALL (' in line:
                        ut_all = line.split('(')[1].split(' ')[0]
                    if 'Main  PASS (' in line:
                        ut_pass = line.split('(')[1].split(' ')[0]
                    if 'Main  FAIL (' in line:
                        ut_fail = line.split('(')[1].split(' ')[0]
                    if 'Main  CRASH (' in line:
                        ut_crash = line.split('(')[1].split(' ')[0]
                    if 'Main  TIMEOUT (' in line:
                        ut_timeout = line.split('(')[1].split(' ')[0]
                    if 'Main  UNKNOWN (' in line:
                        ut_unknow = line.split('(')[1].split(' ')[0]

                if ut_all != '' and ut_pass != '' and int(ut_all) == int(ut_pass):
                    rs = 'PASS'
                else:
                    rs = 'FAIL'

            (filter_suite, count_skip) = _calc_filter(device_type, target_arch, suite)

            if count_skip > 0:
                ut_all = str(int(ut_all) + count_skip)

            ut_skip = str(count_skip)

            # Generate the html
            ut_tr_start = '''<tr>'''
            ut_bs_td_start = '''<td>'''
            ut_rs_td_start = '''<td>'''
            ut_td_end = '''</td>'''

            if bs == 'PASS':
                ut_bs_td_start = '''<td style='color:green'>'''
                if rs == 'PASS':
                    ut_tr_start = '''<tr style='color:green'>'''
                elif rs == 'FAIL':
                    ut_rs_td_start = '''<td style='color:red'>'''
            elif bs == 'FAIL':
                ut_bs_td_start = '''<td style='color:red'>'''

            ut_row = ut_tr_start + '''
                         <td> <strong>''' + suite + ''' <strong></td> ''' + ut_bs_td_start + bs + ut_td_end + ut_rs_td_start + rs + ut_td_end + '''
                         <td>''' + ut_all + '''</td>
                         <td>''' + ut_pass + '''</td>
                         <td>''' + ut_skip + '''</td>
                         <td>''' + ut_fail + '''</td>
                         <td>''' + ut_crash + '''</td>
                         <td>''' + ut_timeout + '''</td>
                         <td>''' + ut_unknow + '''</td></tr>'''
            html += ut_row
        html += '''
        </tbody>
      </table>
        '''

    html += html_end
    return html


def _hack_app_process():
    for device in devices:
        if not execute_adb_shell("test -d /system/lib64", device=device):
            continue

        for file in ['am', 'pm']:
            execute(adb('pull /system/bin/' + file + ' /tmp/' + file))
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount') + ' && ' + adb(cmd='push /tmp/' + file + ' /system/bin/')
                execute(cmd)


def _setup_list(var):
    if var in args_dict and args_dict[var]:
        if args_dict[var] == 'all':
            list_temp = eval(var + '_default')
        else:
            list_temp = eval('args.' + var).split(',')
    else:
        if (var + '_default') in globals():
            list_temp = eval(var + '_default')
        else:
            list_temp = []
    return list_temp


def _calc_filter(device_type, target_arch, suite):
    filter_temp = []

    if suite in test_suite_filter[(device_type, target_arch)]:
        filter_temp += test_suite_filter[(device_type, target_arch)][suite]

    if suite in test_suite_filter[(device_type, 'all')]:
        filter_temp += test_suite_filter[(device_type, 'all')][suite]

    if suite in test_suite_filter[('all', target_arch)]:
        filter_temp += test_suite_filter[('all', target_arch)][suite]

    if suite in test_suite_filter[('all', 'all')]:
        filter_temp += test_suite_filter[('all', 'all')][suite]

    count_filter_temp = len(filter_temp)

    if count_filter_temp > 0:
        filter_str = '*:-' + ':'.join(filter_temp)
    else:
        filter_str = '*'

    return (filter_str, count_filter_temp)


if __name__ == '__main__':
    handle_option()
    setup()
    clean()
    sync()
    patch()
    build()

    test_build()
    test_run()
    analyze()

    batch_build()
    batch_test()
