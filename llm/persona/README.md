# persona（チャット由来の記憶）

資料由来のプロフィール（OneDrive の MyAI/profile/）とは別管理。Claudeのチャットで「persona 更新」「性格は？」と言うと更新される。

## ファイル
- persona.json … 原本（質問・進め方、日々の行動、方針・目標、性格、健康など）
- persona_backup.json … persona.json から消えた行を日時付きで保管
- add_persona.py … persona.json を記憶 data/llm_memory.json に反映し、LM Studio・Ollama にも同期

## 呼び出し方
- python3 ~/MyTool/llm/persona/add_persona.py（--no-sync でアプリ側への同期をしない）

英語日記・健康ログ・プロフィールの原本は OneDrive の ドキュメント/MyAI（diary/・health/・profile/）にある。
