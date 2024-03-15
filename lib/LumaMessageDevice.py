
from lib.demo_opts import get_device
#from luma.core.virtual import terminal
from luma.core.render import canvas
from PIL import Image,ImageDraw,ImageFont
import time, threading, sched

class LumaMessageDevice:
  '''
  Create a full screen window on a small LCD screen - tested with
  and shd1106 controller and Luma
  
  Settings argument is an object from lib/Settings which parses the json file
  
  message_device.display_text("text string") breaks the text into words 
  by whitespace and attempts to get the most number of words per line
  that will fit that line until the words are finished. It will the show
  those lines in the canvas. If the number of words is less than or equal
  to the number of lines on the display then the words are displayed on
  individual lines. 
  
  If there are more lines to display that window/canvas space allows then
  it will scroll additional lines in every second.
  
  After 5 minutes of no new messages the canvas will be cleared.
  There are some methods to change background and stroke colors and the
  current 'font' (one out of three predetermined sizes).
  
  Some arguments belong to Tk versions of this code. We don't use them
  for devices that use Luma librarys
  '''
  
  def __init__(self, settings, tkwindow = None, tkclose = None, args=None):
    self.log = settings.log
    self.devFnt = None
    self.devLnH = 16
    self.settings = settings
    self.canvas = None 
    self.screen_height = 100
    self.screen_width = 100
    self.lnY = []
    self.font1 = settings.font1
    self.font2 = settings.font2
    self.font3 = settings.font3
    self.viewPortW = None       # kind of best quess/max width
    self.devLns = None
    self.text_lines = []
    self.stroke_fill = ""       # color name
    self.background = settings.background
    self.blank_minutes = 5
    self.scroll_thread = None
    self.saver_thread = None
    self.cmdRun = None
    
    self.device = get_device(settings.luma_args)
    self.screen_width = self.device.width
    self.screen_height = self.device.height
    self.log.info(f'device: {self.screen_width} X {self.screen_height}')
    
    # Fonts and measurements
    self.font1 = ImageFont.truetype(settings.font1, settings.font1sz[0])
    self.font2 = ImageFont.truetype(settings.font2, settings.font2sz[0])
    self.font3 = ImageFont.truetype(settings.font2, settings.font3sz[0])
    '''
    self.font1 = font.Font(family=settings.font1, size=settings.font1sz[0])
    self.font2 = font.Font(family=settings.font2, size=settings.font2sz[0])
    self.font3 = font.Font(family=settings.font3, size=settings.font3sz[0])
    '''
    fnt = settings.deflt_font
    self.stroke_fill = settings.stroke_fill
    self.set_font(fnt)
    
    
  # 
  # ----------------- Visible (public)
  #
    
  def cmdOff(self, args):

    self.cmdRun = False
    self.log.info('cmdOff')
    self.device.hide()
    
  def cmdOn(self, args):

    self.cmdRun = True
    self.log.info('cmdOn')
    self.device.show()
  
  def display_text(self, payload):
    # should not have json for this call back
    if payload[0] == '{':
      self.log.warn("no json processed on text/set")
    self.device.clear()
    self.cmdRun = True
    words = payload.split()
    nwd = len(words)
    self.notify_timer(self.blank_minutes*60)
    self.device.show()
    self.textLines = []
    if self.scroll_thread:
      self.scroll_thread.cancel()
      
    self.needscroll = self.layoutLines(self.textLines, self.devLns, nwd, words)
    if self.needscroll:
      # set 1 sec timer
      self.scroll_thread =  threading.Timer(1, self.scroll_timer_fired)
      self.scroll_thread.start()
      #self.log.info(f'setup scroll for {len(textLines)} lines')
      self.displayLines(0, self.devLns, self.textLines)
    else:
      self.displayLines(0, self.devLns, self.textLines)
      
  def set_font(self, fnt):
    if fnt == 2:
      self.devFnt = self.font2
      self.devLnH = self.settings.font2sz[1] # ex: 16
    elif fnt == 3:
      self.devFnt = self.font3
      self.devLnH = self.settings.font3sz[1] # ex: 21
    else:
      self.devFnt = self.font1 
      self.devLnH = self.settings.font1sz[1] # ex: 32
    self.devLns = int(self.device.height/self.devLnH)     # number of lines = device.height/Font_Height
    self.log.info(f'devLnH: {self.devLnH}')
    self.log.info(f'devLns: {self.devLns}={self.device.height}/{self.devLnH}')
    
  def set_stroke(self, color_str):
    self.log.info(f"Setting stroke to {color_str}")
    self.stroke_fill = color_str
    
  def set_background(self, color_str):
    self.log.info(f'Setting background to {color_str}')
    self.background = color_str
    self.canvas.configure(background=self.background)
    
  def set_timeout(self, tmo):
    self.log.info(f"Setting blank time to {tmo}")
    self.blank_minutes = int(tmo)
    
  # --------- Private methods below ----------------------

  # returns True if we need to scroll 
  def layoutLines(self, lns, nln, nwd, words):
    lns.clear()
    self.log.info(f'layoutlines: {nln} {nwd} {words}')
    with canvas(self.device, dither=True) as draw:
      if nwd <= nln:
          y = 0
          for wd in words:
            #self.log.info(f"check width of {wd} with {self.devFnt}")
            wid = draw.textlength(wd, font=self.devFnt)
            lns.append(wd)
            y += self.devLnH
      else: 
        ln = ""
        wid = 0
        y = 0
        for wd in words:
          w = draw.textlength(' '+wd, font=self.devFnt)
          if (wid + w) > self.device.width:
            lns.append(ln)
            wid = 0
            ln = ""
            y += self.devLnH
          if wid == 0:
            ln = wd
            wid = w
            #self.log.info(f'first word |{ln}|{wid}')
          else:
            ln = ln+' '+wd
            wid = draw.textlength(ln, font=self.devFnt)
            #self.log.info(f'partial |{ln}|')
  
        # anything left over in ln ?
        if wid > 0:
          lns.append(ln)
          
    return len(lns) > nln


  # st is index (0 based), end 1 higher  
  def displayLines(self, st, end, textLines):
    self.firstLine = st
    self.device.clear()
    #self.log.info(f'dspL {st} {end}')
    if len(self.textLines) < end:
      end = len(self.textLines)
      #self.log.info(f'fixing up end to {end}')
    with canvas(self.device, dither=True) as draw:
      y = 0
      for i in range(st, end):
        wid = draw.textlength(self.textLines[i], font=self.devFnt)
        x = (self.device.width - wid)/2
        draw.multiline_text((x,y), self.textLines[i], font=self.devFnt, fill=self.stroke_fill)
        y += self.devLnH
  '''
  def leading(self, word):
  return int(max(0, (8 - len(word))/2))
  '''
  # need to track the top line # displayed: global firstLine, 0 based.
  def scroll_timer_fired(self):
    #global firstLine, textLines, nlns, devLns, scroll_thread
    #self.log.info(f'scroll firstLine: {firstLine}')
    self.firstLine = self.firstLine + self.devLns
    maxl = len(self.textLines)
    if self.firstLine > maxl:
      # at the end, roll over
      self.firstLine = 0
    end = min(self.firstLine + self.devLns, maxl)
    self.displayLines(self.firstLine, end, self.textLines)
    self.scroll_thread =  threading.Timer(1, self.scroll_timer_fired)
    self.scroll_thread.start()

  # no message for 5 minutes, stop the display and any scrolling
  def notify_timer_fired(self):
    #global scroll_thread, saver_thread
    self.saver_thread = None
    self.log.info('TMO fired')
    if self.scroll_thread:
      self.scroll_thread.cancel()
      self.scroll_thread = None
    self.device.hide()
  
  def notify_timer(self, secs):
    #global saver_thread
    if self.saver_thread:
      # reset unfired timer by canceling.
      self.saver_thread.cancel()
    
    self.saver_thread = threading.Timer(secs, self. notify_timer_fired)
    self.saver_thread.start()
  
