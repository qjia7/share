import sys
sys.path.append(sys.path[0] + '/..')
from util import *
from common import *


# Define result for good rev
benchmarks = {
    'cocos': ['>20'],
    'galacticmobile': ['>50'],
}

target_os = ''
target_arch = ''
target_module = ''
benchmark = ''
rev_list = []
comb_name = ''

################################################################################


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to bisect regression',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -g 218527 -b 226662 --benchmark cocos

''')
    parser.add_argument('--target-os', dest='target_os', help='target os', choices=target_os_all, default='android')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=target_arch_all, default='x86')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all, default='content_shell')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', required=True)
    parser.add_argument('-g', '--good-rev', dest='good_rev', type=int, help='small revision, which is good')
    parser.add_argument('-b', '--bad-rev', dest='bad_rev', type=int, help='big revision, which is bad')

    args = parser.parse_args()


def setup():
    global target_os, target_arch, target_module, comb_name, benchmark

    target_os = args.target_os
    target_arch = args.target_arch
    target_module = args.target_module
    benchmark = args.benchmark
    comb_name = get_comb_name(target_os, target_arch, target_module)

    if args.good_rev:
        rev_min = args.good_rev
    else:
        rev_min = rev_default[0]

    if args.bad_rev:
        rev_max = args.bad_rev
    else:
        rev_max = rev_default[1]

    get_rev_list(rev_min, rev_max)
    #print rev_list

    if target_os == 'linux' and target_module == 'chrome':
        sandbox_file = '/usr/local/sbin/chrome-devel-sandbox'
        if not os.path.exists(sandbox_file):
            error('SUID Sandbox file "' + sandbox_file + '" does not exist')
        sandbox_env = os.getenv('CHROME_DEVEL_SANDBOX')
        if not sandbox_env:
            error('SUID Sandbox environmental variable does not set')


def parse_result(benchmark, output):
    # Result is in format: result is [1,2,3]
    results = []
    pattern = re.compile('result is \[(.*)\]')
    match = pattern.search(output)
    if match:
        results = match.group(1).split(',')
    return results


def is_good(rev):
    backup_dir('../webmark')
    r = execute('python webmark.py --target-os ' + target_os + ' --target-arch ' + target_arch + ' --target-module ' + target_module + ' --target-module-path ' + dir_out_server + '/' + get_comb_name(target_os, target_arch, target_module) + '/' + str(rev) + '.apk' + ' --benchmark ' + benchmark, return_output=True)
    restore_dir()

    if r[0]:
        error('Failed to run benchmark ' + benchmark + ' with revision ' + str(rev))

    results = parse_result(benchmark, r[1])

    for index, result in enumerate(results):
        condition = result + benchmarks[benchmark][index]
        if not eval(condition):
            info(str(rev) + ': Bad')
            return False

    info(str(rev) + ': Good')
    return True


def get_commit(rev_good, rev_bad):
    backup_dir(dir_root + '/project/chromium-' + target_os + '/src')
    execute('git log origin master >git_log', show_command=False)
    file = open('git_log')
    lines = file.readlines()
    file.close()

    pattern_commit = re.compile('^commit (.*)')
    pattern_rev = re.compile('git-svn-id: .*@(.*) (.*)')
    need_print = False
    suspect_log = dir_log + '/suspect.log'
    for line in lines:
        match = pattern_commit.search(line)
        if match:
            commit = match.group(1)
            if need_print:
                execute('git show ' + commit + ' >>' + suspect_log, show_command=False)

        match = pattern_rev.search(line)
        if match:
            rev = int(match.group(1))

            if rev <= rev_good:
                break

            if rev > rev_bad:
                continue

            if not need_print:
                need_print = True
                execute('git show ' + commit + ' >>' + suspect_log, show_command=False)

    info('Check ' + suspect_log + ' for suspected checkins')
    restore_dir()


def bisect(index_good, index_bad, check_boundry=False):
    rev_good = rev_list[index_good]
    rev_bad = rev_list[index_bad]

    if check_boundry:
        if not is_good(rev_good):
            error('Revision ' + str(rev_good) + ' should not be bad')

        if is_good(rev_bad):
            error('Revision ' + str(rev_bad) + ' should not be good')

    #print 'index_good:' + str(index_good) + ' index_bad:' + str(index_bad)
    if index_good + 1 == index_bad:
        rev_good_final = rev_list[index_good]
        rev_bad_final = rev_list[index_bad]

        if rev_good_final + 1 == rev_bad_final:
            info('Revision ' + str(rev_bad) + ' is the exact commit for regression')
        else:
            info('The regression is between revisions (' + rev_list[index_good] + ',' + rev_list[index_bad] + '], but there is no build for further investigation')

        if rev_bad_final - rev_good_final < 15:
            get_commit(rev_good_final, rev_bad_final)
        else:
            info('There are too many checkins in between, please manually check the checkin info')

        exit(0)

    index_mid = (index_good + index_bad) / 2
    rev_mid = rev_list[index_mid]
    if is_good(rev_mid):
        bisect(index_mid, index_bad)
    else:
        bisect(index_good, index_mid)


def get_rev_list(rev_min, rev_max):
    global rev_list
    for file in os.listdir(dir_out_server + '/' + comb_name):
        pattern = re.compile(comb_valid[target_os, target_arch, target_module][0])
        match = pattern.search(file)
        if match:
            rev = int(match.group(1))
            if rev >= rev_min and rev <= rev_max:
                rev_list.append(rev)

    rev_list = sorted(rev_list)


if __name__ == '__main__':
    handle_option()
    setup()
    bisect(0, len(rev_list) - 1, check_boundry=True)
