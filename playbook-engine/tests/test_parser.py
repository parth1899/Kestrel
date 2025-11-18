from pathlib import Path
import sys
from pathlib import Path as _P
# add project root to path so `src` becomes importable
sys.path.append(str(_P(__file__).resolve().parents[1]))
from src.core.parser import parse_playbook_text, PlaybookValidationError

GOOD = """
id: pb-process-high
version: "1.0"
metadata:
  event_type: process
  severity: high
preconditions: []
steps:
  - name: Kill
    action: kill_process
    params: {agent_id: a-1, pid: 123}
rollback: []
"""

BAD = """
id: pb-bad
steps:
  - name: Unknown
    action: non_existent
    params: {}
"""


def test_parse_good():
    pb = parse_playbook_text(GOOD)
    assert pb.id == "pb-process-high"
    assert pb.steps[0].action == "kill_process"


def test_parse_bad():
    try:
        parse_playbook_text(BAD)
        assert False, "should raise"
    except PlaybookValidationError:
        assert True
