osascript <<END
tell application "Terminal"
    try
        set miniaturized of windows to true
    end try
end tell
END

cd /Users/dsk_nagaoka/MyTool
python3 mytool.py

# pip install pyperclip
# pip install pyautogui
# pip install selenium
# pip install webdriver_manager
# pip install mysql
# pip install mysql.connector
# chmod 777 MyTool.command
