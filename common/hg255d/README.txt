* 更新方法：
把e8_Config_backup拷贝到优盘根目录
192.168.1.1，在web上的"管理->设备管理"勾选启动usb自动恢复配置文件，然后点击重启设备。大约等个1-2分钟，设备重启完毕，就有了新的配置了。

* 目前配置
totalterminalnumber=15



****************************************************************
<config>
http://blog.xisix.com/post-83.html
* 插入u盘，备份
http://192.168.1.1/html/ehomeclient/cfgUSBRestore.cgi?coverusbpath=usb1_1
* IE打开crack.html，获取超级用户密码和宽带账号
telecomadmin, telecomadmin35646731
useradmin, fashion
PPPOE: ad48865435, 83783967 (sh.189.cn)

* 修改配置文件
@ 解除4台限制
config file里TotalTerminalNumber改成16，ComputerNumber改成13
<X_CT-COM_MWBAND Mode="1" TotalTerminalNumber="4" STBRestrictEnable="0" STBNumber="1" CameraRestrictEnable="0" CameraNumber="1" ComputerRestrictEnable="0" ComputerNumber="1" PhoneRestrictEnable="0" PhoneNumber="1"/>
@ 自定义SSID
config file SSID(只能修改config文件，web方式设置时必须"ChinaNet-"开头)
@ 开启FTP
config file
username: Anonymous password: 123456
@ 开启DMZ
@ 开启PNP: 缺省已经开启
@ 把改好的东西放到crack.html里面加密，拷贝到优盘备份目录。在web上的"管理->设备管理"勾选启动usb自动恢复配置文件，然后点击重启设备。大约等个1-2分钟，设备重启完毕，就有了新的配置了。

* 开启802.11n：网络->WLAN设置
* ipv6，选择DHCP，不知道是不是对，也不知道ipv6是不是有用。
*
网络->WLAN配置
802.11b/g/n
信道auto
SSID: ChinaNet-fashion
安全：WPA-PSK/WPA2-PSK,today

</config>


*********************************************************************

* http://bbs.pceva.com.cn/thread-17434-1-1.html
http://blog.sina.com.cn/s/blog_8a95fdf1010187w9.html

解除4台限制
InternetGatewayDevice.Services.X_CT-COM_MWBAND.Mode=0


自定义SSID
重启路由器后生效InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID=XiaoBu


开启802.11n(300M)
由Tintin提供InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.Standard=b,g,n&InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.X_ATP_Wlan11NGIControl=short&InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.X_ATP_Wlan11NBWControl=20/40&InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.X_ATP_11NHtMcs=33&InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.WPAWPA2EncryptionModes=AESEncryption


彻底关闭tr069（远程管理）InternetGatewayDevice.WANDevice.1.WANConnectionDevice.2.WANIPConnection.1.Enable=0&InternetGatewayDevice.ManagementServer.PeriodicInformEnable=0


开启DMZ主机
对于p2p下载和一些对战游戏有很大的好处，强烈建议开启。IP地址可按需修改。InternetGatewayDevice.WANDevice.1.WANConnectionDevice.3.WANPPPConnection.1.X_ATP_DMZ.DMZEnable=1&InternetGatewayDevice.WANDevice.1.WANConnectionDevice.3.WANPPPConnection.1.X_ATP_DMZ.DMZHostIPAddress=192.168.1.2


开启UPNP
这一项默认是开启的，一般不需要设置。InternetGatewayDevice.DeviceInfo.X_CT-COM_UPNP.Enable=1


开启FTP服务器InternetGatewayDevice.DeviceInfo.X_CT-COM_ServiceManage.FtpEnable=1


设置FTP服务器
用户名：InternetGatewayDevice.DeviceInfo.X_CT-COM_ServiceManage.FtpUserName=ftp


密码：InternetGatewayDevice.DeviceInfo.X_CT-COM_ServiceManage.FtpPassword=ftp


端口：InternetGatewayDevice.DeviceInfo.X_CT-COM_ServiceManage.FtpPort=21


路径：InternetGatewayDevice.DeviceInfo.X_CT-COM_ServiceManage.FtpPath=mnt


修改PPPOE拨号MAC地址InternetGatewayDevice.WANDevice.1.WANConnectionDevice.3.WANPPPConnection.1.MACAddress=00:00:00:00:00:00&InternetGatewayDevice.WANDevice.1.WANConnectionDevice.3.WANPPPConnection.1.MACAddressOverride=1


修改wlan的MAC地址(BSSID)InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.BSSID=00:00:00:00:00:00