"""Runtime compatibility patch for the 162-0 Render service."""
from pathlib import Path
import builtins
import re
try:
    from pydantic import BaseModel
    builtins.BaseModel = BaseModel
except Exception:
    pass
p=Path(__file__).with_name('server.py')
if p.exists():
    s=p.read_text(encoding='utf-8')
    # Era choices: modern baseball only, beginning with the 1960s.
    s=re.sub(r"ERAS=\[[^\n]+\]", "ERAS=['1960s','1970s','1980s','1990s','2000s','2010s','2020s']; ERA_YEARS={e:int(e[:4])+5 for e in ERAS}", s, count=1)
    # The draft UI requests 100 candidates and should be allowed to receive them.
    s=re.sub(r"Query\(60,ge=20,le=70\)", "Query(100,ge=20,le=100)", s, count=1)
    s=s.replace('pool=hitters[:45]+pitchers[:25]', 'pool=hitters[:75]+pitchers[:25]')
    s=s.replace('pool=pool[:max(20,min(int(limit),70))]', 'pool=pool[:max(20,min(int(limit),100))]')
    s=s.replace("'players':pool[:10]", "'players':pool[:60]")
    s=s.replace("'version':'3.1'", "'version':'4.0'")
    p.write_text(s,encoding='utf-8')
