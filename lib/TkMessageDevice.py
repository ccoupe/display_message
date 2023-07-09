from tkinter import *
from tkinter import ttk
from tkinter import font
#from PIL import Image, ImageTk
#from threading import Lock, Thread
import time, threading, sched

class TkMessageDevice:
  '''
  Create a Tk top level window or accept one. The window can be created
  fullscreen with the args {'fullscreen": True}
  
  A canvas will be created of the specified size (if not fullscreen) the canvas
  will be pack'ed into the window.
  
  Settings argument is an object from lib/Settings which parse the json file
  
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
    
    if args.get('width', False):
      self.screen_width = args['width']
    else:
      self.screen_width = settings.width
    if args.get('height', False):
      self.screen_height = args['height']
    else:
      self.screen_height = settings.height
    
    if tkwindow is None:
      self.tkroot = Tk()
      self.device = self.tkroot #Toplevel(self.tkroot)
      
      # Tkinter Window Configurations
      self.device.wm_attributes('-alpha',1)
      self.device.wm_attributes("-topmost", False)
      if args.get('fullscreen',False):
        self.device.attributes('-fullscreen', True)
        self.screen_width = device.winfo_screenwidth()
        self.screen_height = device.winfo_screenheight()
      else:
        self.screen_width = args.get('width', 200)
        self.screen_height = args.get('height', 120)
        self.device.geometry(f"{self.screen_width}x{self.screen_height}")   
      self.device.attributes("-zoomed", True)
      self.device.state('normal')
    else:
      self.device = tkwindow
      self.log.info(f"Creating Child Window {self.screen_width}X{self.screen_height}")
      
    # create canvas 
    self.canvas = Canvas(self.device, background=self.background, borderwidth = 0)
    self.canvas.create_rectangle(0, 0, self.screen_width, self.screen_height,
        fill = self.background)
    self.canvas.pack(expand="yes",fill="both")
    
    # Fonts and measurements
    self.font1 = font.Font(family=settings.font1, size=settings.font1sz[0])
    self.font2 = font.Font(family=settings.font2, size=settings.font2sz[0])
    self.font3 = font.Font(family=settings.font3, size=settings.font3sz[0])
    fnt = settings.deflt_font
    self.stroke_fill = settings.stroke_fill
    self.set_font(fnt)
    
    if args.get('allow_escape', False):
      for seq in ['<Any-KeyPress>', '<Any-Button> ', '<Any-Motion>']:
        device.bind_all(seq, saver_closing)

    self.device.state('normal')
    
    if tkclose is not None:
      self.tkclose = tkclose
    else:
      self.tkclose = self.our_close
    self.device.protocol("WM_DELETE_WINDOW", self.tkclose)


    self.log.info("Leaving __init__")
    
  # 
  # ----------------- Visible (public)
  #
  
  def tk_loop(self):
    self.tkroot.mainloop()
    
  def display_text(self, message):
    # called with mqtt payload (a string of text)
    #log.info(f"display_text {payload}")
    self.canvas.delete('all')
    # new timer for a new message
    self.set_blanking_timer()
    words = message.split()
    nln = len(self.lnY)       # number of display lines 
    #log.info(f'nln: {nln} nwd: {words}')
    self.textLines = []
    if self.scroll_thread:
      self.scroll_thread.cancel()
    
    self.need_scrolling= self.layoutLines(self.devLns, len(words), words)
    if self.need_scrolling:
      # set 1 sec timer
      self.scroll_thread =  threading.Timer(1, self.scroll_timer_fired)
      self.scroll_thread.start()
      #log.info(f'setup scroll for {len(textLines)} lines')
      self.displayLines(0, self.devLns)
    else:
      self.displayLines(0, self.devLns)


  def set_font(self, fnt):
    self.lnY = []
    if fnt == 2:
      self.devFnt = self.font2
      self.devLnH = self.devFnt.metrics()['linespace'] 
      lns = 3
    elif fnt == 3:
      self.devFnt = self.font3
      self.devLnH = self.devFnt.metrics()['linespace']
      lns = 4
    else:
      self.devFnt = self.font1 
      self.devLnH = self.devFnt.metrics()['linespace'] 
      lns = 2
    fw = int(self.devFnt.measure('MWTH') / 4)
    lw = fw * 8;
    # anything larger than viewPortW, *may* cause a new line.
    self.viewPortW = min(self.screen_width,lw)
    #self.log.info(f"fw: {fw} self.viewPortW: {self.viewPortW}")
    vh = (lns * self.devLnH) 
    yp = (self.screen_height-vh)/2
    # array of line positions
    for i in range(lns):
      self.lnY.append(yp)
      yp += self.devLnH
    self.devLns = lns  # number of lines on screen. Fixed by font choice. 
    #self.log.info(f' {self.devLnH} {self.screen_width} X {self.screen_height}')
    self.log.info(f'lnY: {self.lnY}')
    
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
  
  def our_close(self):
    self.log.info("Destroy Window")
    self.tkroot.destroy()
    exit()
      
  def layoutLines(self, nln, nwd, words):
    # TODO: we don't need it to return anything.  
    # returns True if we need to scroll 
    self.textLines.clear()
    #log.info(f'layoutLines nln: {nln}, nwd: {nwd}, words: {words}')
    if nwd <= nln:
      y = 0
      for wd in words:
        wid = self.devFnt.measure(text=wd)
        self.textLines.append(wd)
        y += self.devLnH
    else: 
      ln = ""
      wid = 0
      for wd in words:
        w = self.devFnt.measure(text=' ' + wd)
        if (wid + w) > self.viewPortW:
          self.textLines.append(ln)
          wid = 0
          ln = ""
        if wid == 0:
          ln = wd
          wid = self.devFnt.measure(text=ln)
          #wid = w
          #log.info(f'first word |{ln}|{wid}')
        else:
          ln = ln+' '+wd
          wid = self.devFnt.measure(text=ln)
          #log.info(f'partial |{ln}|')
  
      # anything left over in ln ?
      if wid > 0:
        self.textLines.append(ln)
    self.need_scrolling = len(self.textLines) > nln
    return self.need_scrolling

  def saver_timer_fired(self):
    self.log.info("should go blank - I hope")
    # set screen contents to all black. 
    self.canvas.delete('all')

    # kill scrolling thread, if there is one
    if self.saver_thread:
      self.saver_thread.cancel()
      self.saver_thread = None
      
  def set_blanking_timer(self):
    if self.saver_thread: 
      # canel timer if exists
      self.saver_thread.cancel()
      self.saver_thread = None
      
    #self.log.info(f"set timer for {self.blank_minutes} min")
    self.saver_thread =  threading.Timer((self.blank_minutes*60)-1, self.saver_timer_fired)
    self.saver_thread.start()
    
  # need to track the top line # displayed: global firstLine, 0 based.
  def scroll_timer_fired(self):
    self.firstLine = self.firstLine + self.devLns
    maxl = len(self.textLines)
    if self.firstLine > maxl:
      # at the end, roll around
      self.firstLine = 0
    end = min(self.firstLine + self.devLns, maxl)
    self.displayLines(self.firstLine, end)
    # depends on the thread being destroyed by one shot nature of timer.
    # Safe assumption ?
    self.scroll_thread =  threading.Timer(1, self.scroll_timer_fired)
    self.scroll_thread.start()
      
  def displayLines(self, st, end):
    self.firstLine = st
    self.canvas.delete('all')
    y = self.lnY[0]
    #self.log.info(f'displayLines st: {st} end: {end} len: {len(self.textLines)}')
    # bug from layoutlines() is fixed up here with the min()
    for i in range(st, min(len(self.textLines), end)):
      self.canvas.create_text(
        (self.screen_width / 2 ),
        y, 
        font=self.devFnt, fill=self.stroke_fill,
        anchor='n',
        justify='center',
        text = self.textLines[i])
      y += self.devLnH
  
