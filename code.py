# SPDX-FileCopyrightText: 2020 Richard Albritton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import board
import microcontroller
import displayio
import busio
from analogio import AnalogIn
import neopixel
import adafruit_adt7410
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_button import Button
import adafruit_touchscreen
from adafruit_pyportal import PyPortal
import adafruit_lsm9ds1
import adafruit_si7021
import adafruit_ds3231

# ------------- Inputs and Outputs Setup ------------- #
try:  # attempt to init. the temperature sensor
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    adt = adafruit_adt7410.ADT7410(i2c_bus)
    adt.high_resolution = True
except ValueError:
    # Did not find ADT7410. Probably running on Titano or Pynt
    adt = None

# init. the light sensor
light_sensor = AnalogIn(board.LIGHT)

'''
while not i2c_bus.try_lock():
    pass
print(i2c_bus.scan())
'''
hum = adafruit_si7021.SI7021(i2c_bus)
imu = adafruit_lsm9ds1.LSM9DS1_I2C(i2c_bus)
rtc = adafruit_ds3231.DS3231(i2c_bus)
#rtc.datetime = time.struct_time((2017, 1, 1, 0, 0, 0, 6, 1, -1))

# Lookup table for names of days (nicer printing).
#days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
days = ("Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun")
months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")#
#months = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")

if False:  # change to True if you want to set the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    current = time.struct_time((2022, 03, 09, 17, 23, 0, 5, -1, -1))
    # you must set year, mon, date, hour, min, sec and weekday
    # yearday is not supported, isdst can be set but we don't do anything with it at this time
    print("Setting time to:", current)  # uncomment for debugging
    rtc.datetime = current
    print()
# pylint: enable-msg=using-constant-test

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=1)
WHITE = 0xffffff
RED = 0xff0000
YELLOW = 0xffff00
GREEN = 0x00ff00
BLUE = 0x0000ff
PURPLE = 0xff00ff
BLACK = 0x000000

# ---------- Sound Effects ------------- #
soundDemo = '/sounds/sound.wav'
soundBeep = '/sounds/beep.wav'
soundTab = '/sounds/tab.wav'

# ------------- Other Helper Functions------------- #
# Helper for cycling through a number set of 1 to x.
def numberUP(num, max_val):
    num += 1
    if num <= max_val:
        return num
    else:
        return 1

# ------------- Screen Setup ------------- #
pyportal = PyPortal()
display = board.DISPLAY
display.rotation = 0

# Backlight function
# Value between 0 and 1 where 0 is OFF, 0.5 is 50% and 1 is 100% brightness.
def set_backlight(val):
    val = max(0, min(1.0, val))
    board.DISPLAY.auto_brightness = False
    board.DISPLAY.brightness = val

# Set the Backlight
if board.board_id == "pyportal_titano":
    # 0.3 brightness does not cause the display to be visible on the Titano
    set_backlight(1)
else:
    set_backlight(0.3)

# Touchscreen setup
# -------Rotate 0:
screen_width = 320
screen_height = 240

ts = adafruit_touchscreen.Touchscreen(board.TOUCH_XL, board.TOUCH_XR,
                                      board.TOUCH_YD, board.TOUCH_YU,
                                      calibration=((5200, 59000), (5800, 57000)),
                                      size=(screen_width, screen_height))

# ------------- Display Groups ------------- #
splash = displayio.Group()  # The Main Display Group
view1 = displayio.Group()  # Group for View 1 objects
view2 = displayio.Group()  # Group for View 2 objects
view3 = displayio.Group()  # Group for View 3 objects
view4 = displayio.Group()  # Group for View 4 objects
view5 = displayio.Group()  # Group for View 5 objects
view6 = displayio.Group()  # Group for View 6 objects

def hideLayer(hide_target):
    try:
        splash.remove(hide_target)
    except ValueError:
        pass

def showLayer(show_target):
    try:
        time.sleep(0.1)
        splash.append(show_target)
    except ValueError:
        pass

# ------------- Setup for Images ------------- #

# Display an image until the loop starts
pyportal.set_background('/images/loading.bmp')


bg_group = displayio.Group()
splash.append(bg_group)


icon_group = displayio.Group()
icon_group.x = 240
icon_group.y = 0
icon_group.scale = 1
view1.append(icon_group)

# This will handel switching Images and Icons
def set_image(group, filename):
    """Set the image file for a given goup for display.
    This is most useful for Icons or image slideshows.
        :param group: The chosen group
        :param filename: The filename of the chosen image
    """
    print("Set image to ", filename)
    if group:
        group.pop()

    if not filename:
        return  # we're done, no icon desired

    # CircuitPython 6 & 7 compatible
    image_file = open(filename, "rb")
    image = displayio.OnDiskBitmap(image_file)
    image_sprite = displayio.TileGrid(image, pixel_shader=getattr(image, 'pixel_shader', displayio.ColorConverter()))

    # # CircuitPython 7+ compatible
    # image = displayio.OnDiskBitmap(filename)
    # image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)

    group.append(image_sprite)

#set_image(bg_group, "/images/solid.bmp")

# ---------- Text Boxes ------------- #
# Set the font and preload letters
font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
font.load_glyphs(b'abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()') # pre-load glyphs for fast printing

# Default Label styling:
TABS_X = 5
TABS_Y = 5

# User 1 ###################################################################
############################################################################
user_group = displayio.Group(x=0, y=50, scale=1)
view1.append(user_group)

item1_group = displayio.Group(x=65, y=55, scale=1)
view1.append(item1_group)

item2_group = displayio.Group(x=100, y=55, scale=1)
view1.append(item2_group)

item3_group = displayio.Group(x=135, y=55, scale=1)
view1.append(item3_group)

item4_group = displayio.Group(x=170, y=55, scale=1)
view1.append(item4_group)

item5_group = displayio.Group(x=65, y=85, scale=1)
view1.append(item5_group)

home1_label = Label(font, x = TABS_X, y = TABS_Y+10, color=0xc29542, scale=2)
view1.append(home1_label)

home2_label = Label(font, x = TABS_X, y = TABS_Y+30, color=0xc29542)
view1.append(home2_label)

sensor_data = Label(font, x = TABS_X, y = 130, color=0xc29542)
view1.append(sensor_data)

stat_data = Label(font, x = TABS_X, y = 90, color=0xc29542)
view1.append(stat_data)

stat2_data = Label(font, x = 5, y = 45, color=0xFFFFFF)
view1.append(stat2_data)

# User 2 ###################################################################
############################################################################
user_group2 = displayio.Group(x=0, y=50, scale=1)
view2.append(user_group2)

item1_group2 = displayio.Group(x=65, y=55, scale=1)
view2.append(item1_group2)

item2_group2 = displayio.Group(x=100, y=55, scale=1)
view2.append(item2_group2)

item3_group2 = displayio.Group(x=135, y=55, scale=1)
view2.append(item3_group2)

item4_group2 = displayio.Group(x=170, y=55, scale=1)
view2.append(item4_group2)

item5_group2 = displayio.Group(x=65, y=85, scale=1)
view2.append(item5_group2)

home1_label2 = Label(font, x = TABS_X, y = TABS_Y+10, color=0xc29542, scale=2)
view2.append(home1_label2)

home2_label2 = Label(font, x = TABS_X, y = TABS_Y+30, color=0xc29542)
view2.append(home2_label2)

sensor_data2 = Label(font, x = TABS_X, y = 130, color=0xc29542)
view2.append(sensor_data2)

stat_data2 = Label(font, x = TABS_X, y = 90, color=0xc29542)
view2.append(stat_data2)

stat2_data2 = Label(font, x = 5, y = 45, color=0xFFFFFF)
view2.append(stat2_data2)

# User 3 ###################################################################
############################################################################
user_group3 = displayio.Group(x=0, y=50, scale=1)
view3.append(user_group3)

item1_group3 = displayio.Group(x=65, y=55, scale=1)
view3.append(item1_group3)

item2_group3 = displayio.Group(x=100, y=55, scale=1)
view3.append(item2_group3)

item3_group3 = displayio.Group(x=135, y=55, scale=1)
view3.append(item3_group3)

item4_group3 = displayio.Group(x=170, y=55, scale=1)
view3.append(item4_group3)

item5_group3 = displayio.Group(x=65, y=85, scale=1)
view3.append(item5_group3)

home1_label3 = Label(font, x = TABS_X, y = TABS_Y+10, color=0xc29542, scale=2)
view3.append(home1_label3)

home2_label3 = Label(font, x = TABS_X, y = TABS_Y+30, color=0xc29542)
view3.append(home2_label3)

sensor_data3 = Label(font, x = TABS_X, y = 130, color=0xc29542)
view3.append(sensor_data3)

stat_data3 = Label(font, x = TABS_X, y = 90, color=0xc29542)
view3.append(stat_data3)

stat2_data3 = Label(font, x = 5, y = 45, color=0xFFFFFF)
view3.append(stat2_data3)

# User 4 ###################################################################
############################################################################
user_group4 = displayio.Group(x=0, y=50, scale=1)
view4.append(user_group4)

item1_group4 = displayio.Group(x=65, y=55, scale=1)
view4.append(item1_group4)

item2_group4 = displayio.Group(x=100, y=55, scale=1)
view4.append(item2_group4)

item3_group4 = displayio.Group(x=135, y=55, scale=1)
view4.append(item3_group4)

item4_group4 = displayio.Group(x=170, y=55, scale=1)
view4.append(item4_group4)

item5_group4 = displayio.Group(x=65, y=85, scale=1)
view4.append(item5_group4)

home1_label4 = Label(font, x = TABS_X, y = TABS_Y+10, color=0xc29542, scale=2)
view4.append(home1_label4)

home2_label4 = Label(font, x = TABS_X, y = TABS_Y+30, color=0xc29542)
view4.append(home2_label4)

sensor_data4 = Label(font, x = TABS_X, y = 130, color=0xc29542)
view4.append(sensor_data4)

stat_data4 = Label(font, x = TABS_X, y = 90, color=0xc29542)
view4.append(stat_data4)

stat2_data4 = Label(font, x = 5, y = 45, color=0xFFFFFF)
view4.append(stat2_data4)

# User 5 ###################################################################
############################################################################
user_group5 = displayio.Group(x=0, y=50, scale=1)
view5.append(user_group5)

item1_group5 = displayio.Group(x=65, y=55, scale=1)
view5.append(item1_group5)

item2_group5 = displayio.Group(x=100, y=55, scale=1)
view5.append(item2_group5)

item3_group5 = displayio.Group(x=135, y=55, scale=1)
view5.append(item3_group5)

item4_group5 = displayio.Group(x=170, y=55, scale=1)
view5.append(item4_group5)

item5_group5 = displayio.Group(x=65, y=85, scale=1)
view5.append(item5_group5)

home1_label5 = Label(font, x = TABS_X, y = TABS_Y+10, color=0xc29542, scale=2)
view5.append(home1_label5)

home2_label5 = Label(font, x = TABS_X, y = TABS_Y+30, color=0xc29542)
view5.append(home2_label5)

sensor_data5 = Label(font, x = TABS_X, y = 130, color=0xc29542)
view5.append(sensor_data5)

stat_data5 = Label(font, x = TABS_X, y = 90, color=0xc29542)
view5.append(stat_data5)

stat2_data5 = Label(font, x = 5, y = 45, color=0xFFFFFF)
view5.append(stat2_data5)



map_group = displayio.Group(x=0, y=0, scale=1)
view6.append(map_group)


text_hight = Label(font, text="M", color=0x03AD31)
# return a reformatted string with word wrapping using PyPortal.wrap_nicely
def text_box(target, top, string, max_chars):
    text = pyportal.wrap_nicely(string, max_chars)
    new_text = ""
    test = ""
    for w in text:
        new_text += '\n'+w
        test += 'M\n'
    text_hight.text = test  # Odd things happen without this
    glyph_box = text_hight.bounding_box
    target.text = ""  # Odd things happen without this
    target.y = int(glyph_box[3]/2)+top
    target.text = new_text

# ---------- Display Buttons ------------- #
# Default button styling:
BUTTON_HEIGHT = 40
BUTTON_WIDTH = 80

# We want three buttons across the top of the screen
TAPS_HEIGHT = 40
TAPS_WIDTH = int(screen_width/3)
TAPS_Y = 0

# We want two big buttons at the bottom of the screen
BIG_BUTTON_HEIGHT = int(screen_height/5)
BIG_BUTTON_WIDTH = int(screen_width/2)
BIG_BUTTON_Y = int(screen_height-BIG_BUTTON_HEIGHT)
BUTTON_Y = int(screen_height-TAPS_HEIGHT)

# This group will make it easy for us to read a button press later.
buttons = []

# Main User Interface Buttons
button_view1 = Button(x=TAPS_WIDTH*2, y=0,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Crew1", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view1)  # adding this button to the buttons group

button_view2 = Button(x=TAPS_WIDTH*2, y=BUTTON_HEIGHT,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Crew2", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view2)  # adding this button to the buttons group

button_view3 = Button(x=TAPS_WIDTH*2, y=BUTTON_HEIGHT*2,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Crew3", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view3)  # adding this button to the buttons group

button_view4 = Button(x=TAPS_WIDTH*2, y=BUTTON_HEIGHT*3,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Crew4", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view4)  # adding this button to the buttons group

button_view5 = Button(x=TAPS_WIDTH*2, y=BUTTON_HEIGHT*4,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Crew5", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view5)  # adding this button to the buttons group

button_view6 = Button(x=TAPS_WIDTH*2, y=BUTTON_HEIGHT*5,
                      width=TAPS_WIDTH, height=TAPS_HEIGHT,
                      label="Map", label_font=font, label_color=0xff7e00,
                      fill_color=0x755e1e, outline_color=0x967824,
                      selected_fill=0xb08409, selected_outline=0xe3b536,
                      selected_label=0x402807)
buttons.append(button_view6)  # adding this button to the buttons group

'''
button_switch = Button(x=0, y=BIG_BUTTON_Y,
                       width=BIG_BUTTON_WIDTH, height=BIG_BUTTON_HEIGHT,
                       label="Switch", label_font=font, label_color=0xff7e00,
                       fill_color=0x755e1e, outline_color=0x967824,
                       selected_fill=0xb08409, selected_outline=0xe3b536,
                       selected_label=0x402807)
buttons.append(button_switch)  # adding this button to the buttons group

button_2 = Button(x=BIG_BUTTON_WIDTH, y=BIG_BUTTON_Y,
                  width=BIG_BUTTON_WIDTH, height=BIG_BUTTON_HEIGHT,
                  label="Button", label_font=font, label_color=0xff7e00,
                  fill_color=0x755e1e, outline_color=0x967824,
                  selected_fill=0xb08409, selected_outline=0xe3b536,
                  selected_label=0x402807)
buttons.append(button_2)  # adding this button to the buttons group
'''

# Add all of the main buttons to the splash Group
for b in buttons:
    splash.append(b)

'''
# Make a button to change the icon image on view2
button_icon = Button(x=150, y=60,
                     width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                     label="Icon", label_font=font, label_color=0xffffff,
                     fill_color=0x8900ff, outline_color=0xbc55fd,
                     selected_fill=0x5a5a5a, selected_outline=0xff6600,
                     selected_label=0x525252, style=Button.ROUNDRECT)
buttons.append(button_icon)  # adding this button to the buttons group

# Add this button to view2 Group
view2.append(button_icon)

# Make a button to play a sound on view2
button_sound = Button(x=150, y=140,
                      width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                      label="Sound", label_font=font, label_color=0xffffff,
                      fill_color=0x8900ff, outline_color=0xbc55fd,
                      selected_fill=0x5a5a5a, selected_outline=0xff6600,
                      selected_label=0x525252, style=Button.ROUNDRECT)
#buttons.append(button_sound)  # adding this button to the buttons group

# Add this button to view2 Group
view3.append(button_sound)
'''
#pylint: disable=global-statement
def switch_view(what_view):
    global view_live
    if what_view == 1:
        hideLayer(view2)
        hideLayer(view3)
        hideLayer(view4)
        hideLayer(view5)
        hideLayer(view6)
        button_view1.selected = False
        button_view2.selected = True
        button_view3.selected = True
        button_view4.selected = True
        button_view5.selected = True
        button_view6.selected = True
        showLayer(view1)
        view_live = 1
        print("View1 On")
    elif what_view == 2:
        hideLayer(view1)
        hideLayer(view3)
        hideLayer(view4)
        hideLayer(view5)
        hideLayer(view6)
        button_view1.selected = True
        button_view2.selected = False
        button_view3.selected = True
        button_view4.selected = True
        button_view5.selected = True
        button_view6.selected = True
        showLayer(view2)
        view_live = 2
        print("View2 On")
    elif what_view == 3:
        hideLayer(view1)
        hideLayer(view2)
        hideLayer(view4)
        hideLayer(view5)
        hideLayer(view6)
        button_view1.selected = True
        button_view2.selected = True
        button_view3.selected = False
        button_view4.selected = True
        button_view5.selected = True
        button_view6.selected = True
        showLayer(view3)
        view_live = 3
        print("View3 On")
    elif what_view == 4:
        hideLayer(view1)
        hideLayer(view2)
        hideLayer(view3)
        hideLayer(view5)
        hideLayer(view6)
        button_view1.selected = True
        button_view2.selected = True
        button_view3.selected = True
        button_view4.selected = False
        button_view5.selected = True
        button_view6.selected = True
        showLayer(view4)
        view_live = 4
        print("View4 On")
    elif what_view == 5:
        hideLayer(view1)
        hideLayer(view2)
        hideLayer(view3)
        hideLayer(view4)
        hideLayer(view6)
        button_view1.selected = True
        button_view2.selected = True
        button_view3.selected = True
        button_view4.selected = True
        button_view5.selected = False
        button_view6.selected = True
        showLayer(view5)
        view_live = 5
        print("View5 On")
    elif what_view == 6:
        hideLayer(view1)
        hideLayer(view2)
        hideLayer(view3)
        hideLayer(view4)
        hideLayer(view5)
        button_view1.selected = True
        button_view2.selected = True
        button_view3.selected = True
        button_view4.selected = True
        button_view5.selected = True
        button_view6.selected = False
        showLayer(view6)
        view_live = 6
        print("View6 On")


#pylint: enable=global-statement

# Set veriables and startup states
button_view1.selected = False
button_view2.selected = True
button_view3.selected = True
button_view4.selected = True
button_view5.selected = True
button_view6.selected = True
showLayer(view1)
hideLayer(view2)
hideLayer(view3)
hideLayer(view4)
hideLayer(view5)
hideLayer(view6)


view_live = 1
icon = 1
icon_name = "Ruby"
button_mode = 1
switch_state = 0
#button_switch.label = "OFF"
#button_switch.selected = True

# Update out Labels with display text.
#text_box(feed2_label, TABS_Y, 'Tap on the Icon button to meet a new friend.', 18)

set_image(user_group, "/images/male_young_hair_style_sunglasses_party.bmp")
set_image(item1_group, "/images/nav.bmp")
set_image(item2_group, "/images/wrench_screwdriver.bmp")
set_image(item3_group, "/images/head_set.bmp")
set_image(item4_group, "/images/flash_light_off_bolt_lightning.bmp")
set_image(item5_group, "/images/video_camera.bmp")

set_image(user_group2, "/images/male_young_party_sunglasses.bmp")
set_image(item1_group2, "/images/mars_rover.bmp")
set_image(item2_group2, "/images/medical_healthcare_firstaid.bmp")
set_image(item3_group2, "/images/head_set.bmp")
set_image(item4_group2, "/images/flash_light_off_bolt_lightning.bmp")
set_image(item5_group2, "/images/wrench_screwdriver.bmp")

set_image(user_group3, "/images/female_afro_hair_style_funk.bmp")
set_image(item1_group3, "/images/fly_flying_helicopter_transport.bmp")
set_image(item2_group3, "/images/ground_satelite_dish.bmp")
set_image(item3_group3, "/images/head_set.bmp")
set_image(item4_group3, "/images/video_camera.bmp")
set_image(item5_group3, "/images/flash_light_off_bolt_lightning.bmp")

set_image(user_group4, "/images/male_afro_hair_beard.bmp")
set_image(item1_group4, "/images/car_travel.bmp")
set_image(item2_group4, "/images/ground_satelite_dish.bmp")
set_image(item3_group4, "/images/interface_ui_plug_in_plugin.bmp")
set_image(item4_group4, "/images/head_set.bmp")
set_image(item5_group4, "/images/restaurant_food_dinner_lunch_knife_fork.bmp")

set_image(user_group5, "/images/male_punk_alternative_industrial_rock.bmp")
set_image(item1_group5, "/images/ship_sea_cruise_navigation.bmp")
set_image(item2_group5, "/images/ground_satelite_dish.bmp")
set_image(item3_group5, "/images/interface_ui_plug_in_plugin.bmp")
set_image(item4_group5, "/images/head_set.bmp")
set_image(item5_group5, "/images/mars_rover.bmp")

set_image(map_group, "/images/map2.bmp")
# ------------- Code Loop ------------- #
while True:
    touch = ts.touch_point
    light = light_sensor.value

    if adt:  # Only if we have the temperature sensor
        tempC = adt.temperature
    else:  # No temperature sensor
        tempC = microcontroller.cpu.temperature

    tempF = tempC * 1.8 + 32
    current = rtc.datetime

    sensor_data.text = 'Pulse: {}bpm\nResp: {}bpm\nTemp: {:.0f}°F\nHumidity: {:.0f}%'.format(52, 12, tempF, hum.relative_humidity)
    sensor_data2.text = 'Pulse: {}bpm\nResp: {}bpm\nTemp: {:.0f}°F\nHumidity: {:.0f}%'.format(67, 14, tempF, hum.relative_humidity)
    sensor_data3.text = 'Pulse: {}bpm\nResp: {}bpm\nTemp: {:.0f}°F\nHumidity: {:.0f}%'.format(88, 13, tempF, hum.relative_humidity)
    sensor_data4.text = 'Pulse: {}bpm\nResp: {}bpm\nTemp: {:.0f}°F\nHumidity: {:.0f}%'.format(92, 16, tempF, hum.relative_humidity)
    sensor_data5.text = 'Pulse: {}bpm\nResp: {}bpm\nTemp: {:.0f}°F\nHumidity: {:.0f}%'.format(77, 12, tempF, hum.relative_humidity)

    stat2_data.text = 'Johnson'
    stat2_data2.text = 'Ford'
    stat2_data3.text = 'Pearson'
    stat2_data4.text = 'Brown'
    stat2_data5.text = 'Shaw'

    home1_label.text = '{:02}:{:02}:{:02}'.format(current.tm_hour, current.tm_min, current.tm_sec)
    home1_label2.text = '{:02}:{:02}:{:02}'.format(current.tm_hour, current.tm_min, current.tm_sec)
    home1_label3.text = '{:02}:{:02}:{:02}'.format(current.tm_hour, current.tm_min, current.tm_sec)
    home1_label4.text = '{:02}:{:02}:{:02}'.format(current.tm_hour, current.tm_min, current.tm_sec)
    home1_label5.text = '{:02}:{:02}:{:02}'.format(current.tm_hour, current.tm_min, current.tm_sec)

    #home2_label.text = '{} {} {}, {}'.format(days[int(current.tm_wday)], months[int(current.tm_mon)], current.tm_mday, current.tm_year)

    # ------------- Handle Button Press Detection  ------------- #
    if touch:  # Only do this if the screen is touched
        # loop with buttons using enumerate() to number each button group as i
        for i, b in enumerate(buttons):
            if b.contains(touch):  # Test each button to see if it was pressed
                print('button%d pressed' % i)
                if i == 0 and view_live != 1:  # only if view1 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(1)
                    while ts.touch_point:
                        pass
                if i == 1 and view_live != 2:  # only if view2 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(2)
                    while ts.touch_point:
                        pass
                if i == 2 and view_live != 3:  # only if view3 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(3)
                    while ts.touch_point:
                        pass
                if i == 3 and view_live != 4:  # only if view4 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(4)
                    while ts.touch_point:
                        pass
                if i == 4 and view_live != 5:  # only if view5 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(5)
                    while ts.touch_point:
                        pass
                if i == 5 and view_live != 6:  # only if view6 is visable
                    pyportal.play_file(soundBeep)
                    switch_view(6)
                    while ts.touch_point:
                        pass
    board.DISPLAY.show(splash)