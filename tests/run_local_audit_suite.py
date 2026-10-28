"""Local-system regression scope: no MQTT/cloud, Chat, OTA or physical runners."""
import unittest,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_*.py')
def cases(group):
 for item in group:
  if isinstance(item,unittest.TestSuite):yield from cases(item)
  elif not any(word in item.id().lower() for word in ('mqtt','cloud','chat','ota','firmware')):yield item
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(cases(suite)))
summary={'scope':'Local-system unit/API regression; excludes MQTT/cloud, Chat, OTA and physical tests','run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful()}
(root/'docs/LOCAL_AUDIT_TEST_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary));sys.exit(not result.wasSuccessful())
