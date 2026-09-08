import os, sqlite3, secrets, hashlib, json, random
from datetime import datetime, timezone, date
from urllib.parse import urlencode
from urllib.request import urlopen
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
DB=os.getenv('DB_PATH','1620.db'); app=FastAPI(title='162–0 Baseball')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
POSITIONS=['P','C','1B','2B','3B','SS','LF','CF','RF']
POSITION_NAMES={'P':'Pitcher','C':'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base','SS':'Shortstop','LF':'Left Field','CF':'Center Field','RF':'Right Field'}
TEAMS=['NYY','BOS','LAD','SFG','CHC','ATL','STL','NYM','SEA','DET','HOU','OAK','PHI','BAL','CLE','MIN','CIN','PIT','SD','TOR']
TEAM_IDS={'NYY':147,'BOS':111,'LAD':119,'SFG':137,'CHC':112,'ATL':144,'STL':138,'NYM':121,'SEA':136,'DET':116,'HOU':117,'OAK':133,'PHI':143,'BAL':110,'CLE':114,'MIN':142,'CIN':113,'PIT':134,'SD':135,'TOR':141}
TEAM_NAMES={'NYY':'New York Yankees','BOS':'Boston Red Sox','LAD':'Los Angeles Dodgers','SFG':'San Francisco Giants','CHC':'Chicago Cubs','ATL':'Atlanta Braves','STL':'St. Louis Cardinals','NYM':'New York Mets','SEA':'Seattle Mariners','DET':'Detroit Tigers','HOU':'Houston Astros','OAK':'Oakland Athletics','PHI':'Philadelphia Phillies','BAL':'Baltimore Orioles','CLE':'Cleveland Guardians','MIN':'Minnesota Twins','CIN':'Cincinnati Reds','PIT':'Pittsburgh Pirates','SD':'San Diego Padres','TOR':'Toronto Blue Jays'}
ERAS=['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s','2020s']; ERA_YEARS={e:int(e[:4])+5 for e in ERAS}
TRIVIA=[(1,'Which team broke an 86-year World Series drought in 2004?',['Boston Red Sox','Chicago Cubs','Cleveland Indians','New York Mets'],0),(1,'How many outs are in a standard half-inning?',['2','3','4','6'],1),(2,'Who threw a perfect game for the Yankees in 1956?',['Don Larsen','Whitey Ford','Allie Reynolds','Bob Feller'],0),(2,'Who holds MLB’s all-time career hits record?',['Derek Jeter','Pete Rose','Ty Cobb','Ichiro Suzuki'],1),(3,'Who won the 2016 World Series?',['Cubs','Indians','Red Sox','Mets'],0),(3,'Which pitcher recorded the most career saves?',['Trevor Hoffman','Mariano Rivera','Lee Smith','Rollie Fingers'],1),(4,'Who was the first unanimous AL MVP?',['Mike Trout','Bryce Harper','Miguel Cabrera','Babe Ruth'],0),(4,'Which franchise drafted Cal Ripken Jr.?',['Orioles','Yankees','Red Sox','Twins'],0),(5,'Who won the Triple Crown and MVP in the same season twice?',['Ted Williams','Miguel Cabrera','Mickey Mantle','Frank Robinson'],0),(5,'Who owns the MLB single-season strikeout record?',['Nolan Ryan','Randy Johnson','Pedro Martinez','Matt Kilroy'],3)]
class Draft(BaseModel): mode:str='Classic'; team:str=''; era:str=''; roster:dict; username:str=''
class User(BaseModel): username:str; password:str
class Challenge(BaseModel): username:str; mode:str='Head to Head'; roster:dict={}; wins:int=0; losses:int=0
def db():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, created TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY, username TEXT, mode TEXT, team TEXT, era TEXT, roster TEXT, wins INTEGER, losses INTEGER, created TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS challenges(id INTEGER PRIMARY KEY, code TEXT UNIQUE, username TEXT, mode TEXT, roster TEXT, wins INTEGER, losses INTEGER, opponent TEXT, created TEXT)'); c.commit(); return c
def pw(x): return hashlib.sha256(x.encode()).hexdigest()
def sim(roster):
 vals=list(roster.values()); offense=sum(float(v.get('offense',v.get('rating',88))) for v in vals)/len(vals); defense=sum(float(v.get('defense',v.get('rating',88))) for v in vals)/len(vals); pitching=float(next((v.get('rating',88) for p,v in roster.items() if p=='P'),88)); balance=100-abs(offense-defense)*.35; strength=.34*offense+.30*defense+.26*pitching+.10*balance; p=max(.18,min(.93,.50+(strength-88)*.019)); wins=0; games=[]
 for g in range(162):
  fatigue=-.012 if g>135 else (-.004 if g>110 else 0); game_p=max(.12,min(.97,p+(0.008 if g%2==0 else -.002)+fatigue+random.uniform(-.025,.025))); w=random.random()<game_p; games.append(int(w)); wins+=int(w)
 return wins,162-wins,games,round(strength,1)
_player_cache={}
def _api(path,params):
 key=path+'?'+urlencode(sorted(params.items()))
 if key in _player_cache:return _player_cache[key]
 try:
  with urlopen('https://statsapi.mlb.com/api/v1/'+path+'?'+urlencode(params),timeout=12) as r: data=json.loads(r.read().decode('utf-8'))
 except Exception: data={}
 _player_cache[key]=data; return data
def _season_for(team,era):
 target=ERA_YEARS.get(era,2025); tid=TEAM_IDS.get(team)
 if not tid:return target
 for delta in [0,-1,1,-2,2,-3,3,-4,4,-5,5,10,-10]:
  y=target+delta
  if y<1876 or y>2026: continue
  d=_api('teams/'+str(tid)+'/roster',{'season':y,'rosterType':'fullRoster'})
  if d.get('roster'): return y
 return target
def _stat_players(team,season,group):
 tid=TEAM_IDS.get(team)
 if not tid:return []
 d=_api('stats',{'stats':'season','group':group,'season':season,'teamId':tid,'limit':100,'sportIds':1}); splits=d.get('stats',[])
 if len(splits)==1 and isinstance(splits[0],dict) and 'splits' in splits[0]: splits=splits[0]['splits']
 out=[]
 for s in splits:
  p=s.get('player') or {}; st=s.get('stat') or {}; pos=(p.get('primaryPosition') or {}).get('abbreviation') or (s.get('position') or {}).get('abbreviation') or ('P' if group=='pitching' else 'DH'); name=p.get('fullName') or s.get('playerName')
  if not name: continue
  if group=='hitting':
   score=float(st.get('ops',0) or 0)*1000+float(st.get('homeRuns',0) or 0)*2+float(st.get('hits',0) or 0)*.05+float(st.get('rbi',0) or 0)*.03; stats={'AVG':st.get('avg','—'),'OBP':st.get('obp','—'),'SLG':st.get('slg','—'),'OPS':st.get('ops','—'),'HR':st.get('homeRuns','—'),'RBI':st.get('rbi','—')}
  else:
   era=float(st.get('era',99) or 99); score=(10-max(0,era))*100+float(st.get('wins',0) or 0)*1.5+float(st.get('strikeOuts',0) or 0)*.04+float(st.get('saves',0) or 0)*.5; stats={'ERA':st.get('era','—'),'WHIP':st.get('whip','—'),'W':st.get('wins','—'),'K':st.get('strikeOuts','—'),'SV':st.get('saves','—'),'IP':st.get('inningsPitched','—')}
  out.append({'name':name,'position':pos,'team':team,'season':season,'stats':stats,'score':score,'playerId':p.get('id')})
 return out
def top_players(team,era):
 season=_season_for(team,era); hitters=_stat_players(team,season,'hitting'); pitchers=_stat_players(team,season,'pitching'); hitters.sort(key=lambda x:x['score'],reverse=True); pitchers.sort(key=lambda x:x['score'],reverse=True); pool=hitters[:15]+pitchers[:5]; pool.sort(key=lambda x:x['score'],reverse=True)
 for i,p in enumerate(pool[:20],1): p['rank']=i
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'players':pool[:20]}
@app.get('/api/health')
def health(): return {'ok':True,'service':'162-0','version':'3.0'}
@app.get('/api/players')
def players(): return {'positions':POSITIONS,'positionNames':POSITION_NAMES,'players':{},'teams':TEAMS,'teamNames':TEAM_NAMES,'eras':ERAS}
@app.get('/api/player-database/top')
def player_database_top(team:str,era:str):
 if team not in TEAM_IDS or era not in ERAS: raise HTTPException(400,'Invalid team or era')
 return top_players(team,era)
@app.get('/api/player-database/draft')
def player_database_draft(team:str,era:str,position:str):
 if team not in TEAM_IDS or era not in ERAS or position not in POSITIONS: raise HTTPException(400,'Invalid team, era, or position')
 season=_season_for(team,era); candidates=[]
 for group in ('hitting','pitching'): candidates.extend(_stat_players(team,season,group))
 def eligible(p):
  pos=p.get('position','')
  if position=='P': return pos=='P'
  if position=='C': return pos in ('C','')
  if position in ('LF','CF','RF'): return pos in ('LF','CF','RF','OF')
  return pos==position
 pool=[p for p in candidates if eligible(p)]; pool.sort(key=lambda x:x['score'],reverse=True)
 return {'team':team,'teamName':TEAM_NAMES.get(team,team),'era':era,'season':season,'position':position,'players':pool[:3]}
@app.get('/api/player-database/search')
def player_database_search(q:str=Query(...,min_length=1)):
 q=q.strip().lower(); results=[]; d=_api('sports/1/players',{'season':2026}); people=d.get('people',[]); matches=[p for p in people if q in p.get('fullName','').lower()][:30]
 for p in matches:
  pid=p.get('id'); position=(p.get('primaryPosition') or {}).get('abbreviation',''); h=_api('people/'+str(pid),{}); person=(h.get('people') or [{}])[0] if h else p; s=_api('people/'+str(pid)+'/stats',{'stats':'yearByYear','group':'hitting'}); splits=s.get('stats',[])
  if len(splits)==1 and isinstance(splits[0],dict) and 'splits' in splits[0]: splits=splits[0]['splits']
  latest=splits[-1].get('stat',{}) if splits else {}; stats={'AVG':latest.get('avg','—'),'OBP':latest.get('obp','—'),'SLG':latest.get('slg','—'),'OPS':latest.get('ops','—'),'HR':latest.get('homeRuns','—'),'RBI':latest.get('rbi','—')}; results.append({'name':person.get('fullName') or p.get('fullName'),'position':position,'team':(p.get('currentTeam') or {}).get('name',''),'season':2026,'stats':stats,'playerId':pid})
 return {'query':q,'players':results}
@app.get('/api/trivia')
def trivia(): return {'questions':[{'tier':t,'question':q,'answers':a,'correct':c} for t,q,a,c in TRIVIA]}
@app.get('/api/daily')
def daily():
 seed=int(hashlib.sha256(date.today().isoformat().encode()).hexdigest()[:12],16); rng=random.Random(seed); return {'date':date.today().isoformat(),'team':rng.choice(TEAMS),'era':rng.choice(ERAS),'seed':seed}
@app.post('/api/signup')
def signup(u:User):
 c=db(); name=u.username.strip()
 if len(name)<3 or len(u.password)<6: c.close(); raise HTTPException(400,'Username must be 3+ characters and password 6+ characters')
 try: c.execute('INSERT INTO users(username,password,created) VALUES(?,?,?)',(name,pw(u.password),datetime.now(timezone.utc).isoformat())); c.commit()
 except sqlite3.IntegrityError: c.close(); raise HTTPException(409,'Username already exists')
 c.close(); return {'token':secrets.token_urlsafe(24),'username':name}
@app.post('/api/login')
def login(u:User):
 c=db(); row=c.execute('SELECT username FROM users WHERE username=? AND password=?',(u.username.strip(),pw(u.password))).fetchone(); c.close()
 if not row: raise HTTPException(401,'Invalid username or password')
 return {'token':secrets.token_urlsafe(24),'username':row[0]}
@app.post('/api/simulate')
def simulate(d:Draft):
 if set(d.roster)!=set(POSITIONS): raise HTTPException(400,'Complete all nine positions')
 wins,losses,games,strength=sim(d.roster); c=db(); c.execute('INSERT INTO games(username,mode,team,era,roster,wins,losses,created) VALUES(?,?,?,?,?,?,?,?)',(d.username.strip(),d.mode,d.team,d.era,json.dumps(d.roster),wins,losses,datetime.now(timezone.utc).isoformat())); c.commit(); c.close(); return {'wins':wins,'losses':losses,'games':games,'perfect':wins==162,'strength':strength}
@app.post('/api/challenges')
def create_challenge(d:Challenge):
 code=secrets.token_urlsafe(5).replace('-','').replace('_','')[:7].upper(); c=db(); c.execute('INSERT INTO challenges(code,username,mode,roster,wins,losses,created) VALUES(?,?,?,?,?,?,?)',(code,d.username,d.mode,json.dumps(d.roster),d.wins,d.losses,datetime.now(timezone.utc).isoformat())); c.commit(); c.close(); return {'code':code}
@app.get('/api/challenges/{code}')
def get_challenge(code:str):
 c=db(); r=c.execute('SELECT code,username,mode,roster,wins,losses,opponent,created FROM challenges WHERE code=?',(code.upper(),)).fetchone(); c.close()
 if not r: raise HTTPException(404,'Challenge not found')
 return dict(zip(['code','username','mode','roster','wins','losses','opponent','created'],r))
@app.get('/api/leaderboard')
def leaderboard():
 c=db(); rows=c.execute("SELECT username,mode,team,era,wins,losses,created FROM games WHERE username!='' ORDER BY wins DESC,losses ASC,id ASC LIMIT 100").fetchall(); c.close(); return {'rows':[dict(zip(['username','mode','team','era','wins','losses','created'],r)) for r in rows]}
@app.get('/api/stats/{username}')
def stats(username:str):
 c=db(); rows=c.execute('SELECT wins,losses,roster,created,mode FROM games WHERE username=? ORDER BY wins DESC,id ASC',(username,)).fetchall(); c.close(); return {'gamesPlayed':len(rows),'bestWins':rows[0][0] if rows else 0,'bestLosses':rows[0][1] if rows else 162,'perfectSeasons':sum(r[0]==162 for r in rows),'bestRoster':json.loads(rows[0][2]) if rows else {},'history':[{'wins':r[0],'losses':r[1],'mode':r[4],'created':r[3]} for r in rows[:10]]}
@app.get('/players')
def player_browser(): return FileResponse('players.html')
@app.get('/')
def index():
 html=open('index.html','r',encoding='utf-8').read(); inject='<a href="/players" style="margin-left:12px;color:#ffb02e;font-weight:800;text-decoration:none">PLAYER DATABASE</a>'; return HTMLResponse(html.replace('</header>',inject+'</header>'))
