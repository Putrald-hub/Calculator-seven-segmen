import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import math

# ==============================================================================
# CONSTANTS & THEME DEFINITION
# ==============================================================================
BG_MAIN = "#0B0F19"       # Deep Obsidian Black
BG_CARD = "#151D30"       # Deep Slate Blue
BORDER_COLOR = "#22314F"  # Slate Blue Border
TEXT_LIGHT = "#F8FAFC"    # Soft White
TEXT_MUTED = "#64748B"    # Cool Gray

# VFD LED Colors
VFD_ON = "#00F5FF"        # Glowing VFD Cyan
VFD_ON_GLOW = "#00A3AD"   # Cyan Glow Border
VFD_OFF = "#0C1D26"       # Very Dark Faded Cyan (Inactive segment)
VFD_OFF_BORDER = "#071217"# Shadow border for inactive segment

# Other Accent Colors
COLOR_OP = "#FF6B35"      # Neon Amber / Orange
COLOR_EQ = "#10B981"      # Emerald Green
COLOR_FN = "#EF4444"      # Crimson Red
COLOR_ACCENT = "#8B5CF6"  # Purple Accent

# Segment mappings for characters (a, b, c, d, e, f, g, dp)
# MSB to LSB byte representation order: [dp, g, f, e, d, c, b, a]
SEGMENT_MAP = {
    '0': (1, 1, 1, 1, 1, 1, 0, 0),
    '1': (0, 1, 1, 0, 0, 0, 0, 0),
    '2': (1, 1, 0, 1, 1, 0, 1, 0),
    '3': (1, 1, 1, 1, 0, 0, 1, 0),
    '4': (0, 1, 1, 0, 0, 1, 1, 0),
    '5': (1, 0, 1, 1, 0, 1, 1, 0),
    '6': (1, 0, 1, 1, 1, 1, 1, 0),
    '7': (1, 1, 1, 0, 0, 0, 0, 0),
    '8': (1, 1, 1, 1, 1, 1, 1, 0),
    '9': (1, 1, 1, 1, 0, 1, 1, 0),
    'A': (1, 1, 1, 0, 1, 1, 1, 0),
    'b': (0, 0, 1, 1, 1, 1, 1, 0),
    'C': (1, 0, 0, 1, 1, 1, 0, 0),
    'd': (0, 1, 1, 1, 1, 0, 1, 0),
    'E': (1, 0, 0, 1, 1, 1, 1, 0),
    'F': (1, 0, 0, 0, 1, 1, 1, 0),
    '-': (0, 0, 0, 0, 0, 0, 1, 0),
    ' ': (0, 0, 0, 0, 0, 0, 0, 0),
}

CHAR_ORDER = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'b', 'C', 'd', 'E', 'F', '-']

# Segment Names & Descriptions for displays
SEG_NAMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'dp']
SEG_DESC = ['Top', 'Top-Right', 'Bottom-Right', 'Bottom', 'Bottom-Left', 'Top-Left', 'Middle', 'Decimal Point']

# Physical IC 10-pin definitions for Standard 7-Segment
PIN_CONFIGS = {
    1:  {"name": "E",   "segment": "e",  "pos": (45, 205),  "label_pos": (45, 235)},
    2:  {"name": "D",   "segment": "d",  "pos": (85, 205),  "label_pos": (85, 235)},
    3:  {"name": "COM", "segment": None, "pos": (125, 205), "label_pos": (125, 235)},
    4:  {"name": "C",   "segment": "c",  "pos": (165, 205), "label_pos": (165, 235)},
    5:  {"name": "DP",  "segment": "dp", "pos": (205, 205), "label_pos": (205, 235)},
    6:  {"name": "B",   "segment": "b",  "pos": (205, 75),  "label_pos": (205, 45)},
    7:  {"name": "A",   "segment": "a",  "pos": (165, 75),  "label_pos": (165, 45)},
    8:  {"name": "COM", "segment": None, "pos": (125, 75),  "label_pos": (125, 45)},
    9:  {"name": "F",   "segment": "f",  "pos": (85, 75),   "label_pos": (85, 45)},
    10: {"name": "G",   "segment": "g",  "pos": (45, 75),   "label_pos": (45, 45)}
}


# ==============================================================================
# CLASS: SEVENSEGMENTDIGIT (POLYGON-BASED DRAWING)
# ==============================================================================
class SevenSegmentDigit:
    def __init__(self, canvas, x, y, width=32, height=60, thickness=5, slant=0.08):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.t = thickness
        self.s = slant  # tilts top to right
        self.gap = 1.2

        self.segment_ids = {}

    def get_points(self, seg_name):
        w, h, t, g = self.w, self.h, self.t, self.gap
        h_half = h / 2

        if seg_name == 'a':
            return [(g, 0), (w - g, 0), (w - g - t, t), (g + t, t)]
        elif seg_name == 'f':
            return [(0, g), (t, g + t), (t, h_half - g - t/2), (0, h_half - g)]
        elif seg_name == 'b':
            return [(w - t, g + t), (w, g), (w, h_half - g), (w - t, h_half - g - t/2)]
        elif seg_name == 'g':
            return [
                (g + t, h_half - t/2), (w - g - t, h_half - t/2), 
                (w - g, h_half), 
                (w - g - t, h_half + t/2), (g + t, h_half + t/2), 
                (g, h_half)
            ]
        elif seg_name == 'e':
            return [(0, h_half + g), (t, h_half + g + t/2), (t, h - g - t), (0, h - g)]
        elif seg_name == 'c':
            return [(w - t, h_half + g + t/2), (w, h_half + g), (w, h - g), (w - t, h - g - t)]
        elif seg_name == 'd':
            return [(g + t, h - t), (w - g - t, h - t), (w - g, h), (g, h)]
        elif seg_name == 'dp':
            return [(w + 3, h - t/2)]
        return []

    def draw(self, char=' ', dp_on=False, common_anode=False, active_seg=None):
        self.clear()

        states = SEGMENT_MAP.get(char, SEGMENT_MAP[' '])
        seg_states = {
            'a': states[0],
            'b': states[1],
            'c': states[2],
            'd': states[3],
            'e': states[4],
            'f': states[5],
            'g': states[6],
            'dp': 1 if dp_on else 0
        }

        # Draw A to G segments
        for seg in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            state = seg_states[seg]
            is_active = (state == 1) if not common_anode else (state == 0)
            override_highlight = (active_seg == seg)
            
            points = self.get_points(seg)
            transformed = []
            for px, py in points:
                sx = px + (self.h - py) * self.s + self.x
                sy = py + self.y
                transformed.append((sx, sy))

            if override_highlight:
                fill_col = "#FF6B35"
                out_col = "#FFA07A"
                width_line = 2
            elif state == 1:
                fill_col = VFD_ON
                out_col = VFD_ON_GLOW
                width_line = 1.5
            else:
                fill_col = VFD_OFF
                out_col = VFD_OFF_BORDER
                width_line = 1

            poly_id = self.canvas.create_polygon(
                transformed, 
                fill=fill_col, 
                outline=out_col, 
                width=width_line,
                tags=("segment", f"seg_{seg}")
            )
            self.segment_ids[seg] = poly_id

        # Draw DP
        dp_state = seg_states['dp']
        override_dp_highlight = (active_seg == 'dp')
        
        px, py = self.get_points('dp')[0]
        sx = px + (self.h - py) * self.s + self.x
        sy = py + self.y
        r = self.t / 2 + 1

        if override_dp_highlight:
            fill_col = "#FF6B35"
            out_col = "#FFA07A"
            width_line = 2
        elif dp_state == 1:
            fill_col = VFD_ON
            out_col = VFD_ON_GLOW
            width_line = 1.5
        else:
            fill_col = VFD_OFF
            out_col = VFD_OFF_BORDER
            width_line = 1

        dp_id = self.canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            fill=fill_col,
            outline=out_col,
            width=width_line,
            tags=("segment", "seg_dp")
        )
        self.segment_ids['dp'] = dp_id

    def clear(self):
        for id_ in self.segment_ids.values():
            self.canvas.delete(id_)
        self.segment_ids.clear()


# ==============================================================================
# CLASS: VFDDISPLAY (THE 8-DIGIT SCREEN)
# ==============================================================================
class VFDDisplay(tk.Canvas):
    def __init__(self, parent, width=400, height=100, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#050B14", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        self.digits = []
        
        # Draw background grid mesh texture
        for i in range(0, width, 6):
            self.create_line(i, 0, i, height, fill="#08101C", width=1)
        for j in range(0, height, 6):
            self.create_line(0, j, width, j, fill="#08101C", width=1)

        # Draw inner chassis shadow
        self.create_rectangle(1, 1, width-1, height-1, outline="#0E1726", width=2)
        
        # Instantiate 8 digits
        digit_w = 28
        digit_h = 52
        spacing = 42
        start_x = 24
        start_y = 26
        
        for i in range(8):
            dx = start_x + i * spacing
            digit = SevenSegmentDigit(self, dx, start_y, width=digit_w, height=digit_h, thickness=4, slant=0.08)
            self.digits.append(digit)

        self.hovered_digit_idx = None
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Leave>", self.on_mouse_leave)
        self.on_digit_hover_callback = None

    def on_mouse_move(self, event):
        x = event.x
        hovered_idx = None
        for i, digit in enumerate(self.digits):
            if digit.x - 5 <= x <= digit.x + digit.w + 12:
                hovered_idx = i
                break
        
        if hovered_idx != self.hovered_digit_idx:
            self.hovered_digit_idx = hovered_idx
            if self.on_digit_hover_callback:
                self.on_digit_hover_callback(hovered_idx)

    def on_mouse_leave(self, event):
        self.hovered_digit_idx = None
        if self.on_digit_hover_callback:
            self.on_digit_hover_callback(None)

    def set_display_string(self, display_str, common_anode=False, active_seg=None):
        parsed = []
        i = 0
        while i < len(display_str):
            char = display_str[i]
            if char == '.' and len(parsed) > 0:
                parsed[-1] = (parsed[-1][0], True)
            else:
                if char == '.':
                    parsed.append((' ', True))
                else:
                    parsed.append((char, False))
            i += 1

        if len(parsed) > 8:
            parsed = parsed[-8:]

        while len(parsed) < 8:
            parsed.insert(0, (' ', False))

        for idx, digit in enumerate(self.digits):
            char, dp = parsed[idx]
            highlight_seg = None
            if active_seg:
                is_target = False
                if self.hovered_digit_idx is not None:
                    is_target = (idx == self.hovered_digit_idx)
                else:
                    rightmost_active = 7
                    for k in range(7, -1, -1):
                        if parsed[k][0] != ' ':
                            rightmost_active = k
                            break
                    is_target = (idx == rightmost_active)
                
                if is_target:
                    highlight_seg = active_seg

            digit.draw(char, dp, common_anode, active_seg=highlight_seg)

        return parsed


# ==============================================================================
# CLASS: PINMAPPERWIDGET (PHYSICAL LAYOUT SIMULATOR)
# ==============================================================================
class PinMapperWidget(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        self.common_anode = False
        self.active_digit_char = ' '
        self.active_digit_dp = False
        self.hovered_pin = None
        self.hovered_seg = None
        self.on_hover_change_callback = None
        self.chip_coords = (90, 80, 190, 200)
        
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Leave>", self.on_mouse_leave)
        self.draw_static_layout()

    def draw_static_layout(self):
        self.delete("all")
        self.create_text(15, 18, text="INTERACTIVE PIN MAP (10-PIN DUAL)", fill=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        self.create_line(15, 28, 265, 28, fill=BORDER_COLOR, width=1)
        
        # Draw Main Board / PCB breadboard
        self.create_rectangle(15, 38, 265, 270, fill="#0D1321", outline=BORDER_COLOR, width=1)
        
        # Draw chip body
        x1, y1, x2, y2 = self.chip_coords
        self.create_rectangle(x1, y1, x2, y2, fill="#161F33", outline="#3B4F75", width=2, tags="chip_body")
        self.create_arc(x1 + 35, y1 - 8, x1 + 65, y1 + 8, start=180, extent=180, fill="#0D1321", outline="#3B4F75", width=1)
        
        # Pins & labels
        for pin_num, config in PIN_CONFIGS.items():
            px, py = config["pos"]
            lx, ly = config["label_pos"]
            name = config["name"]
            
            is_top = (py < 140)
            p_x1, p_x2 = px - 6, px + 6
            p_y1 = py - 8 if is_top else py
            p_y2 = py if is_top else py + 8
            
            self.create_rectangle(p_x1, p_y1, p_x2, p_y2, fill="#7C8BA1", outline="#4B596E", width=1, tags=f"pin_metal_{pin_num}")
            self.create_text(lx, ly, text=f"{pin_num}:{name}", fill=TEXT_MUTED, font=("Consolas", 7, "bold"), tags=f"pin_lbl_{pin_num}")

        self.tooltip_id = self.create_text(140, 252, text="Hover over pins/segments to inspect logic", fill=TEXT_MUTED, font=("Consolas", 8, "italic"))

    def draw_logic_state(self, active_char=' ', dp_on=False, common_anode=False, active_seg=None):
        self.active_digit_char = active_char
        self.active_digit_dp = dp_on
        self.common_anode = common_anode
        
        states = SEGMENT_MAP.get(active_char, SEGMENT_MAP[' '])
        seg_states = {
            'a': states[0], 'b': states[1], 'c': states[2], 'd': states[3],
            'e': states[4], 'f': states[5], 'g': states[6], 'dp': 1 if dp_on else 0
        }

        self.delete("dynamic")

        # Draw single digit inside chip
        self.digit_renderer = SevenSegmentDigit(self, 129, 120, width=22, height=40, thickness=3.5, slant=0.06)
        self.digit_renderer.draw(active_char, dp_on, common_anode, active_seg=self.hovered_seg)
        
        # Draw wires connecting pins to segments
        for pin_num, config in PIN_CONFIGS.items():
            seg = config["segment"]
            px, py = config["pos"]
            is_top = (py < 140)
            
            if seg is None:
                is_active = True
                wire_color = "#FFD700" if common_anode else "#708090"
                wire_width = 1.5
            else:
                state = seg_states[seg]
                is_active = (state == 1)
                
                if self.hovered_pin == pin_num or self.hovered_seg == seg:
                    wire_color = "#FF6B35"
                    wire_width = 2.5
                elif is_active:
                    wire_color = VFD_ON
                    wire_width = 1.5
                else:
                    wire_color = "#1F2E45"
                    wire_width = 1
            
            pin_end_x = px
            pin_end_y = py
            
            # Destination coordinates inside chip VFD
            if seg == 'a':       dest = (140, 120)
            elif seg == 'b':     dest = (149, 130)
            elif seg == 'c':     dest = (147, 150)
            elif seg == 'd':     dest = (138, 160)
            elif seg == 'e':     dest = (130, 150)
            elif seg == 'f':     dest = (132, 130)
            elif seg == 'g':     dest = (140, 140)
            elif seg == 'dp':    dest = (156, 158)
            else:                dest = (140, 140)
            
            mid_y = (pin_end_y + dest[1]) / 2
            self.create_line(pin_end_x, pin_end_y, pin_end_x, mid_y, dest[0], mid_y, dest[0], dest[1],
                             fill=wire_color, width=wire_width, tags=("dynamic", "wire"))
            
            dot_color = "#FFA07A" if (self.hovered_pin == pin_num) else (VFD_ON if is_active else "#2C3E55")
            r_dot = 2.5 if (self.hovered_pin == pin_num) else 1.5
            self.create_oval(pin_end_x - r_dot, pin_end_y - r_dot, pin_end_x + r_dot, pin_end_y + r_dot,
                             fill=dot_color, outline="", tags="dynamic")

        # Highlight pin metals on hover
        if self.hovered_pin:
            px, py = PIN_CONFIGS[self.hovered_pin]["pos"]
            is_top = (py < 140)
            p_x1, p_x2 = px - 6, px + 6
            p_y1 = py - 8 if is_top else py
            p_y2 = py if is_top else py + 8
            self.create_rectangle(p_x1, p_y1, p_x2, p_y2, fill="#FF6B35", outline="#FFA07A", width=1.5, tags="dynamic")
            
        # Update Tooltip text
        if self.hovered_pin:
            config = PIN_CONFIGS[self.hovered_pin]
            seg = config["segment"]
            name = config["name"]
            
            if seg is None:
                state_str = "VCC (+5V)" if common_anode else "GND (0V)"
                desc = f"Pin {self.hovered_pin} (COM): Tied to {state_str}"
            else:
                state = seg_states[seg]
                if common_anode:
                    logic = "LOW (0V) -> SEGMENT ON" if state == 1 else "HIGH (+5V) -> SEGMENT OFF"
                else:
                    logic = "HIGH (+5V) -> SEGMENT ON" if state == 1 else "LOW (0V) -> SEGMENT OFF"
                desc = f"Pin {self.hovered_pin} (Seg {name.upper()}): {logic}"
            self.itemconfig(self.tooltip_id, text=desc, fill="#FF6B35")
        elif self.hovered_seg:
            seg = self.hovered_seg
            state = seg_states[seg]
            target_pin = next((p for p, cfg in PIN_CONFIGS.items() if cfg["segment"] == seg), None)
            logic = ("LOW (0V) -> ON" if state == 1 else "HIGH (+5V) -> OFF") if common_anode else ("HIGH (+5V) -> ON" if state == 1 else "LOW (0V) -> OFF")
            desc = f"Segment {seg.upper()} (Pin {target_pin}): Logic {logic}"
            self.itemconfig(self.tooltip_id, text=desc, fill=VFD_ON)
        else:
            self.itemconfig(self.tooltip_id, text="Hover over pins/segments to inspect logic", fill=TEXT_MUTED)

    def on_mouse_move(self, event):
        x, y = event.x, event.y
        old_hover_pin = self.hovered_pin
        old_hover_seg = self.hovered_seg
        
        self.hovered_pin = None
        self.hovered_seg = None
        
        # Check hover on pins
        for pin_num, config in PIN_CONFIGS.items():
            px, py = config["pos"]
            is_top = (py < 140)
            p_x1, p_x2 = px - 8, px + 8
            p_y1 = py - 12 if is_top else py - 2
            p_y2 = py + 2 if is_top else py + 12
            
            if p_x1 <= x <= p_x2 and p_y1 <= y <= p_y2:
                self.hovered_pin = pin_num
                self.hovered_seg = config["segment"]
                break
                
        # Check hover on central digits
        if not self.hovered_pin and hasattr(self, 'digit_renderer'):
            if 120 <= x <= 162 and 115 <= y <= 165:
                if y < 125 and 125 <= x <= 155: self.hovered_seg = 'a'
                elif y > 153 and 125 <= x <= 155: self.hovered_seg = 'd'
                elif 136 <= y <= 144 and 128 <= x <= 152: self.hovered_seg = 'g'
                elif x < 136:
                    self.hovered_seg = 'f' if y < 140 else 'e'
                elif 136 <= x <= 152:
                    if y < 140:
                        self.hovered_seg = 'f' if x < 142 else 'b'
                    else:
                        self.hovered_seg = 'e' if x < 142 else 'c'
                else:
                    self.hovered_seg = 'b' if y < 140 else ('dp' if y > 150 and x > 150 else 'c')

        if self.hovered_pin != old_hover_pin or self.hovered_seg != old_hover_seg:
            self.draw_logic_state(self.active_digit_char, self.active_digit_dp, self.common_anode)
            if self.on_hover_change_callback:
                self.on_hover_change_callback(self.hovered_seg)

    def on_mouse_leave(self, event):
        self.hovered_pin = None
        self.hovered_seg = None
        self.draw_logic_state(self.active_digit_char, self.active_digit_dp, self.common_anode)
        if self.on_hover_change_callback:
            self.on_hover_change_callback(None)


# ==============================================================================
# CLASS: DECODERDETAILSWIDGET (STATS PANEL)
# ==============================================================================
class DecoderDetailsWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        lbl_title = tk.Label(self, text="ACTIVE DIGIT DECODER LOGIC", bg=BG_CARD, fg=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        lbl_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        line = tk.Frame(self, height=1, bg=BORDER_COLOR)
        line.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        
        # Large active character preview
        self.lbl_char_val = tk.Label(self, text="8", bg="#0D1321", fg=VFD_ON, font=("Consolas", 36, "bold"), width=3, bd=1, relief="solid", highlightbackground=BORDER_COLOR)
        self.lbl_char_val.grid(row=2, column=0, rowspan=4, padx=(15, 10), pady=5, sticky="nsew")
        
        # Segment states indicators (A-G, DP)
        self.seg_frame = tk.Frame(self, bg=BG_CARD)
        self.seg_frame.grid(row=2, column=1, rowspan=4, padx=(0, 15), pady=5, sticky="nsew")
        
        self.seg_labels = {}
        segs = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'dp']
        for idx, s in enumerate(segs):
            r = idx // 4
            c = idx % 4
            f = tk.Frame(self.seg_frame, bg="#0D1321", highlightthickness=1, highlightbackground=BORDER_COLOR, width=32, height=32)
            f.grid(row=r, column=c, padx=3, pady=3)
            f.grid_propagate(False)
            
            lbl_name = tk.Label(f, text=s.upper(), bg="#0D1321", fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
            lbl_name.pack(side="top", pady=(1, 0))
            lbl_val = tk.Label(f, text="1", bg="#0D1321", fg=VFD_ON, font=("Consolas", 9, "bold"))
            lbl_val.pack(side="top", pady=(0, 1))
            
            self.seg_labels[s] = (f, lbl_name, lbl_val)
            
        self.lbl_bin_lbl = tk.Label(self, text="BINARY [dp,g,f,e,d,c,b,a]:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold"), anchor="w")
        self.lbl_bin_lbl.grid(row=6, column=0, columnspan=2, padx=15, pady=(12, 2), sticky="w")
        self.lbl_bin_val = tk.Label(self, text="0b01111111", bg="#0D1321", fg="#F59E0B", font=("Consolas", 12, "bold"), anchor="w", padx=10, pady=5)
        self.lbl_bin_val.grid(row=7, column=0, columnspan=2, padx=15, pady=(0, 8), sticky="ew")
        
        self.lbl_hex_lbl = tk.Label(self, text="HEXADECIMAL BYTEVALUE:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold"), anchor="w")
        self.lbl_hex_lbl.grid(row=8, column=0, columnspan=2, padx=15, pady=(2, 2), sticky="w")
        self.lbl_hex_val = tk.Label(self, text="0x7F", bg="#0D1321", fg=COLOR_EQ, font=("Consolas", 12, "bold"), anchor="w", padx=10, pady=5)
        self.lbl_hex_val.grid(row=9, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")

    def update_decoder(self, char=' ', dp_on=False, common_anode=False, hovered_seg=None):
        self.lbl_char_val.config(text="-" if char == ' ' else char)
            
        states = SEGMENT_MAP.get(char, SEGMENT_MAP[' '])
        seg_states = {
            'a': states[0], 'b': states[1], 'c': states[2], 'd': states[3],
            'e': states[4], 'f': states[5], 'g': states[6], 'dp': 1 if dp_on else 0
        }
        
        raw_bits = [
            seg_states['dp'], seg_states['g'], seg_states['f'], seg_states['e'],
            seg_states['d'], seg_states['c'], seg_states['b'], seg_states['a']
        ]
        
        logic_bits = [0 if bit == 1 else 1 for bit in raw_bits] if common_anode else raw_bits
                
        byte_val = 0
        for bit in logic_bits:
            byte_val = (byte_val << 1) | bit
            
        bin_str = "".join(str(b) for b in logic_bits)
        self.lbl_bin_val.config(text=f"0b{bin_str}")
        self.lbl_hex_val.config(text=f"0x{byte_val:02X}")
        
        for s, (frame, lbl_name, lbl_val) in self.seg_labels.items():
            state = seg_states[s]
            bit = (0 if state == 1 else 1) if common_anode else (1 if state == 1 else 0)
                
            if hovered_seg == s:
                frame.config(highlightbackground="#FF6B35")
                lbl_name.config(fg="#FF6B35")
                lbl_val.config(text=str(bit), fg="#FF6B35")
            else:
                frame.config(highlightbackground=BORDER_COLOR)
                lbl_name.config(fg=TEXT_MUTED)
                lbl_val.config(text=str(bit), fg=VFD_ON if state == 1 else TEXT_MUTED)


# ==============================================================================
# CLASS: STEPFLOWWIDGET (STEP BY STEP PROCESS DISPLAY)
# ==============================================================================
class StepFlowWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        lbl_title = tk.Label(self, text="STEP-BY-STEP CALCULATION PROSES", bg=BG_CARD, fg=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        lbl_title.pack(side="top", fill="x", padx=15, pady=(15, 5))
        
        line = tk.Frame(self, height=1, bg=BORDER_COLOR)
        line.pack(side="top", fill="x", padx=15, pady=(0, 10))
        
        # Scrolled Text Box
        self.text_area = tk.Text(self, bg="#0D1321", fg=TEXT_LIGHT, font=("Consolas", 9), bd=0, wrap="word", highlightthickness=0)
        self.text_area.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        
        scrollbar = tk.Scrollbar(self, command=self.text_area.yview, width=10, bg=BG_CARD, bd=0)
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        # Tags for styling
        self.text_area.tag_configure("header", foreground="#00F5FF", font=("Consolas", 10, "bold"))
        self.text_area.tag_configure("highlight", foreground="#FF6B35", font=("Consolas", 9, "bold"))
        self.text_area.tag_configure("green", foreground="#10B981", font=("Consolas", 9, "bold"))
        self.text_area.tag_configure("muted", foreground="#64748B")
        self.text_area.tag_configure("bold", font=("Consolas", 9, "bold"))
        self.text_area.tag_configure("carry", foreground="#EF4444", font=("Consolas", 9, "bold"))

    def update_steps(self, a, b, op, rStr, current_val):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        
        # Detect if we have a live preview of operand B
        is_preview = False
        if a is not None and b is None and current_val != "0" and current_val != "":
            try:
                b = float(current_val)
                is_preview = True
            except ValueError:
                pass
                
        if a is None:
            # Simple Display Mode
            self.text_area.insert(tk.END, "▶ INPUT AKTIF SAAT INI\n", "header")
            self.text_area.insert(tk.END, "  Nilai Desimal: ", "bold")
            self.text_area.insert(tk.END, f"{current_val}\n\n", "green")
            
            try:
                val_f = float(current_val)
                val_i = int(round(val_f))
                bin_str = bin(abs(val_i))[2:].zfill(8)
                self.text_area.insert(tk.END, "▶ KONVERSI DESIMAL → BINER (INTEGER)\n", "header")
                self.text_area.insert(tk.END, f"  Absolut Integer: {abs(val_i)}\n", "bold")
                self.text_area.insert(tk.END, f"  Biner (8-bit):   {bin_str}₂\n\n", "highlight")
            except ValueError:
                pass
                
            self.text_area.insert(tk.END, "▶ SEVEN SEGMENT CODER ENCODING SUMMARY\n", "header")
            chars = [c for c in current_val if c in SEGMENT_MAP or c == '.']
            for c in chars:
                if c == '.':
                    self.text_area.insert(tk.END, "  '.' → Decimal Point (DP) Aktif\n", "muted")
                else:
                    states = SEGMENT_MAP[c]
                    code = "".join(str(bit) for bit in states[:7])
                    self.text_area.insert(tk.END, f"  '{c}' → Segmen [a-g]: ", "bold")
                    self.text_area.insert(tk.END, f"{code}", "highlight")
                    self.text_area.insert(tk.END, " | Hex: ", "bold")
                    self.text_area.insert(tk.END, f"0x{int(code, 2):02X}\n", "green")
                    
            self.text_area.config(state="disabled")
            return
            
        # Math calculation step details
        op_sym = {'+': '+', '-': '−', '*': '×', '/': '÷'}.get(op, op)
        op_name = {'+': 'Penjumlahan', '-': 'Pengurangan', '*': 'Perkalian', '/': 'Pembagian'}.get(op, "Operasi")
        
        self.text_area.insert(tk.END, "▶ STEP 1 · INPUT OPERAND\n", "header")
        self.text_area.insert(tk.END, "  A = ", "bold")
        self.text_area.insert(tk.END, f"{a}", "highlight")
        
        if b is not None:
            self.text_area.insert(tk.END, " | B = ", "bold")
            self.text_area.insert(tk.END, f"{b}\n", "green")
        else:
            self.text_area.insert(tk.END, " | B = [Menunggu Masukan...]\n", "muted")
            
        self.text_area.insert(tk.END, f"  Operasi: {op_name} ({op_sym})\n\n", "muted")
        
        # If we have both variables (or preview)
        if b is not None:
            try:
                val_a = int(round(abs(a)))
                val_b = int(round(abs(b)))
                bits = max(len(bin(val_a)[2:]), len(bin(val_b)[2:])) + 1
                bits = max(bits, 8)
                
                bin_a = bin(val_a)[2:].zfill(bits)
                bin_b = bin(val_b)[2:].zfill(bits)
                
                self.text_area.insert(tk.END, "▶ STEP 2 · KONVERSI BINER ABSOLUT\n", "header")
                self.text_area.insert(tk.END, f"  |A| = {val_a} → ", "bold")
                self.text_area.insert(tk.END, f"{bin_a}₂\n", "highlight")
                self.text_area.insert(tk.END, f"  |B| = {val_b} → ", "bold")
                self.text_area.insert(tk.END, f"{bin_b}₂\n\n", "green")
            except Exception:
                bin_a, bin_b, bits = "", "", 8
                
            self.text_area.insert(tk.END, "▶ STEP 3 · PERHITUNGAN MATEMATIS BINER\n", "header")
            if op == '+':
                # Carry calculation
                carry = [0] * (bits + 1)
                res_bits = []
                for i in range(bits - 1, -1, -1):
                    bit_a = int(bin_a[i])
                    bit_b = int(bin_b[i])
                    c = carry[i + 1]
                    s = bit_a + bit_b + c
                    res_bits.append(str(s % 2))
                    carry[i] = s // 2
                res_bits.reverse()
                bin_res = "".join(res_bits)
                carry_str = "".join(str(x) for x in carry[1:])
                
                self.text_area.insert(tk.END, "  Carry:  ", "bold")
                self.text_area.insert(tk.END, f"{carry_str}\n", "carry")
                self.text_area.insert(tk.END, "  A:      ", "bold")
                self.text_area.insert(tk.END, f"{bin_a}\n", "highlight")
                self.text_area.insert(tk.END, "  B:      ", "bold")
                self.text_area.insert(tk.END, f"{bin_b}\n", "green")
                self.text_area.insert(tk.END, "  -------------------\n", "muted")
                self.text_area.insert(tk.END, "  Hasil:  ", "bold")
                self.text_area.insert(tk.END, f"{bin_res}₂ ({a + b})\n\n", "green")
            elif op == '-':
                self.text_area.insert(tk.END, f"  Pengurangan desimal: {a} - {b} = {a - b}\n", "bold")
                self.text_area.insert(tk.END, "  Proses biner menggunakan propagasi borrow:\n", "muted")
                self.text_area.insert(tk.END, f"  |A|:    {bin_a}\n", "highlight")
                self.text_area.insert(tk.END, f"  |B|:    {bin_b}\n", "green")
                self.text_area.insert(tk.END, "  -------------------\n", "muted")
                self.text_area.insert(tk.END, f"  Hasil:  {a-b}\n\n", "green")
            elif op == '*':
                try:
                    res_val = int(round(abs(a * b)))
                    bin_res = bin(res_val)[2:].zfill(bits * 2)
                    self.text_area.insert(tk.END, f"  Perkalian desimal: {a} × {b} = {a * b}\n", "bold")
                    self.text_area.insert(tk.END, "  Proses biner menggunakan shift-and-add:\n", "muted")
                    self.text_area.insert(tk.END, f"  Hasil Biner Absolut: {bin_res}₂\n\n", "green")
                except Exception:
                    pass
            elif op == '/':
                if b == 0:
                    self.text_area.insert(tk.END, "  ERROR: DIVISION BY ZERO (Pembagian dengan nol tidak terdefinisi)\n\n", "carry")
                else:
                    q = int(abs(a) // abs(b))
                    r = int(abs(a) % abs(b))
                    self.text_area.insert(tk.END, f"  Pembagian desimal: {a} ÷ {b}\n", "bold")
                    self.text_area.insert(tk.END, f"  Hasil Bagi (Quotient)  = {q}\n", "green")
                    self.text_area.insert(tk.END, f"  Sisa Bagi (Remainder)  = {r}\n", "highlight")
                    self.text_area.insert(tk.END, f"  Hasil Desimal:          {a / b}\n\n", "green")
                    
            step_num = 4
            if op in ['+', '-']:
                step_num = 4
            
            # Step 4: Output
            self.text_area.insert(tk.END, f"▶ STEP {step_num} · OUTPUT HASIL DESIMAL\n", "header")
            self.text_area.insert(tk.END, "  Hasil Akhir: ", "bold")
            self.text_area.insert(tk.END, f"{rStr}\n\n", "green")
            
            # Step 5: Encoding Summary
            if rStr != "Error":
                self.text_area.insert(tk.END, f"▶ STEP {step_num + 1} · SEVEN SEGMENT CODER ENCODE\n", "header")
                chars = [c for c in rStr if c in SEGMENT_MAP or c == '.']
                for c in chars:
                    if c == '.':
                        self.text_area.insert(tk.END, "  '.' → Decimal Point (DP) Aktif\n", "muted")
                    else:
                        states = SEGMENT_MAP[c]
                        code = "".join(str(bit) for bit in states[:7])
                        self.text_area.insert(tk.END, f"  '{c}' → Segmen [a-g]: ", "bold")
                        self.text_area.insert(tk.END, f"{code}", "highlight")
                        self.text_area.insert(tk.END, " | Hex: ", "bold")
                        self.text_area.insert(tk.END, f"0x{int(code, 2):02X}\n", "green")
            
            if is_preview:
                self.text_area.insert(tk.END, "\n* Preview Perhitungan Live (Tekan = untuk hasil akhir) *", "muted")
                
        self.text_area.config(state="disabled")


# ==============================================================================
# CLASS: DECTOBINWIDGET (DECIMAL -> BINARY CONVERT GRID)
# ==============================================================================
class DecToBinWidget(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        self.draw_static_layout()
        
    def draw_static_layout(self):
        self.delete("all")
        self.create_text(15, 18, text="DECIMAL → BINARY WEIGHT TABLES", fill=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        self.create_line(15, 28, 265, 28, fill=BORDER_COLOR, width=1)
        self.tooltip_id = self.create_text(140, 562, text="Press operations to analyze values", fill=TEXT_MUTED, font=("Consolas", 8, "italic"))

    def update_binary_tables(self, a, b, rStr, current_val):
        self.delete("dynamic")
        
        # List of values to render
        values_to_render = []
        if a is not None:
            values_to_render.append(("Operand A", a))
        if b is not None:
            values_to_render.append(("Operand B", b))
        else:
            # Check if we can preview B
            if a is not None and current_val != "0" and current_val != "":
                try:
                    values_to_render.append(("Operand B (Live)", float(current_val)))
                except ValueError:
                    pass
        
        if rStr != "Error" and a is not None:
            try:
                values_to_render.append(("Result", float(rStr)))
            except ValueError:
                pass
        elif a is None:
            try:
                values_to_render.append(("Input", float(current_val)))
            except ValueError:
                pass
                
        # Draw up to 3 tables stacked
        cy = 42
        for title, val in values_to_render[:3]:
            try:
                val_i = int(round(abs(val)))
                bin_str = bin(val_i)[2:].zfill(8)
                if len(bin_str) > 8:
                    bin_str = bin_str[-8:]
            except Exception:
                continue
                
            is_neg = (val < 0)
            neg_label = " (Negative)" if is_neg else ""
            self.create_text(15, cy, text=f"▶ {title} = {val}{neg_label}", fill=COLOR_OP if title == "Result" else TEXT_LIGHT, font=("Consolas", 8, "bold"), anchor="w", tags="dynamic")
            
            cx = 20
            weights = ["128", "64", "32", "16", "8", "4", "2", "1"]
            for idx, w in enumerate(weights):
                # Draw weight labels
                self.create_text(cx + 14, cy + 15, text=w, fill=TEXT_MUTED, font=("Consolas", 7), tags="dynamic")
                
                # Draw grid cells
                bit = bin_str[idx]
                cell_bg = "#10B981" if bit == '1' else "#0D1321"
                cell_fg = TEXT_LIGHT if bit == '1' else "#1E293B"
                cell_border = "#34D399" if bit == '1' else BORDER_COLOR
                
                self.create_rectangle(cx, cy + 24, cx + 28, cy + 44, fill=cell_bg, outline=cell_border, width=1, tags="dynamic")
                self.create_text(cx + 14, cy + 34, text=bit, fill=cell_fg, font=("Consolas", 9, "bold"), tags="dynamic")
                cx += 30
                
            # Draw decimal to hexadecimal conversion details
            self.create_text(15, cy + 53, text=f"HEX: 0x{val_i:02X}  |  OCT: {val_i:o}  |  BIN: 0b{bin_str}", fill=TEXT_MUTED, font=("Consolas", 7), anchor="w", tags="dynamic")
            cy += 74
            
        if not values_to_render:
            self.create_text(140, 140, text="No numeric inputs to convert", fill=TEXT_MUTED, font=("Consolas", 9), tags="dynamic")


# ==============================================================================
# CLASS: SEGENCODEWIDGET (SEVEN SEGMENT ENCODE CARDS)
# ==============================================================================
class SegEncodeWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        lbl_title = tk.Label(self, text="SEVEN SEGMENT ENCODE CARDS", bg=BG_CARD, fg=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        lbl_title.pack(side="top", fill="x", padx=15, pady=(15, 5))
        
        line = tk.Frame(self, height=1, bg=BORDER_COLOR)
        line.pack(side="top", fill="x", padx=15, pady=(0, 10))
        
        # Scrollable Canvas container for cards
        self.canvas = tk.Canvas(self, bg=BG_CARD, bd=0, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        
        self.scrollbar = tk.Scrollbar(self, command=self.canvas.yview, width=10, bg=BG_CARD, bd=0)
        self.scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        
        self.card_frame = tk.Frame(self.canvas, bg=BG_CARD)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.card_frame, anchor="nw")
        
        self.card_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def update_encoder_cards(self, rStr, common_anode=False):
        # Clear previous cards
        for widget in self.card_frame.winfo_children():
            widget.destroy()
            
        chars = []
        i = 0
        while i < len(rStr):
            char = rStr[i]
            if char == '.' and len(chars) > 0:
                chars[-1] = (chars[-1][0], True)
            else:
                if char == '.':
                    chars.append((' ', True))
                else:
                    chars.append((char, False))
            i += 1
            
        valid_chars = [(c, dp) for (c, dp) in chars if c in SEGMENT_MAP]
        
        if not valid_chars:
            lbl_empty = tk.Label(self.card_frame, text="No digits to encode", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 9))
            lbl_empty.pack(pady=40, fill="x")
            return
            
        for char, dp_on in valid_chars:
            card = tk.Frame(self.card_frame, bg="#0D1321", highlightthickness=1, highlightbackground=BORDER_COLOR, pady=8, padx=10)
            card.pack(fill="x", pady=4, padx=5)
            
            # Left: big char and code info
            info_frame = tk.Frame(card, bg="#0D1321")
            info_frame.pack(side="left", fill="both")
            
            lbl_big = tk.Label(info_frame, text=char if char != ' ' else "[DP]", bg="#0D1321", fg=VFD_ON, font=("Consolas", 24, "bold"), width=3)
            lbl_big.pack(side="left", padx=(0, 10))
            
            states = SEGMENT_MAP[char]
            bits = []
            for bit in states[:7]:
                bits.append(0 if bit == 1 else 1 if common_anode else bit)
            dp_bit = 0 if dp_on else 1 if common_anode else (1 if dp_on else 0)
            bits.append(dp_bit)
            
            bin_str = "".join(str(b) for b in bits)
            byte_val = 0
            for b in bits:
                byte_val = (byte_val << 1) | b
                
            code_frame = tk.Frame(info_frame, bg="#0D1321")
            code_frame.pack(side="left", fill="y")
            
            tk.Label(code_frame, text=f"BIN: 0b{bin_str}", bg="#0D1321", fg="#10B981", font=("Consolas", 8, "bold"), anchor="w").pack(anchor="w")
            tk.Label(code_frame, text=f"HEX: 0x{byte_val:02X}", bg="#0D1321", fg=COLOR_OP, font=("Consolas", 8, "bold"), anchor="w").pack(anchor="w")
            
            # Right: segment bit badges
            badge_frame = tk.Frame(card, bg="#0D1321")
            badge_frame.pack(side="right", fill="both", expand=True)
            
            names = ["A", "B", "C", "D", "E", "F", "G", "DP"]
            for idx, name in enumerate(names):
                f = tk.Frame(badge_frame, bg="#090E17", highlightthickness=1, highlightbackground=BORDER_COLOR, width=28, height=36)
                f.pack(side="left", padx=2, expand=True)
                f.pack_propagate(False)
                
                tk.Label(f, text=name, bg="#090E17", fg=TEXT_MUTED, font=("Consolas", 6, "bold")).pack(side="top", pady=(1, 0))
                
                bit_val = bits[idx]
                bit_col = TEXT_MUTED
                if bit_val == (0 if common_anode else 1):
                    bit_col = VFD_ON
                    
                tk.Label(f, text=str(bit_val), bg="#090E17", fg=bit_col, font=("Consolas", 9, "bold")).pack(side="top")


# ==============================================================================
# CLASS: MINIACTIVEDIAGRAMWIDGET (SIDE-BY-SIDE MINI CANVAS REPS)
# ==============================================================================
class MiniActiveDiagramWidget(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        self.digits = []
        self.draw_static_layout()
        
    def draw_static_layout(self):
        self.delete("all")
        self.create_text(15, 15, text="DIAGRAM SEGMEN AKTIF (SIDE-BY-SIDE REPRESENTATION)", fill=TEXT_LIGHT, font=("Consolas", 9, "bold"), anchor="w")
        self.create_line(15, 25, 565, 25, fill=BORDER_COLOR, width=1)
        
    def update_diagrams(self, rStr, common_anode=False):
        self.delete("dynamic")
        
        chars = []
        i = 0
        while i < len(rStr):
            char = rStr[i]
            if char == '.' and len(chars) > 0:
                chars[-1] = (chars[-1][0], True)
            else:
                if char == '.':
                    chars.append((' ', True))
                else:
                    chars.append((char, False))
            i += 1
            
        n = len(chars)
        if n == 0:
            self.create_text(290, 55, text="No active digits to display", fill=TEXT_MUTED, font=("Consolas", 9), tags="dynamic")
            return
            
        total_w = n * 28
        start_x = (580 - total_w) / 2
        
        for idx, (char, dp_on) in enumerate(chars):
            dx = start_x + idx * 28
            digit = SevenSegmentDigit(self, dx, 32, width=16, height=30, thickness=2, slant=0.04)
            digit.draw(char, dp_on, common_anode)
            
            for seg, poly_id in digit.segment_ids.items():
                self.addtag_withtag("dynamic", poly_id)
            self.create_text(dx + 8, 70, text=char if char != ' ' else "DP", fill=TEXT_MUTED, font=("Consolas", 7, "bold"), tags="dynamic")


# ==============================================================================
# CLASS: TRUTHTABLEWIDGET (LIVE HIGHLIGHTING TRUTH TABLE)
# ==============================================================================
class TruthTableWidget(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        self.common_anode = False
        self.active_row_char = None
        self.row_height = 15
        self.col_widths = [45, 30, 30, 30, 30, 30, 30, 30, 35, 60]
        self.start_y = 45
        self.start_x = 20
        
        self.draw_table_headers()
        self.draw_table_rows()

    def draw_table_headers(self):
        self.delete("headers")
        
        self.create_text(15, 18, text="TRUTH TABLE SEVEN SEGMENT (ABCDEFG)", fill=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w", tags="headers")
        self.create_line(15, 28, 565, 28, fill=BORDER_COLOR, width=1, tags="headers")
        
        headers = ["CHAR", "A", "B", "C", "D", "E", "F", "G", "DP", "HEX BYTE"]
        cx = self.start_x
        for i, header in enumerate(headers):
            w = self.col_widths[i]
            col_cx = cx + w/2
            self.create_text(col_cx, 38, text=header, fill=TEXT_MUTED, font=("Consolas", 8, "bold"), tags="headers")
            cx += w + 20
            
        self.create_line(15, 45, 565, 45, fill=BORDER_COLOR, width=1, tags="headers")

    def draw_table_rows(self):
        self.delete("rows")
        
        cy = self.start_y + 10
        for idx, char in enumerate(CHAR_ORDER):
            states = SEGMENT_MAP[char]
            
            raw_bits = [states[7], states[6], states[5], states[4], states[3], states[2], states[1], states[0]]
            logic_bits = [0 if bit == 1 else 1 for bit in raw_bits] if self.common_anode else raw_bits
            byte_val = 0
            for bit in logic_bits:
                byte_val = (byte_val << 1) | bit
            
            is_active_row = (char == self.active_row_char)
            bg_color = "#202E4C" if is_active_row else ("#0D1321" if idx % 2 == 0 else BG_CARD)
            border_col = "#FF6B35" if is_active_row else ""
            
            row_id = self.create_rectangle(15, cy - 8, 565, cy + 8, fill=bg_color, outline=border_col, width=1 if is_active_row else 0, tags="rows")
            self.tag_bind(row_id, "<Button-1>", lambda event, c=char: self.on_row_click(c))
            
            cx = self.start_x
            
            # Character Column
            cell_cx = cx + self.col_widths[0]/2
            t_id = self.create_text(cell_cx, cy, text=char if char != ' ' else "[BLANK]", fill=COLOR_OP if is_active_row else TEXT_LIGHT, font=("Consolas", 8, "bold"), tags="rows")
            self.tag_bind(t_id, "<Button-1>", lambda event, c=char: self.on_row_click(c))
            cx += self.col_widths[0] + 20
            
            # Segments A-G, DP Columns
            for seg_idx, bit in enumerate(states):
                disp_bit = (0 if bit == 1 else 1) if self.common_anode else bit
                cell_cx = cx + self.col_widths[seg_idx + 1]/2
                bit_color = "#10B981" if disp_bit == (0 if self.common_anode else 1) else TEXT_MUTED
                if is_active_row:
                    bit_color = VFD_ON
                
                t_id2 = self.create_text(cell_cx, cy, text=str(disp_bit), fill=bit_color, font=("Consolas", 8), tags="rows")
                self.tag_bind(t_id2, "<Button-1>", lambda event, c=char: self.on_row_click(c))
                cx += self.col_widths[seg_idx + 1] + 20
                
            # Hex Column
            cell_cx = cx + self.col_widths[9]/2
            hex_str = f"0x{byte_val:02X}"
            t_id3 = self.create_text(cell_cx, cy, text=hex_str, fill="#F59E0B" if is_active_row else TEXT_MUTED, font=("Consolas", 8, "bold"), tags="rows")
            self.tag_bind(t_id3, "<Button-1>", lambda event, c=char: self.on_row_click(c))
            
            cy += self.row_height

    def on_row_click(self, char):
        if hasattr(self, 'row_click_callback') and self.row_click_callback:
            self.row_click_callback(char)

    def set_active_row(self, char, common_anode=False):
        self.common_anode = common_anode
        
        # Norm maps
        if char == 'A' or char == 'a': char = 'A'
        elif char == 'B' or char == 'b': char = 'b'
        elif char == 'C' or char == 'c': char = 'C'
        elif char == 'D' or char == 'd': char = 'd'
        elif char == 'E' or char == 'e': char = 'E'
        elif char == 'F' or char == 'f': char = 'F'
        
        self.active_row_char = char if char in CHAR_ORDER or char is None else None
        self.draw_table_rows()


# ==============================================================================
# CLASS: CALCULATORENGINE (LOGICAL MATH ENGINE)
# ==============================================================================
class CalculatorEngine:
    def __init__(self):
        self.expression = ""
        self.display_value = "0"
        self.is_result_shown = False
        self.max_digits = 8
        
        # Operand states for logic processes
        self.operand_a = None
        self.operand_b = None
        self.operator = None

    def press_key(self, key):
        if key == 'C':
            self.expression = ""
            self.display_value = "0"
            self.is_result_shown = False
            self.operand_a = None
            self.operand_b = None
            self.operator = None
        elif key == 'CE':
            if self.is_result_shown:
                self.expression = ""
                self.display_value = "0"
                self.is_result_shown = False
                self.operand_a = None
                self.operand_b = None
                self.operator = None
            else:
                if len(self.display_value) > 1:
                    if self.display_value[-1] == '.' and len(self.display_value) > 2:
                        self.display_value = self.display_value[:-2]
                    else:
                        self.display_value = self.display_value[:-1]
                else:
                    self.display_value = "0"
        elif key == '+/-':
            if self.display_value != "0" and self.display_value != "Error":
                if self.display_value.startswith('-'):
                    self.display_value = self.display_value[1:]
                else:
                    self.display_value = '-' + self.display_value
        elif key in ['+', '-', '*', '/']:
            if self.expression != "" and not self.is_result_shown and self.display_value != "0":
                # Chaining operations
                try:
                    full_expr = self.expression + self.display_value
                    val = eval(full_expr.replace(' ', ''))
                    self.operand_a = val
                    self.expression = str(val) + " " + key + " "
                except Exception:
                    self.operand_a = 0.0
                    self.expression = "0 " + key + " "
            else:
                if self.is_result_shown:
                    self.expression = self.display_value + " " + key + " "
                    self.is_result_shown = False
                else:
                    if self.expression == "" or self.display_value != "0":
                        self.expression += self.display_value + " " + key + " "
                    else:
                        self.expression = self.expression[:-3] + " " + key + " "
                
                try:
                    self.operand_a = float(self.display_value)
                except ValueError:
                    self.operand_a = 0.0
            
            self.operator = key
            self.operand_b = None
            self.display_value = "0"
        elif key == '=':
            if self.expression != "":
                try:
                    self.operand_b = float(self.display_value)
                except ValueError:
                    self.operand_b = 0.0
                
                full_expr = self.expression + self.display_value
                try:
                    val = eval(full_expr.replace(' ', ''))
                    if isinstance(val, float):
                        if val.is_integer():
                            self.display_value = str(int(val))
                        else:
                            self.display_value = self.format_float(val)
                    else:
                        self.display_value = str(val)
                    
                    if len(self.display_value.replace('.', '')) > self.max_digits:
                        if abs(val) > 99999999:
                            self.display_value = "Error"
                        else:
                            self.display_value = self.format_float(val)
                except ZeroDivisionError:
                    self.display_value = "Error"
                except Exception:
                    self.display_value = "Error"
                
                self.expression = full_expr + " ="
                self.is_result_shown = True
        elif key == '.':
            if self.is_result_shown:
                self.display_value = "0."
                self.expression = ""
                self.is_result_shown = False
            elif '.' not in self.display_value:
                if len(self.display_value.replace('-', '')) < self.max_digits:
                    self.display_value += '.'
        else: # Digits 0-9
            if self.display_value == "0" or self.is_result_shown or self.display_value == "Error":
                self.display_value = key
                if self.is_result_shown:
                    self.expression = ""
                    self.is_result_shown = False
                    self.operand_a = None
                    self.operand_b = None
                    self.operator = None
            else:
                length = len(self.display_value.replace('-', '').replace('.', ''))
                if length < self.max_digits:
                    self.display_value += key
                    
        return self.expression, self.display_value

    def format_float(self, value):
        is_neg = value < 0
        max_len = 7 if is_neg else 8
        s_val = f"{value:.10f}"
        if '.' in s_val:
            integer_part, decimal_part = s_val.split('.')
            integer_len = len(integer_part.replace('-', ''))
            
            if integer_len > max_len:
                return "Error"
                
            allowed_decimals = max_len - integer_len
            if allowed_decimals > 0:
                truncated = f"{value:.{allowed_decimals}f}"
                while truncated.endswith('0') and '.' in truncated:
                    truncated = truncated[:-1]
                if truncated.endswith('.'):
                    truncated = truncated[:-1]
                return truncated
            else:
                return integer_part
        return str(value)


# ==============================================================================
# MAIN APPLICATION WINDOW
# ==============================================================================
class CalculatorApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Neon 7-Segment Laboratory Console")
        self.geometry("1100x700")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)

        self.common_anode = False
        self.calc_engine = CalculatorEngine()
        
        # State: last active character and dot for decoder breakdown
        self.active_char = '0'
        self.active_dp = False
        
        self.setup_header()
        self.setup_layout()
        self.update_system_state()

    def setup_header(self):
        header_frame = tk.Frame(self, bg=BG_MAIN, height=60)
        header_frame.pack(side="top", fill="x", padx=25, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        # LED blinking animation
        self.led_canvas = tk.Canvas(header_frame, width=20, height=20, bg=BG_MAIN, bd=0, highlightthickness=0)
        self.led_canvas.pack(side="left", padx=(0, 10))
        self.led_dot = self.led_canvas.create_oval(3, 3, 17, 17, fill="#10B981", outline="#34D399", width=1)
        self.blink_state = True
        self.blink_led()
        
        text_frame = tk.Frame(header_frame, bg=BG_MAIN)
        text_frame.pack(side="left")
        
        lbl_title = tk.Label(text_frame, text="7-SEGMENT DIGITAL CODER & CALCULATOR", bg=BG_MAIN, fg=TEXT_LIGHT, font=("Consolas", 14, "bold"), anchor="w")
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(text_frame, text="DIGITAL CIRCUIT LABS · HARDWARE INTERACTIVE SCHEMATIC", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8), anchor="w")
        lbl_sub.pack(anchor="w")

        control_frame = tk.Frame(header_frame, bg=BG_MAIN)
        control_frame.pack(side="right", fill="y")
        
        lbl_toggle = tk.Label(control_frame, text="LOGIC STANDARD:", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        lbl_toggle.pack(side="left", padx=5)
        
        self.btn_mode = tk.Label(control_frame, text="COMMON CATHODE", bg="#1E293B", fg="#10B981", font=("Consolas", 9, "bold"), 
                                 padx=12, pady=6, bd=1, relief="solid", highlightbackground=BORDER_COLOR, cursor="hand2")
        self.btn_mode.pack(side="left", padx=5)
        self.btn_mode.bind("<Button-1>", self.toggle_logic_mode)
        self.btn_mode.bind("<Enter>", lambda e: self.btn_mode.config(bg="#2D3D5A"))
        self.btn_mode.bind("<Leave>", lambda e: self.btn_mode.config(bg="#1E293B"))

    def blink_led(self):
        color = "#10B981" if self.blink_state else "#064E3B"
        glow = "#34D399" if self.blink_state else "#022C22"
        self.led_canvas.itemconfig(self.led_dot, fill=color, outline=glow)
        self.blink_state = not self.blink_state
        self.after(1000, self.blink_led)

    def setup_layout(self):
        main_container = tk.Frame(self, bg=BG_MAIN)
        main_container.pack(side="top", fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Left Panel (Calculator Frame)
        left_panel = tk.Frame(main_container, bg=BG_MAIN, width=420)
        left_panel.pack(side="left", fill="both", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        # VFD Display Chassis
        display_chassis = tk.Frame(left_panel, bg="#080E18", bd=2, relief="sunken", highlightthickness=1, highlightbackground=BORDER_COLOR)
        display_chassis.pack(side="top", fill="x", pady=(0, 15))
        
        self.lbl_expr = tk.Label(display_chassis, text="", bg="#050B14", fg=COLOR_OP, font=("Consolas", 10), anchor="e", height=1, padx=15, pady=5)
        self.lbl_expr.pack(side="top", fill="x")
        
        self.vfd_screen = VFDDisplay(display_chassis, width=416, height=110)
        self.vfd_screen.pack(side="top", fill="x", padx=2, pady=(0, 2))
        self.vfd_screen.on_digit_hover_callback = self.on_digit_hovered
        
        # Keypad chassis
        keypad_frame = tk.Frame(left_panel, bg=BG_CARD, bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=15, pady=15)
        keypad_frame.pack(side="top", fill="both", expand=True)
        
        buttons = [
            ('C', 'fn'),  ('CE', 'fn'), ('+/-', 'fn'), ('/', 'op'),
            ('7', 'num'), ('8', 'num'), ('9', 'num'),  ('*', 'op'),
            ('4', 'num'), ('5', 'num'), ('6', 'num'),  ('-', 'op'),
            ('1', 'num'), ('2', 'num'), ('3', 'num'),  ('+', 'op'),
            ('0', 'num'), ('.', 'num'), ('=', 'eq'),   (None, None)
        ]
        
        for c in range(4):
            keypad_frame.columnconfigure(c, weight=1)
        for r in range(5):
            keypad_frame.rowconfigure(r, weight=1)
            
        btn_idx = 0
        for r in range(5):
            for c in range(4):
                if btn_idx >= len(buttons):
                    break
                text, btn_type = buttons[btn_idx]
                if text is None:
                    btn_idx += 1
                    continue
                    
                btn = self.create_keypad_button(keypad_frame, text, btn_type)
                if text == '=':
                    btn.grid(row=r, column=c, columnspan=2, padx=4, pady=4, sticky="nsew")
                    btn_idx += 1
                else:
                    btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                
                btn_idx += 1
                
        # Right Panel (Tabbed Notebook / Dashboard)
        right_panel = tk.Frame(main_container, bg=BG_MAIN)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # 1. Custom Tab Bar Frame
        self.tab_bar = tk.Frame(right_panel, bg=BG_MAIN)
        self.tab_bar.pack(side="top", fill="x", pady=(0, 10))
        
        # Tab definitions
        self.tabs = [
            ("Logic & Pin Map", self.show_tab_logic),
            ("Step-by-Step Flow", self.show_tab_steps),
            ("Binary & Encoder", self.show_tab_binary),
            ("Truth Table & Diagrams", self.show_tab_truth)
        ]
        self.tab_buttons = []
        self.tab_frames = []
        
        # Tab container frame where panels will go
        self.tab_container = tk.Frame(right_panel, bg=BG_MAIN)
        self.tab_container.pack(side="top", fill="both", expand=True)
        
        # Tab 1: Logic & Pin Map Frame
        self.frame_logic = tk.Frame(self.tab_container, bg=BG_MAIN)
        self.pin_mapper = PinMapperWidget(self.frame_logic, width=280, height=280)
        self.pin_mapper.pack(side="left", fill="both", expand=False)
        self.pin_mapper.on_hover_change_callback = self.on_pin_or_segment_hovered
        
        self.decoder_details = DecoderDetailsWidget(self.frame_logic, height=280)
        self.decoder_details.pack(side="left", fill="both", expand=True, padx=(15, 0))
        self.tab_frames.append(self.frame_logic)
        
        # Tab 2: Step-by-Step Flow Frame
        self.frame_steps = tk.Frame(self.tab_container, bg=BG_MAIN)
        self.step_flow = StepFlowWidget(self.frame_steps, height=590)
        self.step_flow.pack(fill="both", expand=True)
        self.tab_frames.append(self.frame_steps)
        
        # Tab 3: Binary & Encoder Frame
        self.frame_binary = tk.Frame(self.tab_container, bg=BG_MAIN)
        self.dec_to_bin = DecToBinWidget(self.frame_binary, width=280, height=590)
        self.dec_to_bin.pack(side="left", fill="both", expand=False)
        
        self.seg_encode = SegEncodeWidget(self.frame_binary, height=590)
        self.seg_encode.pack(side="left", fill="both", expand=True, padx=(15, 0))
        self.tab_frames.append(self.frame_binary)
        
        # Tab 4: Truth Table & Diagrams Frame
        self.frame_truth = tk.Frame(self.tab_container, bg=BG_MAIN)
        self.truth_table = TruthTableWidget(self.frame_truth, height=480)
        self.truth_table.pack(side="top", fill="both", expand=True)
        self.truth_table.row_click_callback = self.on_truth_table_row_clicked
        
        self.active_diagrams = MiniActiveDiagramWidget(self.frame_truth, height=100)
        self.active_diagrams.pack(side="top", fill="x", pady=(10, 0))
        self.tab_frames.append(self.frame_truth)
        
        # Pack Tab Buttons
        for idx, (title, cmd) in enumerate(self.tabs):
            btn = tk.Label(self.tab_bar, text=title, bg="#111827", fg=TEXT_MUTED, font=("Consolas", 9, "bold"),
                           padx=15, pady=8, bd=1, relief="solid", highlightbackground=BORDER_COLOR, cursor="hand2")
            btn.pack(side="left", padx=(0, 5))
            btn.bind("<Button-1>", lambda event, i=idx: self.select_tab(i))
            self.tab_buttons.append(btn)
            
        self.select_tab(0)

    def select_tab(self, idx):
        # Hide all frames and reset buttons
        for i, frame in enumerate(self.tab_frames):
            frame.pack_forget()
            self.tab_buttons[i].config(bg="#111827", fg=TEXT_MUTED, highlightbackground=BORDER_COLOR)
            
        # Show active frame and highlight active button
        self.tab_frames[idx].pack(fill="both", expand=True)
        self.tab_buttons[idx].config(bg=BG_CARD, fg=VFD_ON, highlightbackground=VFD_ON_GLOW)

    def show_tab_logic(self): pass
    def show_tab_steps(self): pass
    def show_tab_binary(self): pass
    def show_tab_truth(self): pass

    def create_keypad_button(self, parent, text, btn_type):
        if btn_type == 'num':
            normal_bg, hover_bg, text_color = "#1E293B", "#334155", TEXT_LIGHT
        elif btn_type == 'op':
            normal_bg, hover_bg, text_color = "#2D3E5E", "#FF6B35", COLOR_OP
        elif btn_type == 'eq':
            normal_bg, hover_bg, text_color = "#0A5C43", "#10B981", TEXT_LIGHT
        elif btn_type == 'fn':
            normal_bg, hover_bg, text_color = "#471D22", "#EF4444", TEXT_LIGHT
            
        lbl = tk.Label(parent, text=text, bg=normal_bg, fg=text_color, font=("Consolas", 14, "bold"),
                       bd=1, relief="solid", highlightbackground=BORDER_COLOR, cursor="hand2", width=5, height=2)
        
        lbl.bind("<Enter>", lambda event: lbl.config(bg=hover_bg, fg=TEXT_LIGHT if btn_type == 'op' else text_color))
        lbl.bind("<Leave>", lambda event: lbl.config(bg=normal_bg, fg=text_color))
        lbl.bind("<Button-1>", lambda event, k=text: self.on_keypad_press(k))
        
        return lbl

    def toggle_logic_mode(self, event):
        self.common_anode = not self.common_anode
        if self.common_anode:
            self.btn_mode.config(text="COMMON ANODE", fg=COLOR_OP)
        else:
            self.btn_mode.config(text="COMMON CATHODE", fg="#10B981")
        self.update_system_state()

    def on_keypad_press(self, key):
        expr, disp = self.calc_engine.press_key(key)
        self.lbl_expr.config(text=expr)
        self.update_system_state()

    def update_system_state(self):
        disp_val = self.calc_engine.display_value
        parsed_digits = self.vfd_screen.set_display_string(disp_val, self.common_anode)
        
        active_idx = 7
        if self.vfd_screen.hovered_digit_idx is not None:
            active_idx = self.vfd_screen.hovered_digit_idx
        else:
            for idx in range(7, -1, -1):
                if parsed_digits[idx][0] != ' ':
                    active_idx = idx
                    break
        
        char, dp = parsed_digits[active_idx]
        self.active_char = char
        self.active_dp = dp
        
        self.pin_mapper.draw_logic_state(char, dp, self.common_anode)
        self.decoder_details.update_decoder(char, dp, self.common_anode)
        self.truth_table.set_active_row(char, self.common_anode)
        
        # === NEW VISUALIZATIONS ===
        a = self.calc_engine.operand_a
        b = self.calc_engine.operand_b
        op = self.calc_engine.operator
        rStr = self.calc_engine.display_value
        
        self.step_flow.update_steps(a, b, op, rStr, disp_val)
        self.dec_to_bin.update_binary_tables(a, b, rStr, disp_val)
        self.seg_encode.update_encoder_cards(disp_val, self.common_anode)
        self.active_diagrams.update_diagrams(disp_val, self.common_anode)

    def on_digit_hovered(self, digit_idx):
        self.update_system_state()

    def on_pin_or_segment_hovered(self, hovered_seg):
        self.vfd_screen.set_display_string(self.calc_engine.display_value, self.common_anode, active_seg=hovered_seg)
        self.decoder_details.update_decoder(self.active_char, self.active_dp, self.common_anode, hovered_seg=hovered_seg)

    def on_truth_table_row_clicked(self, char):
        self.calc_engine.display_value = char
        self.calc_engine.expression = f"Selected: '{char}'"
        self.lbl_expr.config(text=self.calc_engine.expression)
        self.update_system_state()


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    app = CalculatorApplication()
    app.mainloop()
