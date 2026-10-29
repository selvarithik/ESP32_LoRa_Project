"""Gateway executable/source launcher. Runtime data stays outside the bundle."""
import sys
from pathlib import Path
if not getattr(sys,'frozen',False):sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from gateway_runtime import cli
if __name__=='__main__':raise SystemExit(cli())
