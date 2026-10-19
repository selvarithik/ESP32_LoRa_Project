"""Known public fixture credential, temporary simulator database only."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
os.environ['SIM_GATEWAY_ADMIN_PASSWORD']='fixture-only-admin-123'
from simulate_devices import main
main(['--serve','--port','5080','--device-port','5081'])
