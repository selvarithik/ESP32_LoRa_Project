"""Opt-in loopback test session; reuses existing accounts, revocation and CSRF."""
import ipaddress
import os
import time
from urllib.parse import urlsplit
from flask import request,jsonify,session
import account_settings

PATH='/api/auth/local-test-session'

def install(app):
    app.config.setdefault('LOCAL_TEST_SESSION',os.environ.get('GATEWAY_LOCAL_TEST_SESSION')=='1')
    app.config.setdefault('LOCAL_TEST_SESSION_DEADLINE',time.monotonic()+3600)
    def create():
        if not app.config.get('LOCAL_TEST_SESSION'):return jsonify(error='NOT_FOUND'),404
        if time.monotonic()>=app.config['LOCAL_TEST_SESSION_DEADLINE']:return jsonify(error='LOCAL_TEST_WINDOW_EXPIRED'),410
        try:
            peer=ipaddress.ip_address(request.remote_addr or '')
            host=urlsplit(request.host_url).hostname
            origin=request.headers.get('Origin')
            valid=peer.is_loopback and host in ('127.0.0.1','localhost','::1') and origin==request.host_url.rstrip('/')
        except ValueError:valid=False
        if not valid:return jsonify(error='LOOPBACK_ONLY'),403
        if request.method!='POST' or request.headers.get('X-Local-Test')!='1' or not request.is_json or request.content_length is None or request.content_length>64 or request.get_json(silent=True)!={}:return jsonify(error='EXPLICIT_LOCAL_TEST_REQUEST_REQUIRED'),400
        db=account_settings.connect()
        try:
            actor=db.execute("SELECT * FROM accounts WHERE role IN ('creator','administrator') AND must_change=0 ORDER BY CASE role WHEN 'creator' THEN 0 ELSE 1 END,id LIMIT 1").fetchone()
            if not actor:return jsonify(error='NO_ELIGIBLE_EXISTING_ACCOUNT'),403
            account_settings.establish(actor)
            return jsonify(success=True,test_session=True,csrf=session['account_csrf'])
        finally:db.close()
    # This exact endpoint alone is handled before the normal auth middleware.
    # All other routes continue through existing account/role/CSRF checks.
    @app.before_request
    def local_test_endpoint():
        if request.path==PATH:return create()
    app.add_url_rule(PATH,'local_test_session',create,methods=['POST'])
