ufw sttus
ufw status
sudo ufw allow ssh
sudo ufw allow 22
ufw status
iptables -A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
ufw allow incoming
ufw allow 80/tcp
ufw allow 443/tcp
vim /etc/default/ufw
vim /etc/ufw/after.rules
ufw logging off
ufw allow 22/tcp
ufw enable
ufw allow ssh
ufw enable
ufw status
reboot now
ls
reboot now
ufw status
ufw deny 22
ufw status
exit
ufw statis
ufw status
sudo appt-get update
sudo apt-get update
ufw allow svn
ufw status
ufw allow git
ufw status
ufw allow out http
ufw allow in http 
ufw allow out https
ufw allow in https
ufw allow out 53
sudo apt-get update
ufw disable
sudo apt-get update
ufw enable
sudo apt-get update
ufw allow 53
sudo apt-get update
ufw status
ufw allow 123
sudo apt-get update
ufw allow 37
sudo apt-get update
ufw allow 101
sudo apt-get update
ufw allow 161
sudo apt-get updat
sudo apt-get update
sudo ufw default allow outgoing
sudo apt-get update
vim /etc/default/ssh 
vim /etc/default/ufw .
sudo apt-get update
sudo ufw allow 1725/udp
sudo apt-get update
ufw status
ufw loggin on
ufw logging on
ufw disable
ufw enable
sudo apt-get install vsftpd
ufw disable
sudo apt-get install vsftpd
vim /etc/vsftpd/conf
vim /etc/vsftpd.conf
sudo ufw allow 21/tcp
sudo ufw allow 990/tcp
sudo ufw allow 40000:50000/tcp
sudo adduser test
sudo mkdir /home/text/ftp
sudo mkdir /home/test/ftp
sudo chown nobody:nogroup /home/test/ftp
sudo chmod a-w /home/test/ftp
sudo ls -la /home/test/ftp
sudo mkdir /home/test/ftp/files
sudo chown test:test /home/test/ftp/files
sudo ls -la /home/test/ftp
echo "vsftpd test file" | sudo tee /home/sammy/ftp/files/test.txt
echo "vsftpd test file" | sudo tee /home/test/ftp/files/test.txt
sudo nano /etc/vsftpd.conf
cp /etc/vsftpd.conf ~/vsftpd.cong.bak
ls
vim /etc/vsftpd.conf 
echo "test" | sudo tee -a /etc/vsftpd.userlist
cat /etc/vsftpd.userlist
sudo systemctl restart vsftpd
ufw status
ufw enable
ufw status
vim /etc/vsftpd.conf 
tail -f /var/log/vsftpd.log 
ifconfig
tail -f /var/log/vsftpd.log 
vim /etc/vsftpd.conf 
service vsftpd restart
ufw disable
reboot now
tail -f /var/log/vsftpd.log 
ufw satus
ufw status
ufw enable
cp /etc/vsftpd.conf ~.vsftpd.conf.bak1
mv /etc/vsftpd.conf /etc/vsftpd.conf
mv -f /etc/vsftpd.conf /etc/vsftpd.conf
rm -rf /etc/vsftpd.conf
mv -f /etc/vsftpd.conf /etc/vsftpd.conf
mv  /etc/vsftpd.conf /etc/vsftpd.conf
mv vsftpd.conf.bak /etc/vsftpd.conf
mv ~/vsftpd.conf.bak /etc/vsftpd.conf
ls
cp vsftpd.cong.bak /etc/vsftpd.conf
service vsftpd restart
vim vsftpd.cong.bak 
ls
rm -rf /etc/vsftpd.conf 
cp \~.vsftpd.conf.bak1 /etc/vsftpd.conf
vim /etc/vsftpd.conf 
sudo service vsftpd restart
vim /etc/vsftpd.conf 
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/vsftpd.pem -out /etc/ssl/private/vsftpd.pem
sudo nano /etc/vsftpd.conf
sudo service vsftpd restart
ls
rm -rf \~.vsftpd.conf.bak1 
ls
mv vsftpd.cong.bak vsftpd.conf.bak 
mount
df
vim /etc/fstab
vim /etc/ssh/sshd_config 
reboot now
exit
vim /etc/vsftpd.
vim /etc/vsftpd.c
vim /etc/vsftpd.conf 
nano /etc/fstab
mount
nano /etc/fstab
df
nano /etc/fstab
mount -o remount,usrquota /home 
mount | grep quota
mount
vim /etc/fstab
mount -o remount,usrquota /home 
vim /etc/fstab
mount -o remount,usrquota /
mount | grep quota
df
modprobe quota_v2 echo 'quota_v2' >> /etc/modules
ufw disable
sudo apt-get install quota quotatool
pwd
cd /
ls
pwd
touch /aquota.user 
touch /aquota.group 
chmod 600 /home/aquota.user /home/aquota.group
chmod 600 /aquota.user /aquota.group
quotacheck -vagum
quotacheck -fvagum
sudo quotacheck -vagum
ufw enable
sudo quotacheck -vagum
Csudo fdisk -l
sudo fdisk -l
quotacheck -vagum -F vfsv0
sudo quotacheck -vagum -F vfsv0
sudo quotacheck -vagum vfsv0
sudo quotacheck -fvagum vfsv0
quotacheck -vagum
quotacheck -fvagum vfsv0
quotacheck -cfmvF vfsv0 /
ls
quotatool -u test -bq 100M -l '5 Mb' / 
quotacheck -fvagum
quotatool -u test -bq 100M -l '5 Mb' / 
/etc/init.d/quota start
quotatool -u test -bq 100M -l '5 Mb' / 
reboot now
quotatool -u test -bq 100M -l '5 Mb' / 
quotatool -u test -bq 4M -l '5 Mb' / 
repquota /
ls
repquota /
quotatool -u test -bq 100M -l '200 Mb' / quotatool -u test -bq 100M -l '200 Mb' / 
√ççççç
exit
quotacheck
repquota /
quotatool -u test -bq 0 -l 0 / 
repquota /
sudo userdel test
sudo rm -rf /home/test
ls
man useradd
useradd test
userdel test
python
cd /home/test
userdel shivam
userdel test
python
userdel shivam
userdel test
python 
useradd -p 22ue4Cugs68nw -s /bin/bash -m -d  /home/test
python
userdel test
python
userdel test
python
userdel test
python
vim /etc/vsftpd.userlist 
getent passwd
userdel shivam
userdel test
pythn
python 
userdel test
python 
userdel shivam
userdel test
python
userdel shivam
sudo deluser –remove-home test
man deluser
sudo  deluser --remove-all-files test
adduser test
cd /home/test
getent
getent /etc/passwd
su test
mkdir ftp
cd ftp
mkdir files
sudo deluser --remove-all-files tes
sudo deluser --remove-all-files test
cd /home/test
man deluser
useradd test -m -d "/home/test"
deluser test --remove-home test
cd ~/
ls
ls -al //hometest
ls -al /home/test
deluser test --remove-home test
userdel test
awk
awk -F
vim /etc/passwd
python
cd /home/test
su - test
mkdir ftp
ls
cd ftp
ls
userdel test
rm -rf /home/shivam
su - test
pytho
python
vim /etc/passwd
pyhon
python
ls -al /home/test
chown -R test /home/test
userdel test
python
cd /home/test
ls
ls -al
userdel test
adduser test
ls
ls -al
rm -rf ftp
mkdir ftp
mkdir ftp/files
chown -R test:test ftp/files 
usredel test
userdel test
python
ls -al
userdel test
python
ls -al
cd ~/
rm -rf /home/test
python
userdel test
python
cd /home/test
mkdir ftp/files
mkdir ftp
mkdir ftp/files
userdel shivam
userdel test
python
ls -al
chown -R test:test test
chown -R test:test ftp/files
userdel test
cd ~/
rm -rf /home/test
python
sudo su test
vim /etc/vsftpd.conf 
sudo service vsftpd restart
tail -f /var/log/vsftpd.log 
ls
sudo su test
userdel test
rm -rf /home/test
python
mkdir /home/test/ftp
mkdir /home/test/ftp/files
chown -R test:test /home/test/ftp/files
userdel test
rm -rf /home/test
python
sudo su - test
userdel test
rm -rf /home/test
adduser test
vim /etc/passwd
userdel test
python
userdel shivam
rm -rf /home/shivam
userdel test
rm -rf /home/test
pytho
python 
sudo su test
tail -f /var/log//vsftpd.log 
ls -al /home/test
vim ~/vsftpd.conf.bak 
vim /etc/vsftpd.
vim /etc/vsftpd.conf 
sudo service vsftpd restart
sudo passwd test
vim /etc/passwd
vim /etc/shadom
vim /etc/shadow
adduser shivam
vim /etc/shadow
vim /etc/passwd
vim /etc/group
rm -rf /home/test
python
vim /etc/passwd
cd /home/test
ls
mkdir ftp
mkdir ftp/files
chown -R test:test ftp/files
userdel test
rm -rf /home/test
userdel shivam
rm -rf /home/shivam
cd ~/
cd /home/test
python
vim /etc/passwd
useradd test
vim /etc/passwd
userdel test
cd /home/test
python
vim /etc/passwd
python
ping -c 2 www.google.com
ping -c 3 www.google.com
ls
ls -al
ls -l
python
ls
cd /home/test
ls
python
