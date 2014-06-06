#/usr/bin/python

# Description:
# This file would help to set up environment after fresh building of a new Ubuntu system.
#
# Pre-installation:
# Backup files in desktop, opened tab in Chrome.
#
# Post-installation:
# sudo apt-get update && sudo apt-get dist-upgrade -y
# Install display card driver, slickedit.
# sudo /workspace/project/chromium/git_upstream/src/build/install-build-deps.sh. This file would help to install many development tools.
# Set keyboard shortcut: "nautilus /workspace" -> ctrl+alt+E
# Set input method: gnome-session-properties
# install jdk 1.6.0.45: copy /usr/lib/jvm/jdk1.6.0_45/

from util import *
import commands
import getpass

dir_repo = '/workspace/project/gyagp/share'
dir_linux = dir_repo + '/linux'
dir_python = dir_repo + '/python'
dir_home = os.getenv("HOME")
user = os.getenv("USER")
profile = ''
username = ''


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to install system',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Examples:
  python %(prog)s
  python %(prog)s --need-update # First time running this script
''')
    parser.add_argument('-p', '--profile', dest='profile', help='designate profile', choices=['direct', 'proxy'], default='proxy')
    parser.add_argument('--need-update', dest='need_update', help='need update', action='store_true')
    args = parser.parse_args()

    #if len(sys.argv) <= 1:
    #    parser.print_help()


def setup():
    global username, profile

    username = getpass.getuser()

    if args.profile == "direct":
        profile = "direct"
    elif args.profile == "proxy":
        profile = "proxy"

    backup_dir(dir_python)


def patch_sudo():
    file_name = '10_' + username + '_sudo'
    sudo_file = '/etc/sudoers.d/' + file_name

    if os.path.exists(sudo_file):
        info("You were able to sudo without password")
    else:
        execute('sudo echo "' + username + ' ALL=NOPASSWD:ALL" >' + file_name)
        execute('chmod 0440 ' + file_name)
        execute('sudo chown root:root ' + file_name)
        result = execute('sudo mv ' + file_name + ' ' + sudo_file)
        if result[0] == 0:
            info("Now you can sudo without password")
            # No need to run following command to take effect
            #execute("/etc/init.d/sudo restart")
        else:
            warning('Failed to enable sudo')


def copy_file(srcFile, destDir, sudo=False, srcSubDir=''):
    if cmp(srcSubDir, "") == 1:
        srcPath = dir_linux + "/" + srcSubDir + "/" + srcFile
    else:
        srcPath = dir_linux + "/" + srcFile

    if not os.path.exists(srcPath):
        error(srcPath + " doesn't exist")
        return -1

    if os.path.exists(destDir + "/" + srcFile):
        info(destDir + "/" + srcFile + " already exists")
        return 0

    if not os.path.exists(destDir):
        commands.getstatusoutput("mkdir -p " + destDir)
        info(srcFile + destDir + " doesn't exist, so just create it")

    command = "cp " + srcPath + " " + destDir
    if sudo:
        command = "sudo " + command

    result = execute(command)
    return result[0]


def overwrite_file(srcFile, destDir, sudo, srcSubDir=""):
    if not os.path.exists(destDir + "/" + srcFile):
        error(destDir + "/" + srcFile + " doesn't exist")
        return -1

    if os.path.exists(destDir + "/" + srcFile + ".bk"):
        info(destDir + "/" + srcFile + " was already overwritten")
        return 0

    command = "mv " + destDir + "/" + srcFile + " " + destDir + "/" + srcFile + ".bk"
    if sudo:
        command = "sudo " + command

    (status, output) = commands.getstatusoutput(command)

    status = copy_file(srcFile, destDir, sudo, srcSubDir)
    if status == 0:
        info(srcFile + " has replaced the original file successfully")
    else:
        error(srcFile + " didn't replace the original file successfully")

    return status


def install_package(pkg_list):
    for pkg in pkg_list:
        if package_installed(pkg):
            info("Package " + pkg + " was already installed")
        else:
            info("Package " + pkg + " is installing...")
            result = execute("sudo apt-get install -y " + pkg, interactive=True)
            if result[0]:
                warning("Package " + pkg + "'s installation failed")


def install_chromium():
    if package_installed('google-chrome-unstable'):
        return

    execute('python upgrade.py -t chrome', show_progress=True)
    install_package(['google-chrome-unstable'])

    # Install Chrome, which needs to use tsocks
    result = execute("sudo apt-key list | grep 7FAC5991")
    if result[0]:
        info("Get the key for Chrome...")

        # Not sure if the key would change, so get the online one in this profile
        if profile == "proxy":
            command = "tsocks wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
        elif profile == "direct":
            command = "cat " + dir_linux + "/chrome_key_pub.txt | sudo apt-key add -"

        result = execute(command)
        if result[0]:
            error("Key for Chrome hasn't been added correctly")
    else:
        info("Key for Chrome has been added")

if __name__ == "__main__":
    handle_option()
    setup()

    # This should be done first
    patch_sudo()

    if args.need_update:
        execute('python upgrade.py')

    install_package([
        'tsocks', 'privoxy',
        'apt-file',
        'zsh',
        'git', 'git-svn',
        'gparted',
        'gnome-shell',
        'vim',
        'ssh',
        'most',
        'binutils',
        'vnc4server',
        'cmake',
        'hibernate',
        'python-boto', 'python-dev', 'python-psutil',
        'ccache',
        'alacarte',
        'libicu-dev',
        # required by Chromium build
        'libspeechd-dev', 'libgdk-pixbuf2.0-dev', 'libgtk2.0-dev', 'libdrm-dev', 'libgnome-keyring-dev', 'libgconf2-dev', 'libudev-dev',
        'libpci-dev', 'linux-tools', 'binutils-dev', 'libelf-dev', 'gperf', 'gcc-4.7-multilib', 'g++-4.7-multilib', 'bison', 'python-pip',
        'module-assistant', 'autoconf', 'automake', 'libnss3-dev', 'ant', 'libcups2-dev', 'libasound2-dev', 'libxss-dev', 'libxtst-dev',
        'libpulse-dev',
        'postfix',  # smtp server
        'android-tools-adb', 'android-tools-adbd', 'android-tools-fastboot',
        'dos2unix',
    ])

    install_chromium()

    # zsh related
    execute('rm -f ~/.zshrc')
    execute('ln -s /workspace/project/gyagp/share/linux/.zshrc ~/')
    execute("sudo chsh -s /bin/zsh " + user)

    copy_file(".gitconfig", dir_home, 0)
    copy_file("servers", dir_home + "/subversion", 1)
    copy_file('.boto', dir_home, 1)
    copy_file(".bashrc", dir_home, 0)
    copy_file(".gdbinit", dir_home, 0)
    copy_file(".vimrc", dir_home, 0)

    copy_file('privoxy_config', '/etc/privoxy', 1)
    os.system('sudo mv -f /etc/privoxy/privoxy_config /etc/privoxy/config')

    overwrite_file("tsocks.conf", "/etc", 1)

    # This takes quite a long time
    #execute('sudo apt-file update' , show_progress=True)

    execute("ccache -M 10G")

    if profile == "direct":
        install_package(['openconnect', 'python-zsi'])

    # Chromium build
    #sudo ln -s /usr/include/x86_64-linux-gnu/asm /usr/include/asm
