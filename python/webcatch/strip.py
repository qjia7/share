from util import *

dir_root = '/workspace/gytemp/large'

if __name__ == '__main__':
    os.chdir(dir_root)
    result = execute('find -maxdepth 1 -size +100M |xargs ls', return_output=True)
    files = result[1].split('\n')
    del files[-1]
    for file in files:
        print file
        execute('tar zxf ' + file)
        execute('rm -f ' + file)
        rev = file.replace('.tar.gz', '')
        rev = rev.replace('./', '')
        execute('strip ' + rev + '/chrome')
        execute('strip ' + rev + '/lib/*')
        execute('tar zcf ' + rev + '.tar.gz ' + rev)
        #execute('rm -rf ' + rev)
