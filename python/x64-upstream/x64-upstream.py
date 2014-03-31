#!/usr/bin/env python

import sys
sys.path.append(sys.path[0] + '/..')
from util import *

import os as OS
import multiprocessing
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

chromium_hash = 'ffe217eec25605f299ef6d5d9eb95ccf8c8d464d'

patches = {
    # Need upstream
    'src/breakpad/src': ['0001-breakpad-Enable-x86_64-for-android.patch'],
    'src/third_party/lss': [
        '0001-lss-fix-the-__unused-issue.patch',
        '0002-lss-fix-__off64_t-issue.patch'
    ],
    'src/third_party/mesa/src': ['0001-disable-log2.patch'],

    # Under review
    'src/third_party/icu': ['0001-third_party-icu-x64-support.patch'],

    # Can not upstream
    'ndk': [
        '0001-ndk-Add-gyp-files.patch',
        '0002-ndk-fix-for-Android-x64.patch',
        '0003-Rename-gdbserver-to-gdbserver64.patch',
    ],
}

dir_script = sys.path[0]
dir_root = ''
dir_src = ''
type = ''
dir_out_type = ''
time = get_datetime()
cpu_count = str(multiprocessing.cpu_count() * 2)
android_ndk_version = 'android64-ndk-' + open('ndk/RELEASE.TXT', 'r').read()
dir_log = 'log-' + time + '/'

unit_tests = [
    'android_webview_test',
    'android_webview_unittests',
    'base_unittests',
    'breakpad_unittests',
    'cc_unittests',
    'components_unittests',
    'content_browsertests',
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
    'unit_tests',
    'webkit_compositor_bindings_unittests',
    'webkit_unit_tests',
    'content_gl_tests',
]

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
''')

    parser.add_argument('--clean', dest='clean', help='clean patches and local changes', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='sync the repo', action='store_true')
    parser.add_argument('--sync-upstream', dest='sync_upstream', help='sync with upstream', action='store_true')
    parser.add_argument('--patch', dest='patch', help='apply patches', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-fail', dest='build_fail', help='allow n build failures before it stops', default='0')
    parser.add_argument('--skip-mk', dest='skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--set-ndk', dest='set_ndk', help='set up ndk', action='store_true')
    parser.add_argument('--type', dest='type', help='type', choices=['release', 'debug'], default='release')
    parser.add_argument('-d', '--dir_root', dest='dir_root', help='set root directory')

    group_unittest = parser.add_argument_group('unittest')
    group_unittest.add_argument('--unittest-build', dest='unittest_build', help='build all unittests', action='store_true')
    group_unittest.add_argument('--unittest-run', dest='unittest_run', help='run all unittests and generate unittests report (adb conection being ready is necessary)', action='store_true')

    group_test = parser.add_argument_group('test')
    group_test.add_argument('--test-build', dest='test_build', help='build test', action='store_true')
    group_test.add_argument('--test-unittest', dest='test_unittest', help='unittest test', action='store_true')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, dir_src, type, dir_out_type

    if not args.dir_root:
        dir_root = get_symbolic_link_dir()
    else:
        dir_root = args.dir_root

    dir_src = dir_root + '/src'
    type = args.type
    dir_out_type = dir_src + '/out/' + type.capitalize()

    OS.putenv('GYP_DEFINES', 'werror= disable_nacl=1 enable_svg=0')
    backup_dir(dir_root)


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

    backup_dir('ndk')
    cmd = bashify('git reset --hard $(git log --oneline|tail -1|awk \'{print $1}\') && rm -rf android_tools_ndk.gyp crazy_linker.gyp .git')
    execute(cmd)
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

    set_ndk(force=True)

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
        command = bashify('. build/android/envsetup.sh && android_gyp -Dtarget_arch=x64 -Dwerror=')
        execute(command, show_progress=True)
        restore_dir()

    ninja_cmd = 'ninja -k' + args.build_fail + ' -j' + cpu_count + ' -C ' + dir_out_type + ' android_webview_apk'
    ninja_cmd += ' 2>&1 |tee ' + dir_root + '/build.log'
    result = execute(ninja_cmd, show_progress=True)
    if result[0]:
        error('Failed to execute command: ' + ninja_cmd, error_code=result[0])


def set_ndk(force=False):
    if not args.set_ndk and not force:
        return

    if not OS.path.exists('ndk'):
        error('Please put ndk under ' + get_symbolic_link_dir())

    if not OS.path.exists('ndk/platforms/android-19/arch-x86_64'):
        execute('ln -s ../android-20/arch-x86_64 ndk/platforms/android-19/arch-x86_64')

    if not OS.path.islink('src/third_party/android_tools/ndk'):
        # Create symbolic link to real ndk
        if not OS.path.exists('src/third_party/android_tools/ndk_bk'):
            cmd = 'mv src/third_party/android_tools/ndk src/third_party/android_tools/ndk_bk'
        else:
            cmd = 'rm -rf src/third_party/android_tools/ndk'
        execute(cmd, show_command=True)
        backup_dir('src/third_party/android_tools')
        execute('ln -s ../../../ndk ./', show_command=False)
        restore_dir()

    # Init a git repo
    if not OS.path.exists('ndk/.git'):
        backup_dir('ndk')
        execute('git init && git add . && git commit -a -m "orig"')
        restore_dir()


def unittest_build(force=False):
    if not args.unittest_build and not force:
        return

    if not OS.path.exists(dir_log):
        OS.mkdir(dir_log)

    for unit_test in unit_tests:
        if unit_test in ['breakpad_unittests', 'sandbox_linux_unittests']:
            cmd = 'ninja -j' + cpu_count + ' -C ' + dir_out_type + ' ' + unit_test + '_stripped' + ' > ' + dir_log + unit_test + '_build.log'
        else:
            cmd = 'ninja -j' + cpu_count + ' -C ' + dir_out_type + ' ' + unit_test + '_apk' + ' > ' + dir_log + unit_test + '_build.log'
        result = execute(cmd, interactive=True)
        if result[0]:
            OS.rename(dir_log + unit_test + '_build.log', dir_log + 'build_fail_' + unit_test + '.log')
            error('Failed to build \'' + unit_test + '\'', error_code=result[0], abort=False)
        else:
            OS.rename(dir_log + unit_test + '_build.log', dir_log + 'build_success_' + unit_test + '.log')
            info('Succeeded to build \'' + unit_test + '\'')


def unittest_run(force=False):
    if not args.unittest_run and not force:
        return

    if not OS.path.exists(dir_log):
        OS.mkdir(dir_log)

    for unit_test in unit_tests:
        if OS.path.exists(dir_out_type + '/' + unit_test + '_apk/') or unit_test in ['breakpad_unittests', 'sandbox_linux_unittests']:
            cmd = 'src/build/android/test_runner.py gtest -s ' + unit_test + ' --' + type + ' > ' + dir_log + unit_test + '_run.log'
            result = execute(cmd, show_progress=False)
            if result[0]:
                OS.rename(dir_log + unit_test + '_run.log', dir_log + 'run_fail_' + unit_test + '.log')
                error('Failed to run \'' + unit_test + '\'', error_code=result[0], abort=False)
            else:
                OS.rename(dir_log + unit_test + '_run.log', dir_log + 'run_success_' + unit_test + '.log')
                info('Succeeded to run \'' + unit_test + '\'')

    _unittest_gen_report()
    _unittest_send_report()


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
    unittest_build(force=True)
    unittest_run(force=True)


def _unittest_gen_report():
    html_start = '''
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=windows-1252">
    <title>
      ChromeForAndroidx64 Unit Tests Report
    </title>
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
          <h1 id="">ChromeForAndroidx64 Unit Tests Report of ''' + time + ''' </h1>

          <h2 id="Environment">Environment</h2>
          <ul>
            <li>Chromium hash: ''' + chromium_hash + '''</li>
            <li>Host OS: ''' + host_os + '''</li>
            <li>Android NDK: ''' + android_ndk_version + '''</li>
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
        </div>
      </div>
    </div>
  </body>
</html>
'''

    for unit_test in unit_tests:
        # build status
        if OS.path.exists(dir_log + 'build_success_' + unit_test + '.log'):
            bs = 'Success'
        elif OS.path.exists(dir_log + 'build_fail_' + unit_test + '.log'):
            bs = 'Fail'
        else:
            bs = ''

        # run status
        if OS.path.exists(dir_log + 'run_success_' + unit_test + '.log'):
            rs = 'Success'
            log_prefix = 'run_success_'
        elif OS.path.exists(dir_log + 'run_fail_' + unit_test + '.log'):
            rs = 'Fail'
            log_prefix = 'run_fail_'
        else:
            rs = ''

        # parse log
        ut_all = ''
        ut_pass = ''
        ut_fail = ''
        ut_crash = ''
        ut_timeout = ''
        ut_unknow = ''

        if len(rs) > 0:
            ut_result = open(dir_log + log_prefix + unit_test + '.log', 'r')
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

        if bs == 'Success':
            ut_bs_td_start = '''<td style='color:green'>'''
            if rs == 'Success':
                ut_tr_start = '''<tr style='color:green'>'''
            elif rs == 'Fail':
                ut_rs_td_start = '''<td style='color:red'>'''
        elif bs == 'Fail':
            ut_bs_td_start = '''<td style='color:red'>'''

        ut_row = ut_tr_start + '''
                     <td> <strong>''' + unit_test + ''' <strong></td> ''' + ut_bs_td_start + bs + ut_td_end + ut_rs_td_start + rs + ut_td_end + '''
                     <td>''' + ut_all + '''</td>
                     <td>''' + ut_pass + '''</td>
                     <td>''' + ut_fail + '''</td>
                     <td>''' + ut_crash + '''</td>
                     <td>''' + ut_timeout + '''</td>
                     <td>''' + ut_unknow + '''</td></tr>'''

        html = html_start + ut_row
    html += html_end

    file_report = dir_log + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html'
    file_html = open(file_report, 'w')
    file_html.write(html)
    file_html.close()
    info(dir_log + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html has been generated successfully')


def _unittest_send_report():
    if not OS.path.exists(dir_log + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html'):
        return

    addressor = 'x64-noreply@intel.com'
    recipients = [
        #'jie.a.chen@intel.com',
        'yang.gu@intel.com',
        #'halton.huo@intel.com',
        #'zhenyu.liang@intel.com',
        #'ying.han@intel.com',
        #'zhiqiangx.yu@intel.com',
    ]
    copyto = [
        #'xiaodan.jiang@intel.com',
    ]

    msg_report = MIMEMultipart('related')
    msg_report['Subject'] = 'ChromeForAndroidx64 Unit Tests Report of ' + time
    msg_report['From'] = addressor
    msg_report['To'] = ','.join(recipients)
    msg_report['Cc'] = ','.join(copyto)

    att_report = MIMEText(open(dir_log + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html', 'rb').read(), 'base64', 'utf-8')
    att_report['Content-Type'] = 'application/octet-stream'
    att_report['content-Disposition'] = 'attachment; filename=' + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html'
    msg_report.attach(att_report)

    try:
        # Unittests running host requires a mail-server installed, such as 'postfix'.
        smtp = smtplib.SMTP('127.0.0.1')
        smtp.sendmail(msg_report['From'], recipients + copyto, msg_report.as_string())
        info(dir_log + 'ChromeForAndroidx64 Unit Tests Report of ' + time + '.html has been sent out successfully')
    except Exception, e:
        error('Failed to send unittest report of ' + time + ': ' + e)
    finally:
        smtp.quit()


if __name__ == '__main__':
    handle_option()
    setup()
    clean()
    sync()
    set_ndk()
    patch()
    build()

    unittest_build()
    unittest_run()

    test_build()
    test_unittest()
