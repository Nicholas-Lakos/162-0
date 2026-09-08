import os, sqlite3, secrets, hashlib, json, random
from datetime import datetime, timezone, date
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
DB=os.getenv('DB_PATH','1620.db'); app=FastAPI(title='162–0 Baseball')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
POSITIONS=['P','C','1B','2B','3B','SS','LF','CF','RF']
POSITION_NAMES={'P':'Pitcher','C':'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base','SS':'Shortstop','LF':'Left Field','CF':'Center Field','RF':'Right Field'}
TEAMS=['NYY','BOS','LAD','SFG','CHC','ATL','STL','NYM','SEA','DET','HOU','OAK','PHI','BAL','CLE','MIN','CIN','PIT','SD','TOR']
ERAS=['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s','2020s']
PLAYERS={'P':[('Sandy Koufax',97),('Pedro Martinez',98),('Randy Johnson',98),('Walter Johnson',99),('Greg Maddux',97),('Cy Young',99),('Nolan Ryan',96),('Tom Seaver',96),('Bob Gibson',97),('Mariano Rivera',96)],'C':[('Johnny Bench',98),('Yogi Berra',96),('Mike Piazza',97),('Roy Campanella',96),('Ivan Rodriguez',95),('Josh Gibson',99),('Carlton Fisk',94),('Gary Carter',94)],'1B':[('Lou Gehrig',99),('Albert Pujols',98),('Frank Thomas',97),('Jimmie Foxx',98),('Willie McCovey',95),('Hank Greenberg',96),('Miguel Cabrera',96)],'2B':[('Rogers Hornsby',99),('Joe Morgan',97),('Jackie Robinson',98),('Roberto Alomar',94),('Nap Lajoie',98),('Rod Carew',97),('Jeff Kent',93)],'3B':[('Mike Schmidt',99),('George Brett',98),('Wade Boggs',97),('Eddie Mathews',97),('Chipper Jones',96),('Adrian Beltre',95)],'SS':[('Derek Jeter',95),('Cal Ripken Jr.',97),('Honus Wagner',99),('Alex Rodriguez',98),('Ozzie Smith',95),('Ernie Banks',96),('Barry Larkin',94)],'LF':[('Ted Williams',99),('Barry Bonds',99),('Rickey Henderson',98),('Stan Musial',98),('Manny Ramirez',95),('Carl Yastrzemski',95)],'CF':[('Willie Mays',99),('Ken Griffey Jr.',98),('Mickey Mantle',99),('Ty Cobb',99),('Joe DiMaggio',97),('Mike Trout',97)],'RF':[('Hank Aaron',99),('Babe Ruth',100),('Ichiro Suzuki',95),('Roberto Clemente',97),('Frank Robinson',96),('Sammy Sosa',94)]}
TRIVIA=[(1,'Which team broke an 86-year World Series drought in 2004?',['Boston Red Sox','Chicago Cubs','Cleveland Indians','New York Mets'],0),(1,'How many outs are in a standard half-inning?',['2','3','4','6'],1),(2,'Who threw a perfect game for the Yankees in 1956?',['Don Larsen','Whitey Ford','Allie Reynolds','Bob Feller'],0),(2,'Who holds MLB’s all-time career hits record?',['Derek Jeter','Pete Rose','Ty Cobb','Ichiro Suzuki'],1),(3,'Who won the 2016 World Series?',['Cubs','Indians','Red Sox','Mets'],0),(3,'Which pitcher recorded the most career saves?',['Trevor Hoffman','Mariano Rivera','Lee Smith','Rollie Fingers'],1),(4,'Who was the first unanimous AL MVP?',['Mike Trout','Bryce Harper','Miguel Cabrera','Babe Ruth'],0),(4,'Which franchise drafted Cal Ripken Jr.?',['Orioles','Yankees','Red Sox','Twins'],0),(5,'Who won the Triple Crown and MVP in the same season twice?',['Ted Williams','Miguel Cabrera','Mickey Mantle','Frank Robinson'],0),(5,'Who owns the MLB single-season strikeout record?',['Nolan Ryan','Randy Johnson','Pedro Martinez','Matt Kilroy'],3)]
class Draft(BaseModel): mode:str='Classic'; team:str=''; era:str=''; roster:dict; username:str=''
class User(BaseModel): username:str; password:str
class Challenge(BaseModel): username:str; mode:str='Head to Head'; roster:dict={}; wins:int=0; losses:int=0
def db():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, created TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY, username TEXT, mode TEXT, team TEXT, era TEXT, roster TEXT, wins INTEGER, losses INTEGER, created TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS challenges(id INTEGER PRIMARY KEY, code TEXT UNIQUE, username TEXT, mode TEXT, roster TEXT, wins INTEGER, losses INTEGER, opponent TEXT, created TEXT)'); c.commit(); return c
def pw(x): return hashlib.sha256(x.encode()).hexdigest()
def card(pos,name,rating):
 seed=int(hashlib.sha256(name.encode()).hexdigest()[:8],16); off=max(60,min(100,rating-2+seed%7)); deff=max(60,min(100,rating-1+(seed//7)%7)); clutch=max(60,min(100,rating+(seed//49)%5-2)); return {'name':name,'rating':rating,'offense':off,'defense':deff,'clutch':clutch,'position':pos}
def sim(roster):
 vals=list(roster.values()); offense=sum(float(v.get('offense',v.get('rating',88))) for v in vals)/len(vals); defense=sum(float(v.get('defense',v.get('rating',88))) for v in vals)/len(vals); pitching=float(next((v.get('rating',88) for p,v in roster.items() if p=='P'),88)); balance=100-abs(offense-defense)*.35; strength=.34*offense+.30*defense+.26*pitching+.10*balance; p=max(.18,min(.93,.50+(strength-88)*.019)); wins=0; games=[]
 for g in range(162):
  fatigue=-.012 if g>135 else (-.004 if g>110 else 0); game_p=max(.12,min(.97,p+(0.008 if g%2==0 else -.002)+fatigue+random.uniform(-.025,.025))); w=random.random()<game_p; games.append(int(w)); wins+=int(w)
 return wins,162-wins,games,round(strength,1)
@app.get('/api/health')
def health(): return {'ok':True,'service':'162-0','version':'2.0'}
@app.get('/api/players')
def players(): return {'positions':POSITIONS,'positionNames':POSITION_NAMES,'players':{p:[card(p,n,r) for n,r in vals] for p,vals in PLAYERS.items()},'teams':TEAMS,'eras':ERAS}
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
@app.get('/')
def index(): return FileResponse('index.html')
