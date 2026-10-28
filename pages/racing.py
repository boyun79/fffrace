// 게임 점수를 주행 단위로 변환하는 공통 아케이드 모델입니다.
// 실제 F1 제원이나 실측값이 아니며, 플레이어와 AI에 동일하게 적용합니다.
const PHYSICS_STEP=1/120, PROFILE_SIZE=720;
function vehicleModel(car){
  const t=score('topSpeed',car),g=score('grip',car),d=score('downforce',car),c=score('cornering',car),b=score('braking',car),s=score('stability',car);
  // 부품 평균으로 좁아진 점수 범위에 맞춘 게임용 감도입니다. 저장 점수는 바꾸지 않습니다.
  // 월드 좌표 1단위=1m, 내부 속도=m/s, 차량 저장값과 HUD=km/h입니다.
  const power=Math.max(0,Math.min(1,(score('acceleration',car)-.75)/.25));
  return {maxSpeed:(210+145*Math.max(0,Math.min(1,(t-.45)/.5)))/3.6,drive:12+24*power,mu:1.1+2.8*g,
    aero:.00008+.00022*d,drag:.00007+.00018*d,
    corner:.55+1.05*c,brake:10+27*b,stability:.65+.35*s};
}
// 짧은 기존 트랙을 위한 공통 아케이드 코너 접지 배율입니다. 특정 차량 보정이 아닙니다.
function lateralCapacity(m,v){return 2.4*m.mu*9.81*(1+m.aero*v*v)*m.corner*m.stability}
function brakeCapacity(m,v){return Math.min(m.brake,m.mu*9.81*(1+m.aero*v*v))*m.stability}
function acceleration(m,v,k){
  const used=Math.min(1,v*v*k/Math.max(.1,lateralCapacity(m,v)));
  const traction=m.mu*9.81*Math.sqrt(Math.max(0,1-used*used));
  // 고속에서 구동력이 너무 일찍 사라지지 않게 하고 항력은 한 번만 차감합니다.
  const engine=m.drive*Math.max(.3,1-.55*Math.pow(v/m.maxSpeed,2));
  return Math.min(traction,engine)-m.drag*v*v;
}
function cornerLimit(m,k){
  if(k<1e-6)return m.maxSpeed;
  // 기존 접지력 부등식의 해석해: 반복 이분 탐색 없이 같은 속도 한계를 구합니다.
  const base=lateralCapacity(m,0),denom=k-base*m.aero;
  return Math.max(4,denom<=0?m.maxSpeed:Math.min(m.maxSpeed,Math.sqrt(base/denom)));
}
// 등거리 접선 샘플로 곡률을 구하고 역방향으로 제동 가능한 속도를 전달합니다.
function trackCurvatures(){
  const ds=length/PROFILE_SIZE;
  return Array.from({length:PROFILE_SIZE},(_,i)=>{
    const a=curve.getTangentAt(((i-1+PROFILE_SIZE)%PROFILE_SIZE)/PROFILE_SIZE);
    const b=curve.getTangentAt(((i+1)%PROFILE_SIZE)/PROFILE_SIZE);
    return Math.max(0,Math.min(2,a.angleTo(b)/(2*ds)));
  });
}
// 곡률의 샘플 단위 흔들림을 줄여 속도 목표가 프레임마다 바뀌는 현상을 완화합니다.
function smoothCircular(values,radius=2){
 const n=values.length;
 return values.map((_,i)=>{
  let total=0,weight=0;
  for(let d=-radius;d<=radius;d++){
   const w=radius+1-Math.abs(d);
   total+=values[(i+d+n)%n]*w;weight+=w;
  }
  return total/weight;
 });
}
let trackK=smoothCircular(trackCurvatures(),2);
function makeSpeedProfile(m){
  const ds=length/PROFILE_SIZE;
  const speeds=trackK.map(k=>cornerLimit(m,k));
  // 랩 경계를 포함해 미리 감속합니다. AI 고정 능력 보정은 사용하지 않습니다.
  for(let pass=0;pass<6;pass++)for(let i=PROFILE_SIZE-1;i>=0;i--){
    const next=speeds[(i+1)%PROFILE_SIZE];
    speeds[i]=Math.min(speeds[i],Math.sqrt(next*next+2*brakeCapacity(m,next)*ds));
  }
  return speeds;
}
// 서킷별 1회 생성: 코너 봉우리에서 apex를 정하고 전후에 바깥쪽 경로를 연결합니다.
let racingLine=[],lineK=[],signedK=[],lineDS=[];
function buildRacingLine(){
 const n=PROFILE_SIZE,ds=length/n,signed=trackK.map((k,i)=>{
  const a=frameAt((i-1)/n).v,b=frameAt((i+1)/n).v;
  return Math.sign(a.z*b.x-a.x*b.z)*k;
 });
 signedK=signed;
 racingLine=Array(n).fill(0);const weight=Array(n).fill(0),limit=Math.max(0,roadWidth/2-3.3);
 const peaks=[];
 for(let i=0;i<n;i++)if(trackK[i]>.004&&trackK[i]>=trackK[(i+n-1)%n]&&trackK[i]>trackK[(i+1)%n])peaks.push(i);
 peaks.sort((a,b)=>trackK[b]-trackK[a]);const used=[];
 for(const peak of peaks){
  const span=Math.max(5,Math.min(Math.floor(n/10),Math.round((32+Math.min(35,trackK[peak]*500))/ds)));
  if(used.some(j=>Math.min(Math.abs(j-peak),n-Math.abs(j-peak))<span))continue;
  used.push(peak);const amp=limit*Math.min(.86,.3+trackK[peak]*12),sign=Math.sign(signed[peak]);
  for(let d=-span;d<=span;d++){
   const x=Math.abs(d)/span,w=Math.pow(Math.cos(x*Math.PI/2),2),i=(peak+d+n)%n;
   // apex 안쪽(+), 진입과 탈출 바깥쪽(-), 구간 양끝은 부드럽게 연결합니다.
   racingLine[i]+=sign*amp*Math.cos(x*Math.PI)*w;weight[i]+=w;
  }
 }
 racingLine=racingLine.map((v,i)=>v/Math.max(1,weight[i]));
 // 연속 코너의 연결까지 고려한 경사·굽힘 제한. 샘플 밀도와 무관한 실제 거리 기준입니다.
 const slope=Math.min(.16,limit/25);
 for(let pass=0;pass<4;pass++)for(let i=0;i<n;i++){
  const j=(i+1)%n;racingLine[j]=Math.max(racingLine[i]-slope*ds,Math.min(racingLine[i]+slope*ds,racingLine[j]));
 }
 for(let pass=0;pass<12;pass++)racingLine=racingLine.map((v,i)=>(racingLine[(i+n-1)%n]+2*v+racingLine[(i+1)%n])/4);
 const points=racingLine.map((l,i)=>{const f=frameAt(i/n);return f.p.clone().addScaledVector(f.side,l)});
 lineDS=points.map((p,i)=>p.distanceTo(points[(i+1)%n]));
 lineK=smoothCircular(points.map((b,i)=>{
  const a=points[(i+n-1)%n],c=points[(i+1)%n],u=b.clone().sub(a),v=c.clone().sub(b);
  return u.angleTo(v)/Math.max(.1,(u.length()+v.length)*.5);
 }),2);
}
function lineAt(progress){const x=(((progress%1)+1)%1)*PROFILE_SIZE,i=Math.floor(x),f=x-i;return racingLine[i]*(1-f)+racingLine[(i+1)%PROFILE_SIZE]*f}
function initializePhysics(car){
 if(!racingLine.length)buildRacingLine();
 car.model=vehicleModel(car);
 // 선택한 실제 경로의 곡률과 구간 길이로 차량별 제동 계획을 생성합니다.
 car.speedProfile=lineK.map(k=>cornerLimit(car.model,k));
 for(let pass=0;pass<6;pass++)for(let i=PROFILE_SIZE-1;i>=0;i--){
  const next=car.speedProfile[(i+1)%PROFILE_SIZE];
  car.speedProfile[i]=Math.min(car.speedProfile[i],Math.sqrt(next*next+2*brakeCapacity(car.model,next)*lineDS[i]));
 }
 car.controlK=0;car.lineCap=Infinity;car.lineCapState=Infinity;car.trafficCapState=Infinity;

}

function updateCar(car,dt,endTime,index){
  if(car.finished){
    // 완주 기록은 고정하고 실제 주행 위치만 유지하며 감속 주행합니다.
    const v=car.speed/3.6,desired=Math.min(18,car.trafficCap??18);
    const next=v>desired?Math.max(desired,v-3*dt):Math.min(desired,v+2*dt);
    car.progress+=(v+next)*.5*dt/length;car.speed=next*3.6;return;
  }
  if(!car.model)initializePhysics(car);
  const m=car.model,wrapped=((car.progress%1)+1)%1;
  const sample=wrapped*PROFILE_SIZE,i=Math.floor(sample)%PROFILE_SIZE,f=sample-Math.floor(sample);
  const target=Math.min(car.speedProfile[i]*(1-f)+car.speedProfile[(i+1)%PROFILE_SIZE]*f,car.lineCap??Infinity);
  const v=Math.max(0,Number.isFinite(car.speed)?car.speed/3.6:0);
  let next;
  // 작은 속도 오차 구간에서는 목표 속도를 유지해 브레이크/가속 반복을 막습니다.
  const speedError=v-target;
  if(speedError>0.65)next=Math.max(target,v-brakeCapacity(m,v)*dt);
  else if(speedError< -0.65)next=Math.min(target,Math.max(0,v+acceleration(m,v,Math.max(lineK[i],car.controlK||0))*dt));
  else next=v;
  next=Math.max(0,Math.min(m.maxSpeed,Number.isFinite(next)?next:0));
  if(Number.isFinite(car.trafficCap)){
    const decel=car.emergency?brakeCapacity(m,v):Math.min(brakeCapacity(m,v),5.5);
    next=Math.min(next,Math.max(car.trafficCap,v-decel*dt));
  }
  // 중심선 거리와 실제 횡방향 주행 거리를 구분합니다.
  const factor=Math.max(.6,car.pathFactor||1);
  const distance=(v+next)*.5*dt/factor,remaining=(1-car.progress)*length;
  car.speed=next*3.6;car.top=Math.max(car.top,car.speed);
  car.progress+=distance/length;
  if(car.progress>=1){
    const fraction=distance>0?Math.max(0,Math.min(1,remaining/distance)):1;
    const crossing=endTime-dt+fraction*dt;
    car.progress-=1;car.laps++;
    car.lastLap=crossing-car.lapStart;car.best=Math.min(car.best,car.lastLap);car.lapStart=crossing;
    if(car.laps>=DATA.laps){car.finished=true;car.finishTime=crossing;car.laps=DATA.laps}
  }

}


function changeCircuit(key){
  if(phase!=='preview'||!DATA.circuits[key])return;
  DATA.circuitKey=key;DATA.circuit=DATA.circuits[key];
  trackObjects.forEach(obj=>{scene.remove(obj);obj.traverse(o=>{o.geometry?.dispose();if(o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())}})});
  trackWaypoints=createWaypoints();curve=new THREE.CatmullRomCurve3(trackWaypoints,true,'centripetal');
  curve.arcLengthDivisions=4096;curve.updateArcLengths();length=curve.getLength();roadWidth=Math.max(18,DATA.circuit.width);
  const previous=new Set(scene.children);createTrack();trackObjects=scene.children.filter(o=>!previous.has(o));
  rebuildMap();mapSvg.innerHTML=svg.innerHTML;mapMarkers.length=0;trackK=smoothCircular(trackCurvatures(),2);racingLine=[];lineK=[];signedK=[];lineDS=[];
  player.progress=0;player.model=null;player.speedProfile=null;placeCar(player,0);
  document.querySelector('#trackPanel .previewTitle').textContent=DATA.circuit.name;
  document.querySelectorAll('[data-circuit]').forEach(b=>{const active=b.dataset.circuit===key;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))});
}
// 차체 약 9m × 4.5m의 트랙 좌표상 점유영역. 곡선에서는 방향 차이를 여유 폭에 반영합니다.
function trafficStep(dt){
 // 시간 단계 시작 상태를 공유하여 갱신 순서에 따른 일방적인 밀어넣기를 피합니다.
 const snap=cars.map(c=>({c,s:(c.laps+c.progress)*length,v:Math.max(0,c.speed/3.6),l:c.lateral||0,lv:c.lateralVelocity||0}));
 const ordered=[...snap].sort((a,b)=>b.s-a.s),reservations=[];
 for(const q of ordered){
  const c=q.c,m=c.model;c.trafficCap=Infinity;c.emergency=false;
  const i=Math.floor((((c.progress%1)+1)%1)*PROFILE_SIZE)%PROFILE_SIZE,k=trackK[i];
  const half=2.35,limit=Math.max(0,roadWidth/2-half-.8),width=2*half+.45;
  const gapTo=r=>{let d=r.s-q.s;return ((d+length/2)%length+length)%length-length/2};
  const neighbors=snap.filter(r=>r!==q&&Math.abs(gapTo(r))<100+q.v);
  // 현재·예측 위치와 차선 이동 중 통과하는 공간을 함께 확인합니다.
  const free=target=>{
   const horizon=Math.min(1.4,Math.max(.5,Math.abs(target-q.l)/3));
   const lo=Math.min(q.l,target)-width,hi=Math.max(q.l,target)+width;
   return neighbors.every(r=>{
    const d=gapTo(r),future=d+(r.v-q.v)*horizon;
    const crossing=Math.min(d,future)<12&&Math.max(d,future)>-12;
    const rl=r.l+r.lv*horizon;
    return !crossing||((r.l<lo&&rl<lo)||(r.l>hi&&rl>hi));
   })&&reservations.every(r=>Math.abs(r.s-q.s)>20||Math.abs(r.l-target)>width);
  };
  let ahead=null,gap=Infinity;
  for(const r of neighbors){const d=gapTo(r);if(d>0&&d<gap&&Math.abs(r.l-q.l)<width){ahead=r;gap=d}}
  const preview=Math.max(8,Math.min(35,q.v*.55));
  let target=lineAt(c.progress+preview/length);
  if(c.passTarget){
   const r=snap.find(r=>r.c===c.passTarget);
   c.passAge=(c.passAge||0)+dt;
   if(!r||gapTo(r)<-14||gapTo(r)>95||c.passAge>9){c.passTarget=null;c.passAge=0}
   else target=c.targetLane;
