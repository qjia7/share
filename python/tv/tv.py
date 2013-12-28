#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

import urllib2
import re
import os
import commands
from sgmllib import SGMLParser
from httplib import BadStatusLine
import time
import datetime
import sys

import multiprocessing
from multiprocessing import Pool

import win32clipboard

# define each line of history
NAME = 0
FORMAT = 1
ID = 2
HISTORY = 3

PAUSE_STR = 'PAUSE'
END_STR = 'END'

URL_PREFIX = 'http://www.yyets.com/php/resource/'

# Enable debug mode or not
debug_mode = 0

# Enable multiprocess mode or not
mp_mode = 1

def get_time():
    return time.strftime('%Y-%m-%d %X', time.localtime(time.time()))

def copy_text_to_clipboard(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()

def update_line(lines, records, record_index):
    records_number = len(records)
    line_index = records[record_index]
    line = lines[line_index]
    fields = line.split(',')

    output_prefix = str(record_index + 1) + '/' + str(records_number) + ' ' + fields[NAME]

    # get the html
    if debug_mode:
        file = open(fields[ID] + '.htm')
        html = file.read()
    else:
        url = URL_PREFIX + fields[ID]
        try:
            u = urllib2.urlopen(url)
        except BadStatusLine:
            print 'Check failed'
            lines.append('== ' + fields[NAME] + ',Check failed,' + get_time() + ' ==\n')
            return (False, line_index, '', '')
        html = u.read()

    # Check if it has update
    xl_pattern = re.compile('thunderrestitle.*?迅')
    urls = xl_pattern.findall(html)

    format_pattern = re.compile(fields[FORMAT])
    episodePattern = re.compile('(' + fields[HISTORY][0:4] + '\d\d)')
    thunderPattern = re.compile('(thunder\:.*)\"')
    new = []
    for url in urls:
        # find all with relative format
        if format_pattern.search(url):
            # find all suitable episode
            episodeMatch = episodePattern.search(url)
            if not episodeMatch:
                continue
            currentEpisode = int(episodeMatch.group(0)[4:6])
            historyEpisode = int(fields[HISTORY][4:6])
            if currentEpisode <= historyEpisode:
                continue

            # get the link
            thunderMatch = thunderPattern.search(url)
            if not thunderMatch:
                continue
            r = []
            r.append(episodeMatch.group(0))
            r.append(thunderMatch.group(1))
            new.append(r)

    # Handle update
    if len(new) > 0:
        print ':) ' + output_prefix + ' has an update'

        line_new = line.replace(fields[HISTORY], new[len(new)-1][0]) + '\n'

        line_added_title = '== ' + fields[NAME] + ',' + new[0][0] + '-' + new[len(new)-1][0] + ',' + get_time() + ' ==\n'
        line_added_link = ''
        for new_index in range(0, len(new)):
            line_added_link = line_added_link + new[new_index][1] + '\n'

        return (True, line_index, line_new, line_added_title, line_added_link)
    else:
        print output_prefix + ' has no update'
        return (False, line_index, '', '', '')

def update_history():
    has_update = False

    # each item is the index of line to be checked
    records = []

    # Get lines
    if debug_mode:
        lines = ['Spar,人人影视.mp4,11176,S03E01', 'Homeland,rmvb,11088,S02E05']
    else:
        file = open('history.txt')
        lines = file.readlines()
        file.close()

    # Update records
    for line_index in range(0, len(lines)):
        # Skip blank line
        if not lines[line_index].strip():
            continue

        # Check if pause meets
        m = re.match(PAUSE_STR + ' (\d+-\d+-\d+ \d+:\d+:\d+)', lines[line_index])
        if m:
            diff = datetime.datetime.today() - datetime.datetime.strptime(m.group(1), '%Y-%m-%d %X')
            if diff.days < 30:
                break
            else:
                lines[line_index] = PAUSE_STR + ' ' + get_time() + '\n'
                continue

        # Check if end meets
        if re.search(END_STR, lines[line_index]):
            break

        # Append to records
        records.append(line_index)


    # Update line
    records_number = len(records)
    all_links = ''
    if mp_mode:
        process_number = min(multiprocessing.cpu_count(), records_number)
        pool = Pool(processes = process_number)
        results = []

        for record_index in range(0, records_number):
            line_index = records[record_index]
            line = lines[line_index]
            fields = line.split(',')
            output_prefix = str(record_index + 1) + '/' + str(records_number) + ' ' + fields[NAME]
            print output_prefix + ' is processing ...'

            results.append(pool.apply_async(update_line, (lines, records, record_index,)))

        print '\n'
        pool.close()
        pool.join()

        for i in results:
            r = i.get()
            if r[0] == True:
                lines[r[1]] = r[2]
                lines.append(r[3])
                lines.append(r[4])
                all_links += r[4]
                has_update = True

    else:
        for record_index in range(0, records_number):
            line_index = records[record_index]
            line = lines[line_index]
            fields = line.split(',')
            output_prefix = str(record_index + 1) + '/' + str(records_number) + ' ' + fields[NAME]
            print output_prefix + ' is processing ...'

            r = update_line(lines, records, record_index)
            if r[0] == True:
                has_update = True

    # Handle no update
    if not has_update:
        print 'There is no update at all!'
        lines.append('== All,No update,' + get_time() + ' ==\n')

    # Update history file
    if debug_mode:
        print lines
    else:
        os.chdir(sys.path[0])
        if os.path.exists('history_old.txt'):
            os.remove('history_old.txt')

        os.rename('history.txt', 'history_old.txt')

        f = open('history.txt', 'w')
        for line in lines:
            f.write(line)
        f.close()

        raw_input('Press <enter>')
        copy_text_to_clipboard(all_links)

if __name__ == '__main__':
    update_history()
