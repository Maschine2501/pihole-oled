#!/usr/bin/python3

import os, sys
import platform
import humanize
import psutil
import requests
import time

#imports for Display
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.sprite_system import framerate_regulator
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageSequence
from datetime import datetime

from fritzconnection.lib.fritzstatus import FritzStatus
from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.lib.fritzwlan import FritzWLAN
from fritzconnection.lib.fritzcall import FritzCall

interface = os.getenv('PIHOLE_OLED_INTERFACE', 'eth0')    #Network interface to retrieve the IP address
mount_point = os.getenv('PIHOLE_OLED_MOUNT_POINT', '/')    #Mount point for disk usage info
hostname = platform.node()

FritzPW = ''

fs = FritzStatus(address='192.168.178.1', password=FritzPW)
fc = FritzCall(address='192.168.178.1', password=FritzPW)
fw = FritzWLAN(address='192.168.178.1', password=FritzPW)
fh = FritzHosts(address='192.168.178.1', password=FritzPW)

serial = i2c(port=1, address=0x3C)
disp = ssd1306(serial)
serial2 = i2c(port=0, address=0x3C)
disp2 = ssd1306(serial2)
width = disp.width
height = disp.height

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

def load_font(filename, font_size):
    font_path = '/home/pi/PiHole-UI/fonts/'
    try:
        font = ImageFont.truetype(font_path + filename, font_size)
    except IOError:
        print('font file not found -> using default font')
        font = ImageFont.load_default()
    return font

font = load_font('Pixelate.ttf', 12)
font1 = load_font('Pixelate.ttf', 12)
font2 = load_font('Pixelate.ttf', 10)
font3 = load_font('PixelOperator.ttf', 10)
font4 = load_font('PixelOperator.ttf', 10)
font = load_font('PixelOperator.ttf', 10)
clockbold = load_font('DSG.ttf', 38)
datebold = load_font('DSG.ttf', 20)

def show_logoleft(filename, device):
    logoImage = Image.new('1', (device.width, device.height))
    img_path = '/home/pi/PiHole-UI/res/'
    try:
        logoImage = Image.open(img_path + filename).convert('1')
    except IOError:
        print("Cannot open file %s" % filename)
        pass
    disp.display(logoImage)

def show_logoright(filename, device):
    logoImage = Image.new('1', (device.width, device.height))
    img_path = '/home/pi/PiHole-UI/res/'
    try:
        logoImage = Image.open(img_path + filename).convert('1')
    except IOError:
        print("Cannot open file %s" % filename)
        pass
    disp2.display(logoImage)

def ClockDisplayL():
    draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
    draw.text((0, 13), time.strftime("%H:%M"), font=clockbold, fill=1)
    disp.display(image)
    time.sleep(-time.time() % 60)

def ClockDisplayR():
    draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
    draw.text((0, 13), 'Datum: ', font=font1, fill=1)
    draw.text((0, 31), time.strftime("%d.%m.%Y"), font=datebold, fill=1)
    disp2.display(image)
    time.sleep(-time.time() % 60)

def LS1():
   #1st Screen CPU/RAM/Uptime..
   addr = psutil.net_if_addrs()[interface][0]
   draw.text((0, 0), "Pi-hole %s" % addr.address.rjust(15), font=font2, fill=255)
   uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
   draw.text((0, 12), "Up: %s" % humanize.naturaltime(uptime), font=font2, fill=255)
   draw.text((0, 22), "    %.1f %.1f %.1f" % os.getloadavg(), font=font2, fill=255)
   cpu = int(psutil.cpu_percent(percpu=False))
   draw.text((0, 34), "CPU", font=font, fill=255)
   draw.rectangle((26, 34, 126, 34 + 6), outline=255, fill=0)
   draw.rectangle((26, 34, 26 + cpu, 34 + 6), outline=255, fill=255)
   mem = int(psutil.virtual_memory().percent)
   draw.text((0, 44), "RAM", font=font, fill=255)
   draw.rectangle((26, 44, 126, 44 + 6), outline=255, fill=0)
   draw.rectangle((26, 44, 26 + cpu, 44 + 6), outline=255, fill=255)
   disk = int(psutil.disk_usage(mount_point).percent)
   draw.text((0, 54), "Disk", font=font, fill=255)
   draw.rectangle((26, 54, 126, 54 + 6), outline=255, fill=0)
   draw.rectangle((26, 54, 26 + disk, 54 + 6), outline=255, fill=255 )
   disp.display(image)

def LS2():
   #2nd Screen PiHole Infos...
   req = requests.get('http://pi.hole/admin/api.php')
   data = req.json()
   draw.text((0, 0), "Pi-hole (%s)" % data["status"], font=font2, fill=255)
   draw.line((0, 12, width, 12), fill=255)
   draw.text((0, 22), "Blocked: %d (%d%%)" % (data["ads_blocked_today"], data["ads_percentage_today"]), font=font2, fill=255)
   draw.text((0, 32), "Queries: %d" % data["dns_queries_today"], font=font2, fill=255)
   draw.line((0, 50, width, 50), fill=255)
   draw.text((0, 54), "Blocklist: %d" % data["domains_being_blocked"], font=font2, fill=255)
   disp.display(image)

def RS1():
    #1st Fritzbox screen (uptime, up-/download)
    fbuptime = fs.str_uptime
    fbspeed = fs.str_max_bit_rate
    draw.text((0, 0), "Fritz.Box infos: ", font=font2, fill=255)
    draw.line((0, 10, width, 10), fill=255)
    draw.text((0, 14), "Uptime: ", font=font2, fill=255)
    draw.text((64, 14), fbuptime, font=font2, fill=255)
    draw.text((0,26), "Upload-Speed: ", font=font2, fill=255)
    draw.text((50,36), fbspeed[0], font=font2, fill=255)
    draw.text((0,46), "Download-Speed: ", font=font2, fill=255)
    draw.text((50,56), fbspeed[1], font=font2, fill=255)
    disp2.display(image)

def RS2():
    #2nd Fritzbox screen
    hosts = fh.host_numbers
    ssid = fw.ssid
    #missedcalls = FritzCall.get_missed_calls(update=True, num=10, days=7)
    draw.text((0, 0), "Fritz.Box infos: ", font=font2, fill=255)
    draw.line((0, 10, width, 10), fill=255)
    draw.text((0, 14), "SSID: ", font=font2, fill=255)
    draw.text((64, 14), ssid, font=font2, fill=255)
    draw.text((0,26), "Hosts: ", font=font2, fill=255)
    draw.text((50,36), str(hosts), font=font2, fill=255)
    draw.text((0,46), "missed calls: ", font=font2, fill=255)
    draw.text((50,56), "missedcalls", font=font2, fill=255)
    disp2.display(image)


def LeftLogo():
   show_logoleft("Pi-.bmp", disp)

def RightLogo():
   show_logoright("Hole.bmp", disp2)

def LeftGif():
    #Gifscreen for left display
    regulator = framerate_regulator(fps=10)
    left_path = '/home/pi/PiHole-UI/res/04L.gif'
    left = Image.open(left_path)
    size = [128, 64]
    posn = (0, 0)
    while True:
         for frame in ImageSequence.Iterator(left):
             with regulator:
                  background = Image.new("RGB", disp.size, "white")
                  background.paste(frame.resize(size, resample=Image.LANCZOS), posn)
                  disp.display(background.convert("1"))

def RightGif():
        #Gifscreen for right display
    regulator2 = framerate_regulator(fps=10)
    right_path = '/home/pi/PiHole-UI/res/04R.gif'
    right = Image.open(right_path)
    size = [128, 64]
    posn = (0, 0)

    while True:
         for frame in ImageSequence.Iterator(right):
             with regulator2:
                 background = Image.new("RGB", disp.size, "white")
                 background.paste(frame.resize(size, resample=Image.LANCZOS), posn)
                 disp2.display(background.convert("1"))


