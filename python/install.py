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
# Run vncserver
# Set keyboard shortcut: "nautilus /workspace" -> ctrl+alt+E
# Set input method: gnome-session-properties

import os
import commands
from optparse import OptionParser

srcDir = "/workspace/project/gyagp/share/linux"
homeDir = os.getenv("HOME")
user = os.getenv("USER")
profile = ''


def info(msg):
    print "[INFO] " + msg + "."


def error(msg):
    print "[ERROR] " + msg + "!"


def patchSudo():
    sudoFile = "10_gyagp_sudo"
    (status, output) = commands.getstatusoutput("timeout 1s sudo cat /etc/sudoers.d/" + sudoFile)
    if status != 0:
        status = copyFile(sudoFile, "/etc/sudoers.d", 1)
        if status == 0:
            info("Now you can sudo without password")
            # No need to run following command to take effect
            #commands.getstatusoutput("/etc/init.d/sudo restart")
    else:
        info("You were able to sudo without password")


def copyFile(srcFile, destDir, sudo, srcSubDir=""):
    if cmp(srcSubDir, "") == 1:
        srcPath = srcDir + "/" + srcSubDir + "/" + srcFile
    else:
        srcPath = srcDir + "/" + srcFile

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

    (status, output) = commands.getstatusoutput(command)
    return status


def overwriteFile(srcFile, destDir, sudo, srcSubDir=""):
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

    status = copyFile(srcFile, destDir, sudo, srcSubDir)
    if status == 0:
        info(srcFile + " has replaced the original file successfully")
    else:
        error(srcFile + " didn't replace the original file successfully")

    return status


def installPackage(pkg):
    (status, output) = commands.getstatusoutput("dpkg -s " + pkg)
    if status != 0:
        info("Package " + pkg + " is installing...")
        (status, output) = commands.getstatusoutput("sudo apt-get install -y " + pkg)
        if status != 0:
            error("Package " + pkg + "'s installation failed")
            return -1
        else:
            return 0

    else:
        info("Package " + pkg + " was already installed")
        return -1


def parseOption():
    global profile

    parser = OptionParser()
    parser.add_option("-p", "--profile", dest="profile", help="designate profile", metavar="DIRECT|PROXY", default="PROXY")
    (options, args) = parser.parse_args()

    if options.profile.upper() == "DIRECT":
        profile = "DIRECT"
    elif options.profile.upper() == "PROXY":
        profile = "PROXY"
    else:
        error("The profile is not correct")
        exit(-1)


if __name__ == "__main__":
    global profile

    parseOption()

    # This should be done first
    patchSudo()

    # Update repo info
    #copyFile("apt.conf", "/etc/apt", 1);
    #copyFile("gyagp.list", "/etc/apt/sources.list.d", 1);
    #(status, output) = commands.getstatusoutput("cat /etc/apt/sources.list |grep 'ubuntu.com'");
    #if status == 0:
    #    (status, output) = commands.getstatusoutput("awk '{print $2}' /etc/issue");
    #    output = output[:-1];
    #    status = overwriteFile("sources.list", "/etc/apt", 1, "apt/" + output);
    #    if status == 0:
    #        os.system("sudo apt-get update");
    #else:
    #    info("/etc/apt/sources.list was already updated");

    status = installPackage("apt-file")
    if status == 0:
        commands.getstatusoutput("sudo apt-file update")

    if profile == "PROXY":
    # Install tsocks
        installPackage("tsocks")
        overwriteFile("tsocks.conf", "/etc", 1)
    # Install privoxy
        installPackage('privoxy')
        copyFile('privoxy_config', '/etc/privoxy', 1)
        os.system('sudo mv -f /etc/privoxy/privoxy_config /etc/privoxy/config')

    # Install Chrome, which needs to use tsocks
    (status, output) = commands.getstatusoutput("sudo apt-key list | grep 7FAC5991")

    if status:
        info("Get the key for Chrome...")

        # Not sure if the key would change, so get the online one in this profile
        if profile == "PROXY":
            command = "tsocks wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
        elif profile == "DIRECT":
            command = "cat " + srcDir + "/chrome_key_pub.txt | sudo apt-key add -"

        (status, output) = commands.getstatusoutput(command)
        if status != 0:
            error("Key for Chrome hasn't been added correctly")
    else:
        info("Key for Chrome has been added")

    installPackage("google-chrome-unstable")

    # zsh related
    status = installPackage("zsh")
    if status == 0:
        copyFile(".zshrc", homeDir, 0)
        # use sudo to bypass password input
        commands.getstatusoutput("sudo chsh -s /bin/zsh " + user)

    # git related
    installPackage("git")
    installPackage("git-svn")
    copyFile("connect", "/usr/bin", 1)
    copyFile("socks-gw", "/usr/bin", 1)
    copyFile("git.sh", "/etc/profile.d", 1)
    copyFile(".gitconfig", homeDir, 0)
    if profile == "PROXY":
        copyFile("servers", homeDir + "/subversion", 1)

    installPackage("gparted")
    installPackage("gnome-shell")
    installPackage("vim")
    installPackage("ssh")
    installPackage("most")
    installPackage("binutils-gold")
    installPackage("vnc4server")
    installPackage("cmake")
    installPackage("hibernate")
    # required by Chromium build
    installPackage("libspeechd-dev")
    installPackage('libgdk-pixbuf2.0-dev')
    installPackage('libgtk2.0-dev')
    installPackage('libdrm-dev')
    installPackage('libgnome-keyring-dev')
    installPackage('libgconf2-dev')
    installPackage('libudev-dev')
    installPackage('libpci-dev')
    installPackage('linux-tools')
    installPackage('binutils-dev')
    installPackage('libelf-dev')
    installPackage('gperf')
    installPackage('gcc-4.7-multilib')
    installPackage('g++-4.7-multilib')
    installPackage('bison')
    installPackage('python-pip')
    installPackage('module-assistant')
    installPackage('autoconf')
    installPackage('automake')
    #installPackage('')

    installPackage('python-boto')
    copyFile('.boto', '~/', 1)

    copyFile(".bashrc", homeDir, 0)
    copyFile(".gdbinit", homeDir, 0)
    copyFile(".vimrc", homeDir, 0)

    # ccache related
    installPackage("ccache")
    commands.getstatusoutput("ccache -M 10G")

    # specific steps for profile == "DIRECT"
    if profile == "DIRECT":
        installPackage("openconnect")
        installPackage("python-zsi")

    # Chromium build
    #sudo ln -s /usr/include/x86_64-linux-gnu/asm /usr/include/asm
