# Let_it_Die_Local_Saver
A tool to automatically locally export the save file of let it die from Steam
<img width="915" height="585" alt="image" src="https://github.com/user-attachments/assets/0ac575a3-e442-412d-bd19-ee2447325745" />


LET IT DIE launcher
===================

Launch LET IT DIE through Steam, wait until you quit, then copy local
saves. The offline edition has no Steam Cloud, so this is does backups.

**Important:** Create a shortcut once (Create shortcut in settings), then launch from that shortcut or from the exe. Steam’s own Play button does not run this backup.
How a launch works
------------------
1. Looks for settings.ini next to the exe (or .py).
2. If INI_PATH points at another ini and that file exists, that file wins.
3. EDIT_SETTINGS=0  -> skip splash, start the game.
   EDIT_SETTINGS=1  -> 3 second splash. Click to open settings.
4. After the game process exits, wait FLUSH_WAIT seconds, then it copy saves.

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
    (uncle glasses / letitdie.ico). If neither exists, shortcut has no custom
    thumbnail.

SOURCE
    Folder the game writes saves into. Example:
    C:\Steam\steamapps\common\LET IT DIE\Savedata
    or Steam userdata\<id>\794600
    Must exist and contain files or backup is aborted.

DEST
    Where backups go. The program creates:
      DEST\current save      latest copy (same filenames)
      DEST\historic saves\let it die YYYY-MM-DD
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
Accept and Activate     save ini and launch
Save settings and close save ini, do not launch
Cancel                  discard form changes
Create shortcut         desktop .lnk to this launcher
Browse                  pick a file or folder
About                   this text

Assets (optional, packed into the exe if present at build time)
--------------------------------------------------------------
Tower_of_Barbs_Painting_ready.png   window background
let it die cursor.png               in-window cursor
uncle glasses ready.png             window icon
letitdie.ico                        shortcut / exe icon
