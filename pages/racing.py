"""F1 Racing Simulator - 3D 자동 주행 시뮬레이션

이 파일만 pages/racing.py에 넣습니다. main.py는 수정하지 않습니다.
"""
import html
import json
import random
import importlib.util
from pathlib import Path
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
    """Garage와 같은 상단·사이드바 정책 및 본문 여백을 적용합니다."""
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@500;700&family=Noto+Sans+KR:wght@400;700&display=swap');
    .stApp{background:radial-gradient(circle at 50% 12%,#202b37,#090c11 48%,#05070a);color:#eff5fa}.block-container{max-width:1680px;padding:0 clamp(.75rem,2vw,1.7rem) 2rem}
    [data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],#MainMenu,footer{display:none!important}
    [data-testid="stAppViewContainer"]{width:100%!important}
    [data-testid="stMainBlockContainer"]{max-width:1680px!important;padding:0 clamp(.75rem,2vw,1.7rem) 2rem!important}
    @media(max-width:800px){[data-testid="stMainBlockContainer"]{padding:0 .65rem 1.4rem!important}}
    .head{border-top:3px solid #ff3158;border-bottom:1px solid #2a3542;padding:12px 16px;background:#0c1118;display:flex;justify-content:space-between}.logo{font:700 25px Oxanium}.logo b{color:#ff3158}.step{font:11px Oxanium;color:#8492a0;letter-spacing:2px}
    .card{background:#0d131b;border:1px solid #2a3542;padding:14px}.title{font:700 12px Oxanium;letter-spacing:2px;color:#9aa8b6;border-bottom:1px solid #293542;padding-bottom:9px;margin-bottom:10px}.chips span{display:inline-block;padding:4px 7px;margin:3px;border:1px solid #354353;color:#9eacba;font-size:10px}.bar-row{margin:8px 0}.bar-top{display:flex;justify-content:space-between;font:700 11px Oxanium}.bar{height:9px;background:#232c36;margin-top:5px;transform:skewX(-12deg);overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,#27d6ff,#8065ff)}
    div[data-testid='stButton'] button{width:100%!important;min-height:58px!important;background:#e51d45!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border:1px solid #ff6681!important;font:700 16px Oxanium!important}div[data-testid='stButton'] button *{color:#fff!important;-webkit-text-fill-color:#fff!important}.empty{max-width:650px;margin:90px auto;padding:30px;text-align:center;background:#0e141c;border-top:3px solid #ff3158}
    
/* 설계 화면과 같은 이동 버튼. 긴 문구는 잘리지 않고 줄바꿈합니다. */
.stApp div[data-testid="stButton"] button {
 background:#10161e!important;background-image:none!important;color:#f4f7fb!important;
 -webkit-text-fill-color:#f4f7fb!important;border:1px solid #354252!important;
 border-radius:4px!important;min-height:44px!important;padding:10px 12px!important;
 font-family:'Noto Sans KR',sans-serif!important;font-size:14px!important;font-weight:700!important;
 line-height:1.5!important;white-space:normal!important;height:auto!important;box-sizing:border-box;
}
.stApp div[data-testid="stButton"] button * {color:inherit!important;-webkit-text-fill-color:inherit!important;white-space:normal!important;overflow-wrap:anywhere;line-height:1.5!important;font-size:14px!important}
.stApp div[data-testid="stButton"] button:hover {background:#172631!important;border-color:#27d6ff!important}
.stApp div[data-testid="stButton"] button:focus-visible {border-color:#ff3158!important;outline:2px solid #ff315866;outline-offset:2px}
@media(max-width:760px){[data-testid="stHorizontalBlock"]:has([data-testid="stButton"]) {flex-wrap:wrap!important;gap:.5rem!important}
[data-testid="stHorizontalBlock"]:has([data-testid="stButton"])>[data-testid="stColumn"] {min-width:min(100%,250px)!important;flex:1 1 250px!important}}

</style>""",unsafe_allow_html=True)


BUILDER_JS = "\nfunction createF1Car(color, cfg) {\n    const car=new THREE.Group(), partGroups={};\n    const mat=(color,metal=.45,rough=.32)=>new THREE.MeshStandardMaterial({color,metalness:metal,roughness:rough});\n    function group(name){const g=new THREE.Group();g.userData.part=name;partGroups[name]=g;car.add(g);return g}\n    function mesh(g,geo,material,pos=[0,0,0],rot=[0,0,0],scale=[1,1,1]){const m=new THREE.Mesh(geo,material);m.position.set(...pos);m.rotation.set(...rot);m.scale.set(...scale);m.castShadow=true;m.receiveShadow=true;m.userData.part=g.userData.part;g.add(m);return m}\n    function capsule(length,radius){return new THREE.CapsuleGeometry(radius,length,8,20)}\n    // 두 지점 사이에 실제 두께가 있는 서스펜션 암을 만드는 도우미입니다.\n    function rodBetween(g,a,b,radius,material){const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),mid=start.clone().add(end).multiplyScalar(.5),length=start.distanceTo(end);const rod=mesh(g,new THREE.CylinderGeometry(radius,radius,length,12),material,[mid.x,mid.y,mid.z]);rod.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),end.clone().sub(start).normalize());return rod}\n    // 매끈한 곡면 차체: 길쭉한 캡슐과 유선형 노즈를 겹쳐 실제 포뮬러카 실루엣을 만듭니다.\n    const body=group('body'), red=mat(color,.72,.24);mesh(body,capsule(3.1,.65),red,[0,.05,0],[Math.PI/2,0,0],[1,1,1]);mesh(body,new THREE.ConeGeometry(.62,4.5,32),red,[0,-.08,3.35],[Math.PI/2,0,0],[1,.55,1]);\n    mesh(body,new THREE.SphereGeometry(1.0,32,18),red,[0,.05,-1.35],[0,0,0],[1.35,.78,1.75]);\n    // 콕핏과 Halo\n    const cockpit=group('cockpit');mesh(cockpit,new THREE.SphereGeometry(.64,28,16,0,Math.PI*2,0,Math.PI*.62),mat(0x111820,.15,.16),[0,.65,-.25],[0,0,0],[1,.62,1.45]);\n    const haloMat=mat(0x242c35,.75,.2);mesh(cockpit,new THREE.TorusGeometry(.62,.055,10,36,Math.PI*1.25),haloMat,[0,1.08,-.05],[Math.PI/2,0,.39]);mesh(cockpit,new THREE.CylinderGeometry(.06,.06,.72,12),haloMat,[0,.82,.35],[0,0,0]);\n    // 사이드포드: 앞은 넓고 뒤로 갈수록 좁아지는 곡면\n    const side=group('sidepods');[-1,1].forEach(s=>{mesh(side,capsule(1.35,.52),red,[s*1.02,-.05,-.65],[Math.PI/2,0,0],[1,.72,1.25]);mesh(side,new THREE.ConeGeometry(.48,2.2,24),red,[s*.94,-.08,-2.0],[-Math.PI/2,0,0],[.75,1,.9])});\n    // 타이어는 실제 회전축을 가진 두꺼운 Torus 3D 메시입니다.\n    const tyres=group('tyres'), tv=cfg.tyres.variant, tyreMat=mat(0x08090b,.05,.58+tv*.1), stripe=mat(cfg.tyres.color,.15,.38);[[-1.55,1.95,.56], [1.55,1.95,.56],[-1.72,-2.15,.72],[1.72,-2.15,.72]].forEach(p=>{const [x,z,r]=p;mesh(tyres,new THREE.TorusGeometry(r,r*(.43-tv*.045),18+tv*5,42),tyreMat,[x,-.35,z],[0,Math.PI/2,0]);mesh(tyres,new THREE.TorusGeometry(r*.99,.035,8,48),stripe,[x,-.35,z],[0,Math.PI/2,0])});\n    // 프론트 윙: 날개 단면을 가진 여러 곡선형 엘리먼트\n    const fw=group('frontWing'), fwM=mat(cfg.frontWing.color,.65,.22), f=cfg.frontWing.shape;Array.from({length:2+cfg.frontWing.variant},(_,i)=>-.18+i*.22).forEach((y,i)=>mesh(fw,new THREE.CapsuleGeometry(.11,3.2*f,6,20),fwM,[0,-.58+y,3.62-i*.25],[0,0,Math.PI/2],[1,1,1]));[-1,1].forEach(s=>mesh(fw,new THREE.ExtrudeGeometry(new THREE.Shape().moveTo(0,0).lineTo(.44,.12).lineTo(.28,.65).lineTo(0,.52),{depth:.06,bevelEnabled:true,bevelSize:.025,bevelThickness:.025}),fwM,[s*1.75*f,-.88,3.35],[0,s<0?0:Math.PI,0]));\n    // 리어 윙: 선택에 따라 폭과 높이가 실제로 변합니다.\n    const rw=group('rearWing'), rwM=mat(cfg.rearWing.color,.68,.2), r=cfg.rearWing.shape;mesh(rw,new THREE.CapsuleGeometry(.16,2.55*r,6,20),rwM,[0,1.05,-3.24],[0,0,Math.PI/2]);Array.from({length:1+cfg.rearWing.variant},(_,i)=>mesh(rw,new THREE.CapsuleGeometry(.09,2.35*r,6,20),rwM,[0,.72-i*.22,-3.0+i*.08],[0,0,Math.PI/2]));[-1,1].forEach(s=>mesh(rw,new THREE.CylinderGeometry(.045,.06,1.3,10),rwM,[s*.92*r,.35,-3.05],[0,0,0]));\n    const floor=group('floor');const floorShape=new THREE.Shape().moveTo(-1.25,-2.7).lineTo(-1.25,1.4).lineTo(-.8,2.8).lineTo(.8,2.8).lineTo(1.25,1.4).lineTo(1.25,-2.7).lineTo(-1.25,-2.7);mesh(floor,new THREE.ExtrudeGeometry(floorShape,{depth:.09,bevelEnabled:true,bevelSize:.04,bevelThickness:.03}),mat(cfg.floor.color,.7,.25),[0,-.92,0],[Math.PI/2,0,0]);\n    const diffuser=group('diffuser'), dm=mat(cfg.diffuser.color,.72,.22);[-.72,-.24,.24,.72].forEach(x=>mesh(diffuser,new THREE.BoxGeometry(.055,.7,1.35*cfg.diffuser.shape),dm,[x,-.62,-3.08],[.38,0,0]));\n    const brakes=group('brakes'), bv=cfg.brakes.variant;[[-1.55,1.95],[1.55,1.95],[-1.72,-2.15],[1.72,-2.15]].forEach(p=>mesh(brakes,new THREE.CylinderGeometry(.38-bv*.055,.38-bv*.055,.07,24+bv*8),mat(cfg.brakes.color,.8,.28),[p[0],-.35,p[1]],[0,0,Math.PI/2]));\n    // 앞·뒤 바퀴 허브와 차체를 위/아래 위시본 및 푸시로드로 연결합니다.\n    const suspension=group('suspension'), sv=cfg.suspension.variant, suspensionMat=mat(cfg.suspension.color,.82,.18), armRadius=.055-sv*.007;\n    [[1.95,1.55],[-2.15,1.72]].forEach(([z,wheelX])=>[-1,1].forEach(side=>{\n      const hub=[side*wheelX,-.34,z], innerX=side*.62;\n      rodBetween(suspension,[innerX,-.28,z-.48],hub,armRadius,suspensionMat);\n      rodBetween(suspension,[innerX,-.28,z+.48],hub,armRadius,suspensionMat);\n      rodBetween(suspension,[innerX,.25,z-.30],hub,armRadius*.9,suspensionMat);\n      rodBetween(suspension,[innerX,.25,z+.30],hub,armRadius*.9,suspensionMat);\n      rodBetween(suspension,[side*.48,.48,z],hub,armRadius*.82,suspensionMat);\n      mesh(suspension,new THREE.SphereGeometry(.12,16,10),suspensionMat,hub);\n    }));\n    const engine=group('engine'), ev=cfg.engine.variant;mesh(engine,new THREE.CapsuleGeometry(.50-ev*.06,1.45-ev*.12,8,18),mat(cfg.engine.color,.65,.24),[0,.22,-1.75],[Math.PI/2,0,0]);\n    const ers=group('ers'), erv=cfg.ers.variant;mesh(ers,new THREE.TorusGeometry(.30-erv*.035,.075-erv*.01,10,28+erv*8),mat(cfg.ers.color,.5,.15),[0,.68,-1.38],[Math.PI/2,0,0]);\n\n  return car;\n}\n"



# 공식 실측 좌표가 아닌 특징 기반 게임용 폐곡선입니다.
CIRCUITS = {'monaco': {'name': 'Monaco Circuit', 'width': 10, 'points': [[-170, 100], [-180, -20], [-140, -100], [-40, -135], [60, -125], [130, -80], [150, -10], [100, 20], [45, -15], [0, 10], [45, 65], [130, 85], [150, 140], [80, 165], [-30, 150], [-110, 180]], 'description': '도심형 게임 레이아웃 · 짧은 직선과 연속 코너'}, 'british': {'name': 'British Circuit', 'width': 14, 'points': [[-280, 150], [-300, -60], [-230, -180], [-90, -200], [25, -120], [140, -180], [270, -160], [300, -40], [220, 40], [110, 20], [50, 110], [140, 200], [30, 270], [-100, 230], [-160, 130]], 'description': '균형형 게임 레이아웃 · 긴 직선과 고속·저속 코너'}, 'australian': {'name': 'Australian Circuit', 'width': 14, 'points': [[-380, 160], [-380, -100], [-300, -200], [-120, -220], [100, -200], [310, -160], [380, -50], [350, 100], [270, 150], [100, 140], [40, 230], [-100, 260], [-220, 200]], 'description': '고속형 게임 레이아웃 · 긴 직선과 완만한 코너'}}

def build_simulation_html(car_data, opponents):
    """준비 화면부터 결과까지 하나의 iframe에서 실행하여 rerun에 따른 중단을 방지합니다."""
    data = {"circuit": CIRCUITS[st.session_state.get("f1_active_circuit", "monaco")], "car": car_data, "laps": TOTAL_LAPS, "circuitKey": st.session_state.get("f1_active_circuit", "monaco"), "opponents": [dict(prepare_car_data(c["config"], c["performance"]), id=c["id"]) for c in opponents]}
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



def _f1_layout_html(document):
    """준비 화면의 고정 480px 패널을 유연한 높이와 좁은 화면 배치로 보완합니다."""
    style = """<style id="f1-preparation-layout-v1">
    html,body{height:auto!important;min-height:100%;overflow:auto!important}
    #game{height:clamp(480px,86vh,680px)!important;min-height:480px}
    #previewPanels{height:auto!important;top:0!important;bottom:100px!important;gap:10px!important;padding:8px!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;min-height:0}
    #trackPanel,#carPanel,#performancePanel{height:100%!important;min-height:0!important;min-width:0}
    #performancePanel{overflow:auto!important;overscroll-behavior:contain;scrollbar-gutter:stable;padding-bottom:18px!important}
    .previewTitle{height:auto!important;min-height:38px;line-height:1.4;white-space:normal;overflow-wrap:anywhere}
    #trackPanel,#carPanel{display:flex;flex-direction:column}
    #trackSvg{height:auto!important;flex:1;min-height:0}
    #start{max-width:calc(100% - 24px);white-space:normal}
    @media(max-width:780px){
      #game.f1-preparation{height:1480px!important;min-height:1480px!important}
      #previewPanels{grid-template-columns:minmax(0,1fr)!important;grid-template-rows:1fr 1.1fr 1.55fr!important;bottom:100px!important}
    }
    </style>"""
    script = """<script>
    // 준비 화면을 벗어나면 기존 레이스 표시 크기로 돌아갑니다.
    // 패널 표시 상태만 관찰하며 게임 진행에는 개입하지 않습니다.
    (()=>{const root=document.getElementById('game');const panels=document.getElementById('previewPanels');
    if(!root||!panels)return;
    const sync=()=>root.classList.toggle('f1-preparation',!panels.hidden);
    sync();new MutationObserver(sync).observe(panels,{attributes:true,attributeFilter:['hidden']});})();
    </script>"""
    return document.replace('</head>', style + '</head>', 1).replace('</body>', script + '</body>', 1)


# main.py를 화면 실행 없이 불러와 실제 부품 표와 계산 함수를 공유합니다.
def garage_rules():
    path = Path(__file__).resolve().parents[1] / "main.py"
    spec = importlib.util.spec_from_file_location("f1_garage_opponent_rules", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_part_data(), module.calculate_car_performance


OPPONENT_KEY = "f1_opponent_roster_v1"


def generate_opponents(parts, calculator, player_config, previous=None):
    """상대 네 대를 독립 생성합니다. 이전 조합·플레이어 조합과 중복하지 않습니다."""
    rng = random.SystemRandom()
    keys = list(parts)
    fingerprint = lambda config: tuple(config.get(k) for k in keys)
    forbidden = {fingerprint(player_config)}
    forbidden.update(fingerprint(c["config"]) for c in (previous or []))
    roster = []
    for i in range(4):
        for attempt in range(10000):
            config = {k: rng.choice(list(parts[k]["options"])) for k in keys}
            signature = fingerprint(config)
            # 외형뿐 아니라 성능 점수도 서로 다른 조합을 선택합니다.
            performance = calculator(parts, config)
            if signature in forbidden or performance == calculator(parts, player_config):
                continue
            if any(performance == car["performance"] for car in roster):
                continue
            if any(sum(config[k] != car["config"][k] for k in keys) < 3 for car in roster):
                continue
            break
        else:
            raise RuntimeError("서로 다른 상대 차량을 생성하지 못했습니다.")
        forbidden.add(signature)
        roster.append({"id": f"AI-{i+1:02d}", "config": dict(config), "performance": dict(performance)})
    return roster


def opponent_preparation(player_config):
    """최초에만 생성하고 확인 화면 전환은 저장된 조합을 그대로 사용합니다."""
    try:
        parts, calculator = garage_rules()
        if OPPONENT_KEY not in st.session_state:
            st.session_state[OPPONENT_KEY] = generate_opponents(parts, calculator, player_config)
    except Exception:
        st.error("상대 차량의 부품 정보를 읽지 못했습니다. main.py 위치를 확인해 주세요.")
        st.stop()
    detail_key = "f1_opponent_detail_view_v2"
    details = st.session_state.get(detail_key, False)
    # 기존 경주 iframe 내부의 실행 상태를 Python에서 추측하지 않습니다.
    # 외부 버튼은 경주 종료 후 준비 화면에서만 사용하도록 명확하게 안내합니다.
    st.caption("상대 확인·변경은 경주 시작 전이나 종료 후에 사용해 주세요. 주행 중 누르면 현재 경주는 초기화되며, 변경한 조합은 새 경주에 적용됩니다.")
    back_col, change_col = st.columns(2)
    with back_col:
        if st.button("🏁 레이싱 준비 화면으로 돌아가기" if details else "🔎 상대 차량 확인",
                     key="f1_opponent_view_toggle_v2", use_container_width=True):
            st.session_state[detail_key] = not details
            st.rerun()
    with change_col:
        if st.button("🔄 상대 차량 바꾸기", key="f1_opponent_change_v2", use_container_width=True):
            try:
                st.session_state[OPPONENT_KEY] = generate_opponents(
                    parts, calculator, player_config, st.session_state[OPPONENT_KEY])
                st.success("모든 상대 차량 조합을 변경했습니다. 새 경주부터 적용됩니다.")
            except RuntimeError:
                st.warning("상대 차량을 변경하지 못했습니다. 기존 조합을 유지합니다.")
    roster = st.session_state[OPPONENT_KEY]
    if details:
        st.markdown("### AI 상대 차량")
        st.caption("현재 저장된 조합입니다. 성능은 게임 점수이며 실제 속도 단위가 아닙니다.")
        # 마커를 포함한 카드 컨테이너에만 펼침 컴포넌트 스타일을 적용합니다.
        st.markdown("""<style>
        [data-testid="stVerticalBlockBorderWrapper"]:has(.f1-opponent-card),
        [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .f1-opponent-card){color:#edf3fa}
        [data-testid="stExpander"]:has(.f1-opponent-part-details){background:#101b29!important;border:1px solid #354252!important;border-radius:6px!important}
        [data-testid="stExpander"]:has(.f1-opponent-part-details) details,
        [data-testid="stExpander"]:has(.f1-opponent-part-details) summary,
        [data-testid="stExpander"]:has(.f1-opponent-part-details) [data-testid="stExpanderDetails"]{
          background:#101b29!important;color:#edf3fa!important}
        [data-testid="stExpander"]:has(.f1-opponent-part-details) summary:hover{background:#192a3b!important}
        [data-testid="stExpander"]:has(.f1-opponent-part-details) summary:focus-visible{outline:2px solid #ff3158!important;outline-offset:-2px}
        [data-testid="stExpander"]:has(.f1-opponent-part-details) summary *,
        [data-testid="stExpander"]:has(.f1-opponent-part-details) p{color:#edf3fa!important;-webkit-text-fill-color:#edf3fa!important}
        .f1-opponent-card{background:#101923;border:1px solid #354252;border-top:3px solid #ff3158;border-radius:8px;padding:16px;margin-bottom:8px;color:#edf3fa}
        .f1-opponent-card h3{margin:0 0 8px;color:#fff;font-size:20px}
        .f1-opponent-card .summary{font-size:12px;line-height:1.7;color:#bfcede;margin-bottom:12px}
        .f1-opponent-metrics{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px}
        .f1-opponent-value{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
        .f1-opponent-bar{height:6px;background:#283442;border-radius:4px;overflow:hidden}
        .f1-opponent-bar i{display:block;height:100%;background:linear-gradient(90deg,#27d6ff,#8065ff)}
        .f1-opponent-part-details{color:#dce6f3;font-size:13px;line-height:1.7}
        .f1-opponent-part-details .part-row{display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-bottom:1px solid #293747}
        </style>""", unsafe_allow_html=True)
        columns = st.columns(2)
        for index, car in enumerate(roster):
            with columns[index % 2]:
                summary = " · ".join(html.escape(parts[k]["ko"] + " " + parts[k]["options"][car["config"][k]]["label"])
                                     for k in ("front_wing", "tyres", "engine") if k in car["config"])
                metrics = ""
                for metric in METRICS:
                    value = car["performance"][metric]
                    width = max(0, min(100, float(value)))
                    label = "접지력" if metric == "그립" else metric
                    metrics += (f'<div><div class="f1-opponent-value"><span>{html.escape(label)}</span>'
                                f'<b>{html.escape(str(value))}</b></div><div class="f1-opponent-bar"><i style="width:{width}%"></i></div></div>')
                st.markdown(f'<section class="f1-opponent-card"><h3>{html.escape(car["id"])}</h3><div class="summary">{summary}</div><div class="f1-opponent-metrics">{metrics}</div></section>', unsafe_allow_html=True)
                # 마커가 접힌 상태에서도 DOM에 있도록 실행 결과로 포함합니다.
                with st.expander(car["id"] + " · 부품별 세부 설정", expanded=False):
                    rows = "".join(f'<div class="part-row"><span>{html.escape(parts[k]["ko"])}</span><span>{html.escape(parts[k]["options"][v]["label"])} ({html.escape(v)})</span></div>' for k, v in car["config"].items())
                    st.markdown('<div class="f1-opponent-part-details">' + rows + '</div>', unsafe_allow_html=True)
    return roster, details


def render_racing_component(document):
    """준비 화면의 서킷 선택만 Python 세션으로 전달합니다."""
    import tempfile
    import uuid
    import sys
    import types
    import importlib.machinery
    # 페이지 실행 모듈(__main__)의 spec 유무에 의존하지 않는 선언 전용 모듈입니다.
    # 세션별 실제 HTML 디렉터리와 등록 이름을 함께 고정해 이름/경로 충돌을 막습니다.
    token = st.session_state.setdefault("f1_component_token", uuid.uuid4().hex)
    folder = st.session_state.get("f1_component_folder")
    if not folder or not Path(folder).is_dir():
        folder = tempfile.mkdtemp(prefix="f1_circuit_")
        st.session_state["f1_component_folder"] = folder
    folder = str(Path(folder).resolve())
    target = Path(folder, "index.html")
    try:
        if not target.exists() or target.read_text(encoding="utf-8") != document:
            target.write_text(document, encoding="utf-8")
        if not target.is_file() or not target.stat().st_size:
            raise OSError("컴포넌트 HTML 파일이 비어 있습니다.")
        module_name = "f1_racing_component_" + token
        module = sys.modules.get(module_name)
        if module is None:
            module = types.ModuleType(module_name)
            module.__file__ = str(Path(folder, "registration.py"))
            module.__spec__ = importlib.machinery.ModuleSpec(module_name, loader=None)
            sys.modules[module_name] = module
            # inspect가 선언 호출자의 모듈을 찾을 수 있도록 등록 후 함수를 생성합니다.
            source = "import streamlit.components.v1 as components\ndef declare(folder):\n    return components.declare_component('f1_circuit_racing', path=folder)\n"
            exec(compile(source, module.__file__, "exec"), module.__dict__)
        component = module.declare(folder)
    except (OSError, RuntimeError) as error:
        st.error("레이싱 화면 구성 파일을 준비하거나 등록하지 못했습니다. 아래 오류 상세를 확인해 주세요.")
        st.exception(error)
        return
    current = st.session_state.get("f1_active_circuit", "monaco")
    selected = component(key="f1_racing_" + token + "_" + current, default=None)
    if isinstance(selected, str) and selected in CIRCUITS and selected != current:
        st.session_state["f1_active_circuit"] = selected
        st.rerun()


def main():
    st.set_page_config(page_title="F1 RACING SIMULATOR", page_icon="🏁",
                       layout="wide", initial_sidebar_state="collapsed")
    apply_page_style()

    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@600;700&display=swap');
    .f1-race-head{display:flex;justify-content:space-between;align-items:center;gap:12px;border-top:3px solid #ff3158;border-bottom:1px solid #27313d;padding:10px 16px;background:#0c1118;margin-bottom:10px}
    .f1-race-head .logo{font:700 25px Oxanium,sans-serif;letter-spacing:2px;color:#eef3f8}.f1-race-head b{color:#ff3158}.f1-race-head .step{font:600 11px Oxanium,sans-serif;color:#8794a3;letter-spacing:2px}
    div[data-testid="stButton"] button{min-height:44px!important;border:1px solid #354252!important;border-radius:4px!important;background:#10161e!important;color:#f4f7fb!important;font-size:14px!important;padding:8px 12px!important;white-space:normal!important}
    @media(max-width:650px){.f1-race-head{flex-wrap:wrap}.f1-race-head .logo{font-size:20px}}
    </style><div class="f1-race-head"><div class="logo">F1 <b>RACING SIMULATOR</b></div><div class="step">RACE SIMULATION</div></div>""", unsafe_allow_html=True)
    garage_col, home_col, ai_col = st.columns(3)
    with garage_col:
        if st.button("🔧 차량 설계 화면으로 돌아가기", use_container_width=True):
            st.session_state.app_view = "garage"
            st.switch_page("main.py")
    with home_col:
        if st.button("🏠 처음 화면으로 돌아가기", use_container_width=True):
            st.session_state.app_view = "home"
            st.switch_page("main.py")
    with ai_col:
        if st.button("🤖 AI 레이스 엔지니어와 대화하기", use_container_width=True):
            st.switch_page("pages/chat.py")
    config, performance = load_my_car()
    if not (config and performance) or not all(
        key in config and config[key] in spec["options"]
        for key, spec in GARAGE_VISUAL_OPTIONS.items()
    ):
        st.warning("먼저 차량을 설계해 주세요.")
        return
    opponents, showing_details = opponent_preparation(config)
    if showing_details:
        return
    st.session_state.setdefault("f1_active_circuit", "monaco")
    car_data = prepare_car_data(config, performance)
    render_racing_component(_f1_layout_html(build_simulation_html(car_data, opponents)))



SIMULATION_HTML = r'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@500;700&display=swap');
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#071019;color:#fff;font-family:Arial,sans-serif} [hidden]{display:none!important}
#game{position:relative;width:100%;height:100%;overflow:hidden;background:#071019}
canvas{display:block;width:100%;height:100%}.hud{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.panel{position:absolute;top:12px;max-width:42%;padding:8px 12px;background:#071019dc;border:1px solid #354758;border-top:2px solid #27d6ff;font-size:11px;letter-spacing:1px}
.panel b{font-size:clamp(16px,2.8vw,26px);white-space:nowrap}.pos{position:static;max-width:none;margin-top:7px;padding:8px 10px;text-align:left}.lap{right:12px;text-align:right}
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
#raceMap{position:absolute;top:8px;left:8px;width:clamp(128px,17vw,182px);padding:7px 9px;background:#091522ed;border:1px solid #365161;pointer-events:none;text-align:center;color:#b9d6e4;font:700 11px Oxanium,Arial,sans-serif;z-index:3}#raceMap svg{display:block;width:100%;height:clamp(125px,18vh,174px)}#raceMap .legend{font-size:9px;color:#b9cbd5;white-space:nowrap}@media(max-width:580px){#raceMap{width:128px;padding:5px}#raceMap svg{height:110px}#raceMap .legend{font-size:7px}}
#back{pointer-events:auto;position:absolute;right:115px;bottom:14px;cursor:pointer;background:#091725;color:#fff;border:1px solid #27d6ff;padding:8px 11px;font-weight:bold}
#result{display:none;width:min(490px,calc(100vw - 32px));max-height:calc(100% - 64px);overflow:auto;background:#09131eef;border:1px solid #ff3158;border-top:3px solid #ff3158;padding:18px;color:#eff5fa;text-shadow:none;text-align:left;box-shadow:0 12px 40px #000a}#result .result-title{text-align:center;font:700 24px Oxanium,Arial,sans-serif;color:#fff;margin:0 0 4px}#result .result-sub{text-align:center;font:700 11px Oxanium,Arial,sans-serif;letter-spacing:2px;color:#ff6681;margin-bottom:14px}#result .result-rank{padding:13px;background:#171e2a;border:1px solid #ff3158;text-align:center;margin-bottom:10px}#result .result-rank span{display:block;color:#b9cbd5;font-size:12px}#result .result-rank strong{font:700 38px Oxanium,Arial,sans-serif;color:#ff4569}#result .result-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}#result .result-card{min-width:0;padding:11px;background:#101b26;border:1px solid #324453}#result .result-card span{display:block;color:#afbdca;font-size:11px;margin-bottom:4px}#result .result-card b{font:700 clamp(15px,3vw,22px) Oxanium,Arial,sans-serif;white-space:nowrap}@media(max-width:410px){#result .result-grid{grid-template-columns:1fr}}
#error{position:absolute;left:12px;bottom:10px;color:#ff7186;background:#08111e}
#circuitControls{pointer-events:auto;flex:none;padding:10px;display:grid;gap:6px;background:#0c1118;border-top:1px solid #354252}
#circuitControls strong{font-size:12px;color:#aebbc9;text-align:left}
#circuitControls button{cursor:pointer;min-height:36px;padding:7px 9px;border:1px solid #354252;border-radius:4px;background:#10161e;color:#f4f7fb;font-size:12px;text-align:left;white-space:normal}
#circuitControls button:hover{border-color:#ff6681}#circuitControls button.active{background:#271622;border-color:#ff3158}#circuitControls button:focus-visible{outline:2px solid #ff6681}
</style><script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.164.1/build/three.module.js"}}</script>
</head><body><div id="game"><div id="previewPanels"><div id="trackPanel"><div class="previewTitle">TRACK TEST CIRCUIT</div><svg id="trackSvg" viewBox="0 0 320 390" preserveAspectRatio="xMidYMid meet"></svg><div id="circuitControls"><strong>트랙 선택</strong><button data-circuit="monaco">🏁 Monaco Circuit</button><button data-circuit="british">🏁 British Circuit</button><button data-circuit="australian">🏁 Australian Circuit</button></div></div><div id="carPanel"><div class="previewTitle">MY 3D F1 CAR</div></div><div id="performancePanel"><div class="previewTitle">CAR PERFORMANCE</div>__PERFORMANCE__</div></div><div class="hud" id="hud" hidden><div class="panel lap">LAP<br><b id="lap">1 / 3</b></div><button id="pause" hidden>⏸ PAUSE</button><div class="speed">SPEED <b id="speed">0</b> km/h</div></div><div id="raceMap" hidden>RACE MAP<svg id="mapSvg" viewBox="0 0 320 390" preserveAspectRatio="xMidYMid meet"></svg><div class="legend">● MY CAR &nbsp; ○ AI CARS</div><div class="panel pos">POSITION<br><b id="position">1 / 5</b></div></div><button id="back" hidden>↩ PREPARATION</button>
<div id="overlay"><p id="message"></p><h1 id="count"></h1><button id="start">SIMULATION START</button><div id="result"></div></div><div id="error"></div></div>
<script type="module">
import * as THREE from 'three';
const DATA=__DATA__,root=document.getElementById('game');
function streamlitMessage(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*')}
function syncFrameHeight(){streamlitMessage('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.scrollHeight)})}
window.addEventListener('message',e=>{if(e.source===window.parent&&e.data?.type==='streamlit:render')syncFrameHeight()});
streamlitMessage('streamlit:componentReady',{apiVersion:1});
new ResizeObserver(syncFrameHeight).observe(root);
document.querySelectorAll('[data-circuit]').forEach(button=>{
  button.classList.toggle('active',button.dataset.circuit===DATA.circuitKey);
  button.setAttribute('aria-pressed',String(button.dataset.circuit===DATA.circuitKey));
  button.addEventListener('click',()=>{
    // 준비 패널은 주행 중 숨겨지므로 진행 중 경로 변경은 허용하지 않습니다.
    if(phase!=='preview'||button.dataset.circuit===DATA.circuitKey)return;
    streamlitMessage('streamlit:setComponentValue',{value:button.dataset.circuit,dataType:'json'});
  });
});

const scene=new THREE.Scene();scene.background=new THREE.Color(0x08121a);
const camera=new THREE.PerspectiveCamera(52,1,.1,5000);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;root.insertBefore(renderer.domElement,root.firstChild);
scene.add(new THREE.HemisphereLight(0xd2e8ff,0x13231b,2.1));
const sun=new THREE.DirectionalLight(0xffffff,2.9);sun.position.set(-25,65,20);sun.castShadow=true;scene.add(sun);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(2400,2400),new THREE.MeshStandardMaterial({color:0x10201e,roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-.08;ground.receiveShadow=true;scene.add(ground);
__CAR_BUILDER__
// 하나의 폐쇄형 중심선이 미리보기·노면·주행 모두에 사용됩니다.
function createWaypoints(){return DATA.circuit.points.map(([x,z])=>new THREE.Vector3(x,0,z))}
const trackWaypoints=createWaypoints();
// 점 간격 차이에 따른 과도한 튀어나옴을 줄이는 공통 중심선입니다.
const curve=new THREE.CatmullRomCurve3(trackWaypoints,true,'centripetal');
curve.arcLengthDivisions=4096;curve.updateArcLengths();
const roadWidth=DATA.circuit.width, length=curve.getLength();
document.querySelector('#trackPanel .previewTitle').textContent=DATA.circuit.name;
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
function score(name,car){let n=Number((car?car.performance:DATA.car.performance)[name]);return Number.isFinite(n)?Math.max(0,Math.min(1,n/100)):.5}
function createPlayerCar(){let mesh=createF1Car(0xff1748,DATA.car.appearance);scene.add(mesh);return {mesh,performance:DATA.car.performance,progress:0,laps:0,speed:0,finished:false,base:1,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity}}
function createAICars(){return DATA.opponents.map((data,i)=>{let mesh=createF1Car([0x24bbfa,0xfcc935,0x8de76b,0xb277fa][i],data.appearance);scene.add(mesh);return {mesh,id:data.id,performance:data.performance,progress:0,laps:0,speed:0,finished:false,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity}})}
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
// 게임 점수를 주행 단위로 변환하는 공통 아케이드 모델입니다.
// 실제 F1 제원이나 실측값이 아니며, 플레이어와 AI에 동일하게 적용합니다.
const PHYSICS_STEP=1/120, PROFILE_SIZE=720;
function vehicleModel(car){
  const t=score('topSpeed',car),g=score('grip',car),d=score('downforce',car),c=score('cornering',car),b=score('braking',car),s=score('stability',car);
  // 부품 평균으로 좁아진 점수 범위에 맞춘 게임용 감도입니다. 저장 점수는 바꾸지 않습니다.
  // 월드 좌표 1단위=1m, 내부 속도=m/s, 차량 저장값과 HUD=km/h입니다.
  const power=(t-.45)/.5;
  return {maxSpeed:(210+145*power)/3.6,drive:12+24*power,mu:1.1+2.8*g,
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
  let lo=0,hi=m.maxSpeed;
  for(let j=0;j<24;j++){let v=(lo+hi)/2;if(v*v*k<=lateralCapacity(m,v))lo=v;else hi=v}
  return Math.max(4,lo);
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
const trackK=trackCurvatures();
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
function initializePhysics(car){car.model=vehicleModel(car);car.speedProfile=makeSpeedProfile(car.model)}
function updateCar(car,dt,endTime,index){
  if(car.finished)return;
  if(!car.model)initializePhysics(car);
  const m=car.model,wrapped=((car.progress%1)+1)%1;
  const sample=wrapped*PROFILE_SIZE,i=Math.floor(sample)%PROFILE_SIZE,f=sample-Math.floor(sample);
  const target=car.speedProfile[i]*(1-f)+car.speedProfile[(i+1)%PROFILE_SIZE]*f;
  const v=Math.max(0,Number.isFinite(car.speed)?car.speed/3.6:0);
  let next;
  if(v>target)next=Math.max(target,v-brakeCapacity(m,v)*dt);
  else next=Math.min(target,Math.max(0,v+acceleration(m,v,trackK[i])*dt));
  next=Math.max(0,Math.min(m.maxSpeed,Number.isFinite(next)?next:0));
  const distance=(v+next)*.5*dt,remaining=(1-car.progress)*length;
  car.speed=next*3.6;car.top=Math.max(car.top,car.speed);
  car.progress+=distance/length;
  if(car.progress>=1){
    const fraction=distance>0?Math.max(0,Math.min(1,remaining/distance)):1;
    const crossing=endTime-dt+fraction*dt;
    car.progress-=1;car.laps++;
    car.lastLap=crossing-car.lapStart;car.best=Math.min(car.best,car.lastLap);car.lapStart=crossing;
    if(car.laps>=DATA.laps){car.finished=true;car.finishTime=crossing;car.progress=0;car.speed=0}
  }

}

function updatePlayerCar(dt,elapsed){updateCar(player,dt,elapsed,0)}
function updateAICars(dt,elapsed){ais.forEach((car,i)=>updateCar(car,dt,elapsed,i+1))}
function rank(){return 1+ais.filter(c=>{
  if(c.finished&&player.finished)return c.finishTime<player.finishTime;
  if(c.finished!==player.finished)return c.finished;
  return c.laps+c.progress>player.laps+player.progress;
}).length}
const targetCamera=new THREE.Vector3();
function updateCamera(dt){let f=frameAt(player.progress);targetCamera.copy(player.mesh.position).addScaledVector(f.v,-16).add(new THREE.Vector3(0,8,0));camera.position.lerp(targetCamera,1-Math.exp(-4*dt));camera.lookAt(player.mesh.position.x,1,player.mesh.position.z)}
function updateHUD(){document.getElementById('position').textContent=rank()+' / 5';document.getElementById('lap').textContent=Math.min(3,player.laps+1)+' / 3';document.getElementById('speed').textContent=Math.round(player.speed)}
let physicsAccumulator=0;
let phase='preview',countEnd=0,startTime=0,lastFrame=performance.now(),elapsed=0,isPaused=false;
document.getElementById('pause').addEventListener('click',()=>{if(phase!=='running')return;isPaused=!isPaused;document.getElementById('pause').textContent=isPaused?'▶ RESUME':'⏸ PAUSE'});
function startCountdown(){if(phase!=='preview')return;
  // 출발 직전에 한 번만 기존 AI 객체를 만들고, 카운트다운과 레이스에 계속 사용합니다.
  ais.push(...createAICars());cars=[player,...ais];
  cars.forEach((car,i)=>{
    car.progress=i===0?0:-(Math.ceil(i/2)*6)/length;
    Object.assign(car,{laps:0,speed:0,finished:false,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity});initializePhysics(car);placeCar(car,i);
  });
  raceMap.hidden=false;updateMinimap();phase='countdown';document.getElementById('previewPanels').hidden=true;document.getElementById('start').hidden=true;camera.position.copy(player.mesh.position).addScaledVector(frameAt(player.progress).v,-27).add(new THREE.Vector3(0,19,0));camera.lookAt(player.mesh.position.x,1,player.mesh.position.z);document.getElementById('message').textContent='RACE STARTING';document.getElementById('hud').hidden=false;document.getElementById('overlay').style.justifyContent='center';countEnd=performance.now()+4000}
function startSimulation(now){document.getElementById('back').hidden=false;phase='running';physicsAccumulator=0;elapsed=0;startTime=now;lastFrame=now;document.getElementById('pause').hidden=false;document.getElementById('count').textContent='';document.getElementById('message').textContent='';document.getElementById('overlay').style.display='none'}
function finishSimulation(){phase='complete';raceMap.hidden=true;document.getElementById('back').hidden=false;document.getElementById('overlay').style.display='flex';document.getElementById('result').style.display='block';document.getElementById('result').innerHTML='<div class="result-title">레이스 결과</div><div class="result-sub">RACE COMPLETED</div><div class="result-rank"><span>최종 순위</span><strong>'+rank()+' / 5</strong></div><div class="result-grid"><div class="result-card"><span>완주 랩 수</span><b>3</b></div><div class="result-card"><span>최고속도</span><b>'+Math.round(player.top)+' km/h</b></div><div class="result-card"><span>랩타임</span><b>'+player.lastLap.toFixed(2)+' sec</b></div><div class="result-card"><span>최고 랩타임</span><b>'+player.best.toFixed(2)+' sec</b></div></div>';document.getElementById('hud').hidden=true;document.getElementById('pause').hidden=true}
function resetSimulation(){
  ais.forEach(car=>scene.remove(car.mesh));ais.length=0;cars=[player];
  Object.assign(player,{progress:0,laps:0,speed:0,finished:false,top:0,lapStart:0,lastLap:0,best:Infinity,finishTime:Infinity});
  placeCar(player,0);physicsAccumulator=0;elapsed=0;countEnd=0;isPaused=false;phase='preview';
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
function animate(now){requestAnimationFrame(animate);const dt=Math.max(0,Math.min((now-lastFrame)/1000,.25));lastFrame=now;
  if(phase==='countdown'){let remaining=countEnd-now;document.getElementById('count').textContent=remaining>1000?String(Math.ceil((remaining-1000)/1000)):'RACE START!';updateMinimap();if(remaining<=0)startSimulation(now)}
  else if(phase==='running'&&!isPaused){
    physicsAccumulator+=dt;
    while(physicsAccumulator>=PHYSICS_STEP){
      elapsed+=PHYSICS_STEP;updatePlayerCar(PHYSICS_STEP,elapsed);updateAICars(PHYSICS_STEP,elapsed);
      physicsAccumulator-=PHYSICS_STEP;
      if(player.finished&&ais.every(car=>car.finished)){physicsAccumulator=0;finishSimulation();break}
    }
    cars.forEach((car,i)=>{placeCar(car,i);if(!car.finished&&car.mesh.userData.rotateWheels)car.mesh.userData.rotateWheels(car.speed*dt*.06)});
    updateCamera(dt);updateHUD();updateMinimap();
  }
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
