from util import *
from common import *
import os as OS


# Define result for good rev
benchmarks = {
    'cocos': ['>100']
}

os = ''
arch = ''
module = ''
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
    parser.add_argument('--os', dest='os', help='os', choices=os_all, default='linux')
    parser.add_argument('--arch', dest='arch', help='arch', choices=arch_all, default='x86')
    parser.add_argument('--module', dest='module', help='module', choices=module_all, default='chrome')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', required=True)
    parser.add_argument('-g', '--good-rev', dest='good_rev', type=int, help='small revision, which is good')
    parser.add_argument('-b', '--bad-rev', dest='bad_rev', type=int, help='big revision, which is bad')

    args = parser.parse_args()


def setup():
    global os, arch, module, comb_name, benchmark

    os = args.os
    arch = args.arch
    module = args.module
    benchmark = args.benchmark
    comb_name = get_comb_name(os, arch, module)

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


def is_good(rev):
    result = execute('python webmark.py --os ' + os + ' --arch ' + arch + ' --module ' + module + ' --rev ' + rev + ' --benchmark ' + benchmark)
    if result[0]:
        error('Failed to run benchmark ' + benchmark + ' with revision ' + str(rev))

    for index, score in enumerate(result[1]):
        condition = score + benchmarks[benchmark][index]
        if not eval(condition):
            info(str(rev) + ': Bad')
            return False

    info(str(rev) + ': Good')
    return True


def bisect(index_good, index_bad, check_boundry=False):
    rev_good = rev_list[index_good]
    rev_bad = rev_list[index_bad]

    if check_boundry:
        if not is_good(rev_good):
            error('Revision ' + str(rev_good) + 'should not be bad')

        if is_good(rev_bad):
            error('Revision ' + str(rev_bad) + ' should not be good')

    #print 'index_good:' + str(index_good) + ' index_bad:' + str(index_bad)
    if index_good + 1 == index_bad:
        info('Revision ' + str(rev_bad) + ' is the exact commit for regression')
        exit(0)

    index_mid = (index_good + index_bad) / 2
    rev_mid = rev_list[index_mid]
    if is_good(rev_mid):
        bisect(index_mid, index_bad)
    else:
        bisect(index_good, index_mid)


def get_rev_list(rev_min, rev_max):
    global rev_list
    for file in OS.listdir(dir_out + '/' + comb_name):
        pattern = re.compile(comb_valid[os, arch, module])
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
