# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['C:/Users/leonm/PycharmProjects/VideoAssistent/video_assistant.py'],
             pathex=['C:\\Users\\leonm\\PycharmProjects\\VideoAssistent'],
             binaries=[],
             datas=[('C:/Users/leonm/PycharmProjects/VideoAssistent/debug.log', '.'), ('C:/Users/leonm/PycharmProjects/VideoAssistent/ffmpeg.exe', '.'), ('C:/Users/leonm/PycharmProjects/VideoAssistent/ffprobe.exe', '.'), ('C:/Users/leonm/PycharmProjects/VideoAssistent/log_level_config.txt', '.'), ('C:/Users/leonm/PycharmProjects/VideoAssistent/p_icon.ico', '.'), ('C:/Users/leonm/PycharmProjects/VideoAssistent/video_assistant.log', '.')],
             hiddenimports=['pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='video_assistant',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon='C:\\Users\\leonm\\PycharmProjects\\VideoAssistent\\p_icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='video_assistant')
