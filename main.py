"""F1 Racing Simulator Garage

실행: streamlit run main.py
필수 패키지: streamlit
3D 렌더링은 Streamlit 안의 Three.js 웹 컴포넌트가 담당합니다.
"""

import html
import json
from copy import deepcopy

import streamlit as st
import streamlit.components.v1 as components


# -----------------------------------------------------------------------------
# 1. 학습 데이터
# -----------------------------------------------------------------------------
METRICS = ["다운포스", "최고속도", "코너링", "그립", "제동", "안정성"]
METRIC_ENGLISH = {
    "다운포스": "DOWNFORCE", "최고속도": "TOP SPEED", "코너링": "CORNERING",
    "그립": "GRIP", "제동": "BRAKING", "안정성": "STABILITY",
}
PHYSICS_HELP = {
    "다운포스": ("차를 트랙 쪽으로 눌러주는 힘", "달릴 때 공기를 이용해 차를 트랙 쪽으로 눌러요. 커지면 코너에서 안정적이지만 공기저항도 커질 수 있어요."),
    "최고속도": ("직선에서 낼 수 있는 속도", "엔진 힘이 크고 공기저항이 작을수록 유리해요. 큰 윙은 코너에는 좋지만 직선 속도를 낮출 수 있어요."),
    "코너링": ("코너를 빠르고 안정적으로 도는 능력", "다운포스, 타이어 그립, 서스펜션이 함께 만드는 종합 성능이에요."),
    "그립": ("타이어가 노면을 붙잡는 힘", "그립이 좋으면 가속·코너링·제동 중 차가 덜 미끄러져요."),
    "제동": ("짧고 안정적으로 감속하는 능력", "브레이크 마찰력뿐 아니라 타이어 그립과 차량 무게도 제동 거리에 영향을 줘요."),
    "안정성": ("차의 움직임을 예측하기 쉬운 정도", "차가 갑자기 미끄러지거나 흔들리지 않고 운전자의 조작에 일정하게 반응하는 정도예요."),
}

# 파츠 이름 위에 마우스를 올렸을 때 보여 줄 초보자용 역할 설명입니다.
PART_HELP = {
    "front_wing": ("앞 타이어의 공기 흐름을 조절하고 다운포스를 만드는 부품", "차량 앞쪽에서 공기의 흐름을 나누고 앞 타이어를 트랙 쪽으로 눌러요. 코너 진입 성능에 큰 영향을 줍니다."),
    "rear_wing": ("차량 뒤쪽의 다운포스와 공기저항을 조절하는 부품", "뒤쪽을 트랙에 눌러 빠른 코너를 안정적으로 돌게 해요. 크게 세우면 코너에는 좋지만 직선 속도는 낮아질 수 있습니다."),
    "tyres": ("트랙과 직접 맞닿아 차량의 그립을 만드는 부품", "엔진과 브레이크의 힘을 실제 노면에 전달해요. 고무 성질에 따라 접지력과 안정성이 달라집니다."),
    "brakes": ("속도를 줄여 원하는 지점에서 코너에 진입하게 하는 부품", "회전하는 바퀴에 마찰을 만들어 운동 에너지를 열로 바꾸고 차량을 감속시킵니다."),
    "suspension": ("바퀴가 노면을 따라가도록 차체와 연결하는 부품", "노면 충격을 받아들이고 타이어가 트랙에서 떨어지지 않도록 도와 그립과 반응성을 조절합니다."),
    "floor": ("차량 밑의 빠른 공기로 다운포스를 만드는 넓은 바닥", "차 아래 공기의 속도와 압력을 조절해 큰 공기역학적 힘을 만듭니다."),
    "diffuser": ("차량 밑 공기를 뒤쪽에서 부드럽게 넓혀 주는 부품", "바닥을 빠져나온 공기를 확산시켜 플로어가 안정적으로 다운포스를 만들도록 돕습니다."),
    "engine": ("연료의 에너지를 바퀴를 움직이는 힘으로 바꾸는 장치", "출력이 높으면 가속과 직선 속도가 좋아지지만 열과 신뢰성 관리가 더 중요해집니다."),
    "ers": ("제동 에너지를 전기로 저장했다가 가속에 사용하는 장치", "버려질 에너지 일부를 회수해 저장하고 필요할 때 모터의 추가 힘으로 사용합니다."),
}



def make_option(label, scores, stars, color, explanation, shape=1.0):
    """모든 옵션을 같은 구조로 저장해 새 파츠 추가를 쉽게 합니다."""
    return {"label": label, "scores": scores, "stars": stars, "color": color,
            "explanation": explanation, "shape": shape}


def get_part_data():
    """파츠별 옵션·성능·3D 색상·쉬운 물리 설명을 반환합니다."""
    return {
        "front_wing": {"name": "Front Wing", "ko": "프론트 윙", "icon": "⌁", "part": "frontWing",
            "options": {
                "low": make_option("LOW DRAG", [48, 94, 57, 61, 60, 62], [2,5,2], "#27d6ff", "윙 각도를 줄여 공기를 덜 막아요. 직선은 빨라지지만 앞바퀴를 누르는 힘은 작아져요.", .82),
                "balanced": make_option("BALANCED", [72, 77, 76, 72, 67, 76], [4,4,4], "#ffb21a", "다운포스와 직선 속도를 고르게 맞춘 설정이에요.", 1.0),
                "high": make_option("HIGH DOWNFORCE", [94, 55, 92, 79, 72, 84], [5,2,5], "#ff3158", "큰 윙이 앞쪽을 강하게 눌러 코너 진입은 좋아지지만 공기저항이 커져요.", 1.18)}},
        "rear_wing": {"name": "Rear Wing", "ko": "리어 윙", "icon": "≋", "part": "rearWing",
            "options": {
                "low": make_option("LOW DRAG", [45, 96, 54, 59, 58, 56], [2,5,2], "#27d6ff", "작은 리어 윙은 직선에 유리하지만 빠른 코너에서 차 뒤쪽이 가벼워질 수 있어요.", .78),
                "balanced": make_option("BALANCED", [73, 76, 76, 70, 64, 78], [4,4,4], "#ffb21a", "직선 속도와 뒤쪽 안정성을 고르게 맞췄어요.", 1.0),
                "high": make_option("HIGH DOWNFORCE", [96, 51, 93, 77, 69, 94], [5,2,5], "#ff3158", "큰 리어 윙은 차 뒤를 강하게 눌러 코너에 유리하지만 공기를 더 많이 막아요.", 1.25)}},
        "tyres": {"name": "Tyres", "ko": "타이어", "icon": "◉", "part": "tyres",
            "options": {
                "soft": make_option("SOFT", [66, 80, 92, 98, 91, 71], [4,4,5], "#ed2939", "부드러운 고무가 노면에 잘 달라붙어 그립이 높지만 실제 경기에서는 빨리 닳아요."),
                "medium": make_option("MEDIUM", [63, 81, 80, 82, 82, 82], [4,4,4], "#ffd326", "그립과 내구성의 균형을 잡은 타이어예요."),
                "hard": make_option("HARD", [60, 82, 68, 70, 73, 89], [3,4,3], "#f4f5f6", "단단해 오래 쓰기 좋지만 즉각적인 그립은 낮아요.")}},
        "brakes": {"name": "Brakes", "ko": "브레이크", "icon": "⊙", "part": "brakes",
            "options": {
                "race": make_option("RACE CARBON", [62, 78, 78, 76, 98, 78], [4,4,5], "#ff5038", "뜨거운 상태에서도 큰 마찰력으로 강하게 감속해요."),
                "balanced": make_option("BALANCED", [61, 80, 76, 74, 84, 88], [4,4,4], "#ffb21a", "제동력과 다루기 쉬운 반응을 함께 고려했어요."),
                "light": make_option("LIGHTWEIGHT", [59, 85, 75, 72, 75, 72], [3,5,3], "#27d6ff", "가벼워 반응은 좋지만 반복되는 강한 제동에는 불리해요.")}},
        "suspension": {"name": "Suspension", "ko": "서스펜션", "icon": "⌇", "part": "suspension",
            "options": {
                "stiff": make_option("STIFF", [73, 80, 91, 80, 77, 67], [4,4,5], "#ff3158", "차체 움직임이 작아 빠른 코너 반응이 좋아요. 울퉁불퉁한 노면에서는 불리할 수 있어요."),
                "balanced": make_option("BALANCED", [68, 81, 82, 82, 80, 88], [4,4,4], "#ffb21a", "반응성과 노면을 따라가는 능력의 균형을 맞췄어요."),
                "soft": make_option("SOFT", [62, 78, 72, 88, 83, 90], [3,4,4], "#27d6ff", "바퀴가 노면 굴곡을 잘 따라가지만 방향 전환은 조금 느려져요.")}},
        "floor": {"name": "Floor", "ko": "플로어", "icon": "▰", "part": "floor",
            "options": {
                "venturi": make_option("VENTURI", [98, 72, 94, 80, 67, 82], [5,3,5], "#9a62ff", "차 밑 공기를 빠르게 흘려 압력을 낮추고 차를 아래로 끌어당겨요."),
                "balanced": make_option("BALANCED", [81, 80, 83, 75, 66, 87], [4,4,4], "#ffb21a", "차 높이가 조금 변해도 안정적으로 다운포스를 만들어요."),
                "light": make_option("LIGHTWEIGHT", [60, 89, 68, 67, 62, 69], [3,5,3], "#27d6ff", "다운포스를 일부 포기하고 저항과 무게를 줄인 설정이에요.")}},
        "diffuser": {"name": "Diffuser", "ko": "디퓨저", "icon": "⋙", "part": "diffuser",
            "options": {
                "large": make_option("LARGE EXIT", [93, 67, 90, 76, 65, 87], [5,3,5], "#9a62ff", "차 밑의 빠른 공기를 뒤에서 부드럽게 넓혀 바닥 다운포스를 강화해요.", 1.2),
                "balanced": make_option("BALANCED", [77, 80, 79, 71, 64, 83], [4,4,4], "#ffb21a", "다운포스와 공기 흐름 안정성을 절충했어요.", 1.0),
                "compact": make_option("COMPACT", [55, 91, 63, 61, 61, 68], [3,5,3], "#27d6ff", "크기가 작아 저항은 낮지만 바닥 다운포스가 줄어요.", .78)}},
        "engine": {"name": "Engine", "ko": "엔진", "icon": "⚙", "part": "engine",
            "options": {
                "power": make_option("MAX POWER", [62, 99, 82, 72, 62, 70], [3,5,4], "#ff3158", "출력이 커 직선과 가속에 유리하지만 냉각과 안정성 부담이 커져요."),
                "balanced": make_option("BALANCED", [62, 88, 80, 72, 64, 87], [3,4,4], "#ffb21a", "출력과 신뢰성을 고르게 맞춘 파워 유닛이에요."),
                "efficient": make_option("EFFICIENT", [60, 82, 79, 72, 65, 92], [3,4,4], "#27d6ff", "최고 출력보다 효율과 일정한 성능에 집중했어요.")}},
        "ers": {"name": "ERS", "ko": "에너지 회수", "icon": "ϟ", "part": "ers",
            "options": {
                "attack": make_option("ATTACK", [60, 97, 82, 71, 65, 70], [3,5,4], "#32f59b", "저장한 전기 에너지를 빠르게 사용해 순간 가속을 높여요."),
                "balanced": make_option("BALANCED", [61, 88, 80, 71, 68, 86], [3,4,4], "#ffb21a", "전기 에너지 사용과 회수를 균형 있게 관리해요."),
                "recovery": make_option("RECOVERY", [60, 80, 76, 70, 78, 91], [3,4,4], "#27d6ff", "감속할 때 운동 에너지를 전기로 더 많이 되찾아요.")}},
    }


# -----------------------------------------------------------------------------
# 2. 성능 계산
# -----------------------------------------------------------------------------
def calculate_car_performance(parts, selections):
    """선택한 모든 파츠 점수의 평균으로 이해하기 쉬운 게임 지표를 만듭니다."""
    totals = {metric: 0 for metric in METRICS}
    for part_key, option_key in selections.items():
        option_scores = parts[part_key]["options"][option_key]["scores"]
        for metric, score in zip(METRICS, option_scores):
            totals[metric] += score
    return {metric: round(total / len(selections)) for metric, total in totals.items()}


def calculate_performance_difference(current, previous):
    """직전 설정과 현재 설정을 비교해 상승·하락 방향을 계산합니다."""
    if previous is None:
        return {metric: 0 for metric in METRICS}
    return {metric: current[metric] - previous[metric] for metric in METRICS}


# -----------------------------------------------------------------------------
# 3. 화면 스타일
# -----------------------------------------------------------------------------
def apply_game_css():
    """Streamlit 기본 화면을 단순한 F1 Garage 게임 화면으로 바꿉니다."""
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@500;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap');
    :root{--bg:#080b10;--panel:#10151d;--line:#27313d;--muted:#8290a0;--red:#ff3158;--cyan:#27d6ff}
    .stApp{background:radial-gradient(circle at 52% 17%,#202a36 0,#090c11 47%,#05070a 100%);color:#eef3f8}
    .block-container{max-width:1680px;padding:0 clamp(.75rem,2vw,1.7rem) 2rem}.stApp,button{font-family:'Noto Sans KR',sans-serif}
    h1,h2,h3,.race{font-family:'Oxanium','Noto Sans KR',sans-serif}/* 헤더를 단순히 투명하게 하지 않고 레이아웃 높이까지 제거합니다. */
    [data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],#MainMenu,footer{display:none!important}
    [data-testid="stAppViewContainer"]{width:100%!important}
    [data-testid="stMainBlockContainer"]{max-width:1680px!important;padding:0 clamp(.75rem,2vw,1.7rem) 2rem!important}
    @media(max-width:800px){[data-testid="stMainBlockContainer"]{padding:0 .65rem 1.4rem!important}}
    .garage-head{display:flex;align-items:center;justify-content:space-between;border-top:3px solid var(--red);border-bottom:1px solid var(--line);padding:10px 16px;background:#0c1118;margin-bottom:10px}
    .logo{font:700 25px 'Oxanium';letter-spacing:2px}.logo b{color:var(--red)}.step{font:600 11px 'Oxanium';color:#8794a3;letter-spacing:2px}
    .intro{display:flex;gap:22px;align-items:center;padding:9px 15px;margin-bottom:12px;background:#10161ed9;border:1px solid #27313d;color:#c5cfda;font-size:12px}.intro strong{color:#fff;font:700 14px 'Oxanium'}
    .section-label{font:700 12px 'Oxanium';letter-spacing:2px;color:#9aa7b5;border-bottom:1px solid #27313d;padding-bottom:9px;margin-bottom:8px}
    /* Streamlit 버전별 버튼 클래스보다 높은 우선순위로 모든 상태의 대비를 고정합니다. */
    .stApp div[data-testid="stButton"] button,
    .stApp div[data-testid="stButton"] button[kind],
    .stApp button[data-testid^="stBaseButton"],
    .stApp .stButton button {width:100%!important;min-height:44px!important;text-align:left!important;background-color:#10161e!important;background-image:none!important;border:1px solid #354252!important;color:#f4f7fb!important;border-radius:4px!important;font-weight:700!important;opacity:1!important;-webkit-text-fill-color:#f4f7fb!important;box-shadow:none!important}
    .stApp div[data-testid="stButton"] button *,
    .stApp button[data-testid^="stBaseButton"] *,
    .stApp .stButton button * {color:#f4f7fb!important;-webkit-text-fill-color:#f4f7fb!important;opacity:1!important}
    .stApp div[data-testid="stButton"] button:hover,
    .stApp button[data-testid^="stBaseButton"]:hover {background-color:#172631!important;border-color:#27d6ff!important;color:#fff!important;-webkit-text-fill-color:#fff!important;box-shadow:inset 3px 0 #27d6ff!important}
    .stApp div[data-testid="stButton"] button:active,
    .stApp div[data-testid="stButton"] button:focus,
    .stApp button[data-testid^="stBaseButton"]:active,
    .stApp button[data-testid^="stBaseButton"]:focus {background-color:#392033!important;border-color:#ff3158!important;color:#fff!important;-webkit-text-fill-color:#fff!important;box-shadow:inset 4px 0 #ff3158!important}
    .stApp div[data-testid="stButton"] button:disabled,
    .stApp button[data-testid^="stBaseButton"]:disabled {background-color:#242c35!important;background-image:none!important;border-color:#46515d!important;color:#c4ced8!important;-webkit-text-fill-color:#c4ced8!important;opacity:1!important}
    .stApp div[data-testid="stButton"] button:disabled * {color:#c4ced8!important;-webkit-text-fill-color:#c4ced8!important;opacity:1!important}
    .part-info-box{margin:-2px 0 9px;padding:11px;background:#080d13;border:1px solid #344353;border-left:3px solid #27d6ff;color:#cbd6df;font-size:11px;line-height:1.55}.part-info-box b{font:700 12px 'Oxanium';color:#fff}
    .active-part{border-left:3px solid var(--red);background:#181f29;padding:10px 12px;margin:4px 0 10px;font:700 13px 'Oxanium';color:#fff}
    .perf{position:relative;padding:11px 10px;margin:8px 0;background:#0d131a;border:1px solid #26313d;border-radius:3px}.perf-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}.perf-name{font:700 13px 'Oxanium';color:#fff;letter-spacing:.5px}.perf-help{font-size:10px;color:#8c9aaa;margin-top:3px;line-height:1.35}.perf-num{font:700 17px 'Oxanium';white-space:nowrap}.track{height:13px;background:#222b35;margin-top:9px;overflow:hidden;border:1px solid #33404d;transform:skewX(-12deg)}.fill{height:100%;background:linear-gradient(90deg,#27d6ff,#7b61ff);box-shadow:0 0 12px #27d6ff77;transition:width .35s ease}.perf:nth-of-type(even) .fill{background:linear-gradient(90deg,#20d7c7,#27d6ff)}
    /* title 속성 대신 순수 :hover 툴팁을 사용하므로 포인터가 벗어나면 즉시 사라집니다. */
    .hover-tip{position:relative;display:inline-block;cursor:help}.hover-tip .tip-box{visibility:hidden;opacity:0;pointer-events:none;position:absolute;z-index:9999;left:0;top:calc(100% + 6px);width:250px;padding:9px 10px;background:#05080c;color:#edf4fa;border:1px solid #415162;border-top:2px solid #27d6ff;box-shadow:0 10px 25px #000b;font-size:10px;line-height:1.5;transition:opacity .08s}.hover-tip:hover .tip-box{visibility:visible;opacity:1}.hover-tip:not(:hover) .tip-box{visibility:hidden;opacity:0}

    .up{color:#37eca0}.down{color:#ff5872}.same{color:#6e7b89}.why{margin:12px 0;padding:11px;border-left:3px solid #27d6ff;background:#0c131b;color:#c9d4de;font-size:12px;line-height:1.55}
    .option-card{border:1px solid #2a3542;background:#0d1219;padding:10px;margin:7px 0}.option-title{font:700 13px 'Oxanium';color:#fff}.stars{color:#ffc52e;letter-spacing:1px;font-size:12px}.option-mini{font-size:10px;color:#8491a0;margin-top:6px}
    .selected-option{border-color:#ff3158;box-shadow:inset 3px 0 #ff3158}.footnote{color:#718090;font-size:10px;margin-top:12px;line-height:1.5}
    .tuning-bay{margin-top:12px;padding:15px;border:1px solid #2b3744;background:linear-gradient(145deg,#101720,#080c11);box-shadow:0 16px 45px #0007}.option-visual{height:126px;border:1px solid #2d3946;background:radial-gradient(circle,#25323d,#0a0e13 72%);display:flex;align-items:center;justify-content:center;margin-bottom:7px}.option-name{text-align:center;font:700 12px 'Oxanium';color:#fff;min-height:30px}.option-desc{min-height:48px;color:#94a1af;font-size:10px;line-height:1.45}.installed{color:#36eca0;text-align:center;font:700 11px 'Oxanium';padding:8px;border:1px solid #2a6a50;background:#10241c}.part-svg{width:96%;height:112px}.part-svg .main{fill:var(--pc);stroke:#d9f6ff;stroke-width:1}.part-svg .dark{fill:#080a0d;stroke:var(--pc);stroke-width:3}.part-svg .line{stroke:var(--pc);stroke-width:6;stroke-linecap:round}.part-svg .thin{stroke:#dbe8f2;stroke-width:2;fill:none}.center-note{color:#8795a4;font-size:11px;line-height:1.55;margin:6px 0 12px}.setup-title{font:700 18px 'Oxanium';color:#fff}.setup-sub{font-size:12px;color:#9aa7b5;margin:3px 0 12px}.option-tip{cursor:help;position:relative}.option-tip .tip-box{visibility:hidden;opacity:0;pointer-events:none;position:absolute;z-index:50;left:8px;right:8px;bottom:8px;padding:7px;background:#05080ced;color:#fff;border:1px solid #27d6ff;font-size:10px;line-height:1.45;transition:opacity .08s}.option-tip:hover .tip-box{visibility:visible;opacity:1}.option-tip:not(:hover) .tip-box{visibility:hidden;opacity:0}
    .part-role{padding:10px 12px;margin:0 0 11px;background:#0c131b;border-left:3px solid var(--cyan);color:#d3dde6;font-size:12px;line-height:1.55}.part-role b{font:700 15px 'Oxanium';color:#fff}.part-role span{color:#91a0af}
    .preview-shell{border:1px solid #2b3744;background:linear-gradient(135deg,#101821,#080c11);margin-top:10px;box-shadow:0 12px 35px #0006}.preview-head{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid #283441}.preview-title{font:700 12px 'Oxanium';letter-spacing:2px}.preview-current{font:700 12px 'Oxanium';color:#ffbd32}.proscons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.pros,.cons{padding:10px;background:#0c1218;border:1px solid #26313d;font-size:11px;line-height:1.7}.pros b{color:#37eca0}.cons b{color:#ff7387}.change-table{margin:10px 0;border:1px solid #293542;background:#0b1016}.change-row{display:grid;grid-template-columns:1.35fr .8fr .8fr .65fr;padding:7px 9px;border-bottom:1px solid #202a34;font:600 11px 'Oxanium'}.change-row:last-child{border-bottom:0}.result-line{padding:12px;background:linear-gradient(90deg,#17251f,#10161d);border:1px solid #2b5947;color:#d8f7e9;font-size:12px;line-height:1.6}.flow-arrow{text-align:center;color:#27d6ff;font:700 18px 'Oxanium';margin:-3px 0 1px}
    @media(max-width:1000px){.intro{flex-wrap:wrap}.block-container{padding:.6rem}.garage-head{position:static}}
    </style>""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. 실제 WebGL 3D 차량
# -----------------------------------------------------------------------------
def build_3d_html(parts, selections, active_part):
    """Three.js로 회전·확대·레이캐스팅이 가능한 3D F1 차량을 만듭니다.

    차량은 평면 이미지가 아니라 여러 개의 곡면 3D 메시로 구성됩니다. 각 메시에는
    실제 파츠 이름을 저장해 두어 마우스 오버와 클릭을 구별할 수 있습니다.
    """
    visual = {}
    for key, selected in selections.items():
        option = parts[key]["options"][selected]
        visual[parts[key]["part"]] = {"color": option["color"], "shape": option["shape"], "key": key, "variant": list(parts[key]["options"]).index(selected)}
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>
    *{{box-sizing:border-box}}html,body,#app{{margin:0;width:100%;height:100%;overflow:hidden;background:#080b10;font-family:Arial,sans-serif}}
    #app{{background:radial-gradient(ellipse at 50% 42%,#273440 0,#10161e 49%,#07090d 80%)}}
    canvas{{display:block}}#hint{{position:absolute;left:18px;top:16px;color:#cbd5df;font-size:12px;background:#070a0ebd;border:1px solid #34404d;padding:8px 11px;pointer-events:none}}
    #badge{{position:absolute;right:18px;top:16px;color:#7f8c9a;font:11px monospace;letter-spacing:1px}}
    #info{{position:absolute;left:50%;bottom:18px;transform:translateX(-50%);min-width:300px;text-align:center;background:#070a0edb;border:1px solid #354251;border-top:2px solid #27d6ff;color:#fff;padding:9px 14px;opacity:0;transition:.15s;pointer-events:none}}
    #info b{{font-size:13px;letter-spacing:1px}}#info span{{display:block;color:#aab5c1;font-size:10px;margin-top:3px}}
    .label{{color:#dce6ef;position:relative;background:#080b10d9;border:1px solid #3b4856;padding:4px 7px;font:bold 9px Arial;letter-spacing:.8px;white-space:nowrap;pointer-events:none}}
    .label:after{{content:'';position:absolute;width:28px;height:1px;background:#708090;left:50%;top:100%;transform:rotate(55deg);transform-origin:left}}.label.active{{color:#fff;background:#35101c;border:2px solid #ff3158;box-shadow:0 0 8px #ff3158,0 0 24px #ff3158,0 0 42px #27d6ff;font-size:11px}}
    </style><script type='importmap'>{{"imports":{{"three":"https://unpkg.com/three@0.164.1/build/three.module.js","three/addons/":"https://unpkg.com/three@0.164.1/examples/jsm/"}}}}</script></head>
    <body><div id='app'></div><div id='hint'>DRAG 회전 · WHEEL 확대/축소 · PART 클릭</div><div id='badge'>REAL-TIME 3D / WEBGL</div><div id='info'></div>
    <script type='module'>
    import * as THREE from 'three';
    import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
    import {{CSS2DRenderer,CSS2DObject}} from 'three/addons/renderers/CSS2DRenderer.js';
    const cfg={json.dumps(visual, ensure_ascii=False)}, active='{active_part}';
    const app=document.getElementById('app'), scene=new THREE.Scene();
    scene.fog=new THREE.Fog(0x080b10,16,34);
    const camera=new THREE.PerspectiveCamera(38,app.clientWidth/app.clientHeight,.1,100);camera.position.set(10,6.5,12);
    const renderer=new THREE.WebGLRenderer({{antialias:true,alpha:true}});renderer.setSize(app.clientWidth,app.clientHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.outputColorSpace=THREE.SRGBColorSpace;app.appendChild(renderer.domElement);
    const labels=new CSS2DRenderer();labels.setSize(app.clientWidth,app.clientHeight);labels.domElement.style.cssText='position:absolute;inset:0;pointer-events:none';app.appendChild(labels.domElement);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=7;controls.maxDistance=24;controls.target.set(0,.4,0);controls.maxPolarAngle=Math.PI*.78;
    scene.add(new THREE.HemisphereLight(0xb9dcff,0x111216,2.0));const key=new THREE.DirectionalLight(0xffffff,3.4);key.position.set(6,10,5);key.castShadow=true;scene.add(key);const rim=new THREE.PointLight(0xff3158,32,18);rim.position.set(-6,3,-5);scene.add(rim);
    const platform=new THREE.Mesh(new THREE.CylinderGeometry(7.1,7.5,.25,96),new THREE.MeshStandardMaterial({{color:0x11171e,metalness:.75,roughness:.36}}));platform.position.y=-1.42;platform.receiveShadow=true;scene.add(platform);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(6.65,.025,8,120),new THREE.MeshBasicMaterial({{color:0x27d6ff}}));ring.rotation.x=Math.PI/2;ring.position.y=-1.27;scene.add(ring);
    const car=new THREE.Group();car.rotation.y=-Math.PI/2;scene.add(car);const pickable=[], partGroups={{}};
    const mat=(color,metal=.45,rough=.32)=>new THREE.MeshStandardMaterial({{color,metalness:metal,roughness:rough}});
    function group(name){{const g=new THREE.Group();g.userData.part=name;partGroups[name]=g;car.add(g);return g}}
    function mesh(g,geo,material,pos=[0,0,0],rot=[0,0,0],scale=[1,1,1]){{const m=new THREE.Mesh(geo,material);m.position.set(...pos);m.rotation.set(...rot);m.scale.set(...scale);m.castShadow=true;m.receiveShadow=true;m.userData.part=g.userData.part;g.add(m);pickable.push(m);return m}}
    function capsule(length,radius){{return new THREE.CapsuleGeometry(radius,length,8,20)}}
    // 두 지점 사이에 실제 두께가 있는 서스펜션 암을 만드는 도우미입니다.
    function rodBetween(g,a,b,radius,material){{const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),mid=start.clone().add(end).multiplyScalar(.5),length=start.distanceTo(end);const rod=mesh(g,new THREE.CylinderGeometry(radius,radius,length,12),material,[mid.x,mid.y,mid.z]);rod.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),end.clone().sub(start).normalize());return rod}}
    // 매끈한 곡면 차체: 길쭉한 캡슐과 유선형 노즈를 겹쳐 실제 포뮬러카 실루엣을 만듭니다.
    const body=group('body'), red=mat(0xd91536,.72,.24);mesh(body,capsule(3.1,.65),red,[0,.05,0],[Math.PI/2,0,0],[1,1,1]);mesh(body,new THREE.ConeGeometry(.62,4.5,32),red,[0,-.08,3.35],[Math.PI/2,0,0],[1,.55,1]);
    mesh(body,new THREE.SphereGeometry(1.0,32,18),red,[0,.05,-1.35],[0,0,0],[1.35,.78,1.75]);
    // 콕핏과 Halo
    const cockpit=group('cockpit');mesh(cockpit,new THREE.SphereGeometry(.64,28,16,0,Math.PI*2,0,Math.PI*.62),mat(0x111820,.15,.16),[0,.65,-.25],[0,0,0],[1,.62,1.45]);
    const haloMat=mat(0x242c35,.75,.2);mesh(cockpit,new THREE.TorusGeometry(.62,.055,10,36,Math.PI*1.25),haloMat,[0,1.08,-.05],[Math.PI/2,0,.39]);mesh(cockpit,new THREE.CylinderGeometry(.06,.06,.72,12),haloMat,[0,.82,.35],[0,0,0]);
    // 사이드포드: 앞은 넓고 뒤로 갈수록 좁아지는 곡면
    const side=group('sidepods');[-1,1].forEach(s=>{{mesh(side,capsule(1.35,.52),red,[s*1.02,-.05,-.65],[Math.PI/2,0,0],[1,.72,1.25]);mesh(side,new THREE.ConeGeometry(.48,2.2,24),red,[s*.94,-.08,-2.0],[-Math.PI/2,0,0],[.75,1,.9])}});
    // 타이어는 실제 회전축을 가진 두꺼운 Torus 3D 메시입니다.
    const tyres=group('tyres'), tv=cfg.tyres.variant, tyreMat=mat(0x08090b,.05,.58+tv*.1), stripe=mat(cfg.tyres.color,.15,.38);[[-1.55,1.95,.56], [1.55,1.95,.56],[-1.72,-2.15,.72],[1.72,-2.15,.72]].forEach(p=>{{const [x,z,r]=p;mesh(tyres,new THREE.TorusGeometry(r,r*(.43-tv*.045),18+tv*5,42),tyreMat,[x,-.35,z],[0,Math.PI/2,0]);mesh(tyres,new THREE.TorusGeometry(r*.99,.035,8,48),stripe,[x,-.35,z],[0,Math.PI/2,0])}});
    // 프론트 윙: 날개 단면을 가진 여러 곡선형 엘리먼트
    const fw=group('frontWing'), fwM=mat(cfg.frontWing.color,.65,.22), f=cfg.frontWing.shape;Array.from({{length:2+cfg.frontWing.variant}},(_,i)=>-.18+i*.22).forEach((y,i)=>mesh(fw,new THREE.CapsuleGeometry(.11,3.2*f,6,20),fwM,[0,-.58+y,3.62-i*.25],[0,0,Math.PI/2],[1,1,1]));[-1,1].forEach(s=>mesh(fw,new THREE.ExtrudeGeometry(new THREE.Shape().moveTo(0,0).lineTo(.44,.12).lineTo(.28,.65).lineTo(0,.52),{{depth:.06,bevelEnabled:true,bevelSize:.025,bevelThickness:.025}}),fwM,[s*1.75*f,-.88,3.35],[0,s<0?0:Math.PI,0]));
    // 리어 윙: 선택에 따라 폭과 높이가 실제로 변합니다.
    const rw=group('rearWing'), rwM=mat(cfg.rearWing.color,.68,.2), r=cfg.rearWing.shape;mesh(rw,new THREE.CapsuleGeometry(.16,2.55*r,6,20),rwM,[0,1.05,-3.24],[0,0,Math.PI/2]);Array.from({{length:1+cfg.rearWing.variant}},(_,i)=>mesh(rw,new THREE.CapsuleGeometry(.09,2.35*r,6,20),rwM,[0,.72-i*.22,-3.0+i*.08],[0,0,Math.PI/2]));[-1,1].forEach(s=>mesh(rw,new THREE.CylinderGeometry(.045,.06,1.3,10),rwM,[s*.92*r,.35,-3.05],[0,0,0]));
    const floor=group('floor');const floorShape=new THREE.Shape().moveTo(-1.25,-2.7).lineTo(-1.25,1.4).lineTo(-.8,2.8).lineTo(.8,2.8).lineTo(1.25,1.4).lineTo(1.25,-2.7).lineTo(-1.25,-2.7);mesh(floor,new THREE.ExtrudeGeometry(floorShape,{{depth:.09,bevelEnabled:true,bevelSize:.04,bevelThickness:.03}}),mat(cfg.floor.color,.7,.25),[0,-.92,0],[Math.PI/2,0,0]);
    const diffuser=group('diffuser'), dm=mat(cfg.diffuser.color,.72,.22);[-.72,-.24,.24,.72].forEach(x=>mesh(diffuser,new THREE.BoxGeometry(.055,.7,1.35*cfg.diffuser.shape),dm,[x,-.62,-3.08],[.38,0,0]));
    const brakes=group('brakes'), bv=cfg.brakes.variant;[[-1.55,1.95],[1.55,1.95],[-1.72,-2.15],[1.72,-2.15]].forEach(p=>mesh(brakes,new THREE.CylinderGeometry(.38-bv*.055,.38-bv*.055,.07,24+bv*8),mat(cfg.brakes.color,.8,.28),[p[0],-.35,p[1]],[0,0,Math.PI/2]));
    // 앞·뒤 바퀴 허브와 차체를 위/아래 위시본 및 푸시로드로 연결합니다.
    const suspension=group('suspension'), sv=cfg.suspension.variant, suspensionMat=mat(cfg.suspension.color,.82,.18), armRadius=.055-sv*.007;
    [[1.95,1.55],[-2.15,1.72]].forEach(([z,wheelX])=>[-1,1].forEach(side=>{{
      const hub=[side*wheelX,-.34,z], innerX=side*.62;
      rodBetween(suspension,[innerX,-.28,z-.48],hub,armRadius,suspensionMat);
      rodBetween(suspension,[innerX,-.28,z+.48],hub,armRadius,suspensionMat);
      rodBetween(suspension,[innerX,.25,z-.30],hub,armRadius*.9,suspensionMat);
      rodBetween(suspension,[innerX,.25,z+.30],hub,armRadius*.9,suspensionMat);
      rodBetween(suspension,[side*.48,.48,z],hub,armRadius*.82,suspensionMat);
      mesh(suspension,new THREE.SphereGeometry(.12,16,10),suspensionMat,hub);
    }}));
    const engine=group('engine'), ev=cfg.engine.variant;mesh(engine,new THREE.CapsuleGeometry(.50-ev*.06,1.45-ev*.12,8,18),mat(cfg.engine.color,.65,.24),[0,.22,-1.75],[Math.PI/2,0,0]);
    const ers=group('ers'), erv=cfg.ers.variant;mesh(ers,new THREE.TorusGeometry(.30-erv*.035,.075-erv*.01,10,28+erv*8),mat(cfg.ers.color,.5,.15),[0,.68,-1.38],[Math.PI/2,0,0]);
    const descriptions={{frontWing:'앞 타이어를 눌러 코너 진입을 돕는 공기역학 부품',rearWing:'차 뒤를 눌러 코너 안정성을 만드는 부품',tyres:'트랙과 직접 맞닿아 그립을 만드는 부품',brakes:'마찰로 차량의 속도를 줄이는 부품',suspension:'바퀴가 노면을 따라가도록 돕는 부품',floor:'차 밑 공기로 다운포스를 만드는 바닥',diffuser:'바닥 공기를 뒤에서 부드럽게 확산하는 부품',engine:'차량을 앞으로 움직이는 동력을 만드는 장치',ers:'에너지를 저장했다가 가속에 사용하는 장치'}};
    const names={{frontWing:'FRONT WING',rearWing:'REAR WING',tyres:'TYRES',brakes:'BRAKES',suspension:'SUSPENSION',floor:'FLOOR',diffuser:'DIFFUSER',engine:'ENGINE',ers:'ERS',cockpit:'COCKPIT',sidepods:'SIDEPOD'}};
    const labelPos={{frontWing:[0,.15,3.65],rearWing:[0,1.65,-3.15],tyres:[-2.2,.4,1.9],brakes:[2.15,.2,1.95],suspension:[2.0,.72,.9],floor:[1.6,-.6,.1],diffuser:[1.4,.1,-3],engine:[0,1.2,-1.7],ers:[.8,1,-1.2],cockpit:[0,1.7,.1],sidepods:[1.65,.55,-.45]}};
    // 라벨 앵커는 발광 파츠 그룹과 분리합니다. 차량 회전만 따라가며 Glow/Pulse의 영향을 받지 않습니다.
    const labelAnchors=new THREE.Group();car.add(labelAnchors);
    Object.entries(labelPos).forEach(([n,p])=>{{const anchor=new THREE.Object3D();anchor.position.set(...p);labelAnchors.add(anchor);const d=document.createElement('div');d.className='label'+(cfg[n]?.key===active?' active':'');d.textContent=names[n];const l=new CSS2DObject(d);l.position.set(0,0,0);anchor.add(l)}});
    // 왼쪽에서 선택한 파츠는 차량에서도 계속 빛나도록 해 프리뷰와 위치를 연결합니다.
    const active3d=Object.keys(cfg).find(n=>cfg[n]?.key===active), activeGroup=partGroups[active3d];
    // 선택하지 않은 부분은 살짝 어둡게 하고, 선택 파츠에는 강한 발광·와이어 박스·점광원을 더합니다.
    Object.entries(partGroups).forEach(([name,g])=>g.traverse(o=>{{if(o.isMesh){{o.material=o.material.clone();if(g!==activeGroup){{o.material.color.multiplyScalar(.62);o.material.opacity=.82;o.material.transparent=true}}}}}}));
    let activeBox=null, activeLight=null;
    if(activeGroup){{activeGroup.traverse(o=>{{if(o.isMesh){{o.material.emissive?.setHex(0x27d6ff);o.material.emissiveIntensity=2.8}}}});activeBox=new THREE.BoxHelper(activeGroup,0x42e8ff);activeBox.material.transparent=true;activeBox.material.opacity=.9;car.add(activeBox);const b=new THREE.Box3().setFromObject(activeGroup),c=new THREE.Vector3();b.getCenter(c);activeLight=new THREE.PointLight(0x27d6ff,42,7);activeLight.position.copy(c);car.add(activeLight)}}
    const ray=new THREE.Raycaster(),mouse=new THREE.Vector2(),info=document.getElementById('info');let hovered=null;
    function hit(e){{const rect=renderer.domElement.getBoundingClientRect();mouse.x=((e.clientX-rect.left)/rect.width)*2-1;mouse.y=-((e.clientY-rect.top)/rect.height)*2+1;ray.setFromCamera(mouse,camera);return ray.intersectObjects(pickable,false)[0]?.object||null}}
    renderer.domElement.addEventListener('pointermove',e=>{{const obj=hit(e);pickable.forEach(m=>{{m.material.emissive?.setHex(m.parent===activeGroup?0x27d6ff:0);m.material.emissiveIntensity=m.parent===activeGroup?2.8:1}});if(obj){{obj.material.emissive?.setHex(obj.parent===activeGroup?0x66ffff:0x243344);hovered=obj.userData.part;renderer.domElement.style.cursor='pointer';info.style.opacity=1;info.innerHTML='<b>'+names[hovered]+'</b><span>'+(descriptions[hovered]||'클릭하면 설정 패널이 열립니다')+'</span>'}}else{{hovered=null;renderer.domElement.style.cursor='grab';info.style.opacity=0}}}});
    renderer.domElement.addEventListener('click',()=>{{const key=cfg[hovered]?.key;if(key){{const u=new URL(window.parent.location.href);u.searchParams.set('part',key);window.parent.location.href=u.toString()}}}});
    window.addEventListener('resize',()=>{{camera.aspect=app.clientWidth/app.clientHeight;camera.updateProjectionMatrix();renderer.setSize(app.clientWidth,app.clientHeight);labels.setSize(app.clientWidth,app.clientHeight)}});
    function animate(t){{requestAnimationFrame(animate);const pulse=1+Math.sin(t*.004)*.22;if(activeBox)activeBox.material.opacity=.62+Math.sin(t*.004)*.28;if(activeLight)activeLight.intensity=38*pulse;if(activeGroup)activeGroup.traverse(o=>{{if(o.isMesh&&o.material.emissive)o.material.emissiveIntensity=2.5*pulse}});controls.update();renderer.render(scene,camera);labels.render(scene,camera)}}animate(0);
    </script></body></html>"""


def render_3d_car(parts, selections, active_part):
    """중앙의 가장 큰 영역에 실제 WebGL 3D 뷰어를 삽입합니다."""
    components.html(build_3d_html(parts, selections, active_part), height=540, scrolling=False)



def build_part_preview_html(parts, selections, active_part):
    """선택한 파츠만 확대해 보여 주는 별도의 회전 가능한 3D 프리뷰를 만듭니다."""
    data = parts[active_part]
    option = data["options"][selections[active_part]]
    cfg = json.dumps({"part": active_part, "color": option["color"], "shape": option["shape"], "variant": list(data["options"]).index(selections[active_part])})
    return f"""<!doctype html><html><head><style>*{{box-sizing:border-box}}html,body,#p{{margin:0;width:100%;height:100%;overflow:hidden;background:radial-gradient(circle,#24313d,#090d12 70%)}}canvas{{display:block}}#tag{{position:absolute;left:14px;bottom:10px;color:#8d9baa;font:10px Arial;letter-spacing:1px}}</style><script type='importmap'>{{"imports":{{"three":"https://unpkg.com/three@0.164.1/build/three.module.js","three/addons/":"https://unpkg.com/three@0.164.1/examples/jsm/"}}}}</script></head><body><div id='p'></div><div id='tag'>DRAG TO INSPECT · 3D PART MODEL</div><script type='module'>
    import * as THREE from 'three';import {{OrbitControls}} from 'three/addons/controls/OrbitControls.js';
    const cfg={cfg},root=document.getElementById('p'),scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(36,root.clientWidth/root.clientHeight,.1,50);camera.position.set(4,2.6,5.5);
    const renderer=new THREE.WebGLRenderer({{antialias:true,alpha:true}});renderer.setSize(root.clientWidth,root.clientHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;root.appendChild(renderer.domElement);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.autoRotate=true;controls.autoRotateSpeed=.8;controls.minDistance=3.5;controls.maxDistance=10;
    scene.add(new THREE.HemisphereLight(0xcce6ff,0x111111,2.7));const light=new THREE.DirectionalLight(0xffffff,4);light.position.set(4,6,3);scene.add(light);const rim=new THREE.PointLight(0x27d6ff,35,15);rim.position.set(-4,2,-2);scene.add(rim);
    const g=new THREE.Group();scene.add(g);const m=new THREE.MeshStandardMaterial({{color:cfg.color,metalness:.7,roughness:.22,emissive:0x101820}}),dark=new THREE.MeshStandardMaterial({{color:0x090b0e,roughness:.65}});
    function add(geo,pos=[0,0,0],rot=[0,0,0],mat=m){{const o=new THREE.Mesh(geo,mat);o.position.set(...pos);o.rotation.set(...rot);o.castShadow=true;g.add(o)}}
    const cap=(r,l)=>new THREE.CapsuleGeometry(r,l,8,28),s=cfg.shape;
    const v=cfg.variant;
    if(cfg.part==='front_wing'){{Array.from({{length:2+v}},(_,i)=>add(cap(.11+v*.015,(3.0+v*.38)*s),[0,-.25+i*.25,-i*.28],[i*.08,0,Math.PI/2]));[-1,1].forEach(x=>add(new THREE.BoxGeometry(.08,.55+v*.15,.62+v*.1),[x*(1.6+v*.18)*s,-.05,.02]))}}
    else if(cfg.part==='rear_wing'){{Array.from({{length:1+v}},(_,i)=>add(cap(.13+v*.02,(2.5+v*.32)*s),[0,.55-i*.4,-i*.16],[i*.1,0,Math.PI/2]));[-1,1].forEach(x=>add(new THREE.BoxGeometry(.1,1.1+v*.25,.18),[x*(1.0+v*.13)*s,-.25,.1]))}}
    else if(cfg.part==='tyres'){{add(new THREE.TorusGeometry(1.05,.50-v*.07,18+v*8,64),[0,0,0],[0,Math.PI/2,0],dark);add(new THREE.TorusGeometry(1.04,.075-v*.012,10,64),[0,0,0],[0,Math.PI/2,0],m);for(let i=0;i<4+v*3;i++)add(new THREE.BoxGeometry(.05,.12,.35),[0,Math.sin(i/(4+v*3)*6.28)*.82,Math.cos(i/(4+v*3)*6.28)*.82],[i,0,0],m)}}
    else if(cfg.part==='brakes'){{add(new THREE.CylinderGeometry(1-v*.12,1-v*.12,.18,36+v*12),[0,0,0],[0,0,Math.PI/2]);add(new THREE.BoxGeometry(.32+v*.1,1.0-v*.1,.45),[0,.25,.72]);for(let i=0;i<v*6;i++)add(new THREE.CylinderGeometry(.035,.035,.25,8),[0,Math.sin(i/6*6.28)*.62,Math.cos(i/6*6.28)*.62],[0,0,Math.PI/2],dark)}}
    else if(cfg.part==='suspension'){{Array.from({{length:2+v}},(_,i)=>-.7+i*(1.4/(1+v))).forEach((x,i)=>add(new THREE.CylinderGeometry(.085-v*.02,.085-v*.02,3.0+v*.15,12),[x,0,0],[0,0,(i-(1+v)/2)*.35]));add(new THREE.CylinderGeometry(.42-v*.06,.42-v*.06,2.1,24),[0,0,0])}}
    else if(cfg.part==='floor'){{const w=1.35+(.5-v*.2), sh=new THREE.Shape().moveTo(-w,-2).lineTo(-1.1-v*.12,2).lineTo(1.1+v*.12,2).lineTo(w,-2).lineTo(-w,-2);add(new THREE.ExtrudeGeometry(sh,{{depth:.10+v*.04,bevelEnabled:true,bevelSize:.05,bevelThickness:.04}}),[0,0,0],[Math.PI/2,0,0]);for(let i=0;i<v+1;i++)add(new THREE.BoxGeometry(.06,.25,3.2),[-.55+i*1.1,-.18,0])}}
    else if(cfg.part==='diffuser'){{Array.from({{length:3+v*2}},(_,i)=>-1.2+i*(2.4/(2+v*2))).forEach(x=>add(new THREE.BoxGeometry(.08,.7+v*.25,(1.7+v*.4)*s),[x,0,0],[.22+v*.12,0,0]));add(new THREE.BoxGeometry(3.1,.12,(1.7+v*.35)*s),[0,-.55,0],[.15+v*.08,0,0])}}
    else if(cfg.part==='engine'){{add(cap(.55+(.18-v*.08),2.0+(.5-v*.2)),[0,0,0],[Math.PI/2,0,0]);[-1,1].forEach(x=>add(new THREE.CylinderGeometry(.24+(.12-v*.03),.4-v*.04,1.2+v*.15,20+v*6),[x*(.72+v*.08),0,0],[Math.PI/2,0,0]))}}
    else{{Array.from({{length:1+v}},(_,i)=>add(new THREE.TorusGeometry(1.05-i*.25,.20-v*.025,18,48),[0,0,i*.18]));add(new THREE.CylinderGeometry(.16+.03*v,.16+.03*v,2.2+v*.2,18),[0,0,0],[0,0,Math.PI/2])}}
    const ground=new THREE.Mesh(new THREE.CircleGeometry(4,64),new THREE.MeshStandardMaterial({{color:0x10161c,metalness:.5,roughness:.5}}));ground.rotation.x=-Math.PI/2;ground.position.y=-1.5;scene.add(ground);
    function tick(){{requestAnimationFrame(tick);controls.update();renderer.render(scene,camera)}}tick();window.addEventListener('resize',()=>{{camera.aspect=root.clientWidth/root.clientHeight;camera.updateProjectionMatrix();renderer.setSize(root.clientWidth,root.clientHeight)}});
    </script></body></html>"""


def render_part_description(active_part, parts):
    """파츠가 무슨 일을 하는지 선택 즉시 한 문장과 툴팁으로 알려 줍니다."""
    short, detail = PART_HELP[active_part]
    name = parts[active_part]["name"].upper()
    st.markdown(f"<div class='part-role'><b>{name}</b><br>{html.escape(short)}</div>", unsafe_allow_html=True)


def render_selected_part_preview(parts, selections, active_part):
    """차량 아래에서 현재 장착한 파츠를 큰 회전형 3D 모델로 보여 줍니다."""
    data = parts[active_part]
    option = data["options"][selections[active_part]]
    st.markdown(f"<div class='flow-arrow'>↓ 차량에서 선택한 위치 ↓</div><div class='preview-shell'><div class='preview-head'><span class='preview-title'>SELECTED PART · {data['name'].upper()}</span><span class='preview-current'>장착 중 · {option['label']}</span></div></div>", unsafe_allow_html=True)
    components.html(build_part_preview_html(parts, selections, active_part), height=255, scrolling=False)
    render_part_description(active_part, parts)


def calculate_option_difference(parts, active_part, option_key):
    """같은 파츠의 균형형 옵션과 비교해 해당 옵션만의 실제 장단점을 계산합니다."""
    options = parts[active_part]["options"]
    keys = list(options)
    baseline_key = keys[1] if len(keys) > 1 else keys[0]
    selected_scores = options[option_key]["scores"]
    baseline_scores = options[baseline_key]["scores"]
    return {metric: selected - baseline for metric, selected, baseline in zip(METRICS, selected_scores, baseline_scores)}


def generate_part_advantages(option_difference):
    """균형형보다 좋아진 실제 지표만 장점으로 표시합니다."""
    result = [f"✓ {metric} ↑ {value}" for metric, value in option_difference.items() if value > 0]
    return result[:3] or ["✓ 여러 성능의 균형 유지"]


def generate_part_disadvantages(option_difference):
    """균형형보다 낮아진 실제 지표만 단점으로 표시합니다."""
    result = [f"△ {metric} ↓ {abs(value)}" for metric, value in option_difference.items() if value < 0]
    return result[:3] or ["△ 뚜렷한 성능 손실 없음"]

def generate_change_explanation(changed_part, parts, selections, differences):
    """실제 상승·하락 조합을 읽어 주행 결과를 동적으로 한 문장으로 만듭니다."""
    if not changed_part:
        return "파츠를 장착하면 실제 주행에서 무엇이 달라지는지 알려드려요."
    if differences.get("그립", 0) > 0:
        return "그립이 증가해 타이어가 트랙을 더 잘 붙잡으므로 코너와 제동 상황에서 차량을 제어하기 쉬워졌어요."
    if differences.get("다운포스", 0) > 0 and differences.get("최고속도", 0) < 0:
        return "다운포스가 증가해 코너에서는 더 안정적으로 달릴 수 있지만, 공기저항도 커져 직선 최고속도는 조금 줄어들 수 있어요."
    if differences.get("최고속도", 0) > 0 and differences.get("다운포스", 0) < 0:
        return "공기저항을 줄이는 방향이라 직선에서는 더 빠르지만, 다운포스가 감소해 코너에서는 조금 불안정할 수 있어요."
    if differences.get("제동", 0) > 0:
        return "제동 성능이 좋아져 더 늦게 브레이크를 밟고도 원하는 코너 진입 속도로 줄이기 쉬워졌어요."
    option = parts[changed_part]["options"][selections[changed_part]]
    return option["explanation"]

def render_change_summary(current, previous, differences, changed_part, parts, selections):
    """변경 전 숫자 → 변경 후 숫자 → 주행 결과를 한 흐름으로 보여 줍니다."""
    if not changed_part or previous is None:
        return
    rows = ""
    for metric in METRICS:
        d = differences[metric]
        if d:
            klass, arrow = ("up", "↑") if d > 0 else ("down", "↓")
            rows += f"<div class='change-row'><span>{METRIC_ENGLISH[metric]}</span><span>{previous[metric]}</span><span>{current[metric]}</span><span class='{klass}'>{arrow}{abs(d)}</span></div>"
    explanation = generate_change_explanation(changed_part, parts, selections, differences)
    st.markdown(f"<div class='section-label'>{parts[changed_part]['name'].upper()} 변경 결과</div><div class='change-table'><div class='change-row'><span>성능</span><span>BEFORE</span><span>AFTER</span><span>CHANGE</span></div>{rows}</div><div class='result-line'>💡 <b>어떤 변화가 생겼나요?</b><br>{html.escape(explanation)}</div>", unsafe_allow_html=True)


def render_advantages_and_disadvantages(parts, active_part, option_key):
    """현재 고른 후보 옵션을 균형형과 비교해 실제 장점과 단점을 표시합니다."""
    difference = calculate_option_difference(parts, active_part, option_key)
    pros = "<br>".join(generate_part_advantages(difference))
    cons = "<br>".join(generate_part_disadvantages(difference))
    st.markdown(f"<div class='proscons'><div class='pros'><b>장점</b><br>{pros}</div><div class='cons'><b>단점</b><br>{cons}</div></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5. 게임 조작 패널
# -----------------------------------------------------------------------------
def render_help_message():
    """처음 온 사용자가 3초 안에 조작법을 이해하도록 짧게 안내합니다."""
    st.markdown("""<div class='intro'><strong>🏎 MY F1 CAR</strong><span>① 차량을 드래그해서 360°로 살펴보세요</span><span>② 부품을 클릭해 설정을 바꾸세요</span><span>③ 성능에 마우스를 올려 물리를 배워보세요</span></div>""", unsafe_allow_html=True)


def render_part_menu(parts, active_part):
    """왼쪽 메뉴는 파츠 선택과 클릭형 물음표 설명만 담당합니다."""
    st.markdown("<div class='section-label'>01 / PARTS</div>", unsafe_allow_html=True)
    for key, data in parts.items():
        part_column, info_column = st.columns([5, 1], gap="small")
        with part_column:
            if st.button(f"{data['icon']}   {data['name']}", key=f"menu_{key}", use_container_width=True):
                st.session_state.active_part = key
                # 다른 파츠를 고르면 이전 설명창은 자연스럽게 닫습니다.
                st.session_state.open_part_info = None
                st.query_params["part"] = key
                st.rerun()
        with info_column:
            if st.button("?", key=f"info_{key}", use_container_width=True):
                st.session_state.open_part_info = None if st.session_state.open_part_info == key else key
                st.rerun()
        if st.session_state.get("open_part_info") == key:
            short, detail = PART_HELP[key]
            st.markdown(
                f"<div class='part-info-box'><b>{data['name'].upper()}</b><br>"
                f"{html.escape(short)}<br><br>{html.escape(detail)}</div>",
                unsafe_allow_html=True,
            )
    st.markdown(f"<div class='active-part'>SELECTED · {parts[active_part]['name'].upper()}</div>", unsafe_allow_html=True)


def stars(value):
    """숫자를 처음 보는 사용자도 빠르게 비교할 수 있도록 별점으로 바꿉니다."""
    return "★" * value + "☆" * (5 - value)


def render_option_svg(part_key, variant, color):
    """세 옵션의 크기·플랩 수·표면 패턴이 확실히 다른 교육용 파츠 SVG를 만듭니다."""
    v = variant
    if part_key == "front_wing":
        width = 125 + v * 24; flaps = "".join(f'<path class="thin" d="M{42-v*7} {55-i*11} Q100 {36-i*8} {158+v*7} {55-i*11}"/>' for i in range(2+v))
        body = f'<path class="main" d="M{100-width/2} 68 Q100 {40-v*5} {100+width/2} 68 L{100+width/2-8} 82 Q100 {58-v*5} {100-width/2+8} 82Z"/>{flaps}<path class="line" d="M38 40v48M162 40v48"/>'
    elif part_key == "rear_wing":
        body = "".join(f'<path class="main" d="M{42-v*8} {38+i*17} Q100 {25+i*14-v*3} {158+v*8} {38+i*17} L{155+v*8} {48+i*17} Q100 {37+i*14} {45-v*8} {48+i*17}Z"/>' for i in range(1+v)) + '<path class="line" d="M50 35v65M150 35v65"/>'
    elif part_key == "tyres":
        grooves="".join(f'<path class="thin" d="M{64+i*12} 30l-8 60"/>' for i in range(3+v*2)); body=f'<ellipse class="dark" cx="100" cy="62" rx="{38-v*3}" ry="50"/><ellipse class="main" cx="100" cy="62" rx="{20-v*2}" ry="31"/>{grooves}'
    elif part_key == "brakes":
        holes="".join(f'<circle cx="{100+28*((i%2)*2-1)}" cy="{38+i*12}" r="3" fill="#071018"/>' for i in range(2+v*2)); body=f'<circle class="main" cx="100" cy="62" r="{42-v*4}"/><circle class="dark" cx="100" cy="62" r="18"/>{holes}<rect class="main" x="132" y="38" width="{20+v*5}" height="48" rx="7"/>'
    elif part_key == "suspension": body="".join(f'<path class="line" d="M{45+i*55/(1+v)} 95 L{75+i*25} 28"/>' for i in range(2+v))+f'<rect class="main" x="88" y="20" width="{24-v*3}" height="84" rx="10"/>'
    elif part_key == "floor": body=f'<path class="main" d="M{42-v*8} 104 L{58+v*5} 18 H{142-v*5} L{158+v*8} 104Z"/>'+"".join(f'<path class="thin" d="M{76+i*24} 25v70"/>' for i in range(1+v))
    elif part_key == "diffuser": body=f'<path class="main" d="M{48-v*6} 96 L{58+v*4} 26 H{142-v*4} L{152+v*6} 96Z"/>'+"".join(f'<path class="line" d="M{62+i*(76/(2+v*2))} 32l-8 58"/>' for i in range(3+v*2))
    elif part_key == "engine": body=f'<ellipse class="main" cx="100" cy="62" rx="{56-v*5}" ry="{30+v*3}"/><circle class="dark" cx="{64+v*4}" cy="62" r="{17-v*2}"/><circle class="dark" cx="{136-v*4}" cy="62" r="{17-v*2}"/>'+"".join(f'<path class="thin" d="M{80+i*12} 35v54"/>' for i in range(1+v*2))
    else: body="".join(f'<ellipse class="main" cx="100" cy="62" rx="{52-i*12}" ry="{34-i*8}"/>' for i in range(1+v))+f'<path class="line" d="M{52-v*5} 62h{96+v*10}"/>'
    return f'<svg class="part-svg" viewBox="0 0 200 125" style="--pc:{color}" aria-label="옵션별 파츠 모습">{body}</svg>'


def render_part_options(parts, active_part, selections):
    """중앙에 세 옵션의 서로 다른 모습을 나란히 보여 주고 그 자리에서 장착하게 합니다."""
    data = parts[active_part]
    st.markdown("<div class='section-label'>옵션을 비교하고 장착하세요</div>", unsafe_allow_html=True)
    columns = st.columns(len(data["options"]), gap="small")
    for variant, ((option_key, option), column) in enumerate(zip(data["options"].items(), columns)):
        with column:
            tooltip = html.escape(option["explanation"], quote=True)
            st.markdown(f"<div class='option-visual option-tip'>{render_option_svg(active_part, variant, option['color'])}<span class='tip-box'>{tooltip}</span></div><div class='option-name'><span class='hover-tip'>{option['label']} ⓘ<span class='tip-box'>{tooltip}</span></span></div><div class='option-desc'>{html.escape(option['explanation'])}</div>", unsafe_allow_html=True)
            if selections[active_part] == option_key:
                st.markdown("<div class='installed'>장착 중 ✓</div>", unsafe_allow_html=True)
            elif st.button("이 파츠 장착", key=f"equip_{active_part}_{option_key}", use_container_width=True):
                # 변경 직전의 전체 성능을 저장해야 오른쪽에서 전/후 숫자를 정확히 비교할 수 있습니다.
                st.session_state.change_before = calculate_car_performance(parts, st.session_state.selections)
                st.session_state.selections[active_part] = option_key
                st.session_state.last_changed_part = active_part
                st.rerun()
    render_advantages_and_disadvantages(parts, active_part, selections[active_part])
    option = data["options"][selections[active_part]]
    st.markdown(f"<div class='result-line'>💡 <b>이 파츠의 특징</b><br>{html.escape(option['explanation'])}</div>", unsafe_allow_html=True)


def render_part_detail(parts, active_part, selections):
    """차량 아래 중앙 튜닝 베이에 프리뷰·옵션·장단점을 순서대로 배치합니다."""
    st.markdown("<div class='tuning-bay'>", unsafe_allow_html=True)
    render_selected_part_preview(parts, selections, active_part)
    render_part_options(parts, active_part, selections)
    st.markdown("</div>", unsafe_allow_html=True)

def render_physics_tooltip(metric):
    """브라우저 기본 툴팁을 이용해 추가 라이브러리 없이 물리 설명을 제공합니다."""
    short, long_text = PHYSICS_HELP[metric]
    return f"<span class='hover-tip'>{html.escape(short)} ⓘ<span class='tip-box'>{html.escape(long_text)}</span></span>"


def render_performance_panel(performance, previous_performance, differences, changed_part, parts, selections):
    """오른쪽에는 핵심 성능만 크게 표시하고 변화 방향을 색으로 강조합니다."""
    st.markdown("<div class='section-label'>02 / CAR PERFORMANCE</div>", unsafe_allow_html=True)
    for metric in METRICS:
        value, difference = performance[metric], differences[metric]
        if difference > 0:
            delta = f"<span class='up'>↑ {difference}</span>"
        elif difference < 0:
            delta = f"<span class='down'>↓ {abs(difference)}</span>"
        else:
            delta = "<span class='same'>━</span>"
        st.markdown(f"""<div class='perf'><div class='perf-top'><div><div class='perf-name'>{METRIC_ENGLISH[metric]}</div><div class='perf-help'>{render_physics_tooltip(metric)}</div></div><div class='perf-num'>{value} {delta}</div></div><div class='track'><div class='fill' style='width:{value}%'></div></div></div>""", unsafe_allow_html=True)
    if changed_part:
        option = parts[changed_part]["options"][selections[changed_part]]
        st.markdown(f"<div class='why'><b>왜 변했나요?</b><br>{html.escape(option['explanation'])}</div>", unsafe_allow_html=True)
    render_change_summary(performance, previous_performance, differences, changed_part, parts, selections)
    st.markdown("<div class='footnote'>0~100은 실제 측정값이 아니라 물리적 경향을 쉽게 비교하기 위한 학습용 게임 지표입니다.</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. 메인 실행 흐름
# -----------------------------------------------------------------------------
def main():
    """데이터 준비 → 사용자 입력 → 계산 → 3D 및 UI 렌더링 순서로 앱을 실행합니다."""
    st.set_page_config(page_title="F1 RACING SIMULATOR", page_icon="🏁", layout="wide", initial_sidebar_state="collapsed")
    apply_game_css()
    if "app_view" not in st.session_state:
        st.session_state.app_view = "home"
    if st.session_state.app_view == "home":
        st.markdown("""<style>
        .home-wrap{max-width:950px;margin:9vh auto 0;text-align:center;padding:32px;color:#eff5fa}
        .home-title{font-size:clamp(32px,5vw,58px);font-weight:900;letter-spacing:2px}
        .home-title b{color:#ff3158}.home-sub{color:#a8bac9;margin:12px 0 35px}
        .home-card{background:#101821;border:1px solid #344353;border-top:3px solid #27d6ff;
        padding:24px;text-align:left;min-height:125px}.home-card h3{margin:0 0 10px}
        .home-card p{color:#a8bac9;font-size:14px}.home-locked{border-top-color:#677481}
        </style>""", unsafe_allow_html=True)
        # CSS와 HTML을 분리합니다. 들여쓴 HTML이 Markdown 코드 블록으로 해석되지 않게 합니다.
        st.markdown(
            "<div class='home-wrap'><div class='home-title'>F1 <b>RACING SIMULATOR</b></div>"
            "<div class='home-sub'>차량을 설계하고 테스트 서킷에서 달려보세요</div></div>",
            unsafe_allow_html=True,
        )
        ready = bool(
            isinstance(st.session_state.get("my_car_config"), dict)
            and isinstance(st.session_state.get("my_car_performance"), dict)
            and all(key in st.session_state["my_car_config"] for key in get_part_data())
            and all(key in st.session_state["my_car_performance"] for key in METRICS)
        )
        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown("<div class='home-card'><h3>🏎 차량 설계하기</h3><p>Garage에서 파츠를 선택하고 내 F1 차량을 완성하세요.</p></div>", unsafe_allow_html=True)
            if st.button("차량 설계하기", use_container_width=True):
                st.session_state.app_view = "garage"
                st.rerun()
        with right:
            st.markdown("<div class='home-card home-locked'><h3>🏁 레이싱 시뮬레이션</h3><p>" +
                        ("설계한 차량으로 테스트 서킷을 달려보세요." if ready else "🔒 먼저 차량을 설계해 주세요.") +
                        "</p></div>", unsafe_allow_html=True)
            if st.button("레이싱 시뮬레이션", disabled=not ready,
                         help=None if ready else "먼저 차량을 설계해 주세요.", use_container_width=True):
                st.switch_page("pages/racing.py")
        return
    parts = get_part_data()

    # 첫 실행에서는 모든 파츠를 다루기 쉬운 균형형 설정으로 시작합니다.
    defaults = {key: list(data["options"].keys())[1] for key, data in parts.items()}
    if "selections" not in st.session_state:
        st.session_state.selections = defaults
    query_part = st.query_params.get("part")
    if query_part in parts:
        st.session_state.active_part = query_part
    if "active_part" not in st.session_state:
        st.session_state.active_part = "front_wing"
    if "open_part_info" not in st.session_state:
        st.session_state.open_part_info = None
    if "last_changed_part" not in st.session_state:
        st.session_state.last_changed_part = None

    selections = st.session_state.selections
    active_part = st.session_state.active_part
    current_performance = calculate_car_performance(parts, selections)
    # Garage에 진입한 뒤 완성된 선택과 계산값을 기존 레이스 데이터 키로 공유합니다.
    if all(key in selections and selections[key] in parts[key]["options"] for key in parts):
        st.session_state["my_car_config"] = dict(selections)
        st.session_state["my_car_performance"] = dict(current_performance)
    previous_performance = st.session_state.get("change_before")
    differences = calculate_performance_difference(current_performance, previous_performance)

    st.markdown("<div class='garage-head'><div class='logo'>F1 <b>RACING SIMULATOR</b> · GARAGE</div><div class='step'>BUILD 02 · INTERACTIVE 3D SETUP</div></div>", unsafe_allow_html=True)
    nav_race, nav_home = st.columns(2)
    with nav_race:
        if st.button("🏁 레이싱 시뮬레이션 시작", disabled=not (
            isinstance(st.session_state.get("my_car_config"), dict)
            and isinstance(st.session_state.get("my_car_performance"), dict)
        ), use_container_width=True):
            st.switch_page("pages/racing.py")
    with nav_home:
        if st.button("⌂ 처음 화면으로 돌아가기", use_container_width=True):
            st.session_state.app_view = "home"
            st.rerun()
    render_help_message()

    left, center, right = st.columns([0.78, 2.45, 1.05], gap="medium")
    with left:
        render_part_menu(parts, active_part)
    with center:
        st.markdown("<div class='section-label'>3D CAR / DRAG TO EXPLORE</div>", unsafe_allow_html=True)
        render_3d_car(parts, selections, active_part)
        render_part_detail(parts, active_part, selections)
    with right:
        render_performance_panel(current_performance, previous_performance, differences, st.session_state.last_changed_part, parts, selections)

    # 마지막 변경 기록은 다음 파츠를 장착할 때까지 유지해 학습 설명이 사라지지 않게 합니다.


if __name__ == "__main__":
    main()
