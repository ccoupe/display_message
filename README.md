## Install
  on the device (node), go to the mounted directory Projects/iot/dpymsg
  and 'make install"
  
### Create a Python virtual environment
pip -m venc dpyluma

pip insall paho-mqtt
pip install luma-core
pip install luma-oled  # for sh1106
pip install times

Edit dpyluma.sh to source that environment

------- LumaMessageDevice -------
SPI vs I2C vs Parallel - The sh1106 is i2c. The ili9846 (480x320) is SPI
and appears to use the 'normal' pi pins 


Wire up the Hosyond
  sudo usermod -a -G spi,gpio,i2c ccoupe
  
See if we get anything from the examples.
Update lib/LumaMessageDevice.py

It should work. Unless both Pi3's have bad gpio's - possible I guess
wire up the pi0 or the pi4 or ...

------- TkMessageDevice ---------
This is not a real screen saver. It's a [full screen] app.
~/Projects/iot/dpymsg - dpymac2.local - pi3 + hysond 480x320 screen
while waiting for the 640x480 waveshare screen to be repaired/replaced

sudo apt-get install python3-pil python3-pil.imagetk

export DISPLAY=:0.0 if using ssh (and we have to)

saver_cvs is the Tk window/frame we write the message to

1. Done: ~/.local/bin/blanking_off.sh: - ssh does not want to run this.
  blanking-off.service and systemd does run. Does not prevent blanking.
  After login /etc/xdg/systemd does work - It Stops blanking and screen-saver-starting!
  
export DISPLAY=:0.0
xset s off
xset s noblank
xset -dpms

2. Done: clear screen after 5 minutes w/o messages. Do our own 'screen saving'

3. compute baseline given Font. Tk is a bit weird  re: anchors
  Font 1 = 71 - just wrong. 72 is more correct but not enough.

4. Done: (partially) Really should be a class instead of so many global vars. Assuming we
want to keep the TK version. (and backport to TB?). Even better, a class
that both could call and compatible with pygame? 
--------------

Pygame seems able to use the framebuffer - kind of like the X11 root that
screensavers use? 
See 
* https://medium.com/@avik.das/writing-gui-applications-on-the-raspberry-pi-without-a-desktop-environment-8f8f840d9867
* http://www.karoltomala.com/blog/?p=679 for some ideas/thoughts

~/Projects/io/dpymac/rain.py demo for pygame.

Mqtt event loop and pygame - how will that work?
  create custom/user event - pygame.event.post()
  https://www.geeksforgeeks.org/how-to-add-custom-events-in-pygame/#
  
Ordered a Pygame book. Due 7/5/23. 
