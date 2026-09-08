"""Runtime compatibility and gameplay patch for the 162-0 Render service."""
from pathlib import Path
import builtins
import math, random
try:
    from pydantic import BaseModel
    builtins.BaseModel = BaseModel
except Exception:
    pass
p=Path(__file__).with_name('server.py')
if p.exists():
    s=p.read_text(encoding='utf-8')
    s=s.replace("ERAS=['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s','2020s']; ERA_YEARS={e:int(e[:4])+5 for e in ERAS}", "ERAS=['1960s','1970s','1980s','1990s','2000s','2010s','2020s']; ERA_YEARS={e:int(e[:4])+5 for e in ERAS}")
    s=s.replace('Query(60,ge=20,le=70)', 'Query(100,ge=20,le=100)')
    s=s.replace('pool=hitters[:45]+pitchers[:25]', 'pool=hitters[:75]+pitchers[:25]')
    s=s.replace('pool=pool[:max(20,min(int(limit),70))]', 'pool=pool[:max(20,min(int(limit),100))]')
    s=s.replace("'players':pool[:10]", "'players':pool[:60]")
    s=s.replace("'version':'3.1'", "'version':'4.0'")
    p.write_text(s,encoding='utf-8')

try:
    import server
    def accurate_sim(roster):
        vals=list(roster.values())
        if not vals:
            games=[1 if random.random()<.5 else 0 for _ in range(162)]
            return sum(games),162-sum(games),games,81.0
        def ov(v):
            try: return max(50.0,min(99.0,float(v.get('rating',v.get('overall',88)))))
            except Exception: return 88.0
        bypos={p:v for p,v in roster.items()}
        offense=sum(ov(v) for p,v in bypos.items() if p!='P')/8.0
        pitching=ov(bypos.get('P',{})); catcher=ov(bypos.get('C',{}))
        middle=(ov(bypos.get('SS',{}))+ov(bypos.get('2B',{})))/2
        corners=(ov(bypos.get('1B',{}))+ov(bypos.get('3B',{})))/2
        outfield=(ov(bypos.get('LF',{}))+ov(bypos.get('CF',{}))+ov(bypos.get('RF',{})))/3
        defense=.35*offense+.20*catcher+.20*middle+.15*corners+.10*outfield
        strength=.45*offense+.35*pitching+.20*defense
        strength=max(55,min(99,strength))
        expected_p=.18+.64*(1/(1+math.exp(-(strength-88.0)/4.8)))
        wins=0; games=[]
        for g in range(162):
            fatigue=-.010 if g>=145 else (-.005 if g>=120 else 0)
            schedule=(.010 if g%4 in (0,1) else -.004)
            game_p=max(.10,min(.90,expected_p+fatigue+schedule+random.gauss(0,.009)))
            w=1 if random.random()<game_p else 0; games.append(w); wins+=w
        return wins,162-wins,games,round(strength,1)
    server.sim=accurate_sim

    from fastapi.responses import Response
    script_path=Path(__file__).with_name('rating-enhancements.js')
    if script_path.exists():
        script=script_path.read_text(encoding='utf-8')
        @server.app.middleware('http')
        async def inject_rating_script(request, call_next):
            response=await call_next(request)
            if 'text/html' not in response.headers.get('content-type','') or not hasattr(response,'body_iterator'):
                return response
            body=b''.join([chunk async for chunk in response.body_iterator])
            tag=("<script>"+script+"</script>").encode('utf-8')
            body=body.replace(b'</body>',tag+b'</body>',1) if b'</body>' in body else body+tag
            headers=dict(response.headers); headers.pop('content-length',None)
            return Response(content=body,status_code=response.status_code,headers=headers,media_type='text/html')
except Exception:
    pass
