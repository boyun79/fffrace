"""F1 Physics Garage - 3D 자동 주행 시뮬레이션

이 파일만 pages/racing.py에 넣습니다. main.py는 수정하지 않습니다.
"""
import html
import json
from copy import deepcopy
import streamlit as st
import streamlit.components.v1 as components

CAR_CONFIG_KEY = "my_car_config"
CAR_PERFORMANCE_KEY = "my_car_performance"
GARAGE_FALLBACK_KEY = "selections"
TOTAL_LAPS = 3
METRICS = ["다운포스", "최고속도", "코너링", "그립", "제동", "안정성"]


def get_part_scores():
    """Garage와 동일한 옵션 점수입니다. 저장된 성능이 없을 때만 사용합니다."""
    return {
        "front_wing":{"low":[48,94,57,61,60,62],"balanced":[72,77,76,72,67,76],"high":[94,55,92,79,72,84]},
        "rear_wing":{"low":[45,96,54,59,58,56],"balanced":[73,76,76,70,64,78],"high":[96,51,93,77,69,94]},
        "tyres":{"soft":[66,80,92,98,91,71],"medium":[63,81,80,82,82,82],"hard":[60,82,68,70,73,89]},
        "brakes":{"race":[62,78,78,76,98,78],"balanced":[61,80,76,74,84,88],"light":[59,85,75,72,75,72]},
        "suspension":{"stiff":[73,80,91,80,77,67],"balanced":[68,81,82,82,80,88],"soft":[62,78,72,88,83,90]},
        "floor":{"venturi":[98,72,94,80,67,82],"balanced":[81,80,83,75,66,87],"light":[60,89,68,67,62,69]},
        "diffuser":{"large":[93,67,90,76,65,87],"balanced":[77,80,79,71,64,83],"compact":[55,91,63,61,61,68]},
        "engine":{"power":[62,99,82,72,62,70],"balanced":[62,88,80,72,64,87],"efficient":[60,82,79,72,65,92]},
        "ers":{"attack":[60,97,82,71,65,70],"balanced":[61,88,80,71,68,86],"recovery":[60,80,76,70,78,91]},
    }


def load_my_car():
    """Garage에서 만든 파츠와 성능을 그대로 읽습니다."""
    config=st.session_state.get(CAR_CONFIG_KEY) or st.session_state.get(GARAGE_FALLBACK_KEY)
    if not isinstance(config,dict): return None,None
    config=deepcopy(config)
    performance=st.session_state.get(CAR_PERFORMANCE_KEY)
    if not isinstance(performance,dict) or not all(k in performance for k in METRICS):
        performance=calculate_performance(config)
    return config,performance


def calculate_performance(config):
    """Garage 성능 저장값이 없을 때 파츠 평균을 계산합니다."""
    data=get_part_scores(); totals=[0]*6; count=0
    for part,choice in config.items():
        if part in data and choice in data[part]:
            totals=[a+b for a,b in zip(totals,data[part][choice])]; count+=1
    return {name:round(value/count) for name,value in zip(METRICS,totals)} if count else None


GARAGE_VISUAL_OPTIONS = {'front_wing': {'part': 'frontWing', 'options': {'low': {'color': '#27d6ff', 'shape': 0.82, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'high': {'color': '#ff3158', 'shape': 1.18, 'variant': 2}}}, 'rear_wing': {'part': 'rearWing', 'options': {'low': {'color': '#27d6ff', 'shape': 0.78, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'high': {'color': '#ff3158', 'shape': 1.25, 'variant': 2}}}, 'tyres': {'part': 'tyres', 'options': {'soft': {'color': '#ed2939', 'shape': 1.0, 'variant': 0}, 'medium': {'color': '#ffd326', 'shape': 1.0, 'variant': 1}, 'hard': {'color': '#f4f5f6', 'shape': 1.0, 'variant': 2}}}, 'brakes': {'part': 'brakes', 'options': {'race': {'color': '#ff5038', 'shape': 1.0, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'light': {'color': '#27d6ff', 'shape': 1.0, 'variant': 2}}}, 'suspension': {'part': 'suspension', 'options': {'stiff': {'color': '#ff3158', 'shape': 1.0, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'soft': {'color': '#27d6ff', 'shape': 1.0, 'variant': 2}}}, 'floor': {'part': 'floor', 'options': {'venturi': {'color': '#9a62ff', 'shape': 1.0, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'light': {'color': '#27d6ff', 'shape': 1.0, 'variant': 2}}}, 'diffuser': {'part': 'diffuser', 'options': {'large': {'color': '#9a62ff', 'shape': 1.2, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'compact': {'color': '#27d6ff', 'shape': 0.78, 'variant': 2}}}, 'engine': {'part': 'engine', 'options': {'power': {'color': '#ff3158', 'shape': 1.0, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'efficient': {'color': '#27d6ff', 'shape': 1.0, 'variant': 2}}}, 'ers': {'part': 'ers', 'options': {'attack': {'color': '#32f59b', 'shape': 1.0, 'variant': 0}, 'balanced': {'color': '#ffb21a', 'shape': 1.0, 'variant': 1}, 'recovery': {'color': '#27d6ff', 'shape': 1.0, 'variant': 2}}}}

def prepare_car_data(config,performance):
    """Garage 이름을 Three.js 생성기가 사용하는 이름으로 한 번만 변환합니다."""
    appearance = {part["part"]: part["options"].get(config.get(key), next(iter(part["options"].values())))
                  for key, part in GARAGE_VISUAL_OPTIONS.items()}
    return {"appearance":appearance,
        "performance":{"downforce":performance["다운포스"],"topSpeed":performance["최고속도"],
        "cornering":performance["코너링"],"grip":performance["그립"],"braking":performance["제동"],
        "stability":performance["안정성"]},"config":config}


def get_f1_car_builder_javascript():
    """차체·윙·타이어·서스펜션·바닥 등이 모두 실제 3D Mesh인 기존 생성기를 재사용합니다."""
    return BUILDER_JS


def apply_page_style():
    """사이드바는 건드리지 않고 Racing 본문만 Garage 분위기로 꾸밉니다."""
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@500;700&family=Noto+Sans+KR:wght@400;700&display=swap');
    .stApp{background:radial-gradient(circle at 50% 12%,#202b37,#090c11 48%,#05070a);color:#eff5fa}.block-container{max-width:1450px;padding-top:1rem}
    .head{border-top:3px solid #ff3158;border-bottom:1px solid #2a3542;padding:12px 16px;background:#0c1118;display:flex;justify-content:space-between}.logo{font:700 25px Oxanium}.logo b{color:#ff3158}.step{font:11px Oxanium;color:#8492a0;letter-spacing:2px}
    .card{background:#0d131b;border:1px solid #2a3542;padding:14px}.title{font:700 12px Oxanium;letter-spacing:2px;color:#9aa8b6;border-bottom:1px solid #293542;padding-bottom:9px;margin-bottom:10px}.chips span{display:inline-block;padding:4px 7px;margin:3px;border:1px solid #354353;color:#9eacba;font-size:10px}.bar-row{margin:8px 0}.bar-top{display:flex;justify-content:space-between;font:700 11px Oxanium}.bar{height:9px;background:#232c36;margin-top:5px;transform:skewX(-12deg);overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,#27d6ff,#8065ff)}
    div[data-testid='stButton'] button{width:100%!important;min-height:58px!important;background:#e51d45!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border:1px solid #ff6681!important;font:700 16px Oxanium!important}div[data-testid='stButton'] button *{color:#fff!important;-webkit-text-fill-color:#fff!important}.empty{max-width:650px;margin:90px auto;padding:30px;text-align:center;background:#0e141c;border-top:3px solid #ff3158}
    </style>""",unsafe_allow_html=True)


BUILDER_JS = "\nfunction createF1Car(color, cfg) {\n    const car=new THREE.Group(), partGroups={};\n    const mat=(color,metal=.45,rough=.32)=>new THREE.MeshStandardMaterial({color,metalness:metal,roughness:rough});\n    function group(name){const g=new THREE.Group();g.userData.part=name;partGroups[name]=g;car.add(g);return g}\n    function mesh(g,geo,material,pos=[0,0,0],rot=[0,0,0],scale=[1,1,1]){const m=new THREE.Mesh(geo,material);m.position.set(...pos);m.rotation.set(...rot);m.scale.set(...scale);m.castShadow=true;m.receiveShadow=true;m.userData.part=g.userData.part;g.add(m);return m}\n    function capsule(length,radius){return new THREE.CapsuleGeometry(radius,length,8,20)}\n    // 두 지점 사이에 실제 두께가 있는 서스펜션 암을 만드는 도우미입니다.\n    function rodBetween(g,a,b,radius,material){const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),mid=start.clone().add(end).multiplyScalar(.5),length=start.distanceTo(end);const rod=mesh(g,new THREE.CylinderGeometry(radius,radius,length,12),material,[mid.x,mid.y,mid.z]);rod.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),end.clone().sub(start).normalize());return rod}\n    // 매끈한 곡면 차체: 길쭉한 캡슐과 유선형 노즈를 겹쳐 실제 포뮬러카 실루엣을 만듭니다.\n    const body=group('body'), red=mat(color,.72,.24);mesh(body,capsule(3.1,.65),red,[0,.05,0],[Math.PI/2,0,0],[1,1,1]);mesh(body,new THREE.ConeGeometry(.62,4.5,32),red,[0,-.08,3.35],[Math.PI/2,0,0],[1,.55,1]);\n    mesh(body,new THREE.SphereGeometry(1.0,32,18),red,[0,.05,-1.35],[0,0,0],[1.35,.78,1.75]);\n    // 콕핏과 Halo\n    const cockpit=group('cockpit');mesh(cockpit,new THREE.SphereGeometry(.64,28,16,0,Math.PI*2,0,Math.PI*.62),mat(0x111820,.15,.16),[0,.65,-.25],[0,0,0],[1,.62,1.45]);\n    const haloMat=mat(0x242c35,.75,.2);mesh(cockpit,new THREE.TorusGeometry(.62,.055,10,36,Math.PI*1.25),haloMat,[0,1.08,-.05],[Math.PI/2,0,.39]);mesh(cockpit,new THREE.CylinderGeometry(.06,.06,.72,12),haloMat,[0,.82,.35],[0,0,0]);\n    // 사이드포드: 앞은 넓고 뒤로 갈수록 좁아지는 곡면\n    const side=group('sidepods');[-1,1].forEach(s=>{mesh(side,capsule(1.35,.52),red,[s*1.02,-.05,-.65],[Math.PI/2,0,0],[1,.72,1.25]);mesh(side,new THREE.ConeGeometry(.48,2.2,24),red,[s*.94,-.08,-2.0],[-Math.PI/2,0,0],[.75,1,.9])});\n    // 타이어는 실제 회전축을 가진 두꺼운 Torus 3D 메시입니다.\n    const tyres=group('tyres'), tv=cfg.tyres.variant, tyreMat=mat(0x08090b,.05,.58+tv*.1), stripe=mat(cfg.tyres.color,.15,.38);[[-1.55,1.95,.56], [1.55,1.95,.56],[-1.72,-2.15,.72],[1.72,-2.15,.72]].forEach(p=>{const [x,z,r]=p;mesh(tyres,new THREE.TorusGeometry(r,r*(.43-tv*.045),18+tv*5,42),tyreMat,[x,-.35,z],[0,Math.PI/2,0]);mesh(tyres,new THREE.TorusGeometry(r*.99,.035,8,48),stripe,[x,-.35,z],[0,Math.PI/2,0])});\n    // 프론트 윙: 날개 단면을 가진 여러 곡선형 엘리먼트\n    const fw=group('frontWing'), fwM=mat(cfg.frontWing.color,.65,.22), f=cfg.frontWing.shape;Array.from({length:2+cfg.frontWing.variant},(_,i)=>-.18+i*.22).forEach((y,i)=>mesh(fw,new THREE.CapsuleGeometry(.11,3.2*f,6,20),fwM,[0,-.58+y,3.62-i*.25],[0,0,Math.PI/2],[1,1,1]));[-1,1].forEach(s=>mesh(fw,new THREE.ExtrudeGeometry(new THREE.Shape().moveTo(0,0).lineTo(.44,.12).lineTo(.28,.65).lineTo(0,.52),{depth:.06,bevelEnabled:true,bevelSize:.025,bevelThickness:.025}),fwM,[s*1.75*f,-.88,3.35],[0,s<0?0:Math.PI,0]));\n    // 리어 윙: 선택에 따라 폭과 높이가 실제로 변합니다.\n    const rw=group('rearWing'), rwM=mat(cfg.rearWing.color,.68,.2), r=cfg.rearWing.shape;mesh(rw,new THREE.CapsuleGeometry(.16,2.55*r,6,20),rwM,[0,1.05,-3.24],[0,0,Math.PI/2]);Array.from({length:1+cfg.rearWing.variant},(_,i)=>mesh(rw,new THREE.CapsuleGeometry(.09,2.35*r,6,20),rwM,[0,.72-i*.22,-3.0+i*.08],[0,0,Math.PI/2]));[-1,1].forEach(s=>mesh(rw,new THREE.CylinderGeometry(.045,.06,1.3,10),rwM,[s*.92*r,.35,-3.05],[0,0,0]));\n    const floor=group('floor');const floorShape=new THREE.Shape().moveTo(-1.25,-2.7).lineTo(-1.25,1.4).lineTo(-.8,2.8).lineTo(.8,2.8).lineTo(1.25,1.4).lineTo(1.25,-2.7).lineTo(-1.25,-2.7);mesh(floor,new THREE.ExtrudeGeometry(floorShape,{depth:.09,bevelEnabled:true,bevelSize:.04,bevelThickness:.03}),mat(cfg.floor.color,.7,.25),[0,-.92,0],[Math.PI/2,0,0]);\n    const diffuser=group('diffuser'), dm=mat(cfg.diffuser.color,.72,.22);[-.72,-.24,.24,.72].forEach(x=>mesh(diffuser,new THREE.BoxGeometry(.055,.7,1.35*cfg.diffuser.shape),dm,[x,-.62,-3.08],[.38,0,0]));\n    const brakes=group('brakes'), bv=cfg.brakes.variant;[[-1.55,1.95],[1.55,1.95],[-1.72,-2.15],[1.72,-2.15]].forEach(p=>mesh(brakes,new THREE.CylinderGeometry(.38-bv*.055,.38-bv*.055,.07,24+bv*8),mat(cfg.brakes.color,.8,.28),[p[0],-.35,p[1]],[0,0,Math.PI/2]));\n    // 앞·뒤 바퀴 허브와 차체를 위/아래 위시본 및 푸시로드로 연결합니다.\n    const suspension=group('suspension'), sv=cfg.suspension.variant, suspensionMat=mat(cfg.suspension.color,.82,.18), armRadius=.055-sv*.007;\n    [[1.95,1.55],[-2.15,1.72]].forEach(([z,wheelX])=>[-1,1].forEach(side=>{\n      const hub=[side*wheelX,-.34,z], innerX=side*.62;\n      rodBetween(suspension,[innerX,-.28,z-.48],hub,armRadius,suspensionMat);\n      rodBetween(suspension,[innerX,-.28,z+.48],hub,armRadius,suspensionMat);\n      rodBetween(suspension,[innerX,.25,z-.30],hub,armRadius*.9,suspensionMat);\n      rodBetween(suspension,[innerX,.25,z+.30],hub,armRadius*.9,suspensionMat);\n      rodBetween(suspension,[side*.48,.48,z],hub,armRadius*.82,suspensionMat);\n      mesh(suspension,new THREE.SphereGeometry(.12,16,10),suspensionMat,hub);\n    }));\n    const engine=group('engine'), ev=cfg.engine.variant;mesh(engine,new THREE.CapsuleGeometry(.50-ev*.06,1.45-ev*.12,8,18),mat(cfg.engine.color,.65,.24),[0,.22,-1.75],[Math.PI/2,0,0]);\n    const ers=group('ers'), erv=cfg.ers.variant;mesh(ers,new THREE.TorusGeometry(.30-erv*.035,.075-erv*.01,10,28+erv*8),mat(cfg.ers.color,.5,.15),[0,.68,-1.38],[Math.PI/2,0,0]);\n\n  return car;\n}\n"


def build_simulation_html(car_data):
    """준비 화면부터 결과까지 하나의 iframe에서 실행하여 rerun에 따른 중단을 방지합니다."""
    data = {"car": car_data, "laps": TOTAL_LAPS}
    # </script> 삽입을 막고 기존 Garage 값의 JSON 구조는 그대로 유지합니다.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    # Garage의 .perf 카드 구조를 재사용합니다. 변화량은 저장되지 않으므로 표시하지 않습니다.
    metrics = "".join(
        f"<div class='perf'><div class='perf-top'><div class='perf-name'>{label}</div>"
        f"<div class='perf-num'>{html.escape(str(car_data['performance'][key]))}</div></div>"
        f"<div class='track'><div class='fill' style='width:{max(0, min(100, float(car_data['performance'][key]))):.0f}%'></div></div></div>"
        for label, key in zip(
            ("DOWNFORCE", "TOP SPEED", "CORNERING", "GRIP", "BRAKING", "STABILITY"),
            ("downforce", "topSpeed", "cornering", "grip", "braking", "stability"),
        )
    )
    return (SIMULATION_HTML.replace("__DATA__", payload)
            .replace("__CAR_BUILDER__", BUILDER_JS)
            .replace("__PERFORMANCE__", metrics))


def main():
    st.set_page_config(page_title="F1 3D Auto Simulation", page_icon="🏁",
                       layout="wide", initial_sidebar_state="expanded")
    apply_page_style()
    config, performance = load_my_car()
    if not config or not performance:
        st.warning("Garage에서 차량을 먼저 설계해 주세요.")
        return
    car_data = prepare_car_data(config, performance)
    st.markdown("<div class='head'><div class='logo'>VIRTUAL <b>RACE</b></div>"
                "<div class='step'>MY 3D F1 CAR · TRACK TEST CIRCUIT</div></div>",
                unsafe_allow_html=True)
    # 성능도 같은 iframe 안에 배치하여 준비/주행 전환 시 함께 표시·숨김 처리합니다.
    components.html(build_simulation_html(car_data), height=560, scrolling=False)


SIMULATION_HTML = r'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@500;700&display=swap');
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#071019;color:#fff;font-family:Arial,sans-serif} [hidden]{display:none!important}
#game{position:relative;width:100%;height:100%;overflow:hidden;background:#071019}
canvas{display:block;width:100%;height:100%}.hud{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.panel{position:absolute;top:12px;max-width:42%;padding:8px 12px;background:#071019dc;border:1px solid #354758;border-top:2px solid #27d6ff;font-size:11px;letter-spacing:1px}
.panel b{font-size:clamp(16px,2.8vw,26px);white-space:nowrap}.pos{left:12px}.lap{right:12px;text-align:right}
.speed{position:absolute;bottom:15px;left:50%;transform:translateX(-50%);white-space:nowrap;background:#071019df;border:1px solid #354758;padding:8px 18px;font-size:clamp(14px,2.5vw,24px)}
#overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;pointer-events:none;text-align:center;text-shadow:0 3px 10px #000}
#overlay h1{margin:0;font-size:clamp(35px,8vw,88px);color:#ff3158}#overlay p{margin:6px;font-size:clamp(14px,2vw,22px)}
#start{pointer-events:auto;cursor:pointer;margin:0 0 13px;padding:14px 27px;border:1px solid #ff6681;background:#e51d45;color:white;font-weight:900;font-size:17px}
#pause{pointer-events:auto;position:absolute;right:12px;bottom:14px;cursor:pointer;background:#091725;color:#fff;border:1px solid #27d6ff;padding:8px 11px;font-weight:bold}#previewPanels{position:absolute;top:0;left:0;right:0;height:480px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;padding:8px;pointer-events:none}
.previewTitle{height:38px;padding:11px 13px;background:#101b27;color:#ccd6e2;font-weight:bold;font-size:13px;letter-spacing:2px}
#trackPanel,#carPanel{position:relative;height:100%;min-width:0;border:1px solid #364555;background:#0d1821}#carPanel{background:transparent;pointer-events:auto;touch-action:none;cursor:grab}#carPanel:active{cursor:grabbing}#trackSvg{width:100%;height:calc(100% - 38px);display:block;background:#101c22}
#performancePanel{height:100%;min-width:0;background:#0b1520;border:1px solid #364555;padding:0 13px;overflow:auto}
.perf{position:relative;padding:11px 10px;margin:8px 0;background:#0d131a;border:1px solid #26313d;border-radius:3px}.perf-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}.perf-name{font:700 13px 'Oxanium';color:#fff;letter-spacing:.5px}.perf-num{font:700 17px 'Oxanium';white-space:nowrap}.track{height:13px;background:#222b35;margin-top:9px;overflow:hidden;border:1px solid #33404d;transform:skewX(-12deg)}.fill{height:100%;background:linear-gradient(90deg,#27d6ff,#7b61ff);box-shadow:0 0 12px #27d6ff77;transition:width .35s ease}.perf:nth-of-type(even) .fill{background:linear-gradient(90deg,#20d7c7,#27d6ff)}
@media(max-width:780px){.previewTitle{font-size:10px;letter-spacing:0;padding:12px 5px}.metric{font-size:10px;padding:9px 0}#previewPanels{gap:4px;padding:4px}}
#raceMap{position:absolute;top:8px;left:50%;transform:translateX(-50%);width:min(178px,27vw);height:206px;padding:5px 7px;background:#091522ed;border:1px solid #365161;pointer-events:none;text-align:center;color:#b9d6e4;font:700 11px Oxanium,Arial,sans-serif;z-index:3}#raceMap svg{display:block;width:100%;height:174px}#raceMap .legend{font-size:9px;color:#b9cbd5;white-space:nowrap}@media(max-width:580px){#raceMap{width:116px;height:158px}#raceMap svg{height:125px}#raceMap .legend{font-size:7px}}
#back{pointer-events:auto;position:absolute;right:115px;bottom:14px;cursor:pointer;background:#091725;color:#fff;border:1px solid #27d6ff;padding:8px 11px;font-weight:bold}
#result{display:none;background:#08111eea;border:1px solid #ff3158;padding:20px;line-height:1.8;min-width:min(340px,85vw)}
#result strong{color:#ff3158;font-size:23px}#error{position:absolute;left:12px;bottom:10px;color:#ff7186;background:#08111e}
</style><script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.164.1/build/three.module.js"}}</script>
</head><body><div id="game"><div id="previewPanels"><div id="trackPanel"><div class="previewTitle">TRACK TEST CIRCUIT</div><svg id="trackSvg" viewBox="0 0 320 390" preserveAspectRatio="xMidYMid meet"></svg></div><div id="carPanel"><div class="previewTitle">MY 3D F1 CAR</div></div><div id="performancePanel"><div class="previewTitle">CAR PERFORMANCE</div>__PERFORMANCE__</div></div><div class="hud" id="hud" hidden><div class="panel pos">POSITION<br><b id="position">1 / 5</b></div><div class="panel lap">LAP<br><b id="lap">1 / 3</b></div><button id="pause" hidden>⏸ PAUSE</button><div class="speed">SPEED <b id="speed">0</b> km/h</div></div><div id="raceMap" hidden>RACE MAP<svg id="mapSvg" viewBox="0 0 320 390" preserveAspectRatio="xMidYMid meet"></svg><div class="legend">● MY CAR &nbsp; ○ AI CARS</div></div><button id="back" hidden>↩ PREPARATION</button>
<div id="overlay"><p id="message"></p><h1 id="count"></h1><button id="start">SIMULATION START</button><div id="result"></div></div><div id="error"></div></div>
<script type="module">
import * as THREE from 'three';
const DATA=__DATA__,root=document.getElementById('game');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x08121a);
const camera=new THREE.PerspectiveCamera(52,1,.1,500);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;root.insertBefore(renderer.domElement,root.firstChild);
scene.add(new THREE.HemisphereLight(0xd2e8ff,0x13231b,2.1));
const sun=new THREE.DirectionalLight(0xffffff,2.9);sun.position.set(-25,65,20);sun.castShadow=true;scene.add(sun);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(260,260),new THREE.MeshStandardMaterial({color:0x10201e,roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-.08;ground.receiveShadow=true;scene.add(ground);
__CAR_BUILDER__
// 하나의 폐쇄형 중심선이 미리보기·노면·주행 모두에 사용됩니다.
function createWaypoints(){return [[-48,0,25],[-42,0,-23],[-30,0,-39],[12,0,-42],[42,0,-29],[50,0,-8],[42,0,15],[20,0,26],[37,0,37],[11,0,43],[-12,0,27],[-34,0,35]].map(p=>new THREE.Vector3(...p))}
const trackWaypoints=createWaypoints();
const curve=new THREE.CatmullRomCurve3(trackWaypoints,true,'catmullrom',.35);
const roadWidth=12, length=curve.getLength();
function frameAt(t){const p=curve.getPointAt((t+1)%1),v=curve.getTangentAt((t+1)%1).normalize();return {p,v,side:new THREE.Vector3(v.z,0,-v.x)}}
function createTrack(){
  const N=500,vertices=[],indices=[],roadMat=new THREE.MeshStandardMaterial({color:0x282e34,roughness:.94,side:THREE.DoubleSide});
  for(let i=0;i<=N;i++){let {p,side}=frameAt(i/N);for(let s of [-1,1]){let q=p.clone().addScaledVector(side,s*roadWidth/2);vertices.push(q.x,.012,q.z)}}
  for(let i=0;i<N;i++){let a=i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2)}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geo.setIndex(indices);geo.computeVertexNormals();
  const road=new THREE.Mesh(geo,roadMat);road.receiveShadow=true;scene.add(road);
  // 커브·중앙선·스타트 라인은 노면과 같은 곡선에서 생성합니다.
  for(let i=0;i<N;i+=7){let t=i/N,{p,v,side}=frameAt(t),angle=Math.atan2(-v.x,-v.z);
    for(let sign of [-1,1]){let curb=new THREE.Mesh(new THREE.BoxGeometry(.85,.09,2.0),new THREE.MeshStandardMaterial({color:(i/7)%2?0xffffff:0xe7274e}));
      curb.position.copy(p).addScaledVector(side,sign*roadWidth/2);curb.position.y=.065;curb.rotation.y=angle;scene.add(curb)}
    if(i%21===0){let mark=new THREE.Mesh(new THREE.BoxGeometry(.15,.025,2.3),new THREE.MeshBasicMaterial({color:0xb7c1c4}));mark.position.copy(p);mark.position.y=.035;mark.rotation.y=angle;scene.add(mark)}
  }
  const start=frameAt(0),line=new THREE.Group();
  for(let j=0;j<12;j++){let box=new THREE.Mesh(new THREE.BoxGeometry(roadWidth/12,.018,1.4),new THREE.MeshBasicMaterial({color:j%2?0xffffff:0x16191d,side:THREE.DoubleSide}));box.position.copy(start.p).addScaledVector(start.side,(j-5.5)*roadWidth/12);box.position.y=.05;box.rotation.y=Math.atan2(-start.v.x,-start.v.z);line.add(box)}
  scene.add(line);
}
createTrack();
// 준비 화면의 두 뷰는 동일한 트랙 객체와 동일한 Garage 차량 객체를 번갈아 렌더링합니다.
const trackObjects=scene.children.filter(obj=>!obj.isLight && obj!==ground);
// 주행에 사용하는 동일한 curve를 위에서 본 2D SVG 중심선으로 투영합니다.
const svg=document.getElementById('trackSvg');
const points=Array.from({length:201},(_,i)=>curve.getPointAt(i/200));
const xs=points.map(p=>p.x),zs=points.map(p=>p.z);
const minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs);
const scale=Math.min(264/(maxX-minX),310/(maxZ-minZ));
const xy=p=>[160+(p.x-(minX+maxX)/2)*scale,195+(p.z-(minZ+maxZ)/2)*scale];
const path=points.map((p,i)=>`${i?'L':'M'}${xy(p)[0].toFixed(1)} ${xy(p)[1].toFixed(1)}`).join(' ')+' Z';
const start=frameAt(0),[sx,sy]=xy(start.p),[ex,ey]=xy(start.p.clone().addScaledVector(start.side,roadWidth/2));
const dx=ex-sx,dy=ey-sy;
svg.innerHTML=`<path d="${path}" fill="none" stroke="#586778" stroke-width="${(roadWidth*scale+4).toFixed(1)}" stroke-linejoin="round"/><path d="${path}" fill="none" stroke="#303740" stroke-width="${(roadWidth*scale).toFixed(1)}" stroke-linejoin="round"/><path d="${path}" fill="none" stroke="#abb5c0" stroke-width="1" stroke-dasharray="5 8"/><line x1="${sx-dx}" y1="${sy-dy}" x2="${sx+dx}" y2="${sy+dy}" stroke="white" stroke-width="5" stroke-dasharray="4 3"/>`;
// 준비 화면 전용 Orbit 스타일 드래그/휠. 주행 카메라 함수는 변경하지 않습니다.
const carPanel=document.getElementById('carPanel');
let orbitYaw=.65,orbitPitch=.34,orbitRadius=16,dragPointer=null,lastX=0,lastY=0;
carPanel.addEventListener('pointerdown',e=>{if(phase!=='preview')return;dragPointer=e.pointerId;lastX=e.clientX;lastY=e.clientY;carPanel.setPointerCapture(e.pointerId)});
carPanel.addEventListener('pointermove',e=>{if(phase!=='preview'||e.pointerId!==dragPointer)return;orbitYaw+=(e.clientX-lastX)*.008;orbitPitch=Math.max(-.25,Math.min(1.1,orbitPitch+(e.clientY-lastY)*.006));lastX=e.clientX;lastY=e.clientY});
carPanel.addEventListener('pointerup',e=>{if(e.pointerId===dragPointer)dragPointer=null});
carPanel.addEventListener('pointercancel',()=>{dragPointer=null});
carPanel.addEventListener('wheel',e=>{if(phase!=='preview')return;e.preventDefault();orbitRadius=Math.max(11,Math.min(25,orbitRadius*Math.exp(e.deltaY*.001)))},{passive:false});
function score(name){let n=Number(DATA.car.performance[name]);return Number.isFinite(n)?Math.max(0,Math.min(1,n/100)):.5}
function createPlayerCar(){let mesh=createF1Car(0xff1748,DATA.car.appearance);scene.add(mesh);return {mesh,progress:0,laps:0,speed:0,finished:false,base:1,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity}}
function createAICars(){return [.97,1.01,.95,1.02].map((base,i)=>{let mesh=createF1Car([0x24bbfa,0xfcc935,0x8de76b,0xb277fa][i],DATA.car.appearance);scene.add(mesh);return {mesh,progress:0,laps:0,speed:0,finished:false,base,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity}})}
const player=createPlayerCar(),ais=[];let cars=[player];
// 미니맵은 준비 화면과 같은 2D 경로를 쓰고 실제 차량 Mesh 위치만 투영합니다.
const mapSvg=document.getElementById('mapSvg'),raceMap=document.getElementById('raceMap');
mapSvg.innerHTML=svg.innerHTML;
const mapMarkers=[];
function updateMinimap(){
  cars.forEach((car,i)=>{
    if(!mapMarkers[i]){
      const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');
      dot.setAttribute('r',i===0?'8':'6');dot.setAttribute('fill',i===0?'#27d6ff':['#24bbfa','#fcc935','#8de76b','#b277fa'][i-1]);
      dot.setAttribute('stroke','#071019');dot.setAttribute('stroke-width','3');
      mapSvg.appendChild(dot);mapMarkers[i]=dot;
    }
    const [x,y]=xy(car.mesh.position);
    mapMarkers[i].setAttribute('cx',x);mapMarkers[i].setAttribute('cy',y);
  });
  mapMarkers.slice(cars.length).forEach(dot=>dot.remove());mapMarkers.length=cars.length;
}

// 차량은 출발선 근처 5열 그리드에 놓되, 선수차는 정확히 출발선 위에 둡니다.
function placeCar(car,index){const f=frameAt(car.progress),offset=index===0?0:(index%2? -2.2:2.2);car.mesh.position.copy(f.p).addScaledVector(f.side,offset);car.mesh.position.y=1.20;car.mesh.rotation.y=Math.atan2(-f.v.x,-f.v.z)+Math.PI}
cars.forEach((car,i)=>{car.progress=i===0?0:1-i*.009;placeCar(car,i)});
// 랩 완주 전 코너 반경을 미리 읽어 자연스럽게 감속하고 탈출할 때 가속합니다.
function cornerSeverity(t){let a=curve.getTangentAt((t+1+.012)%1),b=curve.getTangentAt((t+1+.035)%1);return Math.min(1,a.angleTo(b)*5.0)}
function updateCar(car,dt,elapsed,index){if(car.finished)return;
  const isPlayer=index===0,turn=cornerSeverity(car.progress),playerTop=235+score('topSpeed')*95,top=isPlayer?playerTop:playerTop*car.base;
  const playerCorner=.48+.22*score('cornering')+.13*score('downforce')+.10*score('grip');
  const corner=isPlayer?playerCorner:Math.min(.94,playerCorner+.025);
  const target=top*(1-turn*(1-corner));
  const playerBrake=2.1+score('braking')*5,playerAccel=1.1+score('grip')*1.4;
  const brake=isPlayer?playerBrake:playerBrake,accel=isPlayer?playerAccel:playerAccel;
  const stability=.5+score('stability')*.5;
  car.speed+= (target-car.speed)*(1-Math.exp(-(target<car.speed?brake:accel)*stability*dt));
  car.top=Math.max(car.top,car.speed);
  // 시간·거리 일관성: km/h → m/s → 정규화된 트랙 거리.
  const old=car.progress;car.progress+=(car.speed/3.6)*dt/length;
  if(car.progress>=1){car.progress-=1;car.laps++;car.lastLap=elapsed-car.lapStart;car.best=Math.min(car.best,car.lastLap);car.lapStart=elapsed;
    if(car.laps>=DATA.laps){car.finished=true;car.finishTime=elapsed;car.progress=0;car.speed=0}}
  placeCar(car,index);if(!car.finished&&car.mesh.userData.rotateWheels)car.mesh.userData.rotateWheels(car.speed*dt*.06);
}
function updatePlayerCar(dt,elapsed){updateCar(player,dt,elapsed,0)}
function updateAICars(dt,elapsed){ais.forEach((car,i)=>updateCar(car,dt,elapsed,i+1))}
function rank(){let distance=c=>c.finished?DATA.laps+1+(100000-c.finishTime)*.00000001:c.laps+c.progress;return 1+ais.filter(c=>distance(c)>distance(player)).length}
const targetCamera=new THREE.Vector3();
function updateCamera(dt){let f=frameAt(player.progress);targetCamera.copy(player.mesh.position).addScaledVector(f.v,-16).add(new THREE.Vector3(0,8,0));camera.position.lerp(targetCamera,1-Math.exp(-4*dt));camera.lookAt(player.mesh.position.x,1,player.mesh.position.z)}
function updateHUD(){document.getElementById('position').textContent=rank()+' / 5';document.getElementById('lap').textContent=Math.min(3,player.laps+1)+' / 3';document.getElementById('speed').textContent=Math.round(player.speed)}
let phase='preview',countEnd=0,startTime=0,lastFrame=performance.now(),elapsed=0,isPaused=false;
document.getElementById('pause').addEventListener('click',()=>{if(phase!=='running')return;isPaused=!isPaused;document.getElementById('pause').textContent=isPaused?'▶ RESUME':'⏸ PAUSE'});
function startCountdown(){if(phase!=='preview')return;
  // 출발 직전에 한 번만 기존 AI 객체를 만들고, 카운트다운과 레이스에 계속 사용합니다.
  ais.push(...createAICars());cars=[player,...ais];
  cars.forEach((car,i)=>{
    car.progress=i===0?0:-(Math.ceil(i/2)*6)/length;
    car.laps=0;car.speed=0;placeCar(car,i);
  });
  raceMap.hidden=false;updateMinimap();phase='countdown';document.getElementById('previewPanels').hidden=true;document.getElementById('start').hidden=true;camera.position.copy(player.mesh.position).addScaledVector(frameAt(player.progress).v,-27).add(new THREE.Vector3(0,19,0));camera.lookAt(player.mesh.position.x,1,player.mesh.position.z);document.getElementById('message').textContent='RACE STARTING';document.getElementById('hud').hidden=false;document.getElementById('overlay').style.justifyContent='center';countEnd=performance.now()+4000}
function startSimulation(now){document.getElementById('back').hidden=false;phase='running';startTime=now;lastFrame=now;document.getElementById('pause').hidden=false;document.getElementById('count').textContent='';document.getElementById('message').textContent='';document.getElementById('overlay').style.display='none'}
function finishSimulation(){phase='complete';document.getElementById('back').hidden=false;document.getElementById('overlay').style.display='flex';document.getElementById('result').style.display='block';document.getElementById('result').innerHTML='<strong>SIMULATION COMPLETE</strong><br>POSITION '+rank()+' / 5<br>LAPS 3<br>TOP SPEED '+Math.round(player.top)+' km/h<br>LAP TIME '+player.lastLap.toFixed(2)+' sec<br>BEST LAP '+player.best.toFixed(2)+' sec';document.getElementById('hud').hidden=true;document.getElementById('pause').hidden=true}
function resetSimulation(){
  ais.forEach(car=>scene.remove(car.mesh));ais.length=0;cars=[player];
  Object.assign(player,{progress:0,laps:0,speed:0,finished:false,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity});
  placeCar(player,0);elapsed=0;countEnd=0;isPaused=false;phase='preview';
  document.getElementById('pause').textContent='⏸ PAUSE';document.getElementById('pause').hidden=true;
  document.getElementById('back').hidden=true;document.getElementById('hud').hidden=true;
  document.getElementById('previewPanels').hidden=false;raceMap.hidden=true;mapMarkers.forEach(dot=>dot.remove());mapMarkers.length=0;document.getElementById('start').hidden=false;
  document.getElementById('overlay').style.display='flex';document.getElementById('overlay').style.justifyContent='flex-end';document.getElementById('message').textContent='';
  document.getElementById('result').style.display='none';document.getElementById('count').textContent='';
  updateHUD();handleResize();
}
function handleResize(){let w=Math.max(root.clientWidth,1),h=Math.max(root.clientHeight,1);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();if(phase==='preview'){const distance=Math.max(125,125/camera.aspect);camera.position.set(-12,distance*.85,64);camera.lookAt(0,0,0)}}
window.addEventListener('resize',handleResize);new ResizeObserver(handleResize).observe(root);handleResize();document.getElementById('start').addEventListener('click',startCountdown);document.getElementById('back').addEventListener('click',resetSimulation);
// requestAnimationFrame은 모든 상태에서 유지되므로 카운트다운 뒤에도 캔버스가 사라지지 않습니다.
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-lastFrame)/1000,.05);lastFrame=now;
  if(phase==='countdown'){let remaining=countEnd-now;document.getElementById('count').textContent=remaining>1000?String(Math.ceil((remaining-1000)/1000)):'RACE START!';updateMinimap();if(remaining<=0)startSimulation(now)}
  else if(phase==='running'&&!isPaused){elapsed+=dt;updatePlayerCar(dt,elapsed);updateAICars(dt,elapsed);updateCamera(dt);updateHUD();updateMinimap();if(player.finished&&ais.every(car=>car.finished))finishSimulation()}
  if(phase==='preview'){
    // 왼쪽 SVG에는 차량이 없고 가운데에는 기존 Three.js 차량만 렌더링합니다.
    const box=carPanel.getBoundingClientRect(),outer=root.getBoundingClientRect(),dpr=renderer.getPixelRatio();
    const x=Math.round((box.left-outer.left)*dpr),y=Math.round((outer.bottom-box.bottom)*dpr);
    const w=Math.max(1,Math.round(box.width*dpr)),h=Math.max(1,Math.round(box.height*dpr));
    trackObjects.forEach(obj=>obj.visible=false);ground.visible=false;player.mesh.visible=true;
    camera.aspect=w/h;camera.updateProjectionMatrix();
    const center=player.mesh.position;
    camera.position.set(center.x+orbitRadius*Math.sin(orbitYaw)*Math.cos(orbitPitch),
      center.y+orbitRadius*Math.sin(orbitPitch)+2,
      center.z+orbitRadius*Math.cos(orbitYaw)*Math.cos(orbitPitch));
    camera.lookAt(center.x,center.y,center.z);
    renderer.setScissorTest(true);renderer.setViewport(x,y,w,h);renderer.setScissor(x,y,w,h);
    renderer.render(scene,camera);renderer.setScissorTest(false);
    trackObjects.forEach(obj=>obj.visible=true);ground.visible=true;
    camera.aspect=root.clientWidth/root.clientHeight;camera.updateProjectionMatrix();
  }else{player.mesh.visible=true;renderer.setViewport(0,0,root.clientWidth*renderer.getPixelRatio(),root.clientHeight*renderer.getPixelRatio());renderer.render(scene,camera)}
}requestAnimationFrame(animate);
</script></body></html>'''


if __name__ == "__main__":
    main()
