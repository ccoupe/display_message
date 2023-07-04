from tkinter import *
from tkinter import ttk
from tkinter import font
#from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import sys
import json
import time
from lib.Settings import Settings
from lib.TkMessageDevice import TkMessageDevice
import argparse
import logging
import logging.handlers
import threading
from threading import Lock, Thread
import os
import sys

device = None
msg_thread = None

def main():
  global settings, device, log, msg_thread
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
        
  #tkroot = Tk()
  #win = Toplevel(tkroot)
  win = Tk()
  win.geometry("480x320")
  
  # Tkinter Window Configurations
  #device.wait_visibility(saver_cvs)
  win.wm_attributes('-alpha',1)
  win.wm_attributes("-topmost", False)
  #device.overrideredirect(1)
  #device.attributes('-fullscreen', True)
  win.attributes("-zoomed", True)
  
  
  msg_thread = threading.Timer(10, feed_msgs)
  msg_thread.start()
  
  device = TkMessageDevice(settings, window=win ,args={"width": 480, "height": 320})
  # get the new window (w = device.canvas)
  
  win.mainloop()
  
  #while True:
  #  time.sleep(10)
    
def feed_msgs():
  global device, log
  log.info("in feed_msgs")
  device.display_text("state cooling")
  exit()

if __name__ == '__main__':
  sys.exit(main())
