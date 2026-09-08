(function(){
  const names={P:'Pitcher',C:'Catcher','1B':'First Base','2B':'Second Base','3B':'Third Base',SS:'Shortstop',LF:'Left Field',CF:'Center Field',RF:'Right Field'};
  const nums=v=>{const n=parseFloat(v);return Number.isFinite(n)?n:null};
  function overall(p){
    const s=p.stats||{};
    if(p.position==='P'){
      const era=nums(s.ERA),whip=nums(s.WHIP),k=nums(s.K),sv=nums(s.SV),w=nums(s.W);
      let r=84;
      if(era!==null) r+=Math.max(-16,Math.min(10,(3.80-era)*5));
      if(whip!==null) r+=Math.max(-8,Math.min(8,(1.35-whip)*16));
      if(k!==null) r+=Math.max(-5,Math.min(7,(k-140)/35));
      if(sv!==null) r+=Math.min(5,sv/12); if(w!==null) r+=Math.min(4,w/6);
      return Math.round(Math.max(60,Math.min(99,r)));
    }
    const avg=nums(s.AVG),ops=nums(s.OPS),hr=nums(s.HR),rbi=nums(s.RBI);
    let r=70;
    if(avg!==null) r+=(avg-.260)*90;
    if(ops!==null) r+=(ops-.700)*45;
    if(hr!==null) r+=Math.min(8,Math.max(-2,hr/12));
    if(rbi!==null) r+=Math.min(5,Math.max(-2,rbi/35));
    return Math.round(Math.max(60,Math.min(99,r)));
  }
  window.__162FinalRoster={}; window.__162SelectedPos=null;
  document.addEventListener('click',e=>{const s=e.target.closest&&e.target.closest('.slot');if(s&&s.dataset.pos)window.__162SelectedPos=s.dataset.pos},{capture:true});
  const wrap=()=>{
    if(typeof window.pickPlayer!=='function'||window.pickPlayer.__overallWrapped)return;
    const original=window.pickPlayer;
    function wrapped(p){
      const pos=window.__162SelectedPos||p.position;
      const result=original(p);
      const slot=document.querySelector('.slot.'+(pos==='1B'?'B1':pos==='2B'?'B2':pos==='3B'?'B3':pos));
      window.__162FinalRoster[pos]={name:p.name,position:pos,overall:overall(p),stats:p.stats||{}};
      return result;
    }
    wrapped.__overallWrapped=true; window.pickPlayer=wrapped;
  };
  const render=()=>{
    const sim=document.getElementById('sim');if(!sim||Object.keys(window.__162FinalRoster).length<9)return;
    if(document.getElementById('final-overalls'))return;
    const order=['P','C','1B','2B','3B','SS','LF','CF','RF'];
    const vals=order.map(p=>window.__162FinalRoster[p]).filter(Boolean); const avg=Math.round(vals.reduce((a,p)=>a+p.overall,0)/vals.length);
    const box=document.createElement('div');box.id='final-overalls';box.innerHTML=`<div style="margin-top:24px;text-align:left"><h3 style="font:900 26px 'Barlow Condensed';margin:0 0 10px">FINAL PLAYER OVERALLS</h3><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">${vals.map(p=>`<div style="background:#101824;border:1px solid #ffffff18;border-radius:8px;padding:9px 10px"><b style="font:800 15px 'Barlow Condensed';display:block">${p.name}</b><span style="color:#8b96a7;font-size:10px">${names[p.position]||p.position}</span><strong style="float:right;color:#ff9418;font:900 22px 'Barlow Condensed'">${p.overall}</strong></div>`).join('')}</div><div style="margin-top:10px;color:#aeb8c6;font-size:12px">LINEUP OVERALL <b style="color:#fff;font-size:16px">${avg}</b></div></div>`;sim.appendChild(box);
  };
  const start=Date.now(); const timer=setInterval(()=>{wrap();if(typeof window.finishDraft==='function'&&Object.keys(window.__162FinalRoster).length>=9){const old=window.finishDraft;if(!old.__overallWrapped){window.finishDraft=function(){const r=old.apply(this,arguments);setTimeout(render,250);return r};window.finishDraft.__overallWrapped=true}} if(Date.now()-start>20000)clearInterval(timer)},100);
  const obs=new MutationObserver(()=>{if(!document.getElementById('sim')?.classList.contains('hidden'))render()});obs.observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});
})();
