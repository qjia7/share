# -*- coding: utf-8 -*-

# Usage:
# t .*
#

import re
import os
from subprocess import Popen, PIPE, STDOUT

GREEN = '\033[0;32m'
RED = '\033[0;31m'
WHITE = '\033[1;37m'


# Below are related to commands
INDEX_TAG = 0
INDEX_COMMAND = 1
INDEX_DESCRIPTION = 2
INDEX_TYPE = 3


TYPE_NULL = 0  # command is not runnable
POS = 0
TYPE_RUNNABLE = 2 << POS
POS = POS + 1
TYPE_BUILTIN = 2 << POS  # command is shell built-in
POS = POS + 1

commands = [
    ('basic', r'find /tmp -type f -printf "%f\n"', 'Only print the file name', TYPE_RUNNABLE),
    ('basic', r'grep -r "str" ./', 'Search string in directory recursively', TYPE_RUNNABLE),
    ('basic', 'find ./ -type f | wc -l', 'Calculate number of files, including sub directory', TYPE_RUNNABLE),
    ('basic', 'sudo !!', 'Execute last command with sudo', TYPE_NULL),
    ('basic', r'^foo^bar', 'Replace str "foo" in last command with "bar"', TYPE_NULL),
    ('basic', r'!!:s/foo/bar', r'Replace str "foo" in last command with "bar"', TYPE_NULL),
    ('basic', 'cp filename{,.bk}', 'Backup file', TYPE_NULL),
    ('basic', r'history -r; history | awk \'{a[$2]++}END{for(i in a){print a[i] " " i}}\' | sort -rn | head', 'List 10 most used commands', TYPE_NULL),
    ('basic', r'history -r; history |grep cd', 'Test shell built-in command', TYPE_BUILTIN),
    ('basic', 'ps -p $$', 'Know current shell', TYPE_RUNNABLE),
    ('basic', 'tar czf - chromium | ssh gyagp@ubuntu-ygu5-02 "cd /workspace/project; tar xzf -"', 'tar and copy to another machine', TYPE_NULL),
    ('basic', 'tar czf - chromium | ssh gyagp@ubuntu-ygu5-02 "cat >/tmp/chromium.tar.gz"', 'tar and copy to another machine', TYPE_NULL),
    ('basic', 'tree -L 1 -i -d', 'list directories', TYPE_RUNNABLE),
    ('basic', 'command 2>&1 |tee log_file', 'direct stdout and stderror to both screen and file', TYPE_NULL),
    ('basic', 'gigolo', 'visit shared folder in Windows from Linux', TYPE_RUNNABLE),
    ('basic', "cat /proc/NNNN/maps | awk '{print $6}' | grep '\.so' | sort | uniq", 'see if a file is opened', TYPE_NULL),
    ('basic', "strace CMD.... 2>&1 | grep '^open(\".*\.so\"'", 'see if a file is opened', TYPE_NULL),
    ('basic', "lsof -p NNNN | awk '{print $9}' | grep '\.so'", 'see if a file is opened', TYPE_NULL),
    ('upgrade', 'do-release-upgrade', 'Upgrade system', TYPE_NULL),
    ('info', 'cat /etc/os-release', 'List distribution info', TYPE_RUNNABLE),
    ('info', 'cat /etc/lsb-release', 'List distribution info', TYPE_RUNNABLE),
    ('vi', ':w !sudo tee %', 'Write a readonly file in vi', TYPE_NULL),
    ('git', r'git log --summary 223286b.. | grep "Author:" | wc -l', 'Count git commits since specific commit', TYPE_RUNNABLE),
    ('git', r'git format-patch -1 hash', 'Generate patch for a specific hash', TYPE_RUNNABLE),
    ('repo', 'add-apt-repository ppa:gwibber-daily/ppa', 'Add repo', TYPE_NULL),
    ('repo', 'sudo tsocks apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 27F5B2C1B3EAC8D9 27F5B2C1B3EAC8D0', 'Import PPA key', TYPE_NULL),
    ('package', 'sudo apt-get install package-name:i386', 'Install 32-bit package on 64-bit system', TYPE_NULL),
    ('rpm', 'rpm -q <package_name>', 'See if the package is installed', TYPE_NULL),
    ('rpm', 'rpm -qi <package_name>', 'Info for installed package', TYPE_NULL),
    ('rpm', 'rpm -ql <package_name>', 'List files in installed package', TYPE_NULL),
    ('rpm', 'rpm -qf <package_name>', 'Find which package the file belongs to in the server', TYPE_NULL),
    ('rpm', 'rpm -ivh <package_name>', 'Install a package, -h show progress, -v show additional info', TYPE_NULL),
    ('rpm', 'rpm -Uvh <package_name>', 'Upgrade a package', TYPE_NULL),
    ('rpm', 'rpm -e <package_name>', 'Remove a package', TYPE_NULL),
    ('rpm', 'rpm -qilp <package_name>', 'List files without installation', TYPE_NULL),
    ('rpm', 'rpm -qa', 'List all installed package', TYPE_RUNNABLE),
    ('deb', 'dpkg -i <package_name>', 'Install deb package', TYPE_NULL),
    ('deb', 'cp /var/cache/apt/archives/file.deb /tmp', 'Copy cached deb file', TYPE_NULL),
    ('deb', 'dpkg -l xserver-xorg-core', 'xorg version', TYPE_RUNNABLE),
    ('deb', 'apt-cache show <package_name>', 'Show package info', TYPE_NULL),
    ('deb', 'apt-cache showpkg <package_name>', 'Show dependency', TYPE_NULL),
    ('deb', 'apt-cache policy <package_name>', 'Show status and version', TYPE_NULL),
    ('deb', 'apt-cache depends <package_name>', 'Show dependency', TYPE_NULL),
    ('deb', 'apt-cache rdepends <package_name>', 'Show reverse dependency', TYPE_NULL),
    ('deb', 'apt-file search <file_name>', 'Find package according to file name', TYPE_NULL),
    ('deb', 'pkg-config --modversion gtk+-2.0', 'Check version of module', TYPE_NULL),
    ('zypper', 'zypper si <package_name>', 'Install source package', TYPE_NULL),
    ('zypper', 'zypper wp <file_name>', 'Find package according to file name', TYPE_NULL),
    ('system', 'X -version', 'xorg version', TYPE_RUNNABLE),
    ('system', 'sudo sysv-rc-conf', 'services after system boot. Need to install package. Run level: 0 for halt, 1 for single user, 2-5 for multi-user (3 for character UI, 5 for GUI), 6 for reboot', TYPE_RUNNABLE),
    ('system', 'sudo dpkg-reconfigure gdm', 'switch between gdm and lightdm', TYPE_RUNNABLE),
    ('uncompress,rpm', 'rpm2cpio file.rpm | cpio -div', 'Uncompress rpm file', TYPE_NULL),
    ('uncompress,deb', 'dpkg-deb -x file.deb ./', 'Uncompress deb file', TYPE_NULL),
    ('uncompress', 'tar zxvf file.tar.gz', 'Uncompress tar.gz file', TYPE_NULL),
    ('uncompress', 'tar zxvf file.tgz', 'Uncompress tgz file', TYPE_NULL),
    ('uncompress', 'bunzip2 file.bz2', 'Uncompress bz2 file', TYPE_NULL),
    ('hardware', 'cat /proc/cpuinfo |grep -i -E "vmx|svm" |wc -l', 'virtualization support, >0 if support, vmx for Intel CPU, and svm for AMD CPU', TYPE_RUNNABLE),
    ('hardware', 'cat /proc/cpuinfo | grep flags | grep "lm"|wc -l', 'CPU 64bit support, >0 if support, lm means long mode. This command doesnt apply for CTP+', TYPE_RUNNABLE),
    ('hardware', 'cat /proc/cpuinfo |grep address', '36 bits physical, 48 bits virtual for 64-bit cpu', TYPE_RUNNABLE),
    ('hardware', 'getconf LONG_BIT', '32 or 64 bit system', TYPE_RUNNABLE),
    ('hardware', 'uname -a', '32 or 64 bit system, x86_64 for 64 bit system', TYPE_RUNNABLE),
    ('hardware', 'file /sbin/init', '32 or 64 bit system, ELF (32|64)-bit LSB executable', TYPE_RUNNABLE),
    ('hardware', 'file /system/xbin/init', '32 or 64 bit system', TYPE_RUNNABLE),
    ('hardware', 'lspci |grep VGA', 'Info of display card', TYPE_RUNNABLE),
    ('tool', 'alacarte', 'menu setting', TYPE_NULL),
    ('tool', 'killall Xvnc4 && vncserver :1 -geometry 1920x1080', 'Start vnc server', TYPE_NULL),
    ('network', 'sudo iftop -i wlan0', 'Network speed. Need to install', TYPE_RUNNABLE),
    ('network', 'sudo iptraf -g', 'Network speed. Need to install', TYPE_RUNNABLE),
    ('network', 'sar -n DEV 1 100', 'Network speed. 1 means 1 time per second, and 100 means to observe 100 times. Need to install sysstat', TYPE_RUNNABLE),
    ('network', 'watch -n 1 "/sbin/ifconfig wlan0 | grep bytes"', 'Network speed.', TYPE_RUNNABLE),
    ('network', 'lsof -Pnl +M -i4', 'List IPV4 connections', TYPE_NULL),
    ('network', 'netstat', '-l Show only listening sockets, -a All sockets, -p Show PID and name, -t tcp, -u udp, -x Unix sockets, -c timer', TYPE_NULL),
    ('misc', 'sudo apt-get remove flashplugin-installer', 'This package will hang all the time during update', TYPE_NULL),
    ('misc', 'watch -n1 -d prebuilts/misc/linux-x86/ccache/ccache -s', 'watch ccache usage', TYPE_NULL),
    ('misc', 'gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=all.pdf -dBATCH *.pdf', 'merge pdf', TYPE_RUNNABLE),
    ('perf', 'ps -e -o “%C : %p : %z : %a”|sort -k5 -nr', 'list processes sorted by memory usage', TYPE_NULL),
    ('perf', 'ps -e -o “%C : %p : %z : %a”|sort -nr', 'list processes sorted by CPU usage', TYPE_NULL),
    ('android', 'adb shell am start -a android.intent.action.MAIN -n com.android.chrome/.Main -d http://baidu.com', 'open web page with Chrome for Android', TYPE_NULL),
    ('python', 'pip install -U selenium', 'update python package', TYPE_NULL),
    ('python', 'su, and tsocks pip install selenium', 'use proxy and need sudo. sudo tsocks and tsocks sudo dont work', TYPE_NULL),
    ('', '', '', TYPE_NULL),
]

commands_cache = []

options = [
    ('t tag', 'Search command by tag'),
    ('d description', 'Search command by description'),
    ('r number', 'Run command with number'),
    ('c command', 'Run command directly'),
    ('q', 'Quit'),
]


def run_command(command, command_type):
    if not command_type & TYPE_RUNNABLE:
        print 'This is not a runnable command!'
        return

    # Need special handle for shell builtin command
    if command_type & TYPE_BUILTIN:
        command = 'bash -i -c "' + command + '"'
        print command
        event = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        print event.communicate()
    else:
        print command
        os.system(command)


def search(string, index_field):
    global commands_cache
    commands_cache = []

    for index_commands in range(0, len(commands)):
        if re.search(string, commands[index_commands][index_field], re.IGNORECASE):
            commands_cache.append(index_commands)

    for command_cache in commands_cache:
        command = commands[command_cache]
        print '[' + str(command_cache) + ']->' + ','.join(str(c) for c in command)

if __name__ == '__main__':
    prompt = GREEN + 'Please choose an option:\n'
    for o in options:
        prompt = prompt + o[0] + ': ' + o[1] + '\n'
    prompt = prompt + '\n' + RED

    while True:
        string = raw_input(prompt)
        if string == 'q':
            quit()

        print WHITE
        m = re.match('(t|d|r|c) (.+)', string)
        if not m:
            print 'Wrong input!'
            continue

        option_type = m.group(1)
        option_content = m.group(2).strip()
        if option_type == 't':
            search(option_content, INDEX_TAG)
        elif option_type == 'd':
            search(option_content, INDEX_DESCRIPTION)
        elif option_type == 'r':
            command_record = commands[int(option_content)]
            run_command(command_record[INDEX_COMMAND], command_record[INDEX_TYPE])
        elif option_type == 'c':
            run_command(option_content, TYPE_RUNNABLE)
