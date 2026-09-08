import os, sqlite3, secrets, hashlib, json, random
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
DB=os.getenv('DB_PATH','1620.db'); app=FastAPI(title='162–0 Baseball')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
POSITIONS=['P','C','1B','2B','3B','SS','LF','CF','RF']
PLAYERS={'P':[('Sandy Koufax',97),('Pedro Martinez',98),('Randy Johnson',98),('Walter Johnson',99),('Greg Maddux',97),('Cy Young',99),('Nolan Ryan',96),('Tom Seaver',96),('Bob Gibson',97),('Mariano Rivera',96)],'C':[('Johnny Bench',98),('Yogi Berra',96),('Mike Piazza',97),('Roy Campanella',96),('Ivan Rodriguez',95),('Josh Gibson',99),('Carlton Fisk',94),('Gary Carter',94)],'1B':[('Lou Gehrig',99),('Albert Pujols',98),('Frank Thomas',97),('Jimmie Foxx',98),('Willie McCovey',95),('Hank Greenberg',96),('Miguel Cabrera',96)],'2B':[('Rogers Hornsby',99),('Joe Morgan',97),('Jackie Robinson',98),('Roberto Alomar',94),('Nap Lajoie',98),('Rod Carew',97),('Jeff Kent',93)],'3B':[('Mike Schmidt',99),('George Brett',98),('Wade Boggs',97),('Eddie Mathews',97),('Chipper Jones',96),('Adrian Beltre',95)],'SS':[('Derek Jeter',95),('Cal Ripken Jr.',97),('Honus Wagner',99),('Alex Rodriguez',98),('Ozzie Smith',95),('Ernie Banks',96),('Barry Larkin',94)],'LF':[('Ted Williams',99),('Barry Bonds',99),('Rickey Henderson',98),('Stan Musial',98),('Manny Ramirez',95),('Carl Yastrzemski',95)],'CF':[('Willie Mays',99),('Ken Griffey Jr.',98),('Mickey Mantle',99),('Ty Cobb',99),('Joe DiMaggio',97),('Mike Trout',97)],'RF':[('Hank Aaron',99),('Babe Ruth',100),('Ichiro Suzuki',95),('Roberto Clemente',97),('Frank Robinson',96),('Sammy Sosa',94)]}
TEAMS=['NYY','BOS','LAD','SFG','CHC','ATL','STL','NYM','SEA','DET','HOU','OAK','PHI','BAL','CLE','MIN','CIN','PIT','SD','TOR']; ERAS=['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s','2020s']
class Draft(BaseModel): mode:str='Classic'; team:str; era:str; roster:dict; username:str=''
class User(BaseModel): username:str; password:str
def db():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, created TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY, username TEXT, mode TEXT, team TEXT, era TEXT, roster TEXT, wins INTEGER, losses INTEGER, created TEXT)'); c.commit(); return c
def pw(x): return hashlib.sha256(x.encode()).hexdigest()
def sim(roster):
 strength=sum(int(v.get('rating',90)) for v in roster.values())/max(1,len(roster)); wins=0; games=[]
 for _ in range(162):
  p=max(.10,min(.96,.50+(strength-90)*.018)); w=random.random()<p; wins+=w; games.append(1 if w else 0)
 return wins,162-wins,games
@app.get('/api/health')
def health(): return {'ok':True,'service':'162-0'}
@app.get('/api/players')
def players(): return {'positions':POSITIONS,'players':{p:[{'name':n,'rating':r} for n,r in vals] for p,vals in PLAYERS.items()},'teams':TEAMS,'eras':ERAS}
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
 wins,losses,games=sim(d.roster); c=db(); c.execute('INSERT INTO games(username,mode,team,era,roster,wins,losses,created) VALUES(?,?,?,?,?,?,?,?)',(d.username.strip(),d.mode,d.team,d.era,json.dumps(d.roster),wins,losses,datetime.now(timezone.utc).isoformat())); c.commit(); c.close(); return {'wins':wins,'losses':losses,'games':games,'perfect':wins==162}
@app.get('/api/leaderboard')
def leaderboard():
 c=db(); rows=c.execute("SELECT username,mode,team,era,wins,losses,created FROM games WHERE username!='' ORDER BY wins DESC,id ASC LIMIT 50").fetchall(); c.close(); return {'rows':[dict(zip(['username','mode','team','era','wins','losses','created'],r)) for r in rows]}
@app.get('/api/stats/{username}')
def stats(username:str):
 c=db(); rows=c.execute('SELECT wins,losses,roster,created FROM games WHERE username=? ORDER BY wins DESC',(username,)).fetchall(); c.close(); return {'gamesPlayed':len(rows),'bestWins':rows[0][0] if rows else 0,'perfectSeasons':sum(r[0]==162 for r in rows),'bestRoster':json.loads(rows[0][2]) if rows else {}}
@app.get('/')
def index(): return FileResponse('index.html')
