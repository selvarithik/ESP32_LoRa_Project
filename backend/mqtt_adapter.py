"""Legacy entry point: canonical TLS service; insecure legacy profiles require migration."""
import mqtt_api

def build_client(host, port, username, password, ca, trust_acl=False):
    # Old-topic callers must explicitly migrate rather than silently change semantics.
    raise ValueError('MIGRATION_REQUIRED: use canonical profile commissioning')

def start_from_environment(portable_acl_confirmed=False):
    return mqtt_api.start(portable_acl_confirmed) if portable_acl_confirmed else mqtt_api.start()
