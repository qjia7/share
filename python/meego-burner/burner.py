#
# This script is writed to burn the meego image automatically.
#
# Author:
#		Ma, Wentao <wentao.ma@intel.com>
#

import os
import time
import threading
import pyudev
import re
import util

# create global path
workspace = util.workspace


TIME_DLT = 5			# detecting the sd card every TIME_DLT second
INTERRUPT_TIME = 20		# after pluging the sd card, you will have INTERRUPT_TIME second to interrupt.
MD = 20000000000

		
def burn(image, sd):
	#print "burning "+image+" to "+sd
	cmd = "nice -n 19 dd bs=1M if="+image+" of="+sd
	print cmd
	print "Please don't remove the sd card from the computer!"
	os.system(cmd)
	print "The image has been burned successfully.\n"

KEY_PRESS = False
def key_press():
	global KEY_PRESS
	try:
		input()
	except:
		KEY_PRESS = True

def get_choice(image_list):
	for i in range(len(image_list)):
		print "[", i, "] ", image_list[i].name
	print "[", i+1, "]  Don't burn any image"
	n = raw_input("enter your choice: ")
	#print n
	ret = -1
	try: ret = int(n)
	except: ret = -1
	if ret < 0 or ret > len(image_list):
		print "press input a number between 0 ~", len(image_list)-1
		ret = get_choice(image_list)
	return ret

def burn_to_sd(sdname):	
	image_list = util.get_image_list(workspace)
	if len(image_list) == 0:
		print "No meego images have been downloaded."
		return
	#get choice of burned images, default is the latest image
	global INTERRUPT_TIME, KEY_PRESS
	KEY_PRESS = False
	t1 = threading.Thread(target=key_press)
	t1.start()
	choice = 0
	i = 0
	while i != INTERRUPT_TIME:
		if KEY_PRESS: 
			KEY_PRESS = False
			choice = get_choice(image_list)
			break
		print "press 'Enter' to interrupt (", INTERRUPT_TIME-i, ")"
		i = i+1
		time.sleep(1)
	# compare the size
	if choice == len(image_list):
		return
	img = image_list[choice]
	sd_list = util.get_disk_list()
	index = util.find(sdname, sd_list) 
	sdsize = sd_list[index].size
	#print sdsize 
	if sdsize < MD and sdsize > img.size:
		burn(img.full_name, sdname)
	else:
		print "The sd's size is too small."


# main program begin
if __name__=="__main__":	
	context = pyudev.Context()
	monitor = pyudev.Monitor.from_netlink(context)
	rp = re.compile("/block/sd[a-z]'")
	print "waiting..."
	for action, device in monitor:
		if action == 'add':
			info = '{0!r} added'.format(device)
			ifos = rp.findall(info)
			if len(ifos) > 0:
				sdcard = ifos[0].replace("block", "dev")
				sdcard = sdcard[:len(sdcard)-1]
				burn_to_sd(sdcard)
				print "waiting..."


