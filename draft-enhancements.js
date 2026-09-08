(function(){
  let selectedPos=null;
  const slotMap={P:'P',C:'B0','1B':'B1','2B':'B2','3B':'B3',SS:'SS',LF:'LF',CF:'CF',RF:'RF'};
  const posNames={P:'Pitcher',C:'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base',SS:'Shortstop',LF:'Left Field',CF:'Center Field',RF:'Right Field'};
  const isCompatible=(p,pos)=>!pos||pos==='P'?(!pos||p.position==='P'):pos==='C'?p.position==='C':['LF','CF','RF'].includes(pos)?['LF','CF','RF','OF'].includes(p.position):p.position===pos;
  function openPosition(pos){
    if(!POS.includes(pos)||roster[pos]) return;
    selectedPos=pos;
    const n=Object.keys(roster).length;
    document.getElementById('round').textContent=`${n+1} OF 9 · SELECT ${posNames[pos].toUpperCase()} · ${gameMode.toUpperCase()}${daily?' · DAILY':''}`;
    document.getElementById('positionTitle').textContent=posNames[pos]||pos;
    document.querySelectorAll('.slot').forEach(s=>s.style.outline=s.dataset.pos===pos?'2px solid var(--orange)':'none');
    activeFilter='ALL';
    document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    renderPlayers(pos);
  }
  function resetBoard2(){
    document.querySelectorAll('.slot').forEach(s=>{s.classList.remove('filled');s.textContent=s.dataset.pos;s.style.outline='none'});
    document.getElementById('draftCount').textContent='0/9';
    document.getElementById('playerSearch').value='';
    activeFilter='ALL';
    document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    selectedPos=null;
  }
  window.resetBoard=resetBoard2;
  window.startGame=function(mode){gameMode=mode;daily=false;round=0;roster={};teamSkip=false;eraSkip=false;document.getElementById('sim').classList.add('hidden');resetBoard2();showPage('game');nextRound()};
  window.startDaily=async function(){daily=true;gameMode='Classic';round=0;roster={};teamSkip=false;eraSkip=false;document.getElementById('sim').classList.add('hidden');resetBoard2();showPage('game');await nextRound()};
  window.nextRound=async function(){
    if(Object.keys(roster).length>=9) return finishDraft();
    round=Object.keys(roster).length+1;
    selectedPos=null;
    await getData();
    document.getElementById('round').textContent=`ROUND ${round} OF 9 · CHOOSE ANY OPEN POSITION · ${gameMode.toUpperCase()}${daily?' · DAILY':''}`;
    document.getElementById('positionTitle').textContent='Choose Any Open Position';
    document.getElementById('team').textContent=data.teams[Math.floor(Math.random()*data.teams.length)];
    document.getElementById('era').textContent=data.eras[Math.floor(Math.random()*data.eras.length)];
    teamSkip=false;eraSkip=false;document.getElementById('teamSkip').disabled=false;document.getElementById('eraSkip').disabled=false;
    activeFilter='ALL';document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));
    document.querySelectorAll('.slot').forEach(s=>s.style.outline=roster[s.dataset.pos]?'none':'2px solid transparent');
    await loadPlayers(null);
  };
  window.loadPlayers=async function(posOverride){
    const team=document.getElementById('team').textContent, era=document.getElementById('era').textContent;
    const pos=posOverride===undefined?selectedPos:posOverride;
    selectedPos=pos||null;
    document.getElementById('count').textContent='Loading MLB players…';
    try{
      const r=await api(`/player-database/top?team=${encodeURIComponent(team)}&era=${encodeURIComponent(era)}&limit=1000`);
      players=r.players||[];
      renderPlayers(selectedPos);
    }catch(e){
      players=[];
      renderPlayers(selectedPos);
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
    document.getElementById('count').textContent=currentPos?`${arr.length} ${posNames[currentPos]||currentPos} players available`:`${arr.length} players available — select any open position`;
    const box=document.getElementById('playerlist');box.innerHTML='';
    if(!arr.length){box.innerHTML='<div class="empty">No players match this team, era, position, or search.</div>';return}
    arr.forEach((p,i)=>{
      const b=document.createElement('button');b.className='player';const st=p.stats||{};const hitting=Object.prototype.hasOwnProperty.call(st,'OPS');
      const values=hitting?[['AVG',st.AVG],['OBP',st.OBP],['SLG',st.SLG],['OPS',st.OPS],['HR',st.HR],['RBI',st.RBI]]:[['ERA',st.ERA],['WHIP',st.WHIP],['W',st.W],['K',st.K],['SV',st.SV],['IP',st.IP]];
      b.innerHTML=`<span class="rank">${p.rank||i+1}</span><span class="pname"><b>${p.name}</b><small class="meta"><span class="position">${p.position||'—'}</span> · ${p.team||document.getElementById('team').textContent} · ${p.season||''}</small></span><span class="stats">${values.map(v=>`<span class="stat"><strong>${v[1]??'—'}</strong><span>${v[0]}</span></span>`).join('')}</span>`;
      b.onclick=()=>pickPlayer(p);box.appendChild(b);
    });
  };
  window.pickPlayer=function(p){
    const pos=selectedPos;
    if(!pos){alert('Select any open position on the baseball diamond first.');return}
    if(roster[pos]){alert(`${posNames[pos]||pos} is already filled. Select another open position.`);return}
    if(!isCompatible(p,pos)){alert(`${p.name} cannot fill ${posNames[pos]||pos}. Select a player at that position or choose another open position.`);return}
    const rating=Math.round(Math.min(99,Math.max(70,p.score||88)));
    roster[pos]={...p,rating,offense:rating,defense:rating,era:document.getElementById('era').textContent,team:document.getElementById('team').textContent};
    const slot=document.querySelector('.slot.'+slotMap[pos]);if(slot){slot.classList.add('filled');slot.innerHTML=`${p.name}<small>${p.position||pos}</small>`;slot.style.outline='none';}
    document.getElementById('draftCount').textContent=`${Object.keys(roster).length}/9`;
    if(Object.keys(roster).length>=9) return finishDraft();
    nextRound();
  };
  document.querySelectorAll('.slot').forEach(s=>s.addEventListener('click',()=>openPosition(s.dataset.pos)));
  document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{activeFilter=b.dataset.filter;renderPlayers(selectedPos)});
  document.getElementById('playerSearch').oninput=()=>renderPlayers(selectedPos);
  document.getElementById('sort').onchange=()=>renderPlayers(selectedPos);
})();