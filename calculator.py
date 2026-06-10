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




# ==============================================================================
# MOUSE WHEEL SCROLLING UTILITY
# ==============================================================================
def bind_mouse_wheel_recursive(widget, canvas):
    """
    Recursively binds mouse wheel scrolling to a widget and all of its descendants,
    directing scroll events to the target canvas.
    """
    widget.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
    for child in widget.winfo_children():
        bind_mouse_wheel_recursive(child, canvas)


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
# CLASS: DECODERDETAILSWIDGET (STATS PANEL)
# ==============================================================================
class DecoderDetailsWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        # Configure row weights to stretch and fill the 300px height nicely
        self.rowconfigure(0, weight=0)  # title
        self.rowconfigure(1, weight=0)  # line separator
        self.rowconfigure(2, weight=1)  # row 2-5 are rowspan 4, we weight them
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)
        self.rowconfigure(6, weight=0)
        self.rowconfigure(7, weight=1)
        self.rowconfigure(8, weight=0)
        self.rowconfigure(9, weight=1)
        
        lbl_title = tk.Label(self, text="VISUALISASI OUTPUT ANGKA", bg=BG_CARD, fg=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        lbl_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        line = tk.Frame(self, height=1, bg=BORDER_COLOR)
        line.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        
        # Large active character preview (font size increased to 72)
        self.lbl_char_val = tk.Label(self, text="8", bg="#0D1321", fg=VFD_ON, font=("Consolas", 72, "bold"), bd=1, relief="solid", highlightbackground=BORDER_COLOR)
        self.lbl_char_val.grid(row=2, column=0, rowspan=4, padx=(15, 10), pady=5, sticky="nsew")
        
        # Segment states indicators (A-G, DP)
        self.seg_frame = tk.Frame(self, bg=BG_CARD)
        self.seg_frame.grid(row=2, column=1, rowspan=4, padx=(0, 15), pady=5, sticky="nsew")
        
        # Configure grid column & row weights on seg_frame so they stretch and fill the space
        for c in range(4):
            self.seg_frame.columnconfigure(c, weight=1)
        for r in range(2):
            self.seg_frame.rowconfigure(r, weight=1)
            
        self.seg_labels = {}
        segs = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'dp']
        for idx, s in enumerate(segs):
            r = idx // 4
            c = idx % 4
            f = tk.Frame(self.seg_frame, bg="#0D1321", highlightthickness=1, highlightbackground=BORDER_COLOR)
            f.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            
            lbl_name = tk.Label(f, text=s.upper(), bg="#0D1321", fg=TEXT_MUTED, font=("Consolas", 10, "bold"))
            lbl_name.pack(side="top", fill="both", expand=True)
            lbl_val = tk.Label(f, text="1", bg="#0D1321", fg=VFD_ON, font=("Consolas", 12, "bold"))
            lbl_val.pack(side="top", fill="both", expand=True)
            
            self.seg_labels[s] = (f, lbl_name, lbl_val)
            
        self.lbl_bin_lbl = tk.Label(self, text="BINARY [dp,g,f,e,d,c,b,a]:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold"), anchor="w")
        self.lbl_bin_lbl.grid(row=6, column=0, columnspan=2, padx=15, pady=(12, 2), sticky="w")
        self.lbl_bin_val = tk.Label(self, text="0b01111111", bg="#0D1321", fg="#F59E0B", font=("Consolas", 12, "bold"), anchor="w", padx=10, pady=5)
        self.lbl_bin_val.grid(row=7, column=0, columnspan=2, padx=15, pady=(0, 8), sticky="nsew")
        
        self.lbl_hex_lbl = tk.Label(self, text="HEXADECIMAL BYTEVALUE:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold"), anchor="w")
        self.lbl_hex_lbl.grid(row=8, column=0, columnspan=2, padx=15, pady=(2, 2), sticky="w")
        self.lbl_hex_val = tk.Label(self, text="0x7F", bg="#0D1321", fg=COLOR_EQ, font=("Consolas", 12, "bold"), anchor="w", padx=10, pady=5)
        self.lbl_hex_val.grid(row=9, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="nsew")

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
        
        # Mousewheel scroll binding for text box
        self.text_area.bind("<MouseWheel>", lambda event: self.text_area.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
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
# CLASS: DECTOBINWIDGET (DECIMAL -> BINARY CONVERT GRID WITH CENTERING)
# ==============================================================================
class DecToBinWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        # Pop height if it exists so we can size to fit contents automatically
        kwargs.pop('height', None)
        super().__init__(parent, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, **kwargs)
        
        self.last_a = None
        self.last_b = None
        self.last_rStr = "0"
        self.last_current_val = "0"
        
        # Title Card
        self.lbl_title = tk.Label(self, text="DECIMAL → BINARY WEIGHT TABLES", bg=BG_CARD, fg=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
        self.lbl_title.pack(side="top", fill="x", padx=15, pady=(15, 5))
        
        self.line = tk.Frame(self, height=1, bg=BORDER_COLOR)
        self.line.pack(side="top", fill="x", padx=15, pady=(0, 10))
        
        # Container frame for active tables
        self.tables_container = tk.Frame(self, bg=BG_CARD)
        self.tables_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Tooltip label at the bottom
        self.lbl_tooltip = tk.Label(self, text="Press operations to analyze values", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "italic"))
        self.lbl_tooltip.pack(side="bottom", fill="x", pady=(5, 15))
        
        self.update_binary_tables(self.last_a, self.last_b, self.last_rStr, self.last_current_val)

    def update_binary_tables(self, a, b, rStr, current_val):
        self.last_a = a
        self.last_b = b
        self.last_rStr = rStr
        self.last_current_val = current_val
        
        # Clear previous tables
        for widget in self.tables_container.winfo_children():
            widget.destroy()
            
        # List of values to render
        values_to_render = []
        if a is not None:
            values_to_render.append(("Operand A", a))
        if b is not None:
            values_to_render.append(("Operand B", b))
        else:
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
                
        if not values_to_render:
            lbl_empty = tk.Label(self.tables_container, text="No numeric inputs to convert", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 9))
            lbl_empty.pack(pady=20, fill="x")
            return
            
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
            
            # Table Frame
            tbl_frame = tk.Frame(self.tables_container, bg=BG_CARD)
            tbl_frame.pack(fill="x", pady=8)
            
            # 1. Header label
            lbl_hdr = tk.Label(tbl_frame, text=f"▶ {title} = {val}{neg_label}", bg=BG_CARD, fg=COLOR_OP if title == "Result" else TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w")
            lbl_hdr.pack(fill="x", pady=(0, 5))
            
            # 2. Grid for the 4 columns x 2 rows (Flexbox-like alignment)
            grid_frame = tk.Frame(tbl_frame, bg=BG_CARD)
            grid_frame.pack(fill="x")
            for c in range(4):
                grid_frame.columnconfigure(c, weight=1, uniform="bits")
                
            weights = ["128", "64", "32", "16", "8", "4", "2", "1"]
            for idx, w in enumerate(weights):
                col_idx = idx % 4
                row_idx = 0 if idx < 4 else 1
                
                # Cell Frame
                cell = tk.Frame(grid_frame, bg=BG_CARD)
                cell.grid(row=row_idx, column=col_idx, padx=4, pady=3, sticky="ew")
                
                # Weight Label
                lbl_w = tk.Label(cell, text=w, bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 9, "bold"))
                lbl_w.pack(side="top", fill="x")
                
                bit = bin_str[idx]
                cell_bg = "#10B981" if bit == '1' else "#0D1321"
                cell_fg = TEXT_LIGHT if bit == '1' else "#1E293B"
                cell_border = "#34D399" if bit == '1' else BORDER_COLOR
                
                # Bit value container (represented as a Label with border)
                lbl_b = tk.Label(cell, text=bit, bg=cell_bg, fg=cell_fg, font=("Consolas", 12, "bold"), bd=1, relief="solid", highlightbackground=cell_border, height=1, pady=3)
                lbl_b.pack(side="top", fill="x", pady=(2, 0))
                
            # 3. Footer summary label
            lbl_ftr = tk.Label(tbl_frame, text=f"HEX: 0x{val_i:02X}  |  OCT: {val_i:o}  |  BIN: 0b{bin_str}", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold"), anchor="w")
            lbl_ftr.pack(fill="x", pady=(5, 0))





# ==============================================================================
# CLASS: TRUTHTABLEWIDGET (LIVE HIGHLIGHTING TRUTH TABLE WITH CENTERING)
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
        
        self.bind("<Configure>", self.on_canvas_configure)
        
        self.draw_table_headers()
        self.draw_table_rows()

    def on_canvas_configure(self, event):
        # Center truth table columns
        total_col_width = sum(self.col_widths) + 20 * (len(self.col_widths) - 1)
        self.start_x = max(20, (event.width - total_col_width) // 2)
        
        self.draw_table_headers()
        self.draw_table_rows()

    def draw_table_headers(self):
        self.delete("headers")
        
        # Dynamic line width
        canvas_width = max(580, self.winfo_width())
        self.create_text(15, 18, text="TRUTH TABLE SEVEN SEGMENT (ABCDEFG)", fill=TEXT_LIGHT, font=("Consolas", 10, "bold"), anchor="w", tags="headers")
        self.create_line(15, 28, canvas_width - 15, 28, fill=BORDER_COLOR, width=1, tags="headers")
        
        headers = ["CHAR", "A", "B", "C", "D", "E", "F", "G", "DP", "HEX BYTE"]
        cx = self.start_x
        for i, header in enumerate(headers):
            w = self.col_widths[i]
            col_cx = cx + w/2
            self.create_text(col_cx, 38, text=header, fill=TEXT_MUTED, font=("Consolas", 8, "bold"), tags="headers")
            cx += w + 20
            
        self.create_line(15, 45, canvas_width - 15, 45, fill=BORDER_COLOR, width=1, tags="headers")

    def draw_table_rows(self):
        self.delete("rows")
        
        canvas_width = max(580, self.winfo_width())
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
            
            # Row Background spans the centered section
            row_id = self.create_rectangle(15, cy - 8, canvas_width - 15, cy + 8, fill=bg_color, outline=border_col, width=1 if is_active_row else 0, tags="rows")
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
# MAIN APPLICATION WINDOW WITH RESIZABLE FULLSCREEN SUPPORT
# ==============================================================================
class CalculatorApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Neon 7-Segment Laboratory Console")
        self.geometry("1100x700")
        self.configure(bg=BG_MAIN)
        
        # ENABLE RESIZING & FULLSCREEN
        self.resizable(True, True)
        self.minsize(1050, 650)
        
        # Keyboard binds for full screen toggle
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        self.common_anode = False
        self.calc_engine = CalculatorEngine()
        
        # State: last active character and dot for decoder breakdown
        self.active_char = '0'
        self.active_dp = False
        
        self.setup_header()
        self.setup_layout()
        self.update_system_state()

    def toggle_fullscreen(self, event=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))
        return "break"
        
    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)
        return "break"

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
        lbl_sub = tk.Label(text_frame, text="DIGITAL CIRCUIT LABS · HARDWARE INTERACTIVE SCHEMATIC · (Press F11 for Full Screen)", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8), anchor="w")
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
        
        # Left Panel (Calculator Frame) - Fixed Width, Fills Vertically
        left_panel = tk.Frame(main_container, bg=BG_MAIN, width=420)
        left_panel.pack(side="left", fill="y", padx=(0, 20), expand=False)
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
                
        # Right Panel (Unified Scrollable Dashboard) - Fills All Remaining Space
        right_panel = tk.Frame(main_container, bg=BG_MAIN)
        right_panel.pack(side="left", fill="both", expand=True)
        
        self.right_canvas = tk.Canvas(right_panel, bg=BG_MAIN, bd=0, highlightthickness=0)
        self.right_canvas.pack(side="left", fill="both", expand=True)
        
        self.right_scrollbar = tk.Scrollbar(right_panel, command=self.right_canvas.yview, width=10, bg=BG_MAIN, bd=0)
        self.right_scrollbar.pack(side="right", fill="y")
        self.right_canvas.config(yscrollcommand=self.right_scrollbar.set)
        
        self.right_container = tk.Frame(self.right_canvas, bg=BG_MAIN)
        self.canvas_window = self.right_canvas.create_window((0, 0), window=self.right_container, anchor="nw")
        
        self.right_container.bind("<Configure>", self.on_right_container_configure)
        self.right_canvas.bind("<Configure>", self.on_right_canvas_configure)
        self.right_canvas.bind("<MouseWheel>", self.on_main_scroll)
        
        # 1. Decoder Details (Visualisasi Output Angka)
        self.decoder_details = DecoderDetailsWidget(self.right_container, height=300)
        self.decoder_details.pack(fill="x", pady=(0, 15))
        
        # 2. Decimal to Binary Table
        self.dec_to_bin = DecToBinWidget(self.right_container)
        self.dec_to_bin.pack(fill="x", pady=(0, 15))
        
        # 3. Step-by-Step Flow
        self.step_flow = StepFlowWidget(self.right_container, height=300)
        self.step_flow.pack(fill="x", pady=(0, 15))
        
        # 4. Truth Table
        self.truth_table = TruthTableWidget(self.right_container, height=350)
        self.truth_table.pack(fill="x", pady=(0, 15))
        self.truth_table.row_click_callback = self.on_truth_table_row_clicked
        
        self.bind_scroll_recursive(self.right_container)

    def on_right_container_configure(self, event):
        self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
        
    def on_right_canvas_configure(self, event):
        canvas_width = event.width
        self.right_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
    def on_main_scroll(self, event):
        if hasattr(self, 'step_flow') and event.widget == self.step_flow.text_area:
            return
        self.right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_scroll_recursive(self, widget):
        if not hasattr(self, 'step_flow') or widget != self.step_flow.text_area:
            widget.bind("<MouseWheel>", self.on_main_scroll)
        for child in widget.winfo_children():
            self.bind_scroll_recursive(child)

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
        
        self.decoder_details.update_decoder(char, dp, self.common_anode)
        self.truth_table.set_active_row(char, self.common_anode)
        
        # === NEW VISUALIZATIONS ===
        a = self.calc_engine.operand_a
        b = self.calc_engine.operand_b
        op = self.calc_engine.operator
        rStr = self.calc_engine.display_value
        
        self.step_flow.update_steps(a, b, op, rStr, disp_val)
        self.dec_to_bin.update_binary_tables(a, b, rStr, disp_val)
        
        # Re-bind scrolling to include any new widgets
        self.bind_scroll_recursive(self.right_container)

    def on_digit_hovered(self, digit_idx):
        self.update_system_state()

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
