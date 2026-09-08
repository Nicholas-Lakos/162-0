(function(){
  let selectedPos='P';
  const slotMap={P:'P',C:'B0','1B':'B1','2B':'B2','3B':'B3',SS:'SS',LF:'LF',CF:'CF',RF:'RF'};
  const posNames={P:'Pitcher',C:'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base',SS:'Shortstop',LF:'Left Field',CF:'Center Field',RF:'Right Field'};
  const isCompatible=(p,pos)=>pos==='P'?p.position==='P':pos==='C'?p.position==='C':['LF','CF','RF'].includes(pos)?['LF','CF','RF','OF'].includes(p.position):p.position===pos;

  // Extra all-time options keep every position deep even when the MLB Stats API
  // returns only a few players for an older team/era combination.
  const extraPool={
    P:[['Christy Mathewson',97],['Lefty Grove',97],['Steve Carlton',97],['Tom Glavine',95],['Fergie Jenkins',95],['Gaylord Perry',95],['Phil Niekro',94],['John Smoltz',95],['Justin Verlander',97],['Clayton Kershaw',97],['Max Scherzer',96],['Roy Halladay',96],['Greg Maddux',97],['Pedro Martinez',98],['Randy Johnson',98],['Nolan Ryan',96],['Bob Gibson',97],['Sandy Koufax',97],['Mariano Rivera',96],['Cy Young',99]],
    C:[['Bill Dickey',95],['Gabby Hartnett',95],['Mickey Cochrane',96],['Roy Campanella',96],['Johnny Bench',98],['Yogi Berra',96],['Mike Piazza',97],['Ivan Rodriguez',95],['Carlton Fisk',94],['Gary Carter',94],['Joe Mauer',94],['Buster Posey',95],['Jorge Posada',92],['Salvador Perez',92],['Javy Lopez',91],['Brian McCann',91]],
    '1B':[['Jimmie Foxx',98],['Lou Gehrig',99],['Hank Greenberg',96],['Johnny Mize',96],['Stan Musial',98],['Willie McCovey',95],['Eddie Murray',95],['Rod Carew',97],['Steve Garvey',92],['Don Mattingly',94],['Frank Thomas',97],['Jeff Bagwell',96],['Jim Thome',95],['Albert Pujols',98],['Miguel Cabrera',96],['Mark McGwire',95],['Adrian Gonzalez',92],['Paul Goldschmidt',94]],
    '2B':[['Nap Lajoie',98],['Rogers Hornsby',99],['Eddie Collins',98],['Charlie Gehringer',97],['Joe Morgan',97],['Jackie Robinson',98],['Roberto Alomar',94],['Rod Carew',97],['Ryne Sandberg',95],['Craig Biggio',94],['Jeff Kent',93],['Chase Utley',94],['Robinson Cano',93],['Jose Altuve',94],['Dustin Pedroia',94],['Lou Whitaker',94]],
    '3B':[['Home Run Baker',96],['Eddie Mathews',97],['Mike Schmidt',99],['George Brett',98],['Wade Boggs',97],['Chipper Jones',96],['Adrian Beltre',95],['Brooks Robinson',96],['Ron Santo',95],['Wade Boggs',97],['Evan Longoria',93],['Nolan Arenado',94],['Scott Rolen',94],['Manny Machado',94],['Jose Ramirez',95]],
    SS:[['Honus Wagner',99],['Joe Cronin',95],['Luke Appling',96],['Arky Vaughan',98],['Ernie Banks',96],['Cal Ripken Jr.',97],['Ozzie Smith',95],['Robin Yount',96],['Alan Trammell',94],['Barry Larkin',94],['Derek Jeter',95],['Alex Rodriguez',98],['Nomar Garciaparra',92],['Francisco Lindor',94],['Carlos Correa',93],['Troy Tulowitzki',94]],
    LF:[['Babe Ruth',100],['Ted Williams',99],['Stan Musial',98],['Rickey Henderson',98],['Barry Bonds',99],['Carl Yastrzemski',95],['Manny Ramirez',95],['Billy Williams',94],['Willie Stargell',95],['Lou Brock',94],['Jim Rice',93],['Tim Raines',94],['Juan Soto',95],['Christian Yelich',93],['Ronald Acuna Jr.',96]],
    CF:[['Ty Cobb',99],['Tris Speaker',98],['Joe DiMaggio',97],['Willie Mays',99],['Mickey Mantle',99],['Ken Griffey Jr.',98],['Duke Snider',95],['Harmon Killebrew',95],['Andre Dawson',94],['Kirby Puckett',94],['Vladimir Guerrero',95],['Mike Trout',97],['Carlos Beltran',94],['Andrew McCutchen',93],['Cesar Cedeno',94]],
    RF:[['Babe Ruth',100],['Hank Aaron',99],['Roberto Clemente',97],['Frank Robinson',96],['Ichiro Suzuki',95],['Sammy Sosa',94],['Al Kaline',96],['Mel Ott',97],['Reggie Jackson',95],['Tony Gwynn',97],['Vladimir Guerrero',95],['Gary Sheffield',94],['Mookie Betts',96],['Aaron Judge',97],['Juan Marichal',90]]
  };

  function extraPlayers(pos){
    return (extraPool[pos]||[]).map((x,i)=>({name:x[0],position:pos,team:'All-Time',season:'All-Era',stats:{AVG:'—',OBP:'—',SLG:'—',OPS:'—',HR:'—',RBI:'—'},score:x[1],playerId:`extra-${pos}-${i}-${x[0].replace(/[^a-z0-9]/gi,'').toLowerCase()}`}));
  }
  function mergeForPosition(arr,pos){
    const seen=new Set(); const out=[];
    [...(arr||[]),...extraPlayers(pos)].forEach(p=>{
      const key=p.playerId!=null?String(p.playerId):p.name.toLowerCase();
      if(seen.has(key)) return; seen.add(key); out.push(p);
    });
    return out;
  }
  function openPosition(pos){
    if(!POS.includes(pos)) return;
    // Once a position is filled, it is locked. Any still-open position can be
    // selected at any time during the draft.
    if(roster[pos]) return;
    selectedPos=pos;
    const n=Object.keys(roster).length;
    document.getElementById('round').textContent=`${n<9?n+1:9} OF 9 · ${pos} · ${gameMode.toUpperCase()}${daily?' · DAILY':''}`;
    document.getElementById('positionTitle').textContent=posNames[pos]||pos;
    document.querySelectorAll('.slot').forEach(s=>s.style.outline=s.dataset.pos===pos?'2px solid var(--orange)':'none');
    activeFilter='ALL';
    document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    loadPlayers(pos);
  }
  function firstEmpty(){return POS.find(p=>!roster[p])||null}
  function resetBoard2(){
    document.querySelectorAll('.slot').forEach(s=>{s.classList.remove('filled');s.textContent=s.dataset.pos;s.style.outline='none'});
    document.getElementById('draftCount').textContent='0/9';
    document.getElementById('playerSearch').value='';
    activeFilter='ALL';
    document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    selectedPos='P';
  }
  window.resetBoard=resetBoard2;
  window.startGame=function(mode){gameMode=mode;daily=false;round=0;roster={};teamSkip=false;eraSkip=false;document.getElementById('sim').classList.add('hidden');resetBoard2();showPage('game');nextRound()};
  window.startDaily=async function(){daily=true;gameMode='Classic';round=0;roster={};teamSkip=false;eraSkip=false;document.getElementById('sim').classList.add('hidden');resetBoard2();showPage('game');await nextRound()};
  window.nextRound=async function(){
    if(Object.keys(roster).length>=9) return finishDraft();
    const p=firstEmpty()||'P'; round=Object.keys(roster).length+1; selectedPos=p;
    await getData();
    document.getElementById('round').textContent=`ROUND ${round} OF 9 · ${p} · ${gameMode.toUpperCase()}${daily?' · DAILY':''}`;
    document.getElementById('positionTitle').textContent=posNames[p]||p;
    document.getElementById('team').textContent=data.teams[Math.floor(Math.random()*data.teams.length)];
    document.getElementById('era').textContent=data.eras[Math.floor(Math.random()*data.eras.length)];
    teamSkip=false;eraSkip=false;document.getElementById('teamSkip').disabled=false;document.getElementById('eraSkip').disabled=false;
    activeFilter='ALL';document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    document.querySelectorAll('.slot').forEach(s=>s.style.outline=s.dataset.pos===p?'2px solid var(--orange)':'none');
    await loadPlayers(p);
  };
  window.loadPlayers=async function(posOverride){
    const team=document.getElementById('team').textContent, era=document.getElementById('era').textContent, pos=posOverride||selectedPos||firstEmpty()||'P';
    selectedPos=pos; document.getElementById('count').textContent='Loading MLB players…';
    try{
      const r=await api(`/player-database/top?team=${encodeURIComponent(team)}&era=${encodeURIComponent(era)}&limit=100`);
      players=mergeForPosition(r.players||[],pos); renderPlayers(pos);
    }catch(e){
      players=mergeForPosition((data.players[pos]||[]).map(x=>({name:x.name,position:pos,team,season:'',stats:{AVG:'—',OPS:'—',HR:'—',RBI:'—'},score:x.rating,playerId:`base-${pos}-${x.name}`})),pos);
      renderPlayers(pos);
    }
  };
  window.renderPlayers=function(currentPos){
    const q=document.getElementById('playerSearch').value.trim().toLowerCase(),sort=document.getElementById('sort').value;
    let arr=players.filter(p=>{
      const filter=activeFilter||'ALL';
      const compatible=isCompatible(p,currentPos);
      const filterMatch=filter==='ALL'||(filter==='P'&&p.position==='P')||(filter==='C'&&p.position==='C')||(filter==='G'&&['1B','2B','3B','SS'].includes(p.position))||(filter==='F'&&['LF','CF','RF','OF'].includes(p.position));
      return compatible&&filterMatch&&(!q||p.name.toLowerCase().includes(q));
    });
    arr=arr.filter(p=>!Object.values(roster).some(x=>x&&x.playerId&&p.playerId&&x.playerId===p.playerId));
    arr.sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):(b.score||0)-(a.score||0));
    document.getElementById('count').textContent=`${arr.length} players available for ${posNames[currentPos]||currentPos}`;
    const box=document.getElementById('playerlist');box.innerHTML='';
    if(!arr.length){box.innerHTML='<div class="empty">No players match this position, team, era, or search.</div>';return}
    arr.forEach((p,i)=>{
      const b=document.createElement('button');b.className='player';const st=p.stats||{};const hitting=Object.keys(st).includes('OPS');
      const values=hitting?[['AVG',st.AVG],['OBP',st.OBP],['SLG',st.SLG],['OPS',st.OPS],['HR',st.HR],['RBI',st.RBI]]:[['ERA',st.ERA],['WHIP',st.WHIP],['W',st.W],['K',st.K],['SV',st.SV],['IP',st.IP]];
      b.innerHTML=`<span class="rank">${p.rank||i+1}</span><span class="pname"><b>${p.name}</b><small class="meta"><span class="position">${p.position||currentPos}</span> · ${p.team||document.getElementById('team').textContent} · ${p.season||''}</small></span><span class="stats">${values.map(v=>`<span class="stat"><strong>${v[1]??'—'}</strong><span>${v[0]}</span></span>`).join('')}</span>`;
      b.onclick=()=>pickPlayer(p);box.appendChild(b);
    });
  };
  window.pickPlayer=function(p){
    const pos=selectedPos||firstEmpty()||'P';
    if(roster[pos]){alert(`${posNames[pos]||pos} is already filled. Select another open position.`);return}
    if(!isCompatible(p,pos)){alert(`Choose a ${posNames[pos]||pos} player for this position.`);return}
    roster[pos]={...p,rating:Math.round(Math.min(99,Math.max(70,(p.score||88)))),offense:Math.min(99,p.score||88),defense:Math.min(99,p.score||88),era:document.getElementById('era').textContent,team:document.getElementById('team').textContent};
    const slot=document.querySelector('.slot.'+slotMap[pos]);if(slot){slot.classList.add('filled');slot.innerHTML=`${p.name}<small>${p.position||pos}</small>`;slot.style.outline='none';}
    document.getElementById('draftCount').textContent=`${Object.keys(roster).length}/9`;
    if(Object.keys(roster).length>=9) return finishDraft();
    // After a pick, automatically move to the next open position, but the user
    // can click any other open diamond position instead.
    nextRound();
  };
  document.querySelectorAll('.slot').forEach(s=>s.addEventListener('click',()=>openPosition(s.dataset.pos)));
  document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{activeFilter=b.dataset.filter;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===b));renderPlayers(selectedPos||firstEmpty()||'P')});
  document.getElementById('playerSearch').oninput=()=>renderPlayers(selectedPos||firstEmpty()||'P');
  document.getElementById('sort').onchange=()=>renderPlayers(selectedPos||firstEmpty()||'P');
})();
