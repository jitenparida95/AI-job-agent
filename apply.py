"""
Auto Apply — CareerOS (4-step bulk apply system)
Compatible with st.radio navigation (no st.session_state.page dependency)
"""
import streamlit as st
import time
from datetime import datetime
from core.store import (get_jobs, save_jobs, get_prefs, get_settings,
                         log_application, get_applied, save_settings)
from core.ai_engine import generate_cover_letter


def render():
    try:
        prefs    = get_prefs()
        settings = get_settings()
        jobs     = get_jobs()
        applied  = get_applied()
        api_key  = settings.get("groq_api_key", "")
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return

    st.markdown("""
<div style='padding:8px 0 24px;'>
  <div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#2d4060;letter-spacing:.2em;'>MODULE 3C</div>
  <h1 style='font-size:30px;font-weight:800;margin:4px 0 6px;color:#e2e8f0;'>Auto Apply</h1>
  <p style='color:#4a6080;font-size:14px;margin:0;'>Bulk-generate cover letters, review each job, then log applications in one batch.</p>
</div>""", unsafe_allow_html=True)

    # ── Init session state safely ──────────────────────────────
    if "apply_step" not in st.session_state:
        st.session_state.apply_step = 1
    if "apply_approved" not in st.session_state:
        st.session_state.apply_approved = {}
    if "apply_cover_letters" not in st.session_state:
        st.session_state.apply_cover_letters = {}
    if "apply_results" not in st.session_state:
        st.session_state.apply_results = {}
    if "apply_batch" not in st.session_state:
        st.session_state.apply_batch = []
    if "apply_limit" not in st.session_state:
        st.session_state.apply_limit = 30

    step = st.session_state.apply_step

    # ── Step indicator ─────────────────────────────────────────
    steps = ["1. Pre-flight","2. Review Jobs","3. Apply Bulk","4. Results"]
    cols = st.columns(4)
    for i, (col, label) in enumerate(zip(cols, steps), 1):
        done   = i < step
        active = i == step
        bg     = "#052e16" if done else ("#1e1b4b" if active else "#0c1020")
        bdr    = "#166534" if done else ("#6366f1" if active else "#1a2540")
        color  = "#22d3a5" if done else ("#a5b4fc" if active else "#2d4060")
        icon   = "✓" if done else str(i)
        with col:
            st.markdown(f"""<div style='background:{bg};border:1px solid {bdr};border-radius:8px;padding:10px;text-align:center;'>
<div style='font-family:JetBrains Mono,monospace;font-size:16px;color:{color};font-weight:700;'>{icon}</div>
<div style='font-size:11px;color:{color};margin-top:4px;'>{label}</div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Compute ready jobs ─────────────────────────────────────
    min_score   = settings.get("min_match_score", 70)
    applied_ids = {a.get("id","") for a in applied}
    ready = [j for j in jobs
             if (j.get("match_score") or 0) >= min_score
             and j.get("id","") not in applied_ids
             and j.get("status","") not in ["applied"]]

    # ── Route to step ──────────────────────────────────────────
    if step == 1:
        _step1(prefs, settings, ready, api_key)
    elif step == 2:
        _step2(prefs, settings, ready, api_key, jobs)
    elif step == 3:
        _step3(prefs, settings, ready, api_key, jobs)
    elif step == 4:
        _step4()


# ─────────────────────────────────────────────────────────────
# STEP 1 — Pre-flight checklist
# ─────────────────────────────────────────────────────────────
def _step1(prefs, settings, ready, api_key):
    st.markdown('<div class="section-header">PRE-FLIGHT CHECKLIST</div>', unsafe_allow_html=True)

    checks = [
        ("Resume uploaded",             bool(prefs.get("resume_text") or prefs.get("resume_path")), "Upload in Resume Optimizer"),
        ("Name & email set",            bool(prefs.get("name") and prefs.get("email")),             "Set in Resume Optimizer → Preferences tab"),
        ("Target roles defined",        bool(prefs.get("target_roles")),                             "Set in Resume Optimizer → Preferences tab"),
        ("Jobs scored & in queue",      len(ready) > 0,                                              "Run Job Discovery → AI Matching first"),
        ("Groq API key (AI letters)",   bool(api_key),                                               "Free at console.groq.com → Settings"),
    ]

    for label, ok, fix in checks:
        icon  = "✓" if ok else "✗"
        color = "#22d3a5" if ok else "#f87171"
        bg    = "#052e16" if ok else "#1c0a0a"
        bdr   = "#166534" if ok else "#7f1d1d"
        st.markdown(f"""<div style='background:{bg};border:1px solid {bdr};border-radius:8px;
padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;'>
<div><span style='color:{color};font-family:JetBrains Mono,monospace;font-weight:700;margin-right:10px;'>{icon}</span>
<span style='color:#e2e8f0;font-size:13px;'>{label}</span></div>
<div style='font-size:11px;color:{"#22d3a5" if ok else "#4a6080"};'>{"✓ Ready" if ok else fix}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">APPLY SETTINGS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        min_score = st.slider("Min match score", 50, 95,
                              value=settings.get("min_match_score", 70), step=5)
    with c2:
        limit = st.number_input("Max jobs this batch", min_value=1, max_value=100,
                                value=int(min(max(len(ready), 1), settings.get("daily_apply_limit", 30))))
    with c3:
        batch_n = min(len(ready), int(limit))
        st.markdown(f"""<div class="metric-card" style='margin-top:8px;'>
<div class="metric-value" style='color:{"#22d3a5" if batch_n>0 else "#f87171"};'>{batch_n}</div>
<div class="metric-label">Jobs in batch</div></div>""", unsafe_allow_html=True)

    if min_score != settings.get("min_match_score", 70):
        settings["min_match_score"] = min_score
        settings["daily_apply_limit"] = int(limit)
        try: save_settings(settings)
        except Exception: pass

    # Portal breakdown
    if ready:
        st.markdown('<div class="section-header">PORTAL BREAKDOWN</div>', unsafe_allow_html=True)
        pc = {}
        for j in ready[:int(limit)]:
            p = j.get("portal","unknown")
            pc[p] = pc.get(p, 0) + 1
        cols = st.columns(max(len(pc), 1))
        for col, (portal, count) in zip(cols, pc.items()):
            col.markdown(f"""<div style='background:#111827;border:1px solid #1a2540;border-radius:8px;
padding:12px;text-align:center;'>
<div style='font-family:JetBrains Mono,monospace;font-size:22px;font-weight:700;color:#6366f1;'>{count}</div>
<div style='font-size:11px;color:#4a6080;margin-top:4px;'>{portal.upper()}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(ready) == 0:
        st.markdown("""<div class="insight-card danger">
<div style='font-weight:600;color:#f87171;margin-bottom:4px;'>No jobs ready to apply</div>
<div style='font-size:13px;color:#7a8faa;'>Run Job Discovery → AI Job Matching first. Jobs need a score ≥ your threshold.</div>
</div>""", unsafe_allow_html=True)
        return

    if st.button(f"→ Review {min(len(ready), int(limit))} Jobs   (Step 2)", use_container_width=True):
        st.session_state.apply_step = 2
        st.session_state.apply_limit = int(limit)
        # Reset batch state for fresh run
        st.session_state.apply_approved = {j.get("id",""):True for j in
            sorted(ready, key=lambda x: x.get("match_score",0), reverse=True)[:int(limit)]}
        st.rerun()


# ─────────────────────────────────────────────────────────────
# STEP 2 — Review & approve jobs
# ─────────────────────────────────────────────────────────────
def _step2(prefs, settings, ready, api_key, jobs):
    limit = st.session_state.apply_limit
    batch = sorted(ready, key=lambda j: j.get("match_score",0), reverse=True)[:limit]

    if not batch:
        st.warning("No jobs available. Go back to Step 1.")
        if st.button("← Back to Step 1"):
            st.session_state.apply_step = 1
            st.rerun()
        return

    # Ensure approved dict is populated
    for j in batch:
        jid = j.get("id","")
        if jid not in st.session_state.apply_approved:
            st.session_state.apply_approved[jid] = True

    approved_n = sum(1 for j in batch
                     if st.session_state.apply_approved.get(j.get("id",""), True))

    st.markdown(f'<div class="section-header">REVIEW {len(batch)} JOBS — APPROVE OR REJECT EACH</div>',
                unsafe_allow_html=True)

    # Bulk controls
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✓ Approve All", use_container_width=True):
            for j in batch:
                st.session_state.apply_approved[j.get("id","")] = True
            st.rerun()
    with c2:
        if st.button("✗ Deselect All", use_container_width=True):
            for j in batch:
                st.session_state.apply_approved[j.get("id","")] = False
            st.rerun()
    with c3:
        st.markdown(f"""<div style='background:#1e1b4b;border:1px solid #3730a3;border-radius:8px;
padding:10px;text-align:center;'>
<div style='font-family:JetBrains Mono,monospace;font-size:22px;color:#a5b4fc;font-weight:700;'>{approved_n}</div>
<div style='font-size:11px;color:#4a6080;'>Approved</div></div>""", unsafe_allow_html=True)

    # Bulk generate cover letters
    if api_key:
        gen_n = len(st.session_state.apply_cover_letters)
        if gen_n < len(batch):
            if st.button(f"⚡ AI-Generate All {len(batch)} Cover Letters", use_container_width=True):
                prog = st.progress(0)
                stat = st.empty()
                for i, job in enumerate(batch):
                    jid = job.get("id","")
                    if jid not in st.session_state.apply_cover_letters:
                        stat.markdown(f'<div style="font-size:12px;color:#6366f1;font-family:JetBrains Mono,monospace;">'
                                      f'Generating: {job.get("title","")} @ {job.get("company","")}</div>',
                                      unsafe_allow_html=True)
                        try:
                            cl = generate_cover_letter(job, prefs,
                                                        prefs.get("cover_letter_template",""), api_key)
                        except Exception:
                            cl = _fallback_cl(job, prefs)
                        st.session_state.apply_cover_letters[jid] = cl
                    prog.progress(int((i+1)/len(batch)*100))
                stat.success(f"✓ {len(batch)} cover letters ready!")
                st.rerun()
        else:
            st.markdown(f'<div style="background:#052e16;border:1px solid #166534;border-radius:6px;'
                        f'padding:8px 12px;font-size:12px;color:#22d3a5;margin:8px 0;">'
                        f'✓ All {gen_n} cover letters generated</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Per-job cards
    for job in batch:
        jid      = job.get("id","")
        score    = job.get("match_score", 0)
        sc       = "score-high" if score>=70 else ("score-mid" if score>=50 else "score-low")
        approved = st.session_state.apply_approved.get(jid, True)
        cl_text  = st.session_state.apply_cover_letters.get(jid, "")
        tick     = "✓" if approved else "✗"

        with st.expander(f"{tick}  {job.get('title','')} @ {job.get('company','')} — {score}% match"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f"**Portal:** {job.get('portal','').upper()} · "
                    f"**Location:** {job.get('location','—')} · "
                    f"**Salary:** {job.get('salary','Not listed')}"
                )
                if job.get("url"):
                    st.markdown(f"[🔗 Open job page]({job['url']})")

                st.markdown("**Cover Letter:**")
                if not cl_text:
                    if st.button("Generate Cover Letter", key=f"gen_{jid}"):
                        try:
                            cl = generate_cover_letter(job, prefs,
                                                        prefs.get("cover_letter_template",""), api_key)
                        except Exception:
                            cl = _fallback_cl(job, prefs)
                        st.session_state.apply_cover_letters[jid] = cl
                        st.rerun()
                else:
                    edited = st.text_area("Edit before sending:", value=cl_text,
                                          height=180, key=f"cl_edit_{jid}",
                                          label_visibility="collapsed")
                    if edited != cl_text:
                        st.session_state.apply_cover_letters[jid] = edited
                    st.download_button("⬇️ Download", data=edited,
                                       file_name=f"cl_{job.get('company','')}.txt",
                                       key=f"dl_{jid}")
            with c2:
                st.markdown(
                    f'<div style="text-align:center;padding:12px;">'
                    f'<div class="match-score {sc}" style="font-size:36px;">{score}%</div>'
                    f'<div style="font-size:11px;color:#4a6080;margin-top:4px;">MATCH</div></div>',
                    unsafe_allow_html=True
                )
                new_app = st.toggle("Include in batch", value=approved, key=f"toggle_{jid}")
                if new_app != approved:
                    st.session_state.apply_approved[jid] = new_app
                    st.rerun()

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Back to Checklist"):
            st.session_state.apply_step = 1
            st.rerun()
    with c2:
        final_n = sum(1 for j in batch
                      if st.session_state.apply_approved.get(j.get("id",""), True))
        if final_n == 0:
            st.warning("Approve at least one job to continue.")
        else:
            if st.button(f"🚀 Apply to {final_n} Approved Jobs   (Step 3)",
                         use_container_width=True):
                st.session_state.apply_step = 3
                st.session_state.apply_batch = [
                    j for j in batch
                    if st.session_state.apply_approved.get(j.get("id",""), True)
                ]
                st.session_state.apply_results = {}  # reset for fresh run
                st.rerun()


# ─────────────────────────────────────────────────────────────
# STEP 3 — Bulk apply with progress
# ─────────────────────────────────────────────────────────────
def _step3(prefs, settings, ready, api_key, jobs):
    batch = st.session_state.apply_batch
    if not batch:
        st.warning("No jobs selected. Go back to Step 2.")
        if st.button("← Back"):
            st.session_state.apply_step = 2
            st.rerun()
        return

    st.markdown(f'<div class="section-header">APPLYING TO {len(batch)} JOBS</div>',
                unsafe_allow_html=True)

    # If already completed, show summary
    results = st.session_state.apply_results
    if len(results) >= len(batch) and results:
        _show_summary(results, batch)
        if st.button("→ View Full Results   (Step 4)", use_container_width=True):
            st.session_state.apply_step = 4
            st.rerun()
        if st.button("← Back to Review"):
            st.session_state.apply_step = 2
            st.rerun()
        return

    # Explain modes
    st.markdown("""
<div style='background:#0c1a3a;border:1px solid #1e3a6a;border-radius:10px;padding:16px 20px;margin-bottom:16px;'>
  <div style='color:#60a5fa;font-size:13px;font-weight:600;margin-bottom:8px;'>📋 How Apply Works</div>
  <div style='color:#7a8faa;font-size:12px;line-height:1.9;'>
    <b style='color:#22d3a5;'>Log + Open URLs</b> — Instantly logs every application in your Tracker.
    Opens each job URL so you paste the cover letter and click Submit. ~30 seconds per job.
    Works on Streamlit Cloud and locally.<br>
    <b style='color:#6366f1;'>Full Auto-Submit</b> — Selenium browser bot submits for you.
    Requires Chrome + running this app locally on your PC.
  </div>
</div>""", unsafe_allow_html=True)

    apply_mode = st.radio(
        "Select apply mode:",
        ["📋  Log + Open URLs  (Recommended — works everywhere)",
         "🤖  Full Auto-Submit  (Local PC only — needs Chrome + Selenium)"],
        key="apply_mode"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(f"🚀  Start Applying to {len(batch)} Jobs NOW", use_container_width=True):
        progress_box = st.empty()
        log_box      = st.empty()
        bar          = st.progress(0)
        log_lines    = [f"[INIT] Batch apply — {len(batch)} jobs..."]
        new_results  = {}

        for i, job in enumerate(batch):
            jid    = job.get("id","")
            title  = job.get("title","")
            co     = job.get("company","")
            score  = job.get("match_score", 0)
            portal = job.get("portal","").upper()

            progress_box.markdown(f"""
<div style='background:#111827;border:1px solid #1a2540;border-radius:8px;padding:12px 16px;'>
  <div style='font-size:11px;color:#6366f1;font-family:JetBrains Mono,monospace;margin-bottom:4px;'>
    APPLYING [{i+1}/{len(batch)}]</div>
  <div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{title} @ {co}</div>
  <div style='font-size:12px;color:#4a6080;margin-top:2px;'>{portal} · {score}% match</div>
</div>""", unsafe_allow_html=True)

            log_lines.append(f"[{i+1}/{len(batch)}] {title[:32]} @ {co[:18]} ({portal})")
            log_box.markdown(
                f'<div class="terminal-log">{"<br>".join(log_lines[-8:])}</div>',
                unsafe_allow_html=True
            )
            bar.progress(int((i + 0.5) / len(batch) * 100))

            # Get or generate cover letter
            cl = st.session_state.apply_cover_letters.get(jid, "")
            if not cl:
                try:
                    cl = generate_cover_letter(job, prefs,
                                               prefs.get("cover_letter_template",""), api_key)
                except Exception:
                    cl = _fallback_cl(job, prefs)
                st.session_state.apply_cover_letters[jid] = cl

            result = {
                "job_id": jid, "title": title, "company": co,
                "portal": job.get("portal",""), "score": score,
                "url": job.get("url",""), "cover_letter": cl,
                "timestamp": datetime.now().isoformat()
            }

            if "Log + Open" in apply_mode:
                try:
                    log_application(job, cl, "applied")
                    job["status"] = "applied"
                except Exception:
                    pass
                result["status"] = "logged"
                result["action"] = "Logged — open URL to submit"
                log_lines.append(f"    ✓ Logged + URL ready")

            else:
                sel = _try_selenium(job, prefs, settings, cl)
                if sel.get("success"):
                    try:
                        log_application(job, cl, "applied")
                        job["status"] = "applied"
                    except Exception:
                        pass
                    result["status"] = "submitted"
                    result["action"] = sel.get("reason","Auto-submitted")
                    log_lines.append(f"    ✓ Submitted via bot")
                else:
                    reason = sel.get("reason","Selenium not available on cloud")
                    try:
                        log_application(job, cl, f"failed:{reason[:30]}")
                    except Exception:
                        pass
                    result["status"] = "failed"
                    result["action"] = reason[:40]
                    log_lines.append(f"    ✗ {reason[:40]}")

            new_results[jid] = result
            time.sleep(0.15)

        try:
            save_jobs(jobs)
        except Exception:
            pass

        bar.progress(100)
        st.session_state.apply_results = new_results

        success_n = sum(1 for r in new_results.values()
                        if r.get("status") in ["logged","submitted"])
        log_lines.append(f"[DONE] ✓ {success_n}/{len(batch)} processed")
        log_box.markdown(
            f'<div class="terminal-log">{"<br>".join(log_lines)}</div>',
            unsafe_allow_html=True
        )
        progress_box.empty()
        _show_summary(new_results, batch)
        st.success(f"✓ {success_n} applications logged! Click 'View Full Results' for links.")
        time.sleep(0.3)
        st.rerun()

    if st.button("← Back to Review"):
        st.session_state.apply_step = 2
        st.rerun()


# ─────────────────────────────────────────────────────────────
# STEP 4 — Results + URL opener
# ─────────────────────────────────────────────────────────────
def _step4():
    results = st.session_state.apply_results
    batch   = st.session_state.apply_batch

    st.markdown('<div class="section-header">BATCH RESULTS</div>', unsafe_allow_html=True)

    if not results:
        st.info("No results yet. Start from Step 1.")
        if st.button("← Start New Batch"):
            _reset()
        return

    success = [r for r in results.values() if r.get("status") in ["logged","submitted"]]
    failed  = [r for r in results.values() if r.get("status") == "failed"]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(results)}</div><div class="metric-label">Total Processed</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#22d3a5;">{len(success)}</div><div class="metric-label">Logged ✓</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#f87171;">{len(failed)}</div><div class="metric-label">Failed ✗</div></div>', unsafe_allow_html=True)
    avg = int(sum(r.get("score",0) for r in results.values()) / max(len(results),1))
    c4.markdown(f'<div class="metric-card"><div class="metric-value">{avg}%</div><div class="metric-label">Avg Match</div></div>', unsafe_allow_html=True)

    # URL opener for logged apps
    url_jobs = [r for r in results.values() if r.get("url") and r.get("status") == "logged"]
    if url_jobs:
        st.markdown('<div class="section-header">OPEN & SUBMIT — ONE CLICK PER JOB</div>',
                    unsafe_allow_html=True)
        st.markdown("""<div class="insight-card info">
<div style='font-size:13px;color:#a5b4fc;font-weight:600;margin-bottom:4px;'>🔗 Applications logged. Now submit each one:</div>
<div style='font-size:12px;color:#7a8faa;'>Click "Open & Apply →" → paste your cover letter → hit Submit. Takes ~30 seconds each.</div>
</div>""", unsafe_allow_html=True)

        for r in url_jobs:
            score = r.get("score", 0)
            sc    = "score-high" if score>=70 else ("score-mid" if score>=50 else "score-low")
            st.markdown(f"""<div class="job-card">
<div style='display:flex;justify-content:space-between;align-items:center;'>
  <div>
    <div class="job-title">{r.get('title','')}
      <span class="job-company"> @ {r.get('company','')}</span></div>
    <div class="job-meta">{r.get('portal','').upper()} · {r.get('timestamp','')[:10]}</div>
  </div>
  <div style='display:flex;align-items:center;gap:12px;'>
    <span class="match-score {sc}">{score}%</span>
    <a href="{r['url']}" target="_blank"
       style='background:#6366f1;color:#fff;padding:6px 14px;border-radius:6px;
              font-size:12px;font-weight:600;text-decoration:none;white-space:nowrap;'>
      Open & Apply →</a>
  </div>
</div>
</div>""", unsafe_allow_html=True)

            with st.expander(f"📋 Cover letter — {r.get('title','')} @ {r.get('company','')}"):
                cl = r.get("cover_letter","")
                st.text_area("Copy this into the application form:",
                             value=cl, height=200,
                             key=f"rc_{r.get('job_id','')}")
                st.download_button("⬇️ Download TXT", data=cl,
                                   file_name=f"cl_{r.get('company','')}.txt",
                                   key=f"rd_{r.get('job_id','')}")

    # Full log
    st.markdown('<div class="section-header">FULL APPLICATION LOG</div>', unsafe_allow_html=True)
    for r in results.values():
        ok    = r.get("status") in ["logged","submitted"]
        icon  = "✓" if ok else "✗"
        color = "#22d3a5" if ok else "#f87171"
        bg    = "#052e16" if ok else "#1c0a0a"
        bdr   = "#166534" if ok else "#7f1d1d"
        st.markdown(f"""<div style='background:{bg};border:1px solid {bdr};border-radius:8px;
padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;'>
<div>
  <span style='color:{color};font-family:JetBrains Mono,monospace;font-weight:700;margin-right:8px;'>{icon}</span>
  <span style='color:#e2e8f0;font-size:13px;'>{r.get('title','')} @ {r.get('company','')}</span>
  <span style='color:#4a6080;font-size:11px;margin-left:10px;
        font-family:JetBrains Mono,monospace;'>{r.get('portal','').upper()}</span>
</div>
<div style='font-size:11px;color:{color};font-family:JetBrains Mono,monospace;'>
  {r.get("action","")[:35].upper()}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Start New Batch", use_container_width=True):
            _reset()
    with c2:
        if st.button("📊 Go to Tracker & Analytics", use_container_width=True):
            # Works with st.radio nav — user clicks Tracker in sidebar
            st.info("→ Click 'Tracker & Analytics' in the left sidebar to view your full pipeline.")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _show_summary(results, batch):
    success = sum(1 for r in results.values() if r.get("status") in ["logged","submitted"])
    st.markdown(f"""
<div style='background:linear-gradient(135deg,#052e16,#0f2d1a);border:1px solid #166534;
border-radius:10px;padding:20px 24px;margin:16px 0;'>
  <div style='font-size:16px;font-weight:700;color:#22d3a5;margin-bottom:12px;'>Batch Complete ✓</div>
  <div style='display:flex;gap:32px;'>
    <div><div style='font-size:32px;font-weight:800;color:#22d3a5;font-family:JetBrains Mono,monospace;'>{success}</div>
         <div style='font-size:11px;color:#4a6080;'>Logged</div></div>
    <div><div style='font-size:32px;font-weight:800;color:#e2e8f0;font-family:JetBrains Mono,monospace;'>{len(batch)}</div>
         <div style='font-size:11px;color:#4a6080;'>Total</div></div>
    <div><div style='font-size:32px;font-weight:800;color:#6366f1;font-family:JetBrains Mono,monospace;'>{int(success/max(len(batch),1)*100)}%</div>
         <div style='font-size:11px;color:#4a6080;'>Success</div></div>
  </div>
</div>""", unsafe_allow_html=True)


def _try_selenium(job, prefs, settings, cover_letter):
    try:
        from core.apply_bot import auto_apply_job
        return auto_apply_job(job, prefs, settings, cover_letter)
    except ImportError:
        return {"success":False, "reason":"Selenium not installed (pip install selenium webdriver-manager)"}
    except Exception as e:
        return {"success":False, "reason":str(e)[:60]}


def _fallback_cl(job, prefs):
    name = (prefs.get("name") or "Jitendra Parida")
    role = job.get("title","Finance Role")
    co   = job.get("company","your company")
    exp  = prefs.get("experience_years", 6)
    kws  = ", ".join((prefs.get("keywords") or ["FP&A","SAP","Power BI"])[:3])
    return (f"With {exp}+ years driving FP&A and supply chain finance across FMCG portfolios, "
            f"I bring the analytical rigour and commercial insight that the {role} role at {co} demands.\n\n"
            f"In my current role at IBM supporting Reckitt's MENARP and Africa markets, I manage a £60M "
            f"supply chain P&L — owning period-close, variance analysis, and Finance Director-level reporting. "
            f"Previously at Capgemini supporting Unilever, I built automated MIS frameworks that cut "
            f"reporting cycle time by 40%.\n\n"
            f"For {co}, I offer hands-on {kws} expertise, supply chain finance (DIO/DSO, working capital "
            f"optimisation), and a strong ERP/BI stack (SAP, Power BI, advanced Excel).\n\n"
            f"I'd welcome a conversation about contributing to your finance team.\n\n"
            f"Best regards,\n{name}")


def _reset():
    for k in ["apply_step","apply_batch","apply_results",
              "apply_approved","apply_cover_letters","apply_limit"]:
        st.session_state.pop(k, None)
    st.rerun()
