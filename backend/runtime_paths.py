"""Source and frozen application paths; runtime data is never bundled."""
import os,sys
from pathlib import Path

def resource_root():return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
def data_dir():
 value=os.environ.get('GATEWAY_DATA_DIR')
 if value:return Path(value).expanduser().resolve()
 if getattr(sys,'frozen',False):return (Path(os.environ.get('LOCALAPPDATA',Path.home()))/'SelvarithikGateway'/'data').resolve()
 return Path(__file__).resolve().parents[1]/'data'
