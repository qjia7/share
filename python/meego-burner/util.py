import os
import time
import re
import sys
import statvfs



def getAvailDisk(path):
    if not os.path.exists(path):
        return 0

    vfs = os.statvfs(path)
    avail = vfs[statvfs.F_BAVAIL] * 4.0 / 1000000
    return avail


scriptDir = sys.path[0]

workspace = scriptDir + "/workspace"
if not os.path.exists(workspace):
	r = os.system("mkdir -p " + workspace)
	if r != 0: 
		print("workspace couldn't be created");
		sys.exit(1)

#unit: kb
def get_free_disk_size():
	data = os.popen("sudo df").read()
	data = data[data.find("\n"):]
	data = data[:data.find("% /")]
	data = data[:data.rfind(" ")]
	data = data.strip()
	data = data[data.rfind(" "):]
	data = data.strip()
	info = float(data)
	info = info / 1000000
	print "The free disk size is: "+str(info)+" GB" 
	#print str
	return int(data)
	

def get_the_earlist_file(dir):
	files = os.listdir( dir )
	ret = ""
	name = ""
	for f in files:
		fn = dir+"/"+f		
		if os.path.isdir(fn):
			info = os.stat( fn )
			ctime = time.localtime( info.st_ctime )
			#print fn,
			#print time.mktime(ctime)
			if ret == "":
				ret = info
				name = fn
			else:
				t1 = time.localtime( ret.st_ctime )
				t2 = time.localtime( info.st_ctime )
				if time.mktime(t2) < time.mktime(t1):
					ret = info
					name = fn
	return name
	
def get_file_data(file):
	fo = open(file)
	data = fo.read()
	fo.close()
	return data

def write_data_to_file(data, file):
	if os.path.exists(file):
		fo = open(file, "w")
		fo.write(data)
		fo.close()
	else: print file, "does not exist."


if __name__=="__main__":
	print get_free_disk_size()


class image:
	def __init__(self):
		self.name = ""
		self.full_name = ""
		self.size = 0
		self.ctime = 0.0
		
	def info(self):
		print "{ ", self.name, self.full_name, self.size, self.ctime, "}"

#this function is called by burner.
def get_image_list(meego_images_path):
	files = os.listdir( meego_images_path )
	image_list = []	
	for f in files:
		fn = meego_images_path+"/"+f		
		if os.path.isdir(fn):
			bin = fn+"/"+f+"-sda.bin"
			fs2 = os.listdir( fn )
			if len(fs2) < 5: continue		# the image has not been extracted			
			if os.path.exists(bin):
				img = image()
				img.name = f+"-sda.bin"
				img.full_name = bin
				info = os.stat( bin )
				ctime = time.localtime( info.st_ctime )
				img.ctime = time.mktime(ctime)
				img.size = info.st_size
				#img.info()
				image_list.append(img)
	sort_by_time(image_list)
	return image_list

def sort_by_time(image_list):
	if len(image_list) < 2:	return
	for i in range(len(image_list)):
		for j in range(1, len(image_list) - i):
			if(image_list[j-1].ctime < image_list[j].ctime ):
				b = image_list[j-1]
				image_list[j-1] = image_list[j]
				image_list[j] = b



class disk:
	def __init__(self):
		self.disk = "/dev/sdb"
		self.id = ""
		self.size = 0
	
	def info(self):
		print "{ ", self.disk, self.size, self.id, "}"

# get current disk info (except sda)
def get_disk_list():
	data = os.popen("sudo fdisk -l").read()
	#parsing data
	rp = re.compile("Disk /dev/.*bytes")
	disks = rp.findall(data)
	disk_names = []
	sizes = []
	rp = re.compile("/dev/sd[a-z]")
	for d in disks:
		disk_names.append(rp.findall(d)[0])
		d = d[:d.rfind(" ")]
		d = d[d.rfind(" "):].strip()
		size = int(d)
		sizes.append(size)
		#print size
	rp = re.compile("Disk identifier.*\n")
	disks = rp.findall(data)
	ids = []
	for d in disks:
		d = d[d.rfind(" "):-1].strip()
		ids.append(d)
		#print d
	#create disk list
	disk_list = []
	for i in range(len(ids)):
		d = disk()
		d.disk = disk_names[i]
		d.id = ids[i]
		d.size = sizes[i]
		disk_list.append(d)
		#d.info()
	del disk_list[0]
	return disk_list


def find(sdname, disk_list):
	if len(disk_list) == 0: 
		return -1
	for i in range(len(disk_list)):
		if disk_list[i].disk == sdname:
			return i
	return -1


def getCurrentTime():
	return time.ctime()
