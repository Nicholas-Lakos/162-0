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
    # The draft UI accepts up to 100 real MLB players from the selected team/era.
    s=s.replace("ERAS=['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s','2020s']", "ERAS=['1960s','1970s','1980s','1990s','2000s','2010s','2020s']")
    s=s.replace('Query(60,ge=20,le=70)', 'Query(100,ge=20,le=100)')
    s=s.replace('pool=hitters[:45]+pitchers[:25]', 'pool=hitters[:75]+pitchers[:25]')
    s=s.replace('pool=pool[:max(20,min(int(limit),70))]', 'pool=pool[:max(20,min(int(limit),100))]')
    s=s.replace("'players':pool[:10]", "'players':pool[:60]")
    # Keep the health version in sync so the deployed build is easy to verify.
    s=s.replace("'version':'3.1'", "'version':'4.0'")
    p.write_text(s,encoding='utf-8')
