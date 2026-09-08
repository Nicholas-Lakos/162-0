"""Runtime compatibility patch for the 162-0 Render service."""
from pathlib import Path
import builtins
try:
    from pydantic import BaseModel
    builtins.BaseModel = BaseModel
except Exception:
    pass
p=Path(__file__).with_name('server.py')
if p.exists():
    s=p.read_text(encoding='utf-8')
    # Accept the 100-player request from the draft UI instead of returning 422.
    s=s.replace('Query(60,ge=20,le=70)','Query(100,ge=20,le=100)')
    s=s.replace('pool=hitters[:45]+pitchers[:25]','pool=hitters[:75]+pitchers[:25]')
    s=s.replace('pool=pool[:max(20,min(int(limit),70))]','pool=pool[:max(20,min(int(limit),100))]')
    s=s.replace("'players':pool[:10]","'players':pool[:60]")
    p.write_text(s,encoding='utf-8')
