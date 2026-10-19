"""Fixed-offset recurring schedule, matching FeatureCore::sleepRemaining (software only)."""
def remaining(config,utc):
 if not config.get('sleep_enabled') or utc<1700000000:return 0
 start=config['sleep_start_minute'];duration=config['sleep_duration_seconds'];days=config['sleep_days_mask'];offset=config['utc_offset_minutes']
 if not (0<=start<1440 and 60<=duration<=86400 and 1<=days<=127 and -720<=offset<=840):return 0
 local=int(utc)+offset*60;day=local//86400
 for anchor in (day,day-1):
  begin=anchor*86400+start*60
  if days&(1<<((anchor+4)%7)) and begin<=local<begin+duration:return begin+duration-local
 return 0
