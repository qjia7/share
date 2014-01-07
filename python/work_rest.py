from util import *


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to sleep several seconds, and hibernate|restart|poweroff on Windows',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:

  python %(prog)s -h
  python %(prog)s -w 5 --hibernate
''')

    parser.add_argument('-s', '--sleep', dest='sleep', help='minutes to sleep', type=int, default=60)
    parser.add_argument('--hibernate', dest='hibernate', help='choose to hibernate', action='store_true')
    parser.add_argument('--restart', dest='restart', help='choose to restart', action='store_true')
    parser.add_argument('--poweroff', dest='poweroff', help='choose to poweroff', action='store_true')
    parser.add_argument('--unit', dest='unit', help='unit for sleep, default is minute', choices=['m', 's', 'h'], default='m')

    args = parser.parse_args()
    if len(sys.argv) <= 1:
        parser.print_help()

    count = 0
    if args.hibernate:
        count = count + 1
    if args.restart:
        count = count + 1
    if args.poweroff:
        count = count + 1
    if count < 1:
        error('Please choose a rest mode')
    if count > 1:
        error('More than one rest mode is chosen')


def sleep():
    if args.unit == 'm':
        second = args.sleep * 60
    elif args.unit == 'h':
        second = args.sleep * 3600
    else:
        second = args.sleep

    time.sleep(second)


def rest():
    if args.hibernate:
        cmd = 'rundll32.exe powrprof.dll,SetSuspendState'

    if args.restart:
        cmd = 'shutdown.exe -r -t 0 -f'

    if args.poweroff:
        cmd = 'shutdown.exe -s -t 0 -f'

    info(get_datetime(format='%Y-%m-%d %X'))
    execute(cmd)


if __name__ == '__main__':
    handle_option()
    sleep()
    rest()
