#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import platform
import sys
import datetime
import argparse
import subprocess
import logging
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket
import inspect

import re
import commands

formatter = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
host_os = platform.system()
host_name = socket.gethostname()
args = argparse.Namespace()
dir_stack = []
timer = {}


def _get_real_dir(path):
    return os.path.split(os.path.realpath(path))[0]
dir_temp = _get_real_dir(__file__)
while not os.path.exists(dir_temp + '/.git'):
    dir_temp = _get_real_dir(dir_temp)
dir_share = dir_temp
dir_python = dir_share + '/python'
dir_linux = dir_share + '/linux'

target_os_all = ['android', 'linux']
target_arch_all = ['x86', 'arm']
target_module_all = ['webview', 'chrome', 'content_shell', 'chrome_stable', 'chrome_beta', 'webview_shell', 'chrome_shell', 'stock_browser']


def get_datetime(format='%Y%m%d%H%M%S'):
    return time.strftime(format, time.localtime())


def info(msg):
    print "[INFO] " + msg + "."


def warning(msg):
    print '[WARNING] ' + msg + '.'


def error(msg, abort=True, error_code=1):
    print "[ERROR] " + msg + "!"
    if abort:
        quit(error_code)


def cmd(msg):
    print '[COMMAND] ' + msg


# Used for debug, so that it can be cleaned up easily
def debug(msg):
    print '[DEBUG] ' + msg


# TODO: The interactive solution doesn't use subprocess now, which can not support show_progress and return_output now.
# show_command: Print command if Ture. Default to True.
# show_duration: Report duration to execute command if True. Default to False.
# show_progress: print stdout and stderr to console if True. Default to False.
# return_output: Put stdout and stderr in result if True. Default to False.
# dryrun: Do not actually run command if True. Default to False.
# abort: Quit after execution failed if True. Default to False.
# log_file: Print stderr to log file if existed. Default to ''.
# interactive: Need user's input if true. Default to False.
def execute(command, show_command=True, show_duration=False, show_progress=False, return_output=False, dryrun=False, abort=False, log_file='', interactive=False):
    if show_command:
        _cmd(command)

    if dryrun:
        return [0, '']

    start_time = datetime.datetime.now().replace(microsecond=0)

    if interactive:
        ret = os.system(command)
        result = [ret / 256, '']
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while show_progress:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        (out, err) = process.communicate()
        ret = process.returncode

        if return_output:
            result = [ret, out + err]
        else:
            result = [ret, '']

    if log_file:
        os.system('echo ' + err + ' >>' + log_file)

    end_time = datetime.datetime.now().replace(microsecond=0)
    time_diff = end_time - start_time

    if show_duration:
        info(str(time_diff) + ' was spent to execute following command: ' + command)

    if abort and result[0]:
        error('Failed to execute', error_code=result[0])

    return result


def bashify(command):
    return 'bash -c "' + command + '"'


def is_system(name):
    if host_os == name:
        return True
    else:
        return False


def is_windows():
    if is_system('Windows'):
        return True
    else:
        return False


def is_linux():
    if is_system('Linux'):
        return True
    else:
        return False


def has_process(name):
    r = os.popen('ps auxf |grep -c ' + name)
    count = int(r.read())
    if count == 2:
        return False

    return True


def shell_source(shell_cmd, use_bash=False):
    if use_bash:
        command = bashify('. ' + shell_cmd + '; env')
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    else:
        pipe = subprocess.Popen('. %s; env' % shell_cmd, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    for line in output.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value


# Get the dir of symbolic link, for example: /workspace/project/chromium-android instead of /workspace/project/gyagp/share/python
def get_symbolic_link_dir():
    if sys.argv[0][0] == '/':  # Absolute path
        script_path = sys.argv[0]
    else:
        script_path = os.getcwd() + '/' + sys.argv[0]
    return os.path.split(script_path)[0]


def backup_dir(new_dir):
    global dir_stack
    dir_stack.append(os.getcwd())
    os.chdir(new_dir)


def restore_dir():
    global dir_stack
    os.chdir(dir_stack.pop())


def package_installed(pkg):
    result = execute('dpkg -s ' + pkg, show_command=False)
    if result[0]:
        return False
    else:
        return True


# To send email on Ubuntu, you may need to install smtp server, such as postfix.
# type: type of content, can be plain or html
def send_mail(sender, to, subject, content, type='plain'):
    if not package_installed('postfix'):
        warning('Email can not be sent as postfix is not installed')
        return

    # Ensure to is a list
    if isinstance(to, str):
        to = [to]

    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = ','.join(to)
    msg['Subject'] = subject
    msg.attach(MIMEText(content, type))

    try:
        smtp = smtplib.SMTP('127.0.0.1')
        smtp.sendmail(sender, to, msg.as_string())
        info('Email was sent successfully')
    except Exception:
        error('Failed to send mail at ' + host_name, abort=False)
    finally:
        smtp.quit()


# upload file to specified samba server
def backup_smb(server, dir_server, file_local):
    result = execute('smbclient %s -N -c "prompt; recurse; cd %s; mput %s"' % (server, dir_server, file_local), interactive=True)
    if result[0]:
        warning('Failed to upload: ' + file_local)
    else:
        info('Succeeded to upload: ' + file_local)


def unsetenv(env):
    if env in os.environ:
        del os.environ[env]


def setenv(env, value):
    os.environ[env] = value


# Execute a adb shell command and know the return value
# adb shell would always return 0, so a trick has to be used here to get return value
def execute_adb(cmd, device=''):
    cmd_adb = 'adb'
    if device != '':
        cmd_adb += ' -s ' + device
    cmd_adb += ' shell "' + cmd + '|| echo FAIL"'
    result = execute(cmd_adb, return_output=True, show_command=False)
    if re.search('FAIL', result[1].rstrip('\n')):
        return False
    else:
        return True


# Setup devices and their names
def setup_device(devices_limit=[]):
    devices = []
    devices_name = []
    cmd = 'adb devices -l'
    device_lines = commands.getoutput(cmd).split('\n')
    for device_line in device_lines:
        if re.match('List of devices attached', device_line):
            continue
        elif re.match('^\s*$', device_line):
            continue

        pattern = re.compile('device:(.*)')
        match = pattern.search(device_line)
        if match:
            device_name = match.group(1)
            devices_name.append(device_name)
            device = device_line.split(' ')[0]
            devices.append(device)

    if devices_limit:
        for index, device in enumerate(devices):
            if device not in devices_limit:
                del devices[index]
                del devices_name[index]

    return (devices, devices_name)


def timer_start(tag):
    if not tag in timer:
        timer[tag] = [0, 0]
    timer[tag][0] = datetime.datetime.now().replace(microsecond=0)


def timer_end(tag):
    timer[tag][1] = datetime.datetime.now().replace(microsecond=0)


def timer_diff(tag):
    if tag in timer:
        return str(timer[tag][1] - timer[tag][0])
    else:
        return '0:00:00'


def get_caller_name():
    return inspect.stack()[1][3]


def connect_device(ip='192.168.42.1'):
    execute('adb disconnect %s && timeout 1s adb connect %s' % (ip, ip), interactive=True)
################################################################################


def _cmd(msg):
    print '[COMMAND] ' + msg
