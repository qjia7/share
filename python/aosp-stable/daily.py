#!/usr/bin/env python

# For a new copies repo, we may do following:
# cd .repo/manifests && git reset --hard HEAD^ && cd - && ./repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/private/topic/aosp_stable/master && cd .repo/manifests && git am /workspace/project/gyagp/share/python/aosp-stable/patches/0001-Replace-webview-and-chromium_org.patch && cd - && ./repo start x64 --all


import sys
sys.path.append(sys.path[0] + '/..')
from util import *

repo_default = ['aosp-stable', 'aosp-stable-cr']
repo = []
date = get_datetime(format='%Y%m%d')


def handle_option():
    global args, args_dict

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -b aosp-stable
  python %(prog)s -b aosp-stable-cr
  python %(prog)s -b all
''')

    parser.add_argument('--repo', dest='repo', help='repo to build', choices=repo_default + ['all'], default='aosp-stable-cr')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('--keep-out', dest='keep_out', help='keep the out dir', action='store_true')
    parser.add_argument('--skip-sync', dest='skip_sync', help='skip sync', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global repo

    repo = _setup_list('repo')
    backup_dir('/workspace/project')


def build():
    if not args.build:
        return

    for repo_temp in repo:
        backup_dir(repo_temp + '-daily')

        # Ensure last good build is kept if available
        if not args.keep_out:
            if not os.path.exists('out_bk'):
                execute('mv out out_bk')
            else:
                if os.path.exists('out/target/product/baytrail_64/live.img'):
                    execute('rm -rf out_bk')
                    execute('mv out out_bk')
                else:
                    execute('rm -rf out')

        cmd = 'python aosp-stable.py --patch --target-arch all --target-device all -b --backup'
        if not args.skip_sync:
            cmd += ' --sync all'
        execute(cmd, interactive=True)
        restore_dir()


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


if __name__ == "__main__":
    handle_option()
    setup()
    build()
