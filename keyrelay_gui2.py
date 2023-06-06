import pygame
import sys
import serial
import time
import threading
import random
import subprocess
from AppKit import NSWorkspace # macOS specific
# from AppKit import NSScreen # macOS specific
from pynput import mouse

LEFT_CTRL = 0b00000001
LEFT_SHIFT = 0b00000010
LEFT_ALT = 0b00000100
LEFT_GUI = 0b00001000
RIGHT_CTRL = 0b00010000
RIGHT_SHIFT = 0b00100000
RIGHT_ALT = 0b01000000
RIGHT_GUI = 0b10000000

pygame_to_hid_lookup = {
    pygame.K_RETURN: 0x28,
    pygame.K_ESCAPE: 0x29,
    pygame.K_BACKSPACE: 0x2a,
    pygame.K_TAB: 0x2b,
    pygame.K_SPACE: 0x2c,
    pygame.K_MINUS: 0x2d,
    pygame.K_EQUALS: 0x2e,
    pygame.K_LEFTBRACKET: 0x2f,
    pygame.K_RIGHTBRACKET: 0x30,
    pygame.K_BACKSLASH: 0x31,
    pygame.K_SEMICOLON: 0x33,
    pygame.K_QUOTE: 0x34,
    pygame.K_BACKQUOTE: 0x35,
    pygame.K_COMMA: 0x36,
    pygame.K_PERIOD: 0x37,
    pygame.K_SLASH: 0x38,
    pygame.K_CAPSLOCK: 0x39,
    pygame.K_F1: 0x3a,
    pygame.K_F2: 0x3b,
    pygame.K_F3: 0x3c,
    pygame.K_F4: 0x3d,
    pygame.K_F5: 0x3e,
    pygame.K_F6: 0x3f,
    pygame.K_F7: 0x40,
    pygame.K_F8: 0x41,
    pygame.K_F9: 0x42,
    pygame.K_F10: 0x43,
    pygame.K_F11: 0x44,
    pygame.K_F12: 0x45,
    pygame.K_SYSREQ: 0x46,
    pygame.K_SCROLLLOCK: 0x47,
    pygame.K_PAUSE: 0x48,
    pygame.K_INSERT: 0x49,
    pygame.K_HOME: 0x4a,
    pygame.K_PAGEUP: 0x4b,
    pygame.K_DELETE: 0x4c,
    pygame.K_END: 0x4d,
    pygame.K_PAGEDOWN: 0x4e,
    pygame.K_RIGHT: 0x4f,
    pygame.K_LEFT: 0x50,
    pygame.K_DOWN: 0x51,
    pygame.K_UP: 0x52,
    pygame.K_NUMLOCK: 0x53,
    pygame.K_KP_DIVIDE: 0x54,
    pygame.K_KP_MULTIPLY: 0x55,
    pygame.K_KP_MINUS: 0x56,
    pygame.K_KP_PLUS: 0x57,
    pygame.K_KP_ENTER: 0x58,
    pygame.K_KP1: 0x59,
    pygame.K_KP2: 0x5a,
    pygame.K_KP3: 0x5b,
    pygame.K_KP4: 0x5c,
    pygame.K_KP5: 0x5d,
    pygame.K_KP6: 0x5e,
    pygame.K_KP7: 0x5f,
    pygame.K_KP8: 0x60,
    pygame.K_KP9: 0x61,
    pygame.K_KP0: 0x62,
    pygame.K_KP_PERIOD: 0x63,
    pygame.K_BACKSLASH: 0x64,
    pygame.K_MENU: 0x65,
    pygame.K_POWER: 0x66,
    pygame.K_KP_EQUALS: 0x67,
    pygame.K_F13: 0x68,
    pygame.K_F14: 0x69,
    pygame.K_F15: 0x6a,
    pygame.K_HELP: 0x75,
    pygame.K_MENU: 0x76
}

pygame_to_hid_mod_lookup = {
    pygame.K_LCTRL: LEFT_CTRL,
    pygame.K_LSHIFT: LEFT_SHIFT,
    pygame.K_LALT: LEFT_ALT,
    pygame.K_LMETA: LEFT_CTRL, # Remapped to LEFT_CTRL. Ori: LEFT_GUI
    pygame.K_RCTRL: RIGHT_CTRL,
    pygame.K_RSHIFT: RIGHT_SHIFT,
    pygame.K_RALT: RIGHT_ALT,
    pygame.K_RMETA: RIGHT_GUI
}

application_active = True

def is_current_application_active(): # macOS specific
    active_application = NSWorkspace.sharedWorkspace().activeApplication() #frontmostApplication()
    if active_application['NSApplicationName'] == 'Python':
        return True
    else:
        return False

def active_monitor_thread():
    global application_active
    while True:
        if is_current_application_active():
            application_active = True
        else:
            application_active = False
        time.sleep(0.5)

# def on_move(x, y):
#     print('Pointer moved to {0}'.format(
#         (x, y)))

# def on_click(x, y, button, pressed):
#     print('{0} at {1} {2}'.format(
#         'Pressed' if pressed else 'Released',
#         (x, y), button))

# def on_scroll(x, y, dx, dy):
#     print('Scrolled {0} at {1}'.format(
#         'down' if dy < 0 else 'up',
#         (x, y)))

def pygame_to_hid(pygame_key):
    hid_value = 0
    mod_byte = 0
    if pygame_key > 96 and pygame_key < 123: # alpha
        hid_value = pygame_key - 93
    elif pygame_key > 47 and pygame_key < 58: # number
        if pygame_key == 48: # KEY_0 HID=0x27, ASCII=0x30
            hid_value = pygame_key - 9
        else:
            hid_value = pygame_key - 19
    elif pygame_key > 1073742047 and pygame_key < 1073742056:
        mod_byte = pygame_to_hid_mod_lookup[pygame_key]
    else:
        hid_value = pygame_to_hid_lookup[pygame_key]

    return (hid_value, mod_byte)

def main():
    global application_active
    port = '/dev/tty.usbserial-01D29067'
    baud_rate = 115200
    ser = serial.Serial(port, baud_rate)

    pygame.init()
    app_icon = pygame.image.load('QuadCube_logo.png')
    pygame.display.set_icon(app_icon)
    pygame.display.set_caption("KeyRelay")

    # main_screen = NSScreen.mainScreen()
    # screen_width = int(main_screen.frame().size.width)
    # screen_height = int(main_screen.frame().size.height)
    # macOS does not support transparent background/overlay for pygame
    screen = pygame.display.set_mode((400, 300), pygame.SRCALPHA, pygame.NOFRAME)
    
    # pygame.display.set_alpha(128)
    # background_color = (41, 42, 47)
    # screen.fill(background_color)

    clock = pygame.time.Clock()
    running = True
    prev_key = None
    hid_buffer = [0, 0, 0, 0, 0, 0, 0, 0]
    prev_hid_buffer = [0, 0, 0, 0, 0, 0, 0, 0]
    mod_byte = 0x00
    current_display_input = 16 # mDP=16, HDMI1=17
    time_since_last_send = time.time()
    while running:
        _6kro_buffer = []
        
        for event in pygame.event.get():
            hid_value = 0
            if event.type == pygame.KEYUP:
                if event.key != pygame.K_PRINT:
                    hid_value, _mod_byte = pygame_to_hid(event.key)
                    if _mod_byte != 0:
                        hid_buffer[0] &= ~_mod_byte & 0xFF
                        # print(f"Key Released: {pygame.key.name(event.key)}")
                    if hid_value != 0:
                        for index in range(6):
                            if hid_buffer[index + 2] == hid_value:
                                hid_buffer[index + 2] = 0
                                # print(f"Key Released: {pygame.key.name(event.key)}")
                
            elif event.type == pygame.KEYDOWN:
                prev_key = event.key
                # print(f"Key Pressed: {event.key} {pygame.key.name(event.key)}")
                if event.key != pygame.K_PRINT:
                    hid_value, _mod_byte = pygame_to_hid(event.key)
                    hid_buffer[0] |= _mod_byte
                    _6kro_buffer.append(hid_value)
                    # print(f"Key Pressed: {event.key} {pygame.key.name(event.key)} [{mod_byte}] {hid_value}")
                else:
                    if current_display_input == 16: # mDP
                        current_display_input = 17
                    else:
                        current_display_input = 16
                    subprocess.run("ddcctl -d 2 -i " + str(current_display_input), shell=True, capture_output=False)
            elif event.type == pygame.QUIT:
                if prev_key in [113, 119]: # prevent Cmd+w/Cmd+q from closing the app
                    continue
                else:
                    running = False

        if _6kro_buffer != []:
            _6kro_buffer = _6kro_buffer[:6]
            _6kro_buffer = [elem for elem in _6kro_buffer if elem not in hid_buffer]
            for index in range(6):
                if hid_buffer[index + 2] == 0:
                    if _6kro_buffer:
                        hid_buffer[index + 2] = _6kro_buffer.pop(0)
                    else:
                        break

        if prev_hid_buffer != hid_buffer:
            ser.write(bytearray(hid_buffer))
            # print(prev_hid_buffer)
            prev_hid_buffer = list(hid_buffer)
            time_since_last_send = time.time()
            # print(hid_buffer)

        if application_active:    
            # Update the Pygame window
            # pygame.display.flip()
            clock.tick(60)

        else:
            if time.time() - time_since_last_send > (250 + random.uniform(30, 120)):
                ser.write(bytearray([1, 0, 0, 0, 0, 0, 0, 0]))
                time.sleep(0.5)
                ser.write(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
                time_since_last_send = time.time()
            clock.tick(20)

    # serial.close()
    pygame.quit()
    sys.exit()

# listener = mouse.Listener(
#     on_move=on_move,
#     on_click=on_click,
#     on_scroll=on_scroll)
# listener.start()

monitor_thread = threading.Thread(target=active_monitor_thread)
monitor_thread.daemon = True
monitor_thread.start()

if __name__ == '__main__':
    main()
