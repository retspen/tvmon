#!/usr/bin/env	python
# -*- coding: utf8 -*-
#
# Copyright  2012 - X-systems
#
import os
import sys
import re
import smtplib
import MySQLdb
from time import strftime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mailsend(toaddr,text,subject):
    dtime = strftime("(%H:%M %d.%m.%y)")
    fromaddr = 'IPTV <user@mail.domain>'
    msg = MIMEMultipart()
    if subject == 'up':
        msg['Subject'] = 'IPTV Ok'
    else:
        msg['Subject'] = 'IPTV Problem'
    msg['From'] = fromaddr
    msg['To'] = toaddr
    mattch = MIMEText(text + ' ' + dtime, 'plain', 'utf-8')
    msg.attach(mattch)
    username = "username"
    password = "password"
    s = smtplib.SMTP('<mail.domain')
    s.login(username, password)
    s.sendmail(fromaddr, toaddr, msg.as_string())
    s.quit()

try:
    conn = MySQLdb.connect (host = "x.x.x.x",
                            user = "user",
                            passwd = "pass",
                            db = "iptv")
except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)

cursor = conn.cursor()
cursor.execute("SET NAMES utf8")
cursor.execute("SELECT id, name, cmd, tvmon_mail FROM itv WHERE status = 1")
rows = cursor.fetchall()

html = """<html>
<head>
<title>IPTV monitoring</title>
<meta http-equiv="refresh" content="600">
<style type="text/css">
body {
    margin: 0;
    padding: 0;
}
td {
    margin: 0;
    padding: 0;
    font: normal 14px Verdana, Arial, Helvetica, sans-serif;
    text-align: center;
}
</style>
</head>
<body>
<table border=0 cellspacing=0 cellpadding=0>"""

errors = ''
allows =  ''
html_name = ''
html_img = ''
newline = []

all_rows = len(rows) - 1

for num, row in enumerate(rows):
    channel = re.sub('^ffrt ','', row[2])
    os.system("timeout 7s cvlc %s --sout file/ts:/var/www/tvmon/video/stream.mpeg --run-time 4 --no-loop --no-repeat --play-and-exit > /dev/null 2>&1" % channel)
    filesize = os.path.getsize("/var/www/tvmon/video/stream.mpeg") / 1024
    img_path = "/var/www/vhost/tvmon/img/" + str(row[0]) + ".jpg"
    try:
        os.remove(img_path)
    except:
        pass

    if filesize < 900:
        cursor.execute("UPDATE itv SET tvmon_status=2 WHERE id=%s", (row[0]))
        if row[3] == 0: 
            cursor.execute("UPDATE itv SET tvmon_mail=1 WHERE id=%s", (row[0]))
            channel_name = row[1]
            if not errors:
                errors = channel_name 
            else:
                errors = errors + ', ' + channel_name
    else:
        os.system("ffmpeg -i /var/www/tvmon/video/stream.mpeg -s 80x40 -y -f mjpeg /var/www/vhost/tvmon/img/%s.jpg > /dev/null 2>&1" % row[0])
        cursor.execute("UPDATE itv SET tvmon_status=1 WHERE id=%s", (row[0]))
        if row[3] == 1: 
            cursor.execute("UPDATE itv SET tvmon_mail=0 WHERE id=%s", (row[0]))
            channel_name = row[1]
            if not allows:
                allows = channel_name 
            else:
                allows = allows + ', ' + channel_name
   
    html_name += "<td style='width:120px;height:25px;'>%s</td>\n" % row[1]
    
    try:
        img_size = os.path.getsize(img_path)
        if img_size != 0:
            html_img += "<td style='width:120px;'><img src='img/%s.jpg'></td>\n" % row[0]
        else:
            html_img += "<td style='width:120px;'><img src='img/error.gif'></td>\n"
    except:
         html_img += "<td style='width:120px;'><img src='img/error.gif'></td>\n"

    tr = [10,21,32,43,54,65,76,87,98]

    if num in tr or num == all_rows:
        newline.append("\n<tr>\n" + html_name + "</tr>\n<tr>\n" + html_img + "</tr>")
        html_name = ''
        html_img = ''
       
for line in newline:
    html += line

html += "\n</table>\n<br>\n</body>\n</html>"

index_file = open('/var/www/tvmon/index.html','w')
index_file.write(html)
index_file.close()

if errors:
    mailsend('user@mail.domain', errors, 'down')

if allows:
    mailsend('user@mail.domain', allows, 'up')

cursor.close()
conn.commit()
conn.close()