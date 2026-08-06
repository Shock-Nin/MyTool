-- WriteToExcel.scpt
-- AppleScript to write data to Excel saya365 sheet from Python via AppleScriptTask

on writeToSaya365(excelPath, csvData)
    tell application "Microsoft Excel"
        activate

        -- Open the workbook if not already open
        set workbookOpen to false
        set targetWorkbook to missing value

        try
            repeat with wb in workbooks
                if (full name of wb) is excelPath then
                    set workbookOpen to true
                    set targetWorkbook to wb
                    exit repeat
                end if
            end repeat
        end try

        if not workbookOpen then
            open excelPath
            set targetWorkbook to active workbook
        end if

        -- Get or create saya365 sheet
        set sheetExists to false
        try
            set targetSheet to worksheet "saya365" of targetWorkbook
            set sheetExists to true
        on error
            set targetSheet to make new worksheet at targetWorkbook with properties {name:"saya365"}
        end try

        -- Clear existing content
        if sheetExists then
            try
                clear contents range "A:ZZ" of targetSheet
            end try
        end if

        -- Parse CSV data
        set AppleScript's text item delimiters to linefeed
        set dataRows to text items of csvData

        -- Write data row by row
        set rowNum to 1
        repeat with dataRow in dataRows
            if length of dataRow > 0 then
                set AppleScript's text item delimiters to ","
                set cellValues to text items of dataRow
                set colNum to 1

                repeat with cellValue in cellValues
                    try
                        set value of cell rowNum of column colNum of targetSheet to cellValue
                    end try
                    set colNum to colNum + 1
                end repeat

                set rowNum to rowNum + 1
            end if
        end repeat

        -- Save workbook
        save targetWorkbook

        return "Successfully wrote " & (rowNum - 1) & " rows to saya365 sheet"
    end tell
end writeToSaya365
