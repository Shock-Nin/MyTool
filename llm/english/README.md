# 英語日記（ChatGPT・Gemini・Copilot の添削をまとめて記録）

記憶には入れず、このフォルダのファイルに記録して必要なときだけ呼び出す。

## ファイル
- diary.json … 日記の記録（1日1件。同じ日の修正版は最後のものを正式な記録として上書き、採点は score_history に修正回ごとに残す）
- diary_config.json … 日付ごとの三者の会話URL（chats_by_date）。同じ日の修正版はその会話に送る
- add_diary.py … 1日分を diary.json に記録
- diary_chart.py … スコアのグラフ（上段＝総合点・初回の点・7回平均、下段＝文法・語彙・自然さの得点率）

## 呼び出し方
- 記録: python3 ~/MyTool/llm/english/add_diary.py --file entry.json
- グラフ: Claudeに「英語」とだけ送る（「英語 30日」で期間指定）／ターミナルでは python3 ~/MyTool/llm/english/diary_chart.py [日数]
