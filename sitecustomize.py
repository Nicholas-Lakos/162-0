"""Runtime compatibility patch for the 162-0 Render service."""
from pathlib import Path
import builtins

# server.py currently references BaseModel without importing it. Make it
# available during module execution so the existing live app can start.
try:
    from pydantic import BaseModel
    builtins.BaseModel = BaseModel
except Exception:
    pass

p = Path(__file__).with_name('server.py')
if p.exists():
    s = p.read_text(encoding='utf-8')
    old = """def top_players(team,era):
 season=_season_for(team,era); hitters=_stat_players(team,season,'hitting'); pitchers=_stat_players(team,season,'pitching'); hitters.sort(key=lambda x:x['score'],reverse=True); pitchers.sort(key=lambda x:x['score'],reverse=True); pool=hitters[:15]+pitchers[:5]; pool.sort(key=lambda x:x['score'],reverse=True)
 for i,p in enumerate(pool[:20],1): p['rank']=i
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'players':pool[:20]}
"""
    new = """def top_players(team,era):
 season=_season_for(team,era)
 hitters=_stat_players(team,season,'hitting'); pitchers=_stat_players(team,season,'pitching')
 hitters.sort(key=lambda x:x['score'],reverse=True); pitchers.sort(key=lambda x:x['score'],reverse=True)
 pool=hitters[:75]+pitchers[:25]; pool.sort(key=lambda x:x['score'],reverse=True)
 for i,p in enumerate(pool,1): p['rank']=i
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'players':pool}
"""
    if old in s: s = s.replace(old, new)
    old2 = """ return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'position':position,'players':pool[:3]}
"""
    new2 = """ return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'position':position,'players':pool[:60]}
"""
    if old2 in s: s = s.replace(old2, new2)
    old3 = """ return HTMLResponse(html.replace('</header>',inject+'</header>'))"""
    new3 = """ html=html.replace('</header>',inject+'</header>')
 html=html.replace('</body>','<script src=\"/draft-enhancements.js?v=4\"></script></body>')
 return HTMLResponse(html)"""
    if old3 in s: s = s.replace(old3, new3)
    p.write_text(s, encoding='utf-8')
