# app.py — Rock–Paper–Scissors (same template)  # mirrors your Trip Planner template:contentReference[oaicite:2]{index=2}
import os, time, json, random, datetime as dt, types, urllib.request
from dataclasses import dataclass
from typing import List
import streamlit as st
try:
    from openai import OpenAI
except Exception:
    OpenAI=None

st.set_page_config(page_title="Rock–Paper–Scissors", layout="wide")

BUDGET_URL=os.getenv("BUDGET_URL","https://raw.githubusercontent.com/RahulBhattacharya1/shared_config/main/budget.py")
DEF={"COOLDOWN_SECONDS":30,"DAILY_LIMIT":40,"HOURLY_SHARED_CAP":250,"DAILY_BUDGET":1.00,"EST_COST_PER_GEN":1.00,"VERSION":"fallback-local"}
def _fetch(u): m=types.ModuleType("b"); 
with urllib.request.urlopen(u,timeout=5) as r: code=r.read().decode()
exec(compile(code,"b","exec"),m.__dict__); 
return {k:getattr(m,k,DEF[k]) for k in DEF}
def _cfg(ttl=300):
    now=time.time(); c=st.session_state.get("_b"); ts=st.session_state.get("_bts",0)
    if c and (now-ts)<ttl: return c
    try: cfg=_fetch(BUDGET_URL)
    except Exception: cfg=DEF.copy()
    cfg["DAILY_BUDGET"]=float(os.getenv("DAILY_BUDGET",cfg["DAILY_BUDGET"]))
    cfg["EST_COST_PER_GEN"]=float(os.getenv("EST_COST_PER_GEN",cfg["EST_COST_PER_GEN"]))
    st.session_state["_b"]=cfg; st.session_state["_bts"]=now; return cfg
_cfg=_cfg(); COOLDOWN_SECONDS=int(_cfg["COOLDOWN_SECONDS"]); DAILY_LIMIT=int(_cfg["DAILY_LIMIT"])
HOURLY_SHARED_CAP=int(_cfg["HOURLY_SHARED_CAP"]); DAILY_BUDGET=float(_cfg["DAILY_BUDGET"])
EST_COST_PER_GEN=float(_cfg["EST_COST_PER_GEN"]); CONFIG_VERSION=str(_cfg["VERSION"])
def _hour(): return dt.datetime.utcnow().strftime("%Y-%m-%d-%H")
@st.cache_resource
def _counters(): return {}
def _init():
    ss=st.session_state; today=dt.date.today().isoformat()
    if ss.get("rl_date")!=today: ss["rl_date"]=today; ss["rl_calls_today"]=0; ss["rl_last_ts"]=0.0
    ss.setdefault("rl_last_ts",0.0); ss.setdefault("rl_calls_today",0)
def _can():
    _init(); ss=st.session_state; now=time.time()
    rem=int(max(0, ss["rl_last_ts"]+COOLDOWN_SECONDS-now))
    if rem>0: return False,f"Wait {rem}s.",rem
    if ss["rl_calls_today"]*EST_COST_PER_GEN>=DAILY_BUDGET: return False,f"Budget reached (${DAILY_BUDGET:.2f}).",0
    if ss["rl_calls_today"]>=DAILY_LIMIT: return False,f"Daily limit {DAILY_LIMIT}.",0
    if HOURLY_SHARED_CAP>0:
        b=_hour(); c=_counters()
        if c.get(b,0)>=HOURLY_SHARED_CAP: return False,"Hourly cap reached.",0
    return True,"",0
def _rec():
    ss=st.session_state; ss["rl_last_ts"]=time.time(); ss["rl_calls_today"]+=1
    if HOURLY_SHARED_CAP>0:
        b=_hour(); c=_counters(); c[b]=c.get(b,0)+1

CHOICES=["rock","paper","scissors"]
def offline_move(hist:List[str])->str:
    if not hist: return random.choice(CHOICES)
    most=max(CHOICES, key=lambda x: hist.count(x))
    return {"rock":"paper","paper":"scissors","scissors":"rock"}[most]
def call_openai(model, hist, temp, max_tok)->str:
    key=st.secrets.get("OPENAI_API_KEY","")
    if not key: raise RuntimeError("OPENAI_API_KEY missing")
    if OpenAI is None: raise RuntimeError("openai package not available")
    client=OpenAI(api_key=key)
    sys="Play RPS. Return JSON with key 'choice' in ['rock','paper','scissors']."
    usr=f"User history (most recent last): {hist}"
    r=client.chat.completions.create(model=model,temperature=float(temp),max_tokens=int(max_tok),
                                     messages=[{"role":"system","content":sys},{"role":"user","content":usr}])
    t=r.choices[0].message.content.strip()
    if t.startswith("```"): t=t.strip("`").split("\n",1)[-1].strip()
    c=str(json.loads(t).get("choice","")).lower()
    return c if c in CHOICES else offline_move(hist)

def result(u,a):
    if u==a: return "draw"
    wins={("rock","scissors"),("paper","rock"),("scissors","paper")}
    return "win" if (u,a) in wins else "lose"

def h2(t,c): st.markdown(f"<h2 style='margin:.25rem 0 .75rem 0; color:{c}'>{t}</h2>", unsafe_allow_html=True)
def card(t,sub=""): st.markdown(f"<div style='border:1px solid #e5e7eb;padding:.75rem 1rem;border-radius:10px;margin:.75rem 0;'><div style='font-weight:600'>{t}</div>{f'<div style=margin-top:.25rem>{sub}</div>' if sub else ''}</div>", unsafe_allow_html=True)

st.title("Rock–Paper–Scissors")
with st.sidebar:
    st.subheader("Generator")
    provider=st.selectbox("Provider",["OpenAI","Offline (rule-based)"])
    model=st.selectbox("Model (OpenAI)",["gpt-4o-mini","gpt-4o","gpt-4.1-mini"])
    brand="#0F62FE"
    temp=st.slider("Creativity (OpenAI)",0.0,1.0,0.4,0.05)
    max_tok=st.slider("Max tokens (OpenAI)",256,2048,600,32)
    _init(); ss=st.session_state
    st.markdown("**Usage limits**")
    st.write(f"<span style='font-size:.9rem'>Today: {ss['rl_calls_today']} / {DAILY_LIMIT}</span>", unsafe_allow_html=True)
    if HOURLY_SHARED_CAP>0:
        used=_counters().get(_hour(),0)
        st.write(f"<span style='font-size:.9rem'>Hour: {used} / {HOURLY_SHARED_CAP}</span>", unsafe_allow_html=True)
    est=ss['rl_calls_today']*EST_COST_PER_GEN
    st.markdown(f"<span style='font-size:.9rem'>Budget: ${est:.2f} / ${DAILY_BUDGET:.2f}</span><br/>"
                f"<span style='font-size:.8rem;opacity:.8'>Version: {CONFIG_VERSION}</span>", unsafe_allow_html=True)

st.session_state.setdefault("hist", [])
st.session_state.setdefault("score", {"wins":0,"losses":0,"draws":0})
h2("Play", brand)
c1,c2,c3=st.columns(3)
choice=None
with c1:
    if st.button("Rock"): choice="rock"
with c2:
    if st.button("Paper"): choice="paper"
with c3:
    if st.button("Scissors"): choice="scissors"

if choice:
    st.session_state.hist.append(choice)
    ok,msg,_=_can()
    try:
        if provider=="OpenAI" and ok:
            ai=call_openai(model, st.session_state.hist[-10:], temp, max_tok); _rec()
        else:
            if provider=="OpenAI" and not ok: st.warning(msg)
            ai=offline_move(st.session_state.hist[-10:])
    except Exception as e:
        st.error(f"AI move error: {e}. Using offline."); ai=offline_move(st.session_state.hist[-10:])
    out=result(choice, ai)
    if out=="win": st.session_state.score["wins"]+=1
    elif out=="lose": st.session_state.score["losses"]+=1
    else: st.session_state.score["draws"]+=1
    card("Round", f"You: {choice} · AI: {ai}<br/>Outcome: {out.capitalize()}")

s=st.session_state.score
card("Score", f"Wins: {s['wins']} · Losses: {s['losses']} · Draws: {s['draws']}")
