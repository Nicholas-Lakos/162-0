from pathlib import Path
p=Path('server.py')
s=p.read_text()
old="""def top_players(team,era):
 season=_season_for(team,era); hitters=_stat_players(team,season,'hitting'); pitchers=_stat_players(team,season,'pitching'); hitters.sort(key=lambda x:x['score'],reverse=True); pitchers.sort(key=lambda x:x['score'],reverse=True); pool=hitters[:15]+pitchers[:5]; pool.sort(key=lambda x:x['score'],reverse=True)
 for i,p in enumerate(pool[:20],1): p['rank']=i
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'players':pool[:20]}
"""
new="""def top_players(team,era):
 season=_season_for(team,era)
 hitters=_stat_players(team,season,'hitting'); pitchers=_stat_players(team,season,'pitching')
 hitters.sort(key=lambda x:x['score'],reverse=True); pitchers.sort(key=lambda x:x['score'],reverse=True)
 pool=hitters[:75]+pitchers[:25]; pool.sort(key=lambda x:x['score'],reverse=True)
 for i,p in enumerate(pool,1): p['rank']=i
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'players':pool}
"""
if old not in s: raise SystemExit('top_players block not found')
s=s.replace(old,new)
old2=""" return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'position':position,'players':pool[:3]}
"""
new2=""" return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'position':position,'players':pool[:60]}
"""
if old2 not in s: raise SystemExit('draft return block not found')
s=s.replace(old2,new2)
# The main page already contains the original draft script. Load the enhanced version after it so the new behavior wins.
old_index="""return HTMLResponse(html.replace('</header>',inject+'</header>'))"""
new_index="""html=html.replace('</header>',inject+'</header>')
 html=html.replace('</body>','<script src=\"/draft-enhancements.js?v=4\"></script></body>')
 return HTMLResponse(html)"""
if old_index not in s: raise SystemExit('index injection block not found')
s=s.replace(old_index,new_index)
p.write_text(s)
print('162-0 server patched: deep player pool + enhanced draft script injection')
