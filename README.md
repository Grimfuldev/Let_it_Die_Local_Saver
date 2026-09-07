# Let_it_Die_Local_Saver
A tool to automatically locally export the save file of let it die from Steam.

The point of this program is to be the least invasive possible so you can forget about saving backups or managing settings. Everything is automatic and only in background after it’s configured. It works like an offline cloud backup that manages itself.
<img width="1034" height="658" alt="image" src="https://github.com/user-attachments/assets/21d12c07-4af6-4d4c-9c90-d30f207f1165" />


LET IT DIE launcher
===================

Launch LET IT DIE through Steam, wait until you quit, then copy local
saves. The offline edition has no Steam Cloud, so this does backups.

**Important:** Create a shortcut once (Create shortcut in settings), then launch from that shortcut or from the exe. Steam’s own Play button does not run this backup.


How a launch works
------------------
1. Looks for settings.ini next to the exe (or .py).
2. If INI_PATH points at another ini and that file exists, that file wins.
3. EDIT_SETTINGS=0  -> skip splash, start the game.
   EDIT_SETTINGS=1  -> 3 second splash. Click to open settings.
4. After the game process exits, wait FLUSH_WAIT seconds, then it copies saves.

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

-----------------
Background is an original edit of a public-domain Tower of Babel painting.
Other UI art is fanmade.
LET IT DIE game is © GungHo / Supertrick. This project is unofficial.

--------------------------------------------------------------
Step 1:
Get it on Github (Releases, the exe file): https://github.com/Grimfuldev/Let_it_Die_Local_Saver/releases/latest
You can put the exe wherever you want. DEST in the settings is the backup folder, it does not have to be the same place as the exe.

Step 2:
Start the program. If you didn't already have a settings.ini next to it, it throws an alert and generates a new one.

That ini is where the launch parameters and backup path live. Keep it next to the program, or set INI_PATH if you want the ini somewhere else.
If an ini already exists, it tries to launch the game in 3 seconds unless you click the button to open settings.

Step 3:
Fill the paths. There is an ABOUT on Github that explains each field if you don't know what something does.

Step 4:
Press Accept and Activate or Save settings and close so the ini actually gets written.

Create shortcut is optional. It drops a shortcut on the desktop with a custom ico. Use the exe or that shortcut to start the game when you want backups. Steam Play does not run the backup script.

Step 5:
If you only hit Save settings and close, start the exe (or the shortcut) again. Wait the 3 seconds and it launches.

You can skip that wait by editing the ini and setting EDIT_SETTINGS=1 to EDIT_SETTINGS=0. To see the settings window again, put it back to 1.

Step 6:
Play normally. After you close the game it waits FLUSH_WAIT seconds, then copies the save from SOURCE into the backup folder you set.

After that you don't touch settings again. Just launch this program every time instead of Play button in Steam.

NOTE:
SOURCE is the folder, not the file.

Steam save folder is usually:
yourSteamFolder\steamapps\common\LET IT DIE\Savedata
Inside that there is a .sav with a long number. Point SOURCE at Savedata folder.
