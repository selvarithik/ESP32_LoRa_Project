"""Explicit reverse-proxy trust and fail-closed deployment safeguards."""
import ipaddress,os
from flask import request,jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
class TrustedProxy:
 def __init__(self,app,proxies):self.app=app;self.proxy=ProxyFix(app,x_for=1,x_proto=1,x_host=1);self.networks=[ipaddress.ip_network(x,strict=False) for x in proxies]
 def __call__(self,environ,start_response):
  try:trusted=any(ipaddress.ip_address(environ.get('REMOTE_ADDR','')) in n for n in self.networks)
  except ValueError:trusted=False
  if trusted:return self.proxy(environ,start_response)
  for key in list(environ):
   if key.startswith('HTTP_X_FORWARDED_') or key=='HTTP_FORWARDED':environ.pop(key,None)
  return self.app(environ,start_response)

def install(app,settings,status):
 app.config.update(DEBUG=False,TESTING=False,LOCAL_TEST_SESSION=False,TRUSTED_HOSTS=settings['allowed_hosts'],SESSION_COOKIE_SECURE=settings['mode']=='proxy',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
 app.wsgi_app=TrustedProxy(app.wsgi_app,settings['trusted_proxies'])
 def enforce_https():
  if settings['mode']=='proxy' and not request.is_secure:return jsonify(error='HTTPS_REQUIRED'),400
 # Run ahead of authentication and the optional development-only endpoint.
 app.before_request_funcs.setdefault(None,[]).insert(0,enforce_https)
 @app.after_request
 def secure_headers(response):
  response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='same-origin'
  response.headers['Permissions-Policy']='camera=(), microphone=()'
  if not request.path.startswith('/static/'):response.headers['Cache-Control']='no-store'
  if request.is_secure and settings['mode']=='proxy':response.headers['Strict-Transport-Security']='max-age=31536000'
  return response
 @app.get('/healthz')
 def deployment_liveness():return jsonify(status='ok' if status().get('running') else 'starting'),200 if status().get('running') else 503
 @app.get('/api/deployment/status')
 def deployment_status():return jsonify(status())
