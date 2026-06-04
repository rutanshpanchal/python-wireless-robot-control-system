import socket
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import math
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════
ESP_IP   = "10.47.152.17"
PORT     = 80
TIMEOUT  = 3
LOG_FILE = "car_log.txt"

# ═══════════════════════════════════════════════════════════════
#   THEME  —  Cyberpunk HUD
# ═══════════════════════════════════════════════════════════════
BG        = "#040608"
PANEL     = "#080c12"
PANEL2    = "#0c1018"
BORDER    = "#1a2235"
ACCENT    = "#00d4ff"
ACCENT2   = "#ff2d55"
ACCENT3   = "#39ff14"
YELLOW    = "#ffd60a"
DIM       = "#1e2d3d"
TXT_PRI   = "#cdd6f4"
TXT_SEC   = "#45566e"
TXT_DIM   = "#1e2d3d"
GREEN     = "#39ff14"
RED       = "#ff2d55"
ORANGE    = "#ff9f0a"

SPEED_STEP = 25

# ═══════════════════════════════════════════════════════════════
#   STATE  (no tk.IntVar here — created after root)
# ═══════════════════════════════════════════════════════════════
cmd_count     = 0
session_start = time.time()
current_dir   = "IDLE"
auto_running  = False
is_connected  = False

# ═══════════════════════════════════════════════════════════════
#   SOCKET
# ═══════════════════════════════════════════════════════════════
def send_command(cmd, label=None):
    def _send():
        global cmd_count, current_dir, is_connected
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect((ESP_IP, PORT))
            spd = speed_val.get()
            request = (
                f"GET /{cmd}?speed={spd} HTTP/1.1\r\n"
                f"Host: {ESP_IP}\r\nConnection: close\r\n\r\n"
            )
            s.sendall(request.encode())
            s.close()

            cmd_count   += 1
            current_dir  = label or cmd
            is_connected = True

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"[{ts}]  {label or cmd}  (speed={spd})\n")

            root.after(0, lambda: _update_status(f"✓  {label or cmd}", GREEN))
            root.after(0, lambda: _log(f"  {_ts()}   {label or cmd}   spd={spd}"))
            root.after(0, _refresh_stats)
            root.after(0, lambda: _set_indicator(True))
            root.after(0, lambda: _update_direction(label or cmd))

        except socket.timeout:
            is_connected = False
            root.after(0, lambda: _update_status("✗  Timed out", RED))
            root.after(0, lambda: _log(f"  {_ts()}   [!] Timeout — {cmd}"))
            root.after(0, lambda: _set_indicator(False))
        except ConnectionRefusedError:
            is_connected = False
            root.after(0, lambda: _update_status("✗  Connection refused", RED))
            root.after(0, lambda: _log(f"  {_ts()}   [!] Refused — {cmd}"))
            root.after(0, lambda: _set_indicator(False))
        except Exception as e:
            is_connected = False
            root.after(0, lambda: _update_status(f"✗  {e}", RED))
            root.after(0, lambda: _log(f"  {_ts()}   [!] Error: {e}"))
            root.after(0, lambda: _set_indicator(False))

    threading.Thread(target=_send, daemon=True).start()


def test_connection():
    _update_status("◌  Pinging…", YELLOW)

    def _ping():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect((ESP_IP, PORT))
            s.close()
            root.after(0, lambda: _update_status("✓  ESP32 Online", GREEN))
            root.after(0, lambda: _log(f"  {_ts()}   PING OK — {ESP_IP}:{PORT}"))
            root.after(0, lambda: _set_indicator(True))
        except Exception as e:
            root.after(0, lambda: _update_status("✗  Unreachable", RED))
            root.after(0, lambda: _log(f"  {_ts()}   PING FAIL: {e}"))
            root.after(0, lambda: _set_indicator(False))

    threading.Thread(target=_ping, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
#   AUTO MODE
# ═══════════════════════════════════════════════════════════════
def auto_mode():
    global auto_running
    if auto_running:
        return
    auto_running = True
    auto_btn.config(state="disabled", fg=TXT_SEC)
    _update_status("⚡  Auto Mode Running", YELLOW)
    _log(f"  {_ts()}   AUTO MODE started")

    seq = [
        (0,    'F', "Forward"),
        (2000, 'L', "Turn Left"),
        (3000, 'F', "Forward"),
        (5000, 'R', "Turn Right"),
        (6000, 'S', "Stop"),
    ]
    for delay, cmd, label in seq:
        root.after(delay, lambda c=cmd, l=label: send_command(c, l))

    def _done():
        global auto_running
        auto_running = False
        auto_btn.config(state="normal", fg=YELLOW)
        _update_status("✓  Auto Mode Done", GREEN)
        _log(f"  {_ts()}   AUTO MODE finished")

    root.after(6500, _done)


# ═══════════════════════════════════════════════════════════════
#   HELPERS
# ═══════════════════════════════════════════════════════════════
def _ts():
    return datetime.now().strftime("%H:%M:%S")

def _update_status(msg, color=TXT_PRI):
    status_label.config(text=msg, fg=color)

def _log(msg):
    log_box.config(state="normal")
    log_box.insert("end", msg + "\n")
    log_box.see("end")
    log_box.config(state="disabled")

def _set_indicator(online: bool):
    color = GREEN if online else RED
    conn_dot.config(bg=color)
    conn_lbl.config(text="ONLINE" if online else "OFFLINE", fg=color)

def _update_direction(label):
    dir_canvas.delete("all")
    _draw_direction_arrow(label)
    dir_text.config(text=label.upper())

def _refresh_stats():
    elapsed = int(time.time() - session_start)
    m, s = divmod(elapsed, 60)
    stat_cmds.config(text=str(cmd_count))
    stat_time.config(text=f"{m:02d}:{s:02d}")
    stat_spd.config(text=f"{speed_val.get()}%")

def _refresh_time():
    elapsed = int(time.time() - session_start)
    m, s = divmod(elapsed, 60)
    stat_time.config(text=f"{m:02d}:{s:02d}")
    root.after(1000, _refresh_time)


# ═══════════════════════════════════════════════════════════════
#   DIRECTION ARROW CANVAS
# ═══════════════════════════════════════════════════════════════
def _draw_direction_arrow(label="IDLE"):
    cx, cy = 55, 55
    r = 38
    dir_canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                           outline=BORDER, width=2, fill=PANEL2)

    arrow_map = {
        "Forward":    (0, -1),
        "Backward":   (0,  1),
        "Turn Left":  (-1, 0),
        "Turn Right": ( 1, 0),
        "Stop":       (0,  0),
        "IDLE":       (0,  0),
    }
    dx, dy = arrow_map.get(label, (0, 0))

    if dx == 0 and dy == 0:
        dir_canvas.create_oval(cx-8, cy-8, cx+8, cy+8,
                               outline=ACCENT2, width=2, fill="")
        dir_canvas.create_text(cx, cy, text="■", fill=ACCENT2,
                               font=("Courier", 10, "bold"))
    else:
        shaft = 24
        tip_x  = cx + dx * shaft
        tip_y  = cy + dy * shaft
        tail_x = cx - dx * shaft
        tail_y = cy - dy * shaft
        dir_canvas.create_line(tail_x, tail_y, tip_x, tip_y,
                               fill=ACCENT, width=3, arrow=tk.LAST,
                               arrowshape=(12, 15, 5))

    dir_canvas.create_text(cx, cy + r + 12, text=label.upper(),
                           fill=TXT_SEC, font=("Courier", 7, "bold"))


# ═══════════════════════════════════════════════════════════════
#   ANIMATED GRID
# ═══════════════════════════════════════════════════════════════
grid_offset = 0

def _animate_grid():
    global grid_offset
    grid_canvas.delete("all")
    w, h = 680, 760
    spacing = 40
    grid_offset = (grid_offset + 0.4) % spacing

    x = -spacing + grid_offset
    while x < w + spacing:
        alpha_factor = 0.5 + 0.5 * math.sin((x / w) * math.pi)
        color = _hex_alpha("#1a2235", alpha_factor * 0.6)
        grid_canvas.create_line(x, 0, x, h, fill=color, width=1)
        x += spacing

    for y in range(0, h + spacing, spacing):
        grid_canvas.create_line(0, y, w, y, fill="#0f1520", width=1)

    for i in range(3):
        sz = 18 + i * 12
        grid_canvas.create_rectangle(
            10 + i*2, 10 + i*2, 10 + sz, 10 + sz,
            outline=_hex_alpha(ACCENT, 0.15 - i*0.04), width=1)

    for i in range(3):
        sz = 18 + i * 12
        grid_canvas.create_rectangle(
            w - 10 - sz - i*2, 10 + i*2, w - 10 - i*2, 10 + sz,
            outline=_hex_alpha(ACCENT, 0.15 - i*0.04), width=1)

    root.after(30, _animate_grid)


def _hex_alpha(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"#{int(r*alpha):02x}{int(g*alpha):02x}{int(b*alpha):02x}"


# ═══════════════════════════════════════════════════════════════
#   KEYBOARD
# ═══════════════════════════════════════════════════════════════
def _key_press(event):
    mapping = {
        'w': ('F', "Forward"),    'W': ('F', "Forward"),
        'a': ('L', "Turn Left"),  'A': ('L', "Turn Left"),
        's': ('S', "Stop"),       'S': ('S', "Stop"),
        'd': ('R', "Turn Right"), 'D': ('R', "Turn Right"),
        'x': ('B', "Backward"),   'X': ('B', "Backward"),
        'Up':    ('F', "Forward"),
        'Down':  ('B', "Backward"),
        'Left':  ('L', "Turn Left"),
        'Right': ('R', "Turn Right"),
        'space': ('S', "Stop"),
    }
    key = event.keysym if event.keysym in mapping else event.char
    if key in mapping:
        cmd, label = mapping[key]
        send_command(cmd, label)
        _flash_btn(key)

def _flash_btn(key):
    btn_map = {
        'w': fwd_btn, 'W': fwd_btn, 'Up': fwd_btn,
        'a': lft_btn, 'A': lft_btn, 'Left': lft_btn,
        's': stp_btn, 'S': stp_btn, 'space': stp_btn,
        'd': rgt_btn, 'D': rgt_btn, 'Right': rgt_btn,
        'x': bwd_btn, 'X': bwd_btn, 'Down': bwd_btn,
    }
    btn = btn_map.get(key)
    if btn:
        original_bg = btn.cget("bg")
        original_fg = btn.cget("fg")
        btn.config(bg=ACCENT, fg=BG)
        root.after(180, lambda: btn.config(bg=original_bg, fg=original_fg))


# ═══════════════════════════════════════════════════════════════
#   BUTTON FACTORY
# ═══════════════════════════════════════════════════════════════
def make_btn(parent, text, cmd, label=None,
             w=13, h=2, bg=DIM, fg=TXT_PRI, accent=ACCENT):
    b = tk.Button(
        parent, text=text, width=w, height=h,
        bg=bg, fg=fg,
        activebackground=accent, activeforeground=BG,
        relief="flat", bd=0, cursor="hand2",
        font=btn_font,
        command=lambda: send_command(cmd, label or text)
    )
    b.bind("<Enter>", lambda e: b.config(bg=_hex_alpha(accent, 0.25), fg=accent))
    b.bind("<Leave>", lambda e: b.config(bg=bg, fg=fg))
    return b


# ═══════════════════════════════════════════════════════════════
#   ROOT  ←  tk.IntVar() created HERE, after Tk()
# ═══════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("ESP32 Car Control — HUD")
root.geometry("680x760")
root.resizable(False, False)
root.configure(bg=BG)

# ✅ Safe to create tk variables now
speed_val = tk.IntVar(master=root, value=100)

# Fonts
title_font   = tkfont.Font(family="Courier", size=17, weight="bold")
sub_font     = tkfont.Font(family="Courier", size=8)
btn_font     = tkfont.Font(family="Courier", size=10, weight="bold")
small_font   = tkfont.Font(family="Courier", size=8)
stat_font    = tkfont.Font(family="Courier", size=18, weight="bold")
statlbl_font = tkfont.Font(family="Courier", size=7)
log_font     = tkfont.Font(family="Courier", size=8)
key_font     = tkfont.Font(family="Courier", size=7, weight="bold")

root.bind("<KeyPress>", _key_press)

# ═══════════════════════════════════════════════════════════════
#   BACKGROUND ANIMATED GRID
# ═══════════════════════════════════════════════════════════════
grid_canvas = tk.Canvas(root, width=680, height=760,
                        bg=BG, highlightthickness=0)
grid_canvas.place(x=0, y=0)

# ═══════════════════════════════════════════════════════════════
#   HEADER
# ═══════════════════════════════════════════════════════════════
hdr = tk.Frame(root, bg=PANEL, height=72)
hdr.place(x=0, y=0, width=680)

tk.Frame(root, bg=ACCENT, height=2).place(x=0, y=0, width=680)

tk.Label(hdr, text="◈  QUANTUM  REBELS  //  CAR  HUD",
         font=title_font, bg=PANEL, fg=ACCENT).place(x=20, y=14)
tk.Label(hdr, text=f"TARGET  {ESP_IP}:{PORT}     WASD / ARROWS / SPACE",
         font=sub_font, bg=PANEL, fg=TXT_SEC).place(x=22, y=46)

conn_dot = tk.Label(hdr, text="  ", bg=RED, width=2)
conn_dot.place(x=590, y=22)
conn_lbl = tk.Label(hdr, text="OFFLINE", font=sub_font, bg=PANEL, fg=RED)
conn_lbl.place(x=608, y=20)

# ═══════════════════════════════════════════════════════════════
#   LEFT COLUMN — D-PAD + SPEED
# ═══════════════════════════════════════════════════════════════
left = tk.Frame(root, bg=BG)
left.place(x=20, y=88, width=360, height=440)

dpad = tk.Frame(left, bg=PANEL2, bd=0, relief="flat")
dpad.place(x=0, y=0, width=355, height=310)

tk.Frame(dpad, bg=ACCENT, height=1).place(x=0, y=0, width=355)
tk.Label(dpad, text="  DRIVE CONTROLS", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=6, y=6)

fwd_btn = make_btn(dpad, "▲   FORWARD", 'F', "Forward", w=15, h=2)
fwd_btn.place(x=100, y=36)

lft_btn = make_btn(dpad, "◄  LEFT", 'L', "Turn Left", w=10, h=2)
lft_btn.place(x=10, y=106)

stp_btn = tk.Button(dpad, text="■  STOP", width=10, height=2,
                    bg=ACCENT2, fg="white",
                    activebackground="#8b0020", activeforeground="white",
                    relief="flat", bd=0, cursor="hand2", font=btn_font,
                    command=lambda: send_command('S', "Stop"))
stp_btn.place(x=128, y=106)

rgt_btn = make_btn(dpad, "RIGHT  ►", 'R', "Turn Right", w=10, h=2)
rgt_btn.place(x=252, y=106)

bwd_btn = make_btn(dpad, "▼  BACKWARD", 'B', "Backward", w=15, h=2)
bwd_btn.place(x=100, y=176)

hint_frame = tk.Frame(dpad, bg=PANEL2)
hint_frame.place(x=10, y=256, width=335)

for txt, col in [("W/↑ FWD", ACCENT), ("A/← LFT", ACCENT),
                 ("SPC STOP", ACCENT2), ("D/→ RGT", ACCENT), ("X/↓ BWD", ACCENT)]:
    tk.Label(hint_frame, text=txt, font=key_font,
             bg="#0a0e16", fg=col, padx=6, pady=3,
             relief="flat").pack(side="left", padx=2)

# ── SPEED CONTROL ──────────────────────────────────────────────
spd_frame = tk.Frame(left, bg=PANEL2)
spd_frame.place(x=0, y=322, width=355, height=108)
tk.Frame(spd_frame, bg=YELLOW, height=1).place(x=0, y=0, width=355)
tk.Label(spd_frame, text="  SPEED CONTROL", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=6, y=6)

spd_val_label = tk.Label(spd_frame, text="100%", font=stat_font,
                          bg=PANEL2, fg=YELLOW)
spd_val_label.place(x=270, y=28)

def _on_speed_change(val):
    v = int(float(val))
    spd_val_label.config(text=f"{v}%")
    try:
        stat_spd.config(text=f"{v}%")
    except Exception:
        pass

speed_slider = tk.Scale(
    spd_frame, from_=0, to=100, orient="horizontal",
    variable=speed_val,
    command=_on_speed_change,
    bg=PANEL2, fg=YELLOW, troughcolor=DIM,
    highlightthickness=0, sliderrelief="flat",
    activebackground=YELLOW, length=240, width=12,
    showvalue=False
)
speed_slider.place(x=10, y=54)

for lbl_text, val, xpos in [("25%", 25, 10), ("50%", 50, 68),
                              ("75%", 75, 126), ("100%", 100, 184)]:
    def _set_spd(v=val):
        speed_val.set(v)
        spd_val_label.config(text=f"{v}%")
        try:
            stat_spd.config(text=f"{v}%")
        except Exception:
            pass
    tk.Button(spd_frame, text=lbl_text, width=5, height=1,
              bg=DIM, fg=YELLOW, activebackground=YELLOW, activeforeground=BG,
              relief="flat", cursor="hand2", font=small_font,
              command=_set_spd).place(x=xpos, y=80)

# ═══════════════════════════════════════════════════════════════
#   RIGHT COLUMN — DIRECTION + STATS + UTIL
# ═══════════════════════════════════════════════════════════════
right = tk.Frame(root, bg=BG)
right.place(x=392, y=88, width=268, height=440)

# ── DIRECTION COMPASS ──────────────────────────────────────────
dir_frame = tk.Frame(right, bg=PANEL2)
dir_frame.place(x=0, y=0, width=268, height=138)
tk.Frame(dir_frame, bg=ACCENT3, height=1).place(x=0, y=0, width=268)
tk.Label(dir_frame, text="  DIRECTION", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=6, y=6)

dir_canvas = tk.Canvas(dir_frame, width=110, height=110,
                       bg=PANEL2, highlightthickness=0)
dir_canvas.place(x=10, y=20)
_draw_direction_arrow("IDLE")

dir_text = tk.Label(dir_frame, text="IDLE",
                    font=tkfont.Font(family="Courier", size=13, weight="bold"),
                    bg=PANEL2, fg=ACCENT3)
dir_text.place(x=130, y=50)

# ── STATS PANEL ────────────────────────────────────────────────
stats_frame = tk.Frame(right, bg=PANEL2)
stats_frame.place(x=0, y=148, width=268, height=130)
tk.Frame(stats_frame, bg=ACCENT, height=1).place(x=0, y=0, width=268)
tk.Label(stats_frame, text="  SESSION STATS", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=6, y=6)

tk.Label(stats_frame, text="COMMANDS", font=statlbl_font,
         bg=PANEL2, fg=TXT_SEC).place(x=12, y=32)
stat_cmds = tk.Label(stats_frame, text="0", font=stat_font,
                     bg=PANEL2, fg=ACCENT)
stat_cmds.place(x=12, y=46)

tk.Label(stats_frame, text="SESSION", font=statlbl_font,
         bg=PANEL2, fg=TXT_SEC).place(x=100, y=32)
stat_time = tk.Label(stats_frame, text="00:00", font=stat_font,
                     bg=PANEL2, fg=ACCENT)
stat_time.place(x=100, y=46)

tk.Label(stats_frame, text="SPEED", font=statlbl_font,
         bg=PANEL2, fg=TXT_SEC).place(x=196, y=32)
stat_spd = tk.Label(stats_frame, text="100%", font=stat_font,
                    bg=PANEL2, fg=YELLOW)
stat_spd.place(x=190, y=46)

# ── UTILITY BUTTONS ────────────────────────────────────────────
util_frame = tk.Frame(right, bg=PANEL2)
util_frame.place(x=0, y=290, width=268, height=150)
tk.Frame(util_frame, bg=ACCENT2, height=1).place(x=0, y=0, width=268)
tk.Label(util_frame, text="  UTILITIES", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=6, y=6)

auto_btn = tk.Button(util_frame, text="⚡  AUTO MODE", width=22, height=2,
                     bg="#1a2a00", fg=YELLOW,
                     activebackground="#2a4000", activeforeground=YELLOW,
                     relief="flat", cursor="hand2", font=btn_font,
                     command=auto_mode)
auto_btn.place(x=10, y=30)

ping_btn = tk.Button(util_frame, text="◌  PING ESP32", width=22, height=2,
                     bg=DIM, fg=ACCENT,
                     activebackground="#0a2030", activeforeground=ACCENT,
                     relief="flat", cursor="hand2", font=btn_font,
                     command=test_connection)
ping_btn.place(x=10, y=90)

# ═══════════════════════════════════════════════════════════════
#   BOTTOM — STATUS + LOG
# ═══════════════════════════════════════════════════════════════
tk.Frame(root, bg=BORDER, height=1).place(x=0, y=540, width=680)

status_label = tk.Label(root, text="●  Press PING to test connection",
                        font=small_font, bg=BG, fg=TXT_SEC, anchor="w")
status_label.place(x=16, y=548, width=650)

# ── LOG BOX ────────────────────────────────────────────────────
log_outer = tk.Frame(root, bg=PANEL2)
log_outer.place(x=16, y=572, width=648, height=172)
tk.Frame(log_outer, bg=ACCENT, height=1).place(x=0, y=0, width=648)
tk.Label(log_outer, text="  COMMAND LOG", font=small_font,
         bg=PANEL2, fg=TXT_SEC).place(x=4, y=4)

log_scroll = tk.Scrollbar(log_outer, bg=PANEL2, troughcolor=PANEL2,
                           activebackground=DIM, relief="flat")
log_scroll.place(x=630, y=22, height=146)

log_box = tk.Text(
    log_outer,
    font=log_font,
    bg="#02040a",
    fg=GREEN,
    insertbackground=ACCENT,
    selectbackground=DIM,
    relief="flat",
    bd=0,
    yscrollcommand=log_scroll.set,
    state="disabled",
    padx=10,
    pady=6
)
log_box.place(x=0, y=22, width=630, height=146)

log_scroll.config(command=log_box.yview)
_animate_grid()
_refresh_time()

root.mainloop()
