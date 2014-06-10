#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

import re
import time
import os
import sys
import shutil

script_dir = sys.path[0]
check_dirs = [u'22月']

origin_dir = u'e:/storage/origin/'
storage_dir = 'e:/storage/'
googleplus_storage_dir = storage_dir + 'GooglePlus/'
skydrive_storage_dir = storage_dir + u'SkyDrive/顾诗云/'

ffmpeg = 'D:/software/active/ffmpeg/bin/ffmpeg.exe'

def info(msg):
    print '[INFO] ' + msg + '.'

def has_file(dir, name):
    files = os.listdir(dir)
    for file in files:
        if file == name:
            return True

    return False

def lock(name):
    f = open(name, 'w')
    f.close()

def unlock(name):
    os.remove(name)

def src_to_dest(src_dir, dest_dir):
    for check_dir in check_dirs:
        src_check_dir = src_dir + check_dir + '/'
        if not os.path.exists(src_check_dir):
            continue

        dest_check_dir = dest_dir + check_dir + '/'
        if not os.path.exists(dest_check_dir):
            os.mkdir(dest_check_dir)
        src_files = os.listdir(src_check_dir)
        for src_file in src_files:
            src_file_suffix = src_file[-4:].upper()
            src_file_path = src_check_dir + src_file
            if src_file_suffix == '.MOV':
                dest_file = src_file.replace(src_file[-4:], '.MP4')
            else:
                dest_file = src_file
            dest_file_path= dest_check_dir + dest_file

            if os.path.exists(dest_file_path):
                continue

            if src_file_suffix == '.JPG':
                info('Copy file ' + src_file_path + ' to ' + dest_file_path)
                shutil.copyfile(src_file_path, dest_file_path)
            elif src_file_suffix == '.MP4':
                if src_dir == origin_dir:
                    info('Copy file ' + src_file_path + ' to ' + dest_file_path)
                    shutil.copyfile(src_file_path, dest_file_path)
                else:
                    command = (ffmpeg + ' -i ' + src_file_path + ' -qscale 0 -s hd720 -f mp4 ' + dest_file + ' 2>>NUL').encode(sys.getfilesystemencoding())
                    info('Convert file ' + src_file_path + ' (1080P) to ' + dest_file_path + ' (720P)')
                    os.system(command)
                    os.rename(dest_file, dest_file_path)
            elif src_file_suffix == '.MOV':
                command = (ffmpeg + ' -i ' + src_file_path + ' -qscale 0 -s hd1080 -f mp4 ' + dest_file + ' 2>>NUL').encode(sys.getfilesystemencoding())
                info('Convert file ' + src_file_path + ' to ' + dest_file_path)
                os.system(command)
                os.rename(dest_file, dest_file_path)

if __name__ == '__main__':
    os.chdir(script_dir)
    lock_file = 'lock'
    if has_file(script_dir, lock_file):
        quit()

    #lock(lock_file)
    src_to_dest(origin_dir, googleplus_storage_dir)
    src_to_dest(googleplus_storage_dir, skydrive_storage_dir)
    #unlock(lock_file)

