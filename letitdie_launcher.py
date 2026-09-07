from __future__ import annotations

import ctypes
import os
import struct
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from tkinter import filedialog, messagebox

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APPID_DEFAULT = "794600"
EXE_DEFAULT = "BrgGame-Steam.exe"
FLUSH_DEFAULT = "15"

BG_COLOR = "#201717"
ENTRY_BG = "#212121"
ENTRY_BD = "#a1a1a1"
TEXT_FG = "#ffffff"
BTN_WHITE = "#ffffff"
BTN_BLACK = "#000000"

ASSET_BG = "Tower_of_Barbs_Painting_ready.png"
ASSET_CURSOR = "let it die cursor.png"
ASSET_ICON = "uncle glasses ready.png"
ASSET_ICO = "lidico.ico"

INI_KEYS = [
    "EDIT_SETTINGS",
    "FLUSH_WAIT",
    "INI_PATH",
    "ICO_PATH",
    "SOURCE",
    "DEST",
    "HISTORIC_EVERY_DAYS",
    "GAME_EXE",
    "STEAM_EXE",
    "APPID",
]

DEFAULTS = {
    "EDIT_SETTINGS": "1",
    "FLUSH_WAIT": FLUSH_DEFAULT,
    "INI_PATH": "",
    "ICO_PATH": "",
    "SOURCE": r"C:\Program Files (x86)\Steam\userdata\YOUR_STEAM_ID\794600",
    "DEST": r"C:\Users\Public\Documents\LETITDIE_Backups",
    "HISTORIC_EVERY_DAYS": "7",
    "GAME_EXE": EXE_DEFAULT,
    "STEAM_EXE": r"C:\Program Files (x86)\Steam\steam.exe",
    "APPID": APPID_DEFAULT,
}

SETTING_ROWS = [
    ("INI_PATH", "file"),
    ("ICO_PATH", "file"),
    ("FLUSH_WAIT", "none"),
    ("SOURCE", "folder"),
    ("DEST", "folder"),
    ("HISTORIC_EVERY_DAYS", "none"),
    ("GAME_EXE", "none"),
    ("STEAM_EXE", "file"),
    ("APPID", "none"),
]

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_CURSOR_HANDLE = 0


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


def local_ini() -> str:
    return os.path.join(app_dir(), "settings.ini")


def find_asset(*names: str) -> str:
    for root in (bundle_dir(), app_dir()):
        if not root:
            continue
        for name in names:
            path = os.path.join(root, name)
            if os.path.isfile(path):
                return path
    return ""


def bundled_ico() -> str:
    return find_asset(ASSET_ICO, "letitdie.ico", ASSET_ICON)


def launcher_target() -> str:
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)


# ---------------------------------------------------------------------------
# Images / cursor / window chrome
# ---------------------------------------------------------------------------

def load_photo(path: str, size: tuple[int, int] | None = None):
    if not path or not os.path.isfile(path):
        return None
    try:
        from PIL import Image, ImageTk

        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        try:
            return tk.PhotoImage(file=path)
        except Exception:
            return None


def png_to_ico(png_path: str, ico_path: str) -> bool:
    try:
        from PIL import Image

        Image.open(png_path).convert("RGBA").save(
            ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)]
        )
        return True
    except Exception:
        return False


def png_to_cur(png_path: str, cur_path: str, size: int = 32) -> bool:
    try:
        from PIL import Image

        img = Image.open(png_path).convert("RGBA")
        box = img.getbbox()
        if box:
            img = img.crop(box)
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(img, (0, 0))

        hx = hy = 0
        found = False
        for y in range(size):
            for x in range(size):
                if canvas.getpixel((x, y))[3] > 40:
                    hx, hy = x, y
                    found = True
                    break
            if found:
                break

        xor = bytearray()
        for y in range(size - 1, -1, -1):
            for x in range(size):
                r, g, b, a = canvas.getpixel((x, y))
                xor += bytes((b, g, r, a))

        row_and = ((size + 31) // 32) * 4
        and_mask = bytearray(row_and * size)
        for y in range(size):
            dest_y = size - 1 - y
            for x in range(size):
                if canvas.getpixel((x, y))[3] < 128:
                    and_mask[dest_y * row_and + (x >> 3)] |= 0x80 >> (x & 7)

        image = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, len(xor), 0, 0, 0, 0)
        image += bytes(xor) + bytes(and_mask)
        header = struct.pack("<HHH", 0, 2, 1)
        entry = struct.pack("<BBBBHHII", size, size, 0, 0, hx, hy, len(image), 22)
        with open(cur_path, "wb") as fh:
            fh.write(header + entry + image)
        return True
    except Exception:
        return False


def apply_cursor(widget: tk.Misc, cur_path: str) -> None:
    global _CURSOR_HANDLE
    if not cur_path or not os.path.isfile(cur_path):
        return
    path = os.path.abspath(cur_path)
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            user32.LoadCursorFromFileW.restype = ctypes.c_void_p
            handle = user32.LoadCursorFromFileW(path)
            if handle:
                _CURSOR_HANDLE = handle
                user32.SetCursor.argtypes = [ctypes.c_void_p]
                hwnd = user32.GetParent(widget.winfo_id()) or widget.winfo_id()
                if hasattr(user32, "SetClassLongPtrW"):
                    user32.SetClassLongPtrW(hwnd, -12, handle)
                else:
                    user32.SetClassLongW(hwnd, -12, handle)
        except Exception:
            pass

        def force(_e=None, handle=_CURSOR_HANDLE):
            if handle:
                try:
                    ctypes.windll.user32.SetCursor(handle)
                except Exception:
                    pass

        widget.bind("<Enter>", force, add="+")
        widget.bind("<Motion>", force, add="+")

    for spec in ("@" + path, "@" + path.replace("\\", "/")):
        try:
            widget.configure(cursor=spec)
            break
        except Exception:
            continue
    for child in widget.winfo_children():
        apply_cursor(child, cur_path)


def color_titlebar(win: tk.Misc, rgb: tuple[int, int, int] = (0, 0, 0)) -> None:
    if sys.platform != "win32":
        return
    try:
        win.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
        color = ctypes.c_int(rgb[0] | (rgb[1] << 8) | (rgb[2] << 16))
        dark = ctypes.c_int(1)
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), 4)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(color), 4)
    except Exception:
        pass


def apply_window_chrome(win: tk.Misc, cfg: dict | None = None) -> None:
    try:
        win.tk_setPalette(background=BG_COLOR, foreground=TEXT_FG)
    except Exception:
        pass

    png = find_asset(ASSET_ICON)
    photo = load_photo(png, (32, 32)) if png else None
    if photo:
        try:
            win.iconphoto(True, photo)
            win._icon_photo = photo
        except Exception:
            pass

    ico_cfg = (cfg or {}).get("ICO_PATH", "")
    ico_file = ""
    if ico_cfg.lower().endswith(".ico") and os.path.isfile(ico_cfg):
        ico_file = ico_cfg
    elif png:
        tmp = os.path.join(tempfile.gettempdir(), "lid_window.ico")
        if png_to_ico(png, tmp):
            ico_file = tmp
    if ico_file:
        try:
            win.iconbitmap(ico_file)
        except Exception:
            pass

    color_titlebar(win, (0, 0, 0))
    cur_png = find_asset(ASSET_CURSOR)
    if not cur_png:
        return
    cur = os.path.join(tempfile.gettempdir(), "lid_cursor.cur")
    if png_to_cur(cur_png, cur):
        apply_cursor(win, cur)
        win.after(80, lambda w=win, c=cur: apply_cursor(w, c))


# ---------------------------------------------------------------------------
# Ini
# ---------------------------------------------------------------------------

def read_ini(path: str) -> dict:
    data = dict(DEFAULTS)
    if not path or not os.path.isfile(path):
        return data
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def write_ini(path: str, data: dict) -> None:
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    lines = [
        "# See ABOUT.txt for what each option does.",
        "# EDIT_SETTINGS=0 skips splash and launches",
        "# EDIT_SETTINGS=1 shows 3 second splash",
    ]
    lines += [f"{key}={data.get(key, DEFAULTS.get(key, ''))}" for key in INI_KEYS]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def resolve_ini() -> tuple[str, dict, bool]:
    created = False
    pointer = local_ini()
    if not os.path.isfile(pointer):
        write_ini(pointer, dict(DEFAULTS))
        created = True
    cfg = read_ini(pointer)
    target = cfg.get("INI_PATH", "").strip()
    if target and os.path.isfile(target):
        cfg = read_ini(target)
        cfg["INI_PATH"] = target
        return target, cfg, created
    cfg["INI_PATH"] = pointer
    return pointer, cfg, created


def save_cfg(cfg: dict) -> None:
    target = cfg.get("INI_PATH", "").strip() or local_ini()
    write_ini(target, cfg)
    if os.path.normpath(target) != os.path.normpath(local_ini()):
        write_ini(local_ini(), cfg)


# ---------------------------------------------------------------------------
# Game / backup
# ---------------------------------------------------------------------------

def process_running(image: str) -> bool:
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {image}"],
            creationflags=NO_WINDOW,
            stderr=subprocess.DEVNULL,
            text=True,
            errors="ignore",
        )
        return image.lower() in out.lower()
    except Exception:
        return False


def wait_process_end(image: str) -> None:
    name = image[:-4] if image.lower().endswith(".exe") else image
    try:
        subprocess.check_call(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Get-Process -Name '{name}' -ErrorAction SilentlyContinue | Wait-Process",
            ],
            creationflags=NO_WINDOW,
        )
    except Exception:
        while process_running(image):
            time.sleep(2)


def copy_tree(src: str, dst: str) -> int:
    os.makedirs(dst, exist_ok=True)
    return subprocess.run(
        ["robocopy", src, dst, "/E", "/XO", "/R:2", "/W:2"],
        creationflags=NO_WINDOW,
    ).returncode


def need_historic(folder: str, days: int) -> bool:
    if not os.path.isdir(folder):
        return True
    try:
        entries = os.listdir(folder)
    except OSError:
        return True
    newest = None
    for name in entries:
        if not name.lower().startswith("let it die"):
            continue
        stamp = os.path.getmtime(os.path.join(folder, name))
        if newest is None or stamp > newest:
            newest = stamp
    if newest is None:
        return True
    return (time.time() - newest) >= days * 86400


def backup(cfg: dict) -> None:
    src, dest = cfg["SOURCE"], cfg["DEST"]
    current = os.path.join(dest, "current save")
    historic = os.path.join(dest, "historic saves")
    os.makedirs(current, exist_ok=True)
    os.makedirs(historic, exist_ok=True)
    if not os.path.isdir(src):
        raise RuntimeError(f"SOURCE folder does not exist:\n{src}")
    if not any(files for _, _, files in os.walk(src)):
        raise RuntimeError(f"no files in SOURCE:\n{src}")
    if copy_tree(src, current) >= 8:
        raise RuntimeError("robocopy current save failed")
    days = int(cfg.get("HISTORIC_EVERY_DAYS") or "7")
    if need_historic(historic, days):
        stamp = time.strftime("%Y-%m-%d")
        copy_tree(src, os.path.join(historic, f"let it die {stamp}"))


def lock_path() -> str:
    return os.path.join(app_dir(), "lid_session.lock")


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}"],
            creationflags=NO_WINDOW,
            stderr=subprocess.DEVNULL,
            text=True,
            errors="ignore",
        )
        return str(pid) in out and "PID" in out
    except Exception:
        return False


def acquire_launch_lock() -> bool:
    path = lock_path()
    if os.path.isfile(path):
        try:
            old = int(open(path, "r", encoding="utf-8").read().strip() or "0")
        except Exception:
            old = 0
        if pid_alive(old) and old != os.getpid():
            return False
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(os.getpid()))
        return True
    except Exception:
        return True


def release_launch_lock() -> None:
    path = lock_path()
    try:
        if os.path.isfile(path):
            stored = int(open(path, "r", encoding="utf-8").read().strip() or "0")
            if stored in (0, os.getpid()):
                os.remove(path)
    except Exception:
        pass


def wait_spawn(exe: str, tries: int = 60) -> bool:
    for _ in range(tries):
        time.sleep(2)
        if process_running(exe):
            return True
    return False


def flush_or_reopened(exe: str, seconds: int) -> bool:
    """Sleep up to `seconds`. Return True if the game started again."""
    if seconds <= 0:
        return process_running(exe)
    left = seconds
    while left > 0:
        time.sleep(1)
        left -= 1
        if process_running(exe):
            return True
    return process_running(exe)


def launch_game(cfg: dict) -> None:
    steam, appid, exe = cfg["STEAM_EXE"], cfg["APPID"], cfg["GAME_EXE"]
    if not os.path.isfile(steam):
        raise RuntimeError(f"Steam not found:\n{steam}")
    wait = int(cfg.get("FLUSH_WAIT") or FLUSH_DEFAULT)
    subprocess.Popen([steam, "-applaunch", appid], close_fds=True)
    if not process_running(exe) and not wait_spawn(exe):
        raise RuntimeError(f"process not found: {exe}")
    while True:
        wait_process_end(exe)
        if flush_or_reopened(exe, wait):
            continue
        backup(cfg)
        return


def create_shortcut(ico_path: str) -> tuple[bool, str]:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    lnk = os.path.join(desktop, "LET IT DIE.lnk")
    icon = ico_path if ico_path and os.path.isfile(ico_path) else bundled_ico()
    icon_ok = bool(icon and os.path.isfile(icon))
    icon_line = f'$s.IconLocation = "{icon},0"' if icon_ok else ""
    target, work = launcher_target(), app_dir()
    ps = (
        "$w = New-Object -ComObject WScript.Shell\n"
        f"$s = $w.CreateShortcut('{lnk.replace(chr(39), chr(39)+chr(39))}')\n"
        f"$s.TargetPath = '{target.replace(chr(39), chr(39)+chr(39))}'\n"
        f"$s.WorkingDirectory = '{work.replace(chr(39), chr(39)+chr(39))}'\n"
        "$s.WindowStyle = 1\n"
        f"{icon_line}\n"
        "$s.Save()\n"
    )
    subprocess.check_call(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        creationflags=NO_WINDOW,
    )
    return icon_ok, lnk


# ---------------------------------------------------------------------------
# UI widgets
# ---------------------------------------------------------------------------

def paint_background(win: tk.Misc, width: int, height: int) -> tk.Canvas:
    canvas = tk.Canvas(win, width=width, height=height, highlightthickness=0, bd=0, bg="black")
    canvas.pack(fill="both", expand=True)
    win._bg_src = find_asset(ASSET_BG)
    win._bg_item = None

    def redraw(_evt=None):
        w = max(win.winfo_width(), width)
        h = max(win.winfo_height(), height)
        canvas.config(width=w, height=h)
        photo = load_photo(win._bg_src, (w, h)) if win._bg_src else None
        if not photo:
            return
        if win._bg_item:
            canvas.delete(win._bg_item)
        win._bg_item = canvas.create_image(0, 0, image=photo, anchor="nw")
        canvas.tag_lower(win._bg_item)
        win._bg_photo = photo

    win.bind("<Configure>", redraw)
    win.after(1, redraw)
    return canvas


def style_entry(parent, var, width: int = 58) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=var,
        width=width,
        bg=ENTRY_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=ENTRY_BD,
        highlightcolor=ENTRY_BD,
        font=("Segoe UI", 10),
    )


def style_action(parent, text: str, cmd) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=cmd,
        bg=BTN_WHITE,
        fg=BTN_BLACK,
        activebackground="#e8e8e8",
        activeforeground=BTN_BLACK,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=BTN_BLACK,
        padx=10,
        pady=4,
        font=("Segoe UI", 9),
    )


def open_about() -> None:
    path = find_asset("ABOUT.txt")
    if path and os.path.isfile(path):
        try:
            os.startfile(path)
            return
        except Exception:
            pass
    messagebox.showinfo("About", ABOUT_TEXT)


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

class SettingsForm(tk.Toplevel):
    def __init__(self, master: tk.Tk, cfg: dict, ini_path: str):
        super().__init__(master)
        self.title("LET IT DIE launcher settings")
        self.resizable(False, False)
        self.geometry("920x560")
        self.result = "cancel"
        self.cfg = dict(cfg)
        self.vars: dict[str, tk.StringVar] = {}
        cv = paint_background(self, 920, 560)
        cv.create_text(
            28, 28, anchor="nw", fill=TEXT_FG, font=("Segoe UI", 10),
            text="Accept and Activate saves and launches. Save and close saves and exits.",
        )
        y = 64
        for key, kind in SETTING_ROWS:
            cv.create_text(28, y + 10, anchor="w", fill=TEXT_FG, font=("Segoe UI", 10), text=key)
            var = tk.StringVar(value=cfg.get(key, DEFAULTS.get(key, "")))
            self.vars[key] = var
            cv.create_window(220, y, anchor="nw", window=style_entry(cv, var), width=520, height=26)
            if kind != "none":
                btn = style_action(cv, "Browse", lambda k=key, t=kind: self.browse(k, t))
                cv.create_window(752, y, anchor="nw", window=btn, height=26)
            y += 38
        x = 28
        actions = (
            ("Accept and Activate", lambda: self.finish("activate")),
            ("Save settings and close", lambda: self.finish("saveonly")),
            ("Cancel", lambda: self.finish("cancel")),
            ("Create shortcut", self.shortcut),
            ("About", open_about),
        )
        for text, cmd in actions:
            cv.create_window(x, y + 10, anchor="nw", window=style_action(cv, text, cmd), height=32)
            x += 176
        self.protocol("WM_DELETE_WINDOW", lambda: self.finish("cancel"))
        apply_window_chrome(self, cfg)
        self.grab_set()

    def browse(self, key: str, kind: str) -> None:
        start = self.vars[key].get() or app_dir()
        if kind == "folder":
            path = filedialog.askdirectory(initialdir=start)
        else:
            path = filedialog.askopenfilename(initialdir=os.path.dirname(start) or app_dir())
        if path:
            self.vars[key].set(path.replace("/", "\\"))

    def collect(self) -> dict:
        data = dict(self.cfg)
        for key, var in self.vars.items():
            data[key] = var.get().strip()
        return data

    def shortcut(self) -> None:
        ico = self.collect().get("ICO_PATH", "").strip()
        try:
            used, lnk = create_shortcut(ico)
        except Exception as exc:
            messagebox.showerror("Shortcut", str(exc))
            return
        note = "" if used else " without custom thumbnail"
        messagebox.showinfo("Shortcut", f"Shortcut created{note}:\n{lnk}")

    def finish(self, result: str) -> None:
        self.result = result
        if result != "cancel":
            self.cfg = self.collect()
        self.destroy()


class Splash(tk.Toplevel):
    def __init__(self, master: tk.Tk, cfg: dict):
        super().__init__(master)
        self.title("LET IT DIE")
        self.resizable(False, False)
        self.result = "launch"
        self.left = 3
        self.attributes("-topmost", True)
        self.geometry("520x360")
        cv = paint_background(self, 520, 360)
        self._splash_cv = cv
        self._count_id = cv.create_text(260, 90, text="3", fill=TEXT_FG, font=("Segoe UI", 72, "bold"))
        cv.create_text(260, 175, text="Game launching", fill=TEXT_FG, font=("Segoe UI", 16))
        cv.create_window(
            260, 250,
            window=style_action(cv, "Click here to open settings", self.open_settings),
            width=360, height=56,
        )
        self.after(1000, self.tick)
        self.protocol("WM_DELETE_WINDOW", self.timeout)
        apply_window_chrome(self, cfg)

    def tick(self) -> None:
        self.left -= 1
        if self.left <= 0:
            self.timeout()
            return
        self._splash_cv.itemconfigure(self._count_id, text=str(self.left))
        self.after(1000, self.tick)

    def open_settings(self) -> None:
        self.result = "settings"
        self.destroy()

    def timeout(self) -> None:
        self.result = "launch"
        self.destroy()


# ---------------------------------------------------------------------------
# About text (also written to ABOUT.txt)
# ---------------------------------------------------------------------------

ABOUT_TEXT = """LET IT DIE launcher
===================

Launch LET IT DIE through Steam, wait until you quit, then copy local
saves. The offline edition has no Steam Cloud, so this is the backup.

How a launch works
------------------
1. Looks for settings.ini next to the exe (or .py).
2. If INI_PATH points at another ini and that file exists, that file wins.
3. EDIT_SETTINGS=0  -> skip splash, start the game.
   EDIT_SETTINGS=1  -> 3 second splash. Click to open settings.
4. After the game process exits, wait FLUSH_WAIT seconds, then copy saves.

settings.ini keys
-----------------
EDIT_SETTINGS
    1 = show the countdown splash.
    0 = skip splash and settings. Hidden skip; edit the ini by hand.

FLUSH_WAIT
    Seconds to wait after the game closes so the save file can flush.
    15 is safe. 0 copies immediately.

INI_PATH
    Full path to the ini to use. Empty = settings.ini next to the program.
    The file next to the exe still stores this pointer.

ICO_PATH
    Optional .ico for the desktop shortcut. Empty = icon packed in the exe
    (uncle glasses / lidico.ico). If neither exists, shortcut has no custom
    thumbnail.

SOURCE
    Folder the game writes saves into. Example:
    D:\\Steam\\steamapps\\common\\LET IT DIE\\Savedata
    or Steam userdata\\<id>\\794600
    Must exist and contain files or backup is aborted.

DEST
    Where backups go. The program creates:
      DEST\\current save      latest copy (same filenames)
      DEST\\historic saves\\let it die YYYY-MM-DD
    Historic folders are only created when none exist yet, or the newest
    "let it die ..." item is older than HISTORIC_EVERY_DAYS.

HISTORIC_EVERY_DAYS
    Minimum days between dated historic snapshots. 7 = weekly. 0 = every quit.

GAME_EXE
    Task Manager image name only, not a shortcut.
    LET IT DIE is usually BrgGame-Steam.exe

STEAM_EXE
    Full path to steam.exe.

APPID
    Steam app id. LET IT DIE is 794600.

Buttons
-------
Accept and Activate  save ini and launch
Save settings and close  save ini, do not launch
Cancel  discard form changes
Create shortcut  desktop .lnk to this launcher
Browse  pick a file or folder
About  this text

Assets (optional, packed into the exe if present at build time)
--------------------------------------------------------------
Tower_of_Barbs_Painting_ready.png   window background
let it die cursor.png               in-window cursor
uncle glasses ready.png             window icon
lidico.ico                          shortcut / exe icon
"""


def write_about_file() -> None:
    path = os.path.join(app_dir(), "ABOUT.txt")
    if os.path.isfile(path):
        return
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(ABOUT_TEXT)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    write_about_file()
    _ini_path, cfg, created = resolve_ini()
    root = tk.Tk()
    root.withdraw()
    apply_window_chrome(root, cfg)
    if not acquire_launch_lock():
        wait = cfg.get("FLUSH_WAIT") or FLUSH_DEFAULT
        messagebox.showinfo(
            "LET IT DIE launcher",
            "The launcher is already running.\n\n"
            "If you just quit, it is waiting "
            f"{wait} seconds so the save can flush, then it copies backups.\n"
            "Do not start a second copy. Wait for that to finish.\n\n"
            "If you already opened the game again, the first launcher will "
            "skip this backup and wait until you quit that session.",
        )
        return 0

    try:
        if created:
            messagebox.showwarning(
                "LET IT DIE",
                "no ini file found in same directory as program\nA new settings.ini was created.",
            )
            want = "settings"
        elif cfg.get("EDIT_SETTINGS", "1").strip() == "0":
            want = "launch"
        else:
            splash = Splash(root, cfg)
            root.wait_window(splash)
            want = splash.result

        if want == "settings":
            form = SettingsForm(root, cfg, _ini_path)
            root.wait_window(form)
            if form.result == "cancel":
                return 0
            cfg = form.cfg
            save_cfg(cfg)
            if form.result == "saveonly":
                return 0

        launch_game(cfg)
    except Exception as exc:
        messagebox.showerror("LET IT DIE launcher", str(exc))
        return 1
    finally:
        release_launch_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())