# -*- mode: python ;coding: utf-8 -*-
"""
Windowsアプリ化コマンド
  pyinstaller mytool_exe.spec --clean --icon=item/img/logo.ico
"""
block_cipher = None
a = Analysis(['mytool.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.datas += [('item/img/logo.ico', '.\\item\\img\\logo.ico', 'Data')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='mytool',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )