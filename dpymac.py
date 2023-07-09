from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import sys
import json
import time
from lib.Settings import Settings
from lib.Homie_MQTT import Homie_MQTT
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
    
  #pulse = pulsectl.Pulse('tblogin')
    
  tkroot = Tk()

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
  # create canvas 
  saver_cvs = Canvas(device, background='black', borderwidth = 0)
  saver_cvs.create_rectangle(0, 0, screen_width, screen_height, fill = 'black')
  saver_cvs.pack(expand="yes",fill="both")
 
  
  font1 = font.Font(family=settings.font1, size=settings.font1sz[0])
  font2 = font.Font(family=settings.font2, size=settings.font2sz[0])
  font3 = font.Font(family=settings.font3, size=settings.font3sz[0])
  fnt = settings.deflt_font
  set_font(fnt)
  stroke_fill = settings.stroke_fill
  '''
  for seq in ['<Any-KeyPress>', '<Any-Button> ', '<Any-Motion>']:
    device.bind_all(seq, saver_closing)
  '''
  # arrange toplevel windows
  saver_running = True
  #device.withdraw()
  #mainwin.state('normal')
  device.state('normal')
  log.info(f'starting mainloop fg: {device.state()}')
    
  # NOTE: mqtt messages seem to arrive just fine. Even though we
  # don't seem to accomodate them
  log.info('starting mqtt loop')
  mqtt_loop()
  #mainwin.mainloop()
  device.mainloop()
  
  while True:
    time.sleep(10)
  
def mqtt_loop():
  global hmqtt, log
  log.info('mqtt_loop-ing')
  hmqtt.client.loop_start()

  
def on_mqtt_msg(topic, payload):
  global log, settings, vid_widget, alarm_btn, voice_btn, laser_btn
  global login_btn, logoff_btn, turrets, mic_btn, mic_imgs, ranger_btn
  global pnl_hdr, status_hdr, msg_hdr, vlc_instance
  global saver_running, textLines, devLn, scroll_thread, devLns
  
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
      screenParseSettings(setargs)
  elif topic == settings.notetext_sub:
    #log.info(f"process message {payload}, saver: {saver_running}")
    saver_cvs.delete('all')
    # new timer for a new message
    set_blanking_timer()
    words = payload.split()
    nln = len(lnY)       # number of display lines 
    #log.info(f'nln: {nln} nwd: {words}')
    textLines = []
    if scroll_thread:
      scroll_thread.cancel()
    needscroll = layoutLines(textLines, devLns, len(words), words)
    if needscroll:
      # set 1 sec timer
      scroll_thread =  threading.Timer(1, scroll_timer_fired)
      scroll_thread.start()
      #log.info(f'setup scroll for {len(textLines)} lines')
      displayLines(0, devLns, textLines)
    else:
      displayLines(0, devLns, textLines)

          
#
# ------------------------Screensaver/notify -------
# TODO: clean up all the globals. Make a class or two or three
# really ugly with the scrooling and globals. Really.
# compute some settings based on font size and screen size

def screenParseSettings(dt):
  global devFnt, font1, font2, font3
  print(f'parseSettings: {dt}')
  if dt['font']:
    set_font(dt['font'])
    

def set_font(fnt):
  global log, devFnt, devLnH, settings, saver_cvs
  global screen_height, screen_width, lnY, font1, font2, font3
  global viewPortW, devLns
  lnY = []
  if fnt == 2:
    devFnt = font2
    devLnH = devFnt.metrics()['linespace'] 
    lns = 3
  elif fnt == 3:
    devFnt = font3
    devLnH = devFnt.metrics()['linespace']
    lns = 4
  else:
    devFnt = font1 
    devLnH = devFnt.metrics()['linespace'] 
    lns = 2
  fw = devFnt.measure('MWTH')/4
  lw = fw * 8;
  vh = (lns * devLnH) 
  yp = (screen_height-vh)/2
  viewPortW = lw
  for i in range(lns):
    lnY.append(yp)
    yp += devLnH
  devLns = lns  # number of lines on screen. Fixed by font choice. 
  log.info(f' {devLnH} {screen_width} X {screen_height}')
  log.info(f'lnY: {lnY}')


# returns True if we need to scroll 
def layoutLines(lns, nln, nwd, words):
  global viewPortW, devFnt, devLnH
  lns.clear()
  #log.info(f'layoutLines nln: {nln}, nwd: {nwd}, words: {words}')
  if nwd <= nln:
    y = 0
    for wd in words:
      wid = devFnt.measure(text=wd)
      lns.append(wd)
      y += devLnH
  else: 
    ln = ""
    wid = 0
    for wd in words:
      w = devFnt.measure(text=' ' + wd)
      if (wid + w) > viewPortW:
        lns.append(ln)
        wid = 0
        ln = ""
      if wid == 0:
        ln = wd
        wid = devFnt.measure(text=ln)
        #wid = w
        #log.info(f'first word |{ln}|{wid}')
      else:
        ln = ln+' '+wd
        wid = devFnt.measure(text=ln)
        #log.info(f'partial |{ln}|')

    # anything left over in ln ?
    if wid > 0:
      lns.append(ln)
  return len(lns) > nln
  
def saver_timer_fired():
  global saver_cvs, saver_thread
  log.info("should go blank - I hope")
  # set screen contents to all black. 
  saver_cvs.delete('all')
  # Remove message...
  # kill scrolling thread, if there is one
  if saver_thread:
    saver_thread.cancel()
    saver_thread = None
    
def set_blanking_timer():
  global saver_thread, blank_minutes
  if saver_thread: 
    # canel timer if exists
    saver_thread.cancel()
    saver_thread = None
    
  log.info(f"set timer for {blank_minutes} min")
  saver_thread =  threading.Timer((blank_minutes*60)-1, saver_timer_fired)
  saver_thread.start()

# Write everything to the screen. Depends on Tk centering 
# which can be confused.
# st is index (0 based), end 1 higher  
def displayLines(st, end, textLines):
  global device, devLnH, firstLine, screen_width,saver_cvs, lnY, devFnt
  global saver_thread, stroke_fill
  firstLine = st
  saver_cvs.delete('all')
  y = lnY[0]
  log.info(f'displayLines st: {st} end: {end} len: {len(textLines)}')
  # bug from layoutlines() is fixed up here with the min()
  for i in range(st, min(len(textLines), end)):
    #log.info(f"display {textLines[i]}")   
    saver_cvs.create_text(
      (screen_width / 2 ),
      y, 
      font=devFnt, fill=stroke_fill,
      anchor='n',
      justify='center',
      text = textLines[i])
    y += devLnH

# need to track the top line # displayed: global firstLine, 0 based.
def scroll_timer_fired():
  global firstLine, textLines, nlns, devLns, scroll_thread
  #log.info(f'scroll firstLine: {firstLine}')
  firstLine = firstLine + devLns
  maxl = len(textLines)
  if firstLine > maxl:
    # at the end, roll around
    firstLine = 0
  end = min(firstLine + devLns, maxl)
  displayLines(firstLine, end, textLines)
  scroll_thread =  threading.Timer(1, scroll_timer_fired)
  scroll_thread.start()

if __name__ == '__main__':
  sys.exit(main())
