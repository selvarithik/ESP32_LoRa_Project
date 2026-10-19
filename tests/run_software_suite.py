"""Current phase excludes Private Chat and OTA; never imports physical acceptance runners."""
import unittest,sys,json
from pathlib import Path
suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
def cases(item):
 for child in item:
  if isinstance(child,unittest.TestSuite):yield from cases(child)
  elif not any(word in child.id().lower() for word in ('chat','ota','firmware')):yield child
selected=unittest.TestSuite(cases(suite));result=unittest.TextTestRunner(verbosity=1).run(selected)
summary=dict(scope='Software unit/API tests; excludes Private Chat, OTA and physical tests',run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),passed=result.wasSuccessful())
(Path(__file__).resolve().parents[1]/'docs/SOFTWARE_TEST_RESULTS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary));sys.exit(0 if result.wasSuccessful() else 1)
