osascript <<END
tell application "Terminal"
    try
        set miniaturized of windows to true
    end try
end tell
END

cd MyTool
source venv/bin/activate
python mytool.py
