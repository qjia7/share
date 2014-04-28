#!/usr/bin/env python

import sys
sys.path.append(sys.path[0] + '/..')
from util import *

import os as OS
import multiprocessing
from multiprocessing import Pool

chromium_hash = '3cbd139ee91537327dadb1baff971f3adccf87da'

patches = {
    'src': [
        # Need upstream

        # Under review
        '0001-Do-ApplyGpuDriverBugWorkarounds-after-InitializeOneO.patch',

        # ndk issues
        '0002-ndk-pending-issues.patch',

        # image issues
        '0003-image-pending-issues.patch',
    ],
}

dir_script = sys.path[0]
dir_root = ''
dir_src = ''
dir_unittest = ''
time = get_datetime()
type = ''
dir_out_type = ''
dir_time = ''
target_arch = ''
target_module = ''
report_name = ''

cpu_count = str(multiprocessing.cpu_count() * 2)
devices = []
devices_name = []
unit_tests = []

################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to sync, build upstream x64 Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --clean -s --patch -b
  python %(prog)s --test-build
  python %(prog)s --test-build --sync-upstream
  python %(prog)s --clean -s --sync-upstream --patch
  python %(prog)s --unittest-build --unittest-run
  python %(prog)s --test-unittest
  python %(prog)s --unittest-to yang.gu@intel.com --unittest-case 'webkit_compositor_bindings_unittests' --unittest-run
''')

    parser.add_argument('--clean', dest='clean', help='clean patches and local changes', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    parser.add_argument('--sync-upstream', dest='sync_upstream', help='sync with upstream', action='store_true')
    parser.add_argument('--patch', dest='patch', help='apply patches', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-fail', dest='build_fail', help='allow n build failures before it stops', default='0')
    parser.add_argument('--skip-mk', dest='skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--type', dest='type', help='type', choices=['release', 'debug'], default='release')
    parser.add_argument('-d', '--dir_root', dest='dir_root', help='set root directory')
    parser.add_argument('--devices', dest='devices', help='device id list separated by ","', default='')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'arm'], default='x86_64')
    parser.add_argument('--target-module', dest='target_module', help='target module to build', choices=['chrome', 'webview', 'content_shell'], default='webview')

    group_unittest = parser.add_argument_group('unittest')
    group_unittest.add_argument('--unittest-build', dest='unittest_build', help='build unit tests', action='store_true')
    group_unittest.add_argument('--unittest-run', dest='unittest_run', help='run all unittests and generate unittests report (adb conection being ready is necessary)', action='store_true')
    group_unittest.add_argument('--unittest-to', dest='unittest_to', help='unittest email receivers that would override the default for test sake')
    group_unittest.add_argument('--unittest-case', dest='unittest_case', help='unittest case')
    group_unittest.add_argument('--unittest-sendmail', dest='unittest_sendmail', help='send mail about result', action='store_true')
    group_unittest.add_argument('--unittest-backup', dest='unittest_backup', help='backup result files to samba server', action='store_true')

    group_test = parser.add_argument_group('test')
    group_test.add_argument('--test-build', dest='test_build', help='build test', action='store_true')
    group_test.add_argument('--test-unittest', dest='test_unittest', help='unittest test', action='store_true')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, dir_src, type, dir_out_type, dir_unittest, dir_time, unit_tests, devices, devices_name, target_arch, target_module, report_name

    target_arch = args.target_arch

    if args.dir_root:
        dir_root = args.dir_root
    else:
        dir_root = get_symbolic_link_dir()

    dir_src = dir_root + '/src'
    type = args.type
    dir_out_type = dir_src + '/out-' + target_arch + '/out/' + type.capitalize()
    dir_unittest = dir_root + '/unittest'
    dir_time = dir_unittest + '/' + time

    report_name = 'Chromium Unit Tests Report '

    OS.putenv('GYP_DEFINES', 'OS=android werror= disable_nacl=1 enable_svg=0')
    backup_dir(dir_root)
    if not OS.path.exists(dir_unittest):
        OS.mkdir(dir_unittest)

    if args.unittest_case:
        unit_tests = args.unittest_case.split(',')
    else:
        unit_tests = [
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
            'content_browsertests',  # Need breakpad
            'unit_tests',  # Need breakpad
        ]

    cmd = 'adb devices -l'
    device_lines = commands.getoutput(cmd).split('\n')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue

        pattern = re.compile('device:(.*)')
        match = pattern.search(device_line)
        device_name = match.group(1)
        devices_name.append(device_name)
        device = device_line.split(' ')[0]
        devices.append(device)

    if args.devices:
        devices_temp = args.devices.split(',')
        for index, device in enumerate(devices):
            if device not in devices_temp:
                print index
                del devices[index]
                del devices_name[index]

    target_module = args.target_module


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
    execute(cmd, show_progress=True)
    restore_dir()


def sync(force=False):
    if not args.sync and not force:
        return

    cmd = 'gclient sync -f -n -j16'
    if not args.sync_upstream:
        cmd += ' --revision src@' + chromium_hash
    result = execute(cmd, show_progress=True)
    if result[0]:
        error('sync failed', error_code=result[0])

    cmd = 'gclient runhooks'
    result = execute(cmd, show_progress=True)
    if result[0]:
        error('sync failed', error_code=result[0])


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

    if not args.skip_mk:
        backup_dir(dir_src)

        if target_arch == 'x86':
            target_arch_temp = 'ia32'
        else:
            target_arch_temp = 'x64'

        command = bashify('. build/android/envsetup.sh && build/gyp_chromium -Dwerror= -Dtarget_arch=' + target_arch_temp + ' --generator-output out-' + target_arch)
        execute(command, show_progress=True)
        restore_dir()

    ninja_cmd = 'ninja -k' + args.build_fail + ' -j' + cpu_count + ' -C ' + dir_out_type
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


def unittest_build(force=False):
    if not args.unittest_build and not force:
        return

    results = []
    for unit_test in unit_tests:
        result = _unittest_build_one(unit_test)
        if result:
            info('Succeeded to build ' + unit_test)
            results.append('PASS')
        else:
            error('Failed to build ' + unit_test, abort=False)
            results.append('FAIL')

    return results


def unittest_run(force=False):
    if not args.unittest_run and not force:
        return

    if not OS.path.exists(dir_unittest):
        OS.mkdir(dir_unittest)

    number_device = len(devices)
    if number_device < 1:
        error('Please ensure test device is connected')

    # Build unit test
    results = unittest_build(force=True)

    OS.mkdir(dir_unittest + '/' + time)
    pool = Pool(processes=number_device)
    for index, device in enumerate(devices):
        pool.apply_async(_unittest_run_device, (index, results))
    pool.close()
    pool.join()


def test_build(force=False):
    if not args.test_build and not force:
        return

    clean(force=True)
    sync(force=True)
    patch(force=True)
    build(force=True)


def test_unittest(force=False):
    if not args.test_unittest and not force:
        return

    test_build(force=True)
    unittest_run(force=True)


def _unittest_build_one(unit_test):
    if unit_test in ['breakpad_unittests', 'sandbox_linux_unittests']:
        cmd = 'ninja -j' + cpu_count + ' -C ' + dir_out_type + ' ' + unit_test + '_stripped'
    else:
        cmd = 'ninja -j' + cpu_count + ' -C ' + dir_out_type + ' ' + unit_test + '_apk'

    if type == 'debug':
        cmd += ' md5sum'
    result = execute(cmd, interactive=True)
    if result[0]:
        return False
    else:
        return True


def _unittest_run_device(index_device, results):
    device = devices[index_device]
    device_name = devices_name[index_device]
    dir_device_name = dir_time + '/' + device_name
    OS.mkdir(dir_device_name)

    for index, unit_test in enumerate(unit_tests):
        if results[index] == 'FAIL':
            continue

        cmd = 'CHROMIUM_OUT_DIR=out-' + target_arch + '/out src/build/android/test_runner.py gtest -d ' + device + ' -s ' + unit_test + ' --' + type + ' 2>&1 | tee ' + dir_device_name + '/' + unit_test + '.log'
        result = execute(cmd, interactive=True)
        if result[0]:
            error('Failed to run \'' + unit_test + '\'', error_code=result[0], abort=False)
        else:
            info('Succeeded to run \'' + unit_test + '\'')

    if args.unittest_sendmail:
        _unittest_report(index_device, results)


def _unittest_report(index_device, results):
    device_name = devices_name[index_device]
    if args.unittest_to:
        to = [args.unittest_to]
    else:
        to = [
            'jie.a.chen@intel.com',
            'yang.gu@intel.com',
            'halton.huo@intel.com',
            'zhenyu.liang@intel.com',
            'ying.han@intel.com',
            'zhiqiangx.yu@intel.com',
            'xiaodan.jiang@intel.com',
        ]

    send_mail('x64-noreply@intel.com', to, report_name + time + ' ' + device_name, _unittest_gen_report(index_device, results), type='html')
    _unittest_backup(index_device)


def _unittest_gen_report(index_device, results):
    device_name = devices_name[index_device]
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
            <li>Chromium hash: ''' + chromium_hash + '''</li>
            <li>Target Device: ''' + device_name + '''</li>
          </ul>

          <h2 id="Details">Details</h2>
          <table>
            <tbody>
              <tr>
                <td> <strong>Test Case Category</strong>  </td>
                <td> <strong>Build Status</strong>  </td>
                <td> <strong>Run Status</strong>  </td>
                <td> <strong>All</strong> </td>
                <td> <strong>Pass</strong> </td>
                <td> <strong>Fail</strong> </td>
                <td> <strong>Crash</strong> </td>
                <td> <strong>Timeout</strong> </td>
                <td> <strong>Unknown</strong> </td>
              </tr>
'''

    html_end = '''
            </tbody>
          </table>
          <h2 id="Attach">Attach</h2>
          <ul>
            <li>http://ubuntu-ygu5-02.sh.intel.com/chromium64/unittest/report/''' + time + '-' + device_name + '-' + 'report.tar.gz' + '''</li>
          </ul>
        </div>
      </div>
    </div>
  </body>
</html>
'''

    html = html_start
    dir_device_name = dir_time + '/' + device_name
    for index, unit_test in enumerate(unit_tests):
        bs = results[index]

        # parse log
        ut_all = ''
        ut_pass = ''
        ut_fail = ''
        ut_crash = ''
        ut_timeout = ''
        ut_unknow = ''

        if len(bs) > 0:
            ut_result = open(dir_device_name + '/' + unit_test + '.log', 'r')
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

        ut_tr_start = '''<tr>'''
        ut_bs_td_start = '''<td>'''
        ut_rs_td_start = '''<td>'''
        ut_td_end = '''</td>'''

        if ut_all != '' and ut_pass != '' and int(ut_all) == int(ut_pass):
            rs = 'PASS'
        else:
            rs = 'FAIL'

        if bs == 'PASS':
            ut_bs_td_start = '''<td style='color:green'>'''
            if rs == 'PASS':
                ut_tr_start = '''<tr style='color:green'>'''
            elif rs == 'FAIL':
                ut_rs_td_start = '''<td style='color:red'>'''
        elif bs == 'FAIL':
            ut_bs_td_start = '''<td style='color:red'>'''

        ut_row = ut_tr_start + '''
                     <td> <strong>''' + unit_test + ''' <strong></td> ''' + ut_bs_td_start + bs + ut_td_end + ut_rs_td_start + rs + ut_td_end + '''
                     <td>''' + ut_all + '''</td>
                     <td>''' + ut_pass + '''</td>
                     <td>''' + ut_fail + '''</td>
                     <td>''' + ut_crash + '''</td>
                     <td>''' + ut_timeout + '''</td>
                     <td>''' + ut_unknow + '''</td></tr>'''

        html += ut_row
    html += html_end

    # Save result
    file_html = dir_device_name + '/' + report_name + ' of WW' + time + '-' + device_name + '.html'
    file_report = open(file_html, 'w')
    file_report.write(html)
    file_report.close()

    return html


def _unittest_backup(index_device):
    if not args.unittest_backup:
        return

    device_name = devices_name[index_device]
    smb_server = '//ubuntu-ygu5-02.sh.intel.com/chromium64/'
    local_dir = './'
    local_file = time + '-' + device_name + '-' + 'report.tar.gz'
    server_dir = 'unittest\\report\\'
    server_file = local_file
    execute('tar zvcf ' + local_file + ' ' + dir_time)

    upload_server(smb_server, local_dir, local_file, server_dir, server_file)
    execute('rm -f ' + local_dir + local_file, interactive=True)


if __name__ == '__main__':
    handle_option()
    setup()
    clean()
    sync()
    patch()
    build()

    unittest_build()
    unittest_run()

    test_build()
    test_unittest()
