from tkinter import *
from tkinter import ttk
from tkinter import font
#from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import sys
import json
import time
from lib.Settings import Settings
from lib.Homie_MQTT import Homie_MQTT
from lib.TkMessageDevice import TkMessageDevice
#from lib.TurretSlider import TurretSlider
import argparse
import logging
import logging.handlers
import threading
from threading import Lock, Thread
import os
import sys
#import vlc
#import pulsectl

# some globals
isOSX = False
settings = None
hmqtt = None
mq_thr = None         # Thread for mqtt 
env_home = None       # env['HOME'] (/home/ccoupe)
os_home = None        # where this script started (/usr/local/lib/tblogin)
mainwin = None        # First Toplevel of root.
content = None        # First frame, contains menu_fr and panel_fr (frames)
menu_fr = None
panel_fr = None

# merging in Screen saver - HE Notify stuff
device = None
saver_running = False
devFnt = None
font1 = None
font2 = None
font3 = None
stroke_fill = 'white'
screen_width = None
screen_height = None
saver_cvs = None
lnY = []
screen_thread = None
saver_thread = None
scroll_thread = None
textLines =[]
devLns = 2
firstLine = 0
blank_minutes = 3
 
def do_quit():
  global mainwin
  mainwin.destroy()
  exit()

def main():
  global settings, hmqtt, log,  env_home, os_home, mq_thr, saver_running
  global mainwin,menu_fr,alarm_btn,voice_btn,laser_btn,login_btn,logoff_btn
  global mic_btn, mic_image, mic_muted,ranger_btn
  global menu_fr, panel_fr, center_img, pnl_middle, message
  global pnl_hdr, status_hdr, msg_hdr, content
  global device,saver_cvs,stroke_fill, screen_height, screen_width
  global font1,font2,font3,devFnt, mic_imgs
  if sys.platform == 'darwin':
    isOSX = True
    print('Darwin not really supported')
  ap = argparse.ArgumentParser()
  ap.add_argument("-c", "--conf", required=True, type=str,
    help="path and name of the json configuration file")
  ap.add_argument("-s", "--syslog", action = 'store_true',
    default=False, help="use syslog")

  args = vars(ap.parse_args())
  
  # logging setup
  log = logging.getLogger('tblogin')
  #applog.setLevel(args['log'])
  if args['syslog']:
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    # formatter for syslog (no date/time or appname. Just  msg, lux, luxavg
    formatter = logging.Formatter('%(name)s-%(levelname)-5s: %(message)-30s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
  else:
    logging.basicConfig(level=logging.DEBUG,datefmt="%H:%M:%S",format='%(asctime)s %(levelname)-5s %(message)-40s')

  env_home = os.getenv('HOME')
  os_home = os.getcwd()
  
  settings = Settings(args["conf"], 
                      log)
  settings.print()

  try:
    hmqtt = Homie_MQTT(settings, on_mqtt_msg)
  except:
    log.fail('failed mqtt setup')
    exit()
    
  tkroot = Tk()
  if settings.fullscreen: 
    # ----- Now the screen saver panel ---
    device = Toplevel(tkroot)
    
    # Tkinter Window Configurations
    #device.wait_visibility(saver_cvs)
    device.wm_attributes('-alpha',1)
    device.wm_attributes("-topmost", False)
    #device.overrideredirect(1)
    device.attributes('-fullscreen', True)
    device.attributes("-zoomed", True)
    #device.attributes("-toolwindow", 1)
    screen_width = device.winfo_screenwidth()
    screen_height = device.winfo_screenheight()
  else:
    # Tkinter Window Configurations
    tkroot.wm_attributes('-alpha',1)
    tkroot.wm_attributes("-topmost", False)
    screen_width = 480
    screen_height = 320
    tkroot.geometry("480x320")    
  # create canvas 
  device = TkMessageDevice(settings, window=tkroot,
      args={"width": screen_width, "height": screen_height})
  
  '''
  for seq in ['<Any-KeyPress>', '<Any-Button> ', '<Any-Motion>']:
    device.bind_all(seq, saver_closing)
  '''
  
  tkroot.state('normal')
  log.info(f'starting mainloop')
    
  # NOTE: mqtt messages seem to arrive just fine. Even though we
  # don't seem to accomodate them
  log.info('starting mqtt loop')
  mqtt_loop()

  tkroot.mainloop()
  
  while True:
    time.sleep(10)
  
def mqtt_loop():
  global hmqtt, log
  log.info('mqtt_loop-ing')
  hmqtt.client.loop_start()

  
def on_mqtt_msg(topic, payload):
  global log, settings, device
  
  log.info(f'on_mqtt: {topic} {payload}')
  #
  # Screen Saver text and commands
  #
  if topic == settings.notecmd_sub:
    args = json.loads(payload)
    cmd = args.get('cmd', None)
    setargs = args.get('settings', None);
    textargs = args.get('text')
    if cmd: 
      if cmd == 'on':
        screenCmdOn(args)
      elif cmd == 'off':
        screenCmdOff(args)
      elif cmd == 'update':
        log.info('ignoring update command')
      else:
        log.info("invalid command")
    elif setargs:
      if setargs.get('font', False):
        device.set_font(setargs['font'])
      elif setargs.get("stroke", False):
        device.set_stroke(setargs['stroke'])
  elif topic == settings.notetext_sub:
    device.display_text(payload)



if __name__ == '__main__':
  sys.exit(main())
