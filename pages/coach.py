import streamlit as st
from core.store import get_prefs, get_settings, get_tracker, get_applied
from core.ai_engine import generate_coach_insights
import json, urllib.request


def render():
    prefs    = get_prefs()
    settings = get_settings()
    api_key  = settings.get("groq_api_key","") or ""
    tracker  = get_tracker()
    applied  = get_applied()

    st.markdown("""<div style='padding:8px 0 28px;'>
<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#2d4060;letter-spacing:.2em;'>MODULE 6</div>
<h1 style='font-size:30px;font-weight:800;margin:4px 0 6px;color:#e2e8f0;'>AI Career Coach</h1>
<p style='color:#4a6080;font-size:14px;margin:0;'>Your personal career strategist — analyzes activity, identifies blockers, tells you exactly what to do next.</p>
</div>""", unsafe_allow_html=True)

    total = len(tracker) + len(applied)

    # Insights
    if "coach_insights" not in st.session_state:
        with st.spinner("Analyzing your job search activity..."):
            try:
                insights = generate_coach_insights(prefs, tracker, applied, api_key)
            except Exception:
                insights = generate_coach_insights(prefs, tracker, applied, "")
        st.session_state["coach_insights"] = insights

    if st.button("🔄 Refresh Insights"):
        st.session_state.pop("coach_insights", None)
        st.rerun()

    data = st.session_state.get("coach_insights", {})
    if not data:
        data = generate_coach_insights(prefs, tracker, applied, "")

    # Score card
    weekly_score = data.get("weekly_score", 0)
    score_label  = data.get("score_label","—")
    score_color  = {"Excellent":"#22d3a5","Good":"#6366f1","Needs Work":"#f59e0b","Critical":"#f87171"}.get(score_label,"#7a8faa")

    col_score, col_head = st.columns([1,3])
    with col_score:
        st.markdown(f"""<div style='background:linear-gradient(135deg,#0f1629,#111827);border:1px solid #1a2540;border-radius:12px;padding:24px;text-align:center;'>
<div style='font-size:52px;font-weight:800;color:{score_color};font-family:JetBrains Mono,monospace;line-height:1;'>{weekly_score}</div>
<div style='font-size:12px;color:{score_color};font-family:JetBrains Mono,monospace;margin-top:6px;font-weight:600;'>{score_label.upper()}</div>
<div style='font-size:10px;color:#4a6080;margin-top:4px;'>Weekly Score</div>
<div class="prob-bar-wrap" style='margin-top:12px;'><div class="prob-bar-fill" style='width:{weekly_score}%;'></div></div>
</div>""", unsafe_allow_html=True)
    with col_head:
        headline  = data.get("headline_insight","")
        conv_rate = int(data.get("conversion_rate",0)*100)
        benchmark = data.get("benchmark_comparison","")
        st.markdown(f"""<div style='background:linear-gradient(135deg,#0f1629,#111827);border:1px solid #1a2540;border-radius:12px;padding:24px;height:100%;'>
<div style='font-size:11px;color:#4a6080;font-family:JetBrains Mono,monospace;margin-bottom:8px;'>COACH'S ASSESSMENT</div>
<div style='font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:14px;'>{headline}</div>
<div style='font-size:13px;color:#7a8faa;margin-bottom:10px;'>{benchmark}</div>
<div style='display:flex;gap:20px;'>
  <div><div style='font-size:22px;font-weight:700;color:#6366f1;font-family:JetBrains Mono,monospace;'>{total}</div><div style='font-size:11px;color:#4a6080;'>Total Applications</div></div>
  <div><div style='font-size:22px;font-weight:700;color:#22d3a5;font-family:JetBrains Mono,monospace;'>{conv_rate}%</div><div style='font-size:11px;color:#4a6080;'>Interview Rate</div></div>
</div>
</div>""", unsafe_allow_html=True)

    # Insights
    st.markdown('<div class="section-header">PERSONALIZED INSIGHTS</div>', unsafe_allow_html=True)
    icons = {"warning":"⚠️","success":"✅","info":"💡","danger":"🚨"}
    for ins in data.get("insights",[]):
        t = ins.get("type","info")
        st.markdown(f"""<div class="insight-card {t}">
<div style='font-size:14px;font-weight:600;color:#e2e8f0;margin-bottom:6px;'>{icons.get(t,"💡")} {ins.get('title','')}</div>
<div style='font-size:13px;color:#7a8faa;line-height:1.7;'>{ins.get('body','')}</div>
</div>""", unsafe_allow_html=True)

    # Focus roles
    focus = data.get("focus_roles",[])
    if focus:
        st.markdown('<div class="section-header">FOCUS ON THESE ROLES THIS WEEK</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(focus),3))
        for col, role in zip(cols, focus[:3]):
            with col:
                st.markdown(f"""<div style='background:#1e1b4b;border:1px solid #3730a3;border-radius:8px;padding:14px;text-align:center;'>
<div style='font-size:14px;font-weight:600;color:#e2e8f0;margin-bottom:4px;'>🎯 {role}</div>
<div style='font-size:11px;color:#6366f1;'>Priority target</div>
</div>""", unsafe_allow_html=True)

    # Action plan
    actions = data.get("this_week_actions",[])
    if actions:
        st.markdown("<div class='section-header'>THIS WEEK'S EXECUTION PLAN</div>", unsafe_allow_html=True)
        for i, action in enumerate(actions):
            st.checkbox(action, key=f"ca_{i}")

    # Chat
    st.markdown('<div class="section-header">ASK YOUR AI COACH</div>', unsafe_allow_html=True)

    if not api_key:
        st.markdown("""<div class="upgrade-banner">
<div style='font-size:14px;font-weight:600;color:#e2e8f0;margin-bottom:4px;'>🔒 Chat requires Groq API Key</div>
<div style='font-size:12px;color:#a5b4fc;'>Add your free Groq API key in Settings to ask the coach anything.</div>
</div>""", unsafe_allow_html=True)
        return

    if "coach_chat" not in st.session_state:
        st.session_state["coach_chat"] = []

    for msg in st.session_state["coach_chat"][-10:]:
        role_label = "You" if msg["role"]=="user" else "🤖 Coach"
        bg    = "#1e1b4b" if msg["role"]=="user" else "#052e16"
        bdr   = "#3730a3" if msg["role"]=="user" else "#166534"
        color = "#e2e8f0" if msg["role"]=="user" else "#22d3a5"
        st.markdown(f"""<div style='background:{bg};border:1px solid {bdr};border-radius:8px;padding:12px 16px;margin-bottom:8px;'>
<div style='font-size:10px;color:#4a6080;font-family:JetBrains Mono,monospace;margin-bottom:4px;'>{role_label}</div>
<div style='font-size:13px;color:{color};'>{msg["content"]}</div>
</div>""", unsafe_allow_html=True)

    user_q = st.text_input("Ask your career coach...",
        placeholder="e.g. Why am I not getting interview calls? / How to negotiate salary?",
        key="coach_q")

    c1,c2 = st.columns([4,1])
    with c1:
        ask = st.button("Ask Coach ↗", use_container_width=True)
    with c2:
        if st.button("Clear", use_container_width=True):
            st.session_state["coach_chat"] = []
            st.rerun()

    if ask and user_q:
        ctx = f"""Expert finance career coach. Candidate: {prefs.get('experience_years',6)}yrs, target={prefs.get('target_roles')}, skills={prefs.get('keywords')}, tracked={total} applications. Be specific, max 150 words."""
        messages = [{"role":"system","content":ctx}]
        for m in st.session_state["coach_chat"][-6:]:
            messages.append(m)
        messages.append({"role":"user","content":user_q})

        answer = ""
        try:
            payload = json.dumps({
                "model":"llama-3.1-8b-instant",
                "messages":messages,
                "max_tokens":400,"temperature":0.5,
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                answer = json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:
            answer = "I'm having trouble connecting. Please verify your Groq API key in Settings is valid and try again."

        st.session_state["coach_chat"].append({"role":"user","content":user_q})
        st.session_state["coach_chat"].append({"role":"assistant","content":answer})
        st.rerun()
