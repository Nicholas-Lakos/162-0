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
 # Keep a deep draft pool so every position has many choices instead of only a Top 20.
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
p.write_text(s)
print('162-0 server draft pool expanded to 100 overall / 60 per position')
