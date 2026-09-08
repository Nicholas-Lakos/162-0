(function(){
  let selectedPos='P';
  const slotMap={P:'P',C:'B0','1B':'B1','2B':'B2','3B':'B3',SS:'SS',LF:'LF',CF:'CF',RF:'RF'};
  const posNames={P:'Pitcher',C:'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base',SS:'Shortstop',LF:'Left Field',CF:'Center Field',RF:'Right Field'};
  const isCompatible=(p,pos)=>pos==='P'?p.position==='P':pos==='C'?p.position==='C':['LF','CF','RF'].includes(pos)?['LF','CF','RF','OF'].includes(p.position):p.position===pos;
  function openPosition(pos){
    if(!POS.includes(pos)||roster[pos]) return;
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
      players=r.players||[];
      renderPlayers(pos);
    }catch(e){
      players=(data.players[pos]||[]).map(x=>({name:x.name,position:pos,team,season:'',stats:{AVG:'—',OPS:'—',HR:'—',RBI:'—'},score:x.rating,playerId:`base-${pos}-${x.name}`}));
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
      const b=document.createElement('button');b.className='player';const st=p.stats||{};const hitting=Object.prototype.hasOwnProperty.call(st,'OPS');
      const values=hitting?[['AVG',st.AVG],['OBP',st.OBP],['SLG',st.SLG],['OPS',st.OPS],['HR',st.HR],['RBI',st.RBI]]:[['ERA',st.ERA],['WHIP',st.WHIP],['W',st.W],['K',st.K],['SV',st.SV],['IP',st.IP]];
      b.innerHTML=`<span class="rank">${p.rank||i+1}</span><span class="pname"><b>${p.name}</b><small class="meta"><span class="position">${p.position||currentPos}</span> · ${p.team||team} · ${p.season||''}</small></span><span class="stats">${values.map(v=>`<span class="stat"><strong>${v[1]??'—'}</strong><span>${v[0]}</span></span>`).join('')}</span>`;
      b.onclick=()=>pickPlayer(p);box.appendChild(b);
    });
  };
  window.pickPlayer=function(p){
    const pos=selectedPos||firstEmpty()||'P';
    if(roster[pos]){alert(`${posNames[pos]||pos} is already filled. Select another open position.`);return}
    if(!isCompatible(p,pos)){alert(`Choose a ${posNames[pos]||pos} player for this position.`);return}
    const rating=Math.round(Math.min(99,Math.max(70,p.score||88)));
    roster[pos]={...p,rating,offense:rating,defense:rating,era:document.getElementById('era').textContent,team:document.getElementById('team').textContent};
    const slot=document.querySelector('.slot.'+slotMap[pos]);if(slot){slot.classList.add('filled');slot.innerHTML=`${p.name}<small>${p.position||pos}</small>`;slot.style.outline='none';}
    document.getElementById('draftCount').textContent=`${Object.keys(roster).length}/9`;
    if(Object.keys(roster).length>=9) return finishDraft();
    nextRound();
  };
  document.querySelectorAll('.slot').forEach(s=>s.addEventListener('click',()=>openPosition(s.dataset.pos)));
  document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{activeFilter=b.dataset.filter;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===b));renderPlayers(selectedPos||firstEmpty()||'P')});
  document.getElementById('playerSearch').oninput=()=>renderPlayers(selectedPos||firstEmpty()||'P');
  document.getElementById('sort').onchange=()=>renderPlayers(selectedPos||firstEmpty()||'P');
})();