from util import *

dir_root = '/workspace/project/gyagp/webcatch/out/android-x86-content_shell'

if __name__ == '__main__':
    os.chdir(dir_root)
    files = os.listdir('.')
    pattern = re.compile('ContentShell@(\d+).apk')
    for file in files:
        match = pattern.search(file)
        rev = match.group(1)
        if re.search('apk$', file):
            execute('mv ' + file + ' ' + rev + '.apk', dryrun=False)
        elif re.search('NULL$', file):
            execute('mv ' + file + ' ' + rev + '.NULL', dryrun=False)
        elif re.search('FAIL$', file):
            execute('mv ' + file + ' ' + rev + '.FAIL', dryrun=False)
