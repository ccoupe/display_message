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

device = None

def do_quit():
  global mainwin
  mainwin.destroy()
  exit()

def main():
  global settings, hmqtt, log, device
  global device,saver_cvs,stroke_fill, screen_height, screen_width
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
  log = logging.getLogger('notify')
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
  
  settings = Settings(args["conf"], log)
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
      log.info(f"setargs is {setargs}")
      if setargs.get('font', False):
        device.set_font(setargs['font'])
      if setargs.get("stroke", False):
        device.set_stroke(setargs['stroke'])
      if setargs.get('blank', False):
        device.set_timeout(setargs['blank'])

  elif topic == settings.notetext_sub:
    device.display_text(payload)



if __name__ == '__main__':
  sys.exit(main())
