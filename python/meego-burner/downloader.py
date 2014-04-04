#
# This script is writed to download the meego-debug-images from https://meego-images.jf.intel.com/acer// automatically.
#
# Author:
#	    Ma, Wentao <wentao.ma@intel.com>
#

import re
import os
import time
import util
import sys

workspace = util.workspace

# meego-images-url
MEEGO_IMAGES_URL = "https://meego-images.jf.intel.com/acer//"
USER_NAME = "yang.gu@intel.com"
PASSWD = "USYjLM42"
TIME_DLT = 3600				# touch the web page every TIME_DLT second
LEAST_FREE_SIZE = 12 	# least free disk size in Gigabyte

WPINFO_NEW = workspace+"/wpinfo.new"
if not os.path.exists(WPINFO_NEW):	os.system("touch "+WPINFO_NEW)
WPINFO_OLD = workspace+"/wpinfo.old"
if not os.path.exists(WPINFO_OLD):	os.system("touch "+WPINFO_OLD)
DOWNLOADLOG = workspace+"/download.log"
if not os.path.exists(DOWNLOADLOG):	os.system("touch "+DOWNLOADLOG)

class image:
	def __init__(self):
		self.name = ""
		self.debug = False
		self.ctime = 0
		self.tt = 0
		self.size = 0
						
	def info(self):
		print "{ ", self.name, self.debug, self.ctime, self.tt, self.size, "}"

def download(url, file_with_path):
	cmd = "wget --http-user="+USER_NAME+" --http-passwd="+PASSWD+" --no-check-certificate"
	cmd = cmd+" --output-document="+file_with_path
	cmd = cmd+" "+ url
	print cmd
	os.system(cmd)
		
# parsing page's info
def get_image_list(data):	
	imageList = []
	rp = re.compile("<a href=.*.tar.bz2.*\n")
	imlist = rp.findall(data)
	for link in imlist:
		rp = re.compile("meego.*.tar.bz2")
		name = rp.findall(link)[0]
		rp = re.compile("<a href.*</a>") 
		ahref = rp.findall(link)[0]
		ts = link.lstrip(ahref)
		ts = ts.partition("  ")
		ctime = ts[0].strip()
		size = ts[2].strip()
		isDebug = name.find("debug")!=-1
		#ls = name.partition(".")[2]
		ls = name[:name.rindex('.')]
		ls = ls[:ls.rindex('.')]
		tt = ls[ls.rindex('.')+1:]
		ls = ls[:ls.rindex('.')]
		ctime = ls[ls.rindex('.')+1:]
		img = image()
		img.name = name
		img.debug = isDebug
		img.ctime = int(ctime)
		img.tt = int(tt)
		img.size = size
		imageList.append(img)
	return imageList

def load_new_page_info():
	os.system("rm -f "+WPINFO_OLD)
	os.system("mv "+WPINFO_NEW+" "+WPINFO_OLD)
	os.system("touch "+WPINFO_NEW)
	download(MEEGO_IMAGES_URL, WPINFO_NEW)	

def load_image(img):
	#check disk free size
	free = util.getAvailDisk(workspace)
	if free < LEAST_FREE_SIZE:
		print "The free disk size is too small"
		fi = util.get_the_earlist_file(workspace)
		os.system("rm -rf "+fi)
	#download...	
	url = MEEGO_IMAGES_URL+img.name
	file = workspace+"/"+img.name
	print "Begin to download image"
	download(url, file)
	t = time.strftime( '%Y-%m-%d %X', time.localtime() )
	downlog = "["+t+"] " + img.name + " is downloaded"
	log_data = util.get_file_data(DOWNLOADLOG)
	util.write_data_to_file(log_data+"\n"+downlog, DOWNLOADLOG)
	#unpack	
	cmd = "tar jxvf "+file + " -C "+workspace
	print cmd
	os.system(cmd)
	cmd = "rm "+file
	print cmd
	os.system(cmd)

def touch_web():
	#print "touch the web page"
	load_new_page_info()
	new_data = util.get_file_data(WPINFO_NEW)
	old_data = util.get_file_data(WPINFO_OLD)
	if cmp(new_data, old_data) != 0:
		print util.getCurrentTime() + ": The web page has been updated"
		imglist = get_image_list(new_data)			
		for img in imglist:
			if not img.debug: continue				# only download debug version
			log_data = util.get_file_data(DOWNLOADLOG)
			if log_data.find(img.name) == -1:
				print "Begin to download " + img.name
				load_image(img)
			#else:
				#print img.name + " has been downloaded."
	else:
		print util.getCurrentTime() + ": The web page has no updating info"

	print "Waiting for new released image..."


while True:	
	touch_web()
	time.sleep(TIME_DLT)

