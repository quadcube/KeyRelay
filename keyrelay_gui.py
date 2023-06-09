import tkinter as tk
import sys
import serial
import time
import random
import subprocess
from AppKit import NSEvent # macOS specific
from Quartz import CGEventMaskBit, CGEventGetIntegerValueField, CGAssociateMouseAndMouseCursorPosition, CFRunLoopGetCurrent, CFMachPortCreateRunLoopSource, CFRunLoopAddSource, CGWarpMouseCursorPosition, CGEventTapCreate, CFRunLoopRemoveSource, CFRelease, CGEventTapEnable, CFRunLoopRun, CFRunLoopRunInMode
from Quartz import kCGEventMouseMoved, kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventLeftMouseDragged, kCGEventRightMouseDown, kCGEventRightMouseUp, kCGEventRightMouseDragged, kCGEventOtherMouseDown, kCGEventOtherMouseUp, kCGEventOtherMouseDragged, kCGEventScrollWheel, kCGEventKeyDown, kCGEventKeyUp, kCGMouseEventDeltaX, kCGMouseEventDeltaY, kCGScrollWheelEventDeltaAxis1, kCGScrollWheelEventDeltaAxis2
from Quartz import kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault, kCFRunLoopDefaultMode, kCGKeyboardEventKeycode, kCGEventFlagsChanged, kCGEventFlagMaskShift, kCGEventFlagMaskControl, kCGEventFlagMaskAlternate, kCGEventFlagMaskCommand, CGEventGetFlags
import struct

mouse_events = (
    CGEventMaskBit(kCGEventMouseMoved) |
    CGEventMaskBit(kCGEventLeftMouseDown) |
    CGEventMaskBit(kCGEventLeftMouseUp) |
    CGEventMaskBit(kCGEventLeftMouseDragged) |
    CGEventMaskBit(kCGEventRightMouseDown) |
    CGEventMaskBit(kCGEventRightMouseUp) |
    CGEventMaskBit(kCGEventRightMouseDragged) |
    CGEventMaskBit(kCGEventOtherMouseDown) |
    CGEventMaskBit(kCGEventOtherMouseUp) |
    CGEventMaskBit(kCGEventOtherMouseDragged) |
    CGEventMaskBit(kCGEventScrollWheel))
    
keyboard_events = (
    CGEventMaskBit(kCGEventKeyDown) |
    CGEventMaskBit(kCGEventKeyUp) |
    CGEventMaskBit(kCGEventFlagsChanged))

macOS_to_hid_lookup = {
    0x00: 0x04,  # A
    0x01: 0x16,  # S
    0x02: 0x07,  # D
    0x03: 0x09,  # F
    0x04: 0x0B,  # H
    0x05: 0x0A,  # G
    0x06: 0x1D,  # Z
    0x07: 0x1B,  # X
    0x08: 0x06,  # C
    0x09: 0x19,  # V
    0x0B: 0x05,  # B
    0x0C: 0x14,  # Q
    0x0D: 0x1A,  # W
    0x0E: 0x08,  # E
    0x0F: 0x15,  # R
    0x10: 0x1C,  # Y
    0x11: 0x17,  # T
    0x12: 0x1E,  # 1
    0x13: 0x1F,  # 2
    0x14: 0x20,  # 3
    0x15: 0x21,  # 4
    0x16: 0x23,  # 6
    0x17: 0x22,  # 5
    0x18: 0x2E,  # Equal
    0x19: 0x26,  # 9
    0x1A: 0x24,  # 7
    0x1B: 0x2D,  # Minus
    0x1C: 0x25,  # 8
    0x1D: 0x27,  # 0
    0x1E: 0x30,  # RightBracket
    0x1F: 0x12,  # O
    0x20: 0x18,  # U
    0x21: 0x2F,  # LeftBracket
    0x22: 0x0C,  # I
    0x23: 0x13,  # P
    0x25: 0x0F,  # L
    0x26: 0x0D,  # J
    0x27: 0x34,  # Quote
    0x28: 0x0E,  # K
    0x29: 0x33,  # Semicolon
    0x2A: 0x31,  # Backslash
    0x2B: 0x36,  # Comma
    0x2C: 0x38,  # Slash
    0x2D: 0x11,  # N
    0x2E: 0x10,  # M
    0x2F: 0x37,  # Period
    0x32: 0x35,  # Grave
    0x24: 0x28,   # kVK_Return
    0x30: 0x2B,   # kVK_Tab
    0x31: 0x2C,   # kVK_Space
    0x33: 0x2A,   # kVK_Delete
    0x35: 0x29,   # kVK_Escape
    0x37: 0xE3,   # kVK_Command
    0x38: 0xE1,   # kVK_Shift
    0x39: 0x39,   # kVK_CapsLock
    0x3A: 0xE2,   # kVK_Option
    0x3B: 0xE0,   # kVK_Control
    0x3C: 0xE5,   # kVK_RightShift
    0x3D: 0xE6,   # kVK_RightOption
    0x3E: 0xE4,   # kVK_RightControl
    # 0x3F: 0x,   # kVK_Function
    0x40: 0x6C,   # kVK_F17
    0x48: 0xED,   # kVK_VolumeUp
    0x49: 0xEE,   # kVK_VolumeDown
    0x4A: 0x7F,   # kVK_Mute
    0x4F: 0x6D,   # kVK_F18
    0x50: 0x6E,   # kVK_F19
    0x5A: 0x6F,   # kVK_F20
    0x60: 0x3E,   # kVK_F5
    0x61: 0x3F,   # kVK_F6
    0x62: 0x40,   # kVK_F7
    0x63: 0x3C,   # kVK_F3
    0x64: 0x41,   # kVK_F8
    0x65: 0x42,   # kVK_F9
    0x67: 0x44,   # kVK_F11
    0x69: 0x68,   # kVK_F13
    0x6A: 0x6B,   # kVK_F16
    0x6B: 0x69,   # kVK_F14
    0x6D: 0x43,   # kVK_F10
    0x6F: 0x45,   # kVK_F12
    0x71: 0x6A,   # kVK_F15
    0x72: 0x75,   # kVK_Help
    0x73: 0x4A,   # kVK_Home
    0x74: 0x4B,   # kVK_PageUp
    0x75: 0x4C,   # kVK_ForwardDelete
    0x76: 0x3D,   # kVK_F4
    0x77: 0x4D,   # kVK_End
    0x78: 0x3B,   # kVK_F2
    0x79: 0x4E,   # kVK_PageDown
    0x7A: 0x3A,   # kVK_F1
    0x7B: 0x50,   # kVK_LeftArrow
    0x7C: 0x4F,   # kVK_RightArrow
    0x7D: 0x51,   # kVK_DownArrow
    0x7E: 0x52,   # kVK_UpArrow
    0x52: 0x62,   # kVK_ANSI_Keypad0
    0x53: 0x59,   # kVK_ANSI_Keypad1
    0x54: 0x5A,   # kVK_ANSI_Keypad2
    0x55: 0x5B,   # kVK_ANSI_Keypad3
    0x56: 0x5C,   # kVK_ANSI_Keypad4
    0x57: 0x5D,   # kVK_ANSI_Keypad5
    0x58: 0x5E,   # kVK_ANSI_Keypad6
    0x59: 0x5F,   # kVK_ANSI_Keypad7
    0x5B: 0x60,   # kVK_ANSI_Keypad8
    0x5C: 0x61,   # kVK_ANSI_Keypad9
    0x47: 0x53,   # kVK_ANSI_KeypadClear
    0x41: 0x63,   # kVK_ANSI_KeypadDecimal
    0x43: 0x55,   # kVK_ANSI_KeypadMultiply
    0x45: 0x57,   # kVK_ANSI_KeypadPlus
    0x4B: 0x54,   # kVK_ANSI_KeypadDivide
    0x4C: 0x58,   # kVK_ANSI_KeypadEnter
    0x4E: 0x56,   # kVK_ANSI_KeypadMinus
    0x51: 0x67,   # kVK_ANSI_KeypadEquals
    0x36: 0xE7,   # kVK_RIGHT_COMMAND
}

remap_left_cmd_to_ctrl = True
application_active = True
lock_inputs = True
ser = None
gui = None
mouse_button = 0x00
hid_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0]
current_display_input = 16 # mDP=16, HDMI1=17
time_since_last_send = time.time()

def pack_signed_char(value):
    if value > 127:
        value = 127
    elif value < -128:
        value = -128
    packed_value = struct.pack('b', value)
    return packed_value

def mouse_handle_event(proxy, event_type, event, refcon):
    global ser, mouse_button, lock_inputs
    if application_active and lock_inputs:
        try: # 1, 2, 3, 4, 5, 6, 7, 22, 25, 26, 27 <- event_type
            rel_x =  CGEventGetIntegerValueField(event, kCGMouseEventDeltaX)
            rel_y =  CGEventGetIntegerValueField(event, kCGMouseEventDeltaY)
            # print("({0},{1})".format(rel_x, rel_y))
        # except AttributeError:
            # This happens during teardown of the virtual machine
        except Exception as e:
            print(e)
            return None
        if event_type == kCGEventMouseMoved:
            values = [1, mouse_button, rel_x, rel_y, 0, 0, 0, 0, 0]
            for value in values:
                ser.write(pack_signed_char(value))
            # print("mouse moved: {0},{1}".format(round(px - prev_x), round(py - prev_y)))

        elif event_type == kCGEventScrollWheel:
            dx = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis2)
            dy = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis1)
            if dy != 0:
                dy = -1 if dy < 0 else 1
            if dx != 0:
                dx = 1 if dx < 0 else -1
            values = [1, mouse_button, 0, 0, dy, dx, 0, 0, 0]
            for value in values:
                ser.write(pack_signed_char(value))
        elif event_type <= kCGEventLeftMouseDragged:
            # print("button: {}".format(event_type))
            if event_type == kCGEventLeftMouseDown:
                mouse_button |= 1
            elif event_type == kCGEventLeftMouseUp:
                mouse_button &= ~1 & 0xFF
            elif event_type == kCGEventLeftMouseDragged:
                mouse_button |= 1
            elif event_type == kCGEventRightMouseDown:
                mouse_button |= 2
            elif event_type == kCGEventRightMouseUp:
                mouse_button &= ~2 & 0xFF
            elif event_type == kCGEventRightMouseDragged:
                mouse_button |= 2
            values = [1, mouse_button, rel_x, rel_y, 0, 0, 0, 0, 0]
            for value in values:
                ser.write(pack_signed_char(value))
        else:
            print("other...{0}".format(event_type))
        return None
    else:
        return event

def keyboard_handle_event(proxy, event_type, event, refcon):
    global ser, hid_buffer, mod_byte, application_active, current_display_input, lock_inputs, gui
    if application_active and lock_inputs:
        send_HID = True
        if event_type == kCGEventKeyUp: # 11, keyboard related events
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            # print("UP {0} = {1}".format(keycode, macOS_to_hid_lookup[keycode]))
            # convert keycode to HID
            if macOS_to_hid_lookup[keycode] in hid_buffer[3:9]:
                for index in range(6):
                    if hid_buffer[index + 3] == macOS_to_hid_lookup[keycode]:
                        hid_buffer[index + 3] = 0
                        break

        elif event_type == kCGEventKeyDown: # 10, keyboard related events
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            # print("DOWN {0} = {1}".format(keycode, macOS_to_hid_lookup[keycode]))
            if keycode not in [105, 106]: # custom sequence: F13, F16
                if macOS_to_hid_lookup[keycode] not in hid_buffer[3:9]:
                    for index in range(6):
                        if hid_buffer[index + 3] == 0:
                            hid_buffer[index + 3] = macOS_to_hid_lookup[keycode]
                            break
            elif keycode == 105: # F13, for toggling display input
                send_HID = False
                if current_display_input == 16: # mDP
                    current_display_input = 17
                else:
                    current_display_input = 16
                subprocess.run("ddcctl -d 2 -i " + str(current_display_input), shell=True, capture_output=False)
            elif keycode == 106:
                if lock_inputs:
                    lock_inputs = False
                    gui.configure(bg="green")
                    gui.update()
                    CGAssociateMouseAndMouseCursorPosition(True)
                else:
                    lock_inputs = True
                    gui.configure(bg="systemWindowBackgroundColor")
                    gui.update()


        elif event_type == kCGEventFlagsChanged:
            flags = CGEventGetFlags(event)
            bit_A = flags & 0b1111111
            mod_byte = 0b0
            # Fit the bits from A into B based on their positions
            if remap_left_cmd_to_ctrl:
                mod_byte |= (bit_A & 1)       # L Ctrl   Left Control
                mod_byte |= (bit_A & 2)       # L Shft   Left Shift
                mod_byte |= (bit_A & 32) >> 3 # R Shft   Left Alt
                mod_byte |= (bit_A & 8) >> 3  # L Cmd    Left Cmd
                mod_byte |= 0                 # R Cmd    Constant 0 (bit 4)
                mod_byte |= (bit_A & 4) << 3  # L Alt    Right Shift
                mod_byte |= (bit_A & 64)      # R Alt    Right Alt
                mod_byte |= (bit_A & 16) << 3 # -----    Right Cmd
            else:
                mod_byte |= (bit_A & 1)       # L Ctrl   Left Control
                mod_byte |= (bit_A & 2)       # L Shft   Left Shift
                mod_byte |= (bit_A & 32) >> 3 # R Shft   Left Alt
                mod_byte |= (bit_A & 8)       # L Cmd    Left Cmd
                mod_byte |= 0                 # R Cmd    Constant 0 (bit 4)
                mod_byte |= (bit_A & 4) << 3  # L Alt    Right Shift
                mod_byte |= (bit_A & 64)      # R Alt    Right Alt
                mod_byte |= (bit_A & 16) << 3 # -----    Right Cmd
            # print("flag: {0} mod:{1} HID_mod:{2}".format(bin(flags), bin(bit_A), format(mod_byte, '08b')))
            hid_buffer[1] = mod_byte
        # print("HID: {0} {1}".format(format(hid_buffer[1], '08b'), hid_buffer[2:]))
        
        if event_type == kCGEventKeyDown:
            if (hid_buffer[1] == 0b1000 and remap_left_cmd_to_ctrl == False) or (hid_buffer[1] == 0b1 and remap_left_cmd_to_ctrl == True):
                if keycode in [0x30]: # Cmd + Tab, allow passthrough
                    lock_inputs = False # unlock input and lock internal event handler
                    return event
            if send_HID: # send output for key down event
                ser.write(bytearray(hid_buffer))
            return None

        if send_HID: # send output (anything except key down events) 
            ser.write(bytearray(hid_buffer))
        return event
    else:
        return event

def main():
    global application_active, ser, prev_x, prev_y, lock_inputs, gui
    gui = tk.Tk()
    gui.title("KeyRelay")
    gui.attributes("-transparent", True)
    gui.attributes("-alpha", 0.6)  # Set the transparency level (0.0 to 1.0)
    gui.iconphoto(False, tk.PhotoImage(file='favicon-logo-512x512.png'))
    gui.geometry(f"{400}x{300}+{1304}+{696}")
    gui.update()

    port = '/dev/tty.usbserial-01D29067'
    baud_rate = 230400 # 115200
    ser = serial.Serial(port, baud_rate)

    # Create an event tap to monitor mouse events
    mouse_event_tap = CGEventTapCreate(
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        mouse_events,
        mouse_handle_event,
        None
    )

    keyboard_event_tap = CGEventTapCreate(
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        keyboard_events,
        keyboard_handle_event,
        None
    )
    
    try:
        if mouse_event_tap and keyboard_event_tap:
            CGAssociateMouseAndMouseCursorPosition(False)
            CGWarpMouseCursorPosition((1504, 846))
            # Create a run loop source from the event tap
            mouse_run_loop_source = CFMachPortCreateRunLoopSource(None, mouse_event_tap, 0)
            keyboard_run_loop_source = CFMachPortCreateRunLoopSource(None, keyboard_event_tap, 0)

            # Get the current run loop
            run_loop = CFRunLoopGetCurrent()
            # Add the run loop source to the run loop
            CFRunLoopAddSource(run_loop, mouse_run_loop_source, kCFRunLoopDefaultMode)
            CFRunLoopAddSource(run_loop, keyboard_run_loop_source, kCFRunLoopDefaultMode)

            # Enable the event tap
            CGEventTapEnable(mouse_event_tap, True)
            CGEventTapEnable(keyboard_event_tap, True)

            # Start the run loop to receive events
            # CFRunLoopRun() # blocking
            while True:
                CFRunLoopRunInMode(kCFRunLoopDefaultMode, 1, True)
                if gui.focus_get() == gui:
                    if application_active == False:
                        time.sleep(0.7)
                        application_active = True
                        CGAssociateMouseAndMouseCursorPosition(False)
                        gui.configure(bg="systemWindowBackgroundColor")
                else:
                    application_active = False
                    lock_inputs = True
                    gui.configure(bg="red")
                    ser.write(bytearray([255, 255, 255, 255, 255, 255, 255, 255, 255]))
                gui.update()

    except Exception as e:
        print(e)
    finally:
        print("Releasing resources...")
        ser.write(bytearray([255, 255, 255, 255, 255, 255, 255, 255, 255]))
        ser.close()
        CFRunLoopRemoveSource(run_loop, mouse_run_loop_source, kCFRunLoopDefaultMode)
        CFRunLoopRemoveSource(run_loop, keyboard_run_loop_source, kCFRunLoopDefaultMode)
        CFRelease(mouse_run_loop_source)
        CFRelease(keyboard_run_loop_source)
        CFRelease(mouse_event_tap)
        CFRelease(keyboard_event_tap)
        gui.destroy()
        sys.exit()

    #         else:
    #             if time.time() - time_since_last_send > (250 + random.uniform(30, 120)):
    #                 ser.write(bytearray([0, 1, 0, 0, 0, 0, 0, 0, 0]))
    #                 time.sleep(0.1)
    #                 ser.write(bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0]))
    #                 time_since_last_send = time.time()
    #             clock.tick(20)



if __name__ == '__main__':
    main()

# 0 left control
# 1 left shift
# 2 right shift
# 3 left cmd
# 4 right cmd
# 5 left alt
# 6 right alt

#     x ctrl            x left
# 0b001000000000100000001 left control
# 0b001000000000000000000 control mask

#      x shift         x left
# 0b000100000000100000010 left shift
# 0b000100000000100000100 right shift
#                     x right
# 0b000100000000000000000 shift mask

#   x cmd            x left
# 0b100000000000100001000 left cmd         
# 0b100000000000100010000 right cmd
#                   x right
# 0b100000000000000000000 cmd mask

#    x alt         x left
# 0b010000000000100100000 left alt
# 0b010000000000101000000 right alt
#                 x right
# 0b010000000000000000000 alt mask

# 0b000000000000100000000 release
#               x mod event
