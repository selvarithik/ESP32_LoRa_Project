"""Trusted local operator settings. Never handles or prints deployment credentials."""
import argparse,json,socket
import local_ip

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--bind');parser.add_argument('--port',type=int,default=5001);parser.add_argument('--enable',action='store_true');parser.add_argument('--expected-revision',type=int)
 args=parser.parse_args();local_ip.service.migrate();old=local_ip.service.settings()
 if not args.apply:print(json.dumps(old,indent=2));return
 if args.bind is None or args.expected_revision is None:parser.error('--apply requires --bind and --expected-revision')
 # Reuse validation, real bind test and rollback; stop only this temporary listener.
 try:result=local_ip.service.configure(dict(expected_revision=args.expected_revision,enabled=args.enable,bind_address=args.bind,port=args.port))
 finally:local_ip.service.stop()
 print('Local listener settings saved. Restart the existing Gateway once; do not run a duplicate server.')

if __name__=='__main__':
 try:main()
 except (ValueError,OSError):raise SystemExit('Local listener configuration rejected; inspect address, port and revision. No secret details displayed.')
