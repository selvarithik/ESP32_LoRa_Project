"""Own one disposable fixture process; never restart the user's Gateway."""
from pathlib import Path
import subprocess,sys,tempfile
root=Path(__file__).resolve().parents[1]
node=Path(r'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
with tempfile.TemporaryFile() as output:
 process=subprocess.Popen([sys.executable,str(root/'tests/gateway_fixture.py')],cwd=root,stdout=output,stderr=subprocess.STDOUT)
 try:
  subprocess.run([str(node),str(root/'tests/sensor_widgets.cjs')],cwd=root,check=True,timeout=90)
 except BaseException:
  output.seek(0);print(output.read().decode("utf-8",errors="replace")[-4000:]);raise
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait()
