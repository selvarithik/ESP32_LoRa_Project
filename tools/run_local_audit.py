"""One loopback Gateway, optional temporary local test session, no MQTT startup."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--local-test-session',action='store_true');args=parser.parse_args()
    import socket
    probe=socket.socket()
    try:
        probe.bind(('127.0.0.1',5000))
    except OSError:raise SystemExit('Gateway port5000 already occupied; no duplicate started.')
    finally:probe.close()
    import server,local_ip
    server.app.config['LOCAL_TEST_SESSION']=args.local_test_session
    server.app.config['TEMPLATES_AUTO_RELOAD']=True
    server.app.jinja_env.auto_reload=True
    try:local_ip.start_saved()
    except ValueError:print('Local device listener needs a valid saved private bind address; dashboard remains available.',flush=True)
    server.socketio.start_background_task(server.server_time_heartbeat)
    print('Local audit Gateway: http://127.0.0.1:5000; MQTT startup deliberately omitted; test session '+('enabled on loopback only' if args.local_test_session else 'disabled'),flush=True)
    server.socketio.run(server.app,host='127.0.0.1',port=5000,debug=False,use_reloader=False,allow_unsafe_werkzeug=True)

if __name__=='__main__':main()
