from util import *
import pexpect


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to build automatically',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -p abc

''')
    parser.add_argument('-p', '--password', dest='password', help='password', required=True)

    args = parser.parse_args()
    if len(sys.argv) <= 1:
        parser.print_help()


def connect():
    cmd = 'sudo openconnect -c /home/gyagp/.cert/certificate.p12 --script /etc/vpnc/vpnc-script 192.102.204.72 --cafile /home/gyagp/.cert/intel-certchain.crt --key-password-from-fsid'
    #child = pexpect.spawn('/bin/bash', ['-c', cmd])
    child = pexpect.spawn(cmd)
    child.logfile = sys.stdout
    child.expect("Enter .*:")
    child.sendline('yes')
    child.expect('Username:')
    child.sendline('yang.gu@intel.com')
    child.expect('Password:')
    child.sendline(args.password)
    child.expect(pexpect.EOF, timeout=None)

if __name__ == '__main__':
    handle_option()
    connect()
