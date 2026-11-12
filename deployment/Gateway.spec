# Single-file Windows bundle. Runtime data and credentials stay external.
from pathlib import Path
ROOT=Path(SPECPATH).parent
analysis=Analysis([str(ROOT/'tools/gateway.py')],pathex=[str(ROOT/'backend')],binaries=[],datas=[(str(ROOT/'dashboard/templates'),'dashboard/templates'),(str(ROOT/'dashboard/static'),'dashboard/static'),(str(ROOT/'deployment/profile.example.json'),'deployment')],hiddenimports=['engineio.async_drivers.threading','socketio','waitress'],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=['amqtt','pytest','tkinter'],noarchive=False)
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,analysis.binaries,analysis.datas,name='Gateway',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=True)
