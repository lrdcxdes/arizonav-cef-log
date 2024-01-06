import win32gui
import win32process

import ctypes
import psutil
import win32gui


ragemp_title = "RAGE Multiplayer"


SetProcessDPIAware = ctypes.windll.user32.SetProcessDPIAware

SetProcessDPIAware(2)


EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible


def getProcessIDByName(name: str = "GTAV.exe"):
    qobuz_pids = []

    for proc in psutil.process_iter():
        if name in proc.name():
            qobuz_pids.append(proc.pid)

    return qobuz_pids


def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        # if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

        if found_pid == pid:
            hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def getWindowTitleByHandle(hwnd):
    length = GetWindowTextLength(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buff, length + 1)
    return buff.value


def getRect(name: str = "GTAV.exe"):
    pids = getProcessIDByName(name)

    for i in pids:
        hwnds = get_hwnds_for_pid(i)
        for hwnd in hwnds:
            if IsWindowVisible(hwnd):
                return win32gui.GetWindowRect(hwnd), hwnd

    return None, None


def getHWND(name: str = "GTA5.exe"):
    pids = getProcessIDByName(name)

    for i in pids:
        hwnds = get_hwnds_for_pid(i)
        for hwnd in hwnds:
            if IsWindowVisible(hwnd):
                return hwnd

    return None


hwnd = getHWND()
print(hwnd)


def is_foreground() -> bool:
    return win32gui.GetForegroundWindow() == hwnd
