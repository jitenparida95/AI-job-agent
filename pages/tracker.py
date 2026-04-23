import streamlit as st
from core.store import get_tracker, save_tracker, get_applied, save_applied, add_tracker_entry
from datetime import datetime, date


STATUSES = ["Applied", "Viewed", "Interview Scheduled", "Technical Round",
            "HR Round", "Final Round", "Offer Received", "Rejected", "Ghosted", "Withdrawn"]

STATUS_BADGES = {
    "Applied": "badge-applied", "Viewed": "badge-applied",
    "Interview Scheduled": "badge-interview", "Technical Round": "badge-interview",
    "HR Round": "badge-interview", "Final Round": "badge-interview",
    "Offer Received": "badge-offer",
    "Rejected": "badge-rejected", "Ghosted": "badge-rejected",
    "Withdrawn": "badge-pending",
}


def render():
    tracker = get_tracker()
    applied = get_applied()
    all_apps = _merge(tracker, applied)

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 5</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Application Tracker</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Track every application. Know your conversion rates. Spot what's working.</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Pipeline", "➕ Log Application", "📈 Analytics"])

    with tab1:
        # ── Metrics ──────────────────────────────────────────
        total = len(all_apps)
        interviews = len([a for a in all_apps if "Interview" in a.get("status", "") or "Round" in a.get("status", "")])
        offers = len([a for a in all_apps if "Offer" in a.get("status", "")])
        rejected = len([a for a in all_apps if a.get("status") in ["Rejected", "Ghosted"]])
        active = total - rejected - offers

        c1, c2, c3, c4, c5 = st.columns(5)
        for col, val, label, color in [
            (c1, total, "Total Tracked", "#e2e8f0"),
            (c2, active, "Active", "#6366f1"),
            (c3, interviews, "Interviews", "#a5b4fc"),
            (c4, offers, "Offers", "#fbbf24"),
            (c5, rejected, "Rejected / Ghosted", "#f87171"),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-value" style="color:{color}">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        # Conversion funnel
        if total > 0:
            int_rate = int(interviews / total * 100)
            offer_rate = int(offers / total * 100) if total else 0
            st.markdown(f"""
            <div style='background:#0c1020; border:1px solid #1a2540; border-radius:10px; padding:16px 20px; margin: 10px 0 20px;'>
                <div style='font-size:11px; color:#4a6080; font-family:JetBrains Mono,monospace; letter-spacing:.1em; margin-bottom:10px;'>CONVERSION FUNNEL</div>
                <div style='display:flex; gap:8px; align-items:center;'>
                    <div style='flex:1; text-align:center;'>
                        <div style='font-size:22px; font-weight:700; color:#e2e8f0; font-family:JetBrains Mono,monospace;'>{total}</div>
                        <div style='font-size:10px; color:#4a6080;'>Applied</div>
                    </div>
                    <div style='color:#2d4060; font-size:20px;'>→</div>
                    <div style='flex:1; text-align:center;'>
                        <div style='font-size:22px; font-weight:700; color:#6366f1; font-family:JetBrains Mono,monospace;'>{interviews} <span style="font-size:13px;">({int_rate}%)</span></div>
                        <div style='font-size:10px; color:#4a6080;'>Interviews</div>
                    </div>
                    <div style='color:#2d4060; font-size:20px;'>→</div>
                    <div style='flex:1; text-align:center;'>
                        <div style='font-size:22px; font-weight:700; color:#fbbf24; font-family:JetBrains Mono,monospace;'>{offers} <span style="font-size:13px;">({offer_rate}%)</span></div>
                        <div style='font-size:10px; color:#4a6080;'>Offers</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Filters ───────────────────────────────────────────
        col_filter, col_sort = st.columns([3, 1])
        with col_filter:
            status_filter = st.multiselect("Filter by Status", STATUSES, default=[], label_visibility="collapsed",
                                           placeholder="Filter by status...")
        with col_sort:
            sort_by = st.selectbox("Sort", ["Newest First", "Oldest First", "By Match Score"], label_visibility="collapsed")

        filtered = all_apps if not status_filter else [a for a in all_apps if a.get("status") in status_filter]

        if sort_by == "Oldest First":
            filtered = sorted(filtered, key=lambda x: x.get("applied_at") or x.get("created_at", ""))
        elif sort_by == "By Match Score":
            filtered = sorted(filtered, key=lambda x: x.get("match_score") or 0, reverse=True)
        else:
            filtered = sorted(filtered, key=lambda x: x.get("applied_at") or x.get("created_at", ""), reverse=True)

        st.markdown(f'<div class="section-header">APPLICATIONS ({len(filtered)} shown)</div>', unsafe_allow_html=True)

        if not filtered:
            st.markdown("""<div style='text-align:center; padding: 48px; background: #0c1020; border: 1px dashed #1a2540; border-radius: 12px;'>
                <div style='font-size: 13px; color: #4a6080;'>No applications tracked yet. Log your first application →</div>
            </div>""", unsafe_allow_html=True)
        else:
            for app in filtered[:50]:
                score = app.get("match_score", 0) or 0
                score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
                status = app.get("status", "Applied")
                badge_cls = STATUS_BADGES.get(status, "badge-pending")
                date_str = (app.get("applied_at") or app.get("created_at", ""))[:10]
                app_id = app.get("id", "")

                with st.expander(f"{app.get('title', 'Unknown')} @ {app.get('company', '')} · {status}"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"""
                        <div style='margin-bottom:8px;'>
                            <span class='status-badge {badge_cls}'>{status}</span>
                            {f'<span style="margin-left:10px; font-size:12px; color:#4a6080;">Match: <span class="{score_cls}">{score}%</span></span>' if score else ''}
                        </div>
                        <div style='font-size:13px; color:#7a8faa;'>
                            Portal: {app.get('portal', 'Manual').upper()} · Applied: {date_str}
                        </div>
                        {f'<div style="margin-top:8px;"><a href="{app.get("url")}" target="_blank" style="color:#6366f1; font-size:12px;">View Job →</a></div>' if app.get("url") else ''}
                        """, unsafe_allow_html=True)

                        notes = st.text_area("Notes", value=app.get("notes", ""), key=f"notes_{app_id}", height=60, label_visibility="collapsed", placeholder="Add notes (interview feedback, next steps...)")
                    with c2:
                        new_status = st.selectbox("Update Status", STATUSES,
                                                   index=STATUSES.index(status) if status in STATUSES else 0,
                                                   key=f"status_{app_id}")
                        if st.button("Save", key=f"save_{app_id}", use_container_width=True):
                            _update_app(app_id, new_status, notes, tracker, applied)
                            st.success("Updated!")
                            st.rerun()

    with tab2:
        st.markdown('<div class="section-header">LOG A NEW APPLICATION</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            role = st.text_input("Job Title *", placeholder="e.g. FP&A Manager")
            company = st.text_input("Company *", placeholder="e.g. Nestlé India")
            portal = st.selectbox("Platform", ["LinkedIn", "Naukri", "Instahyre", "Company Website",
                                               "Referral", "Foundit", "Wellfound", "Email", "Other"])
        with c2:
            status = st.selectbox("Current Status", STATUSES)
            app_date = st.date_input("Application Date", value=date.today())
            match_score = st.slider("Your Confidence / Match Score (%)", 0, 100, 70)

        job_url = st.text_input("Job URL (optional)")
        notes = st.text_area("Notes / Next Steps", height=60)

        if st.button("➕ Log Application", use_container_width=True):
            if role and company:
                add_tracker_entry({
                    "title": role, "company": company,
                    "portal": portal.lower(), "status": status,
                    "match_score": match_score,
                    "url": job_url, "notes": notes,
                    "applied_at": app_date.isoformat(),
                })
                st.success(f"✓ Logged: {role} at {company}")
                st.rerun()
            else:
                st.error("Job Title and Company are required.")

    with tab3:
        if not all_apps:
            st.info("Log at least one application to see analytics.")
            return

        st.markdown('<div class="section-header">PERFORMANCE ANALYTICS</div>', unsafe_allow_html=True)

        # Status breakdown
        status_counts = {}
        for a in all_apps:
            s = a.get("status", "Applied")
            status_counts[s] = status_counts.get(s, 0) + 1

        col_chart, col_stats = st.columns([2, 1])
        with col_chart:
            st.markdown("**Applications by Status**")
            for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
                pct = int(count / total * 100)
                badge = STATUS_BADGES.get(status, "badge-pending")
                st.markdown(f"""<div style='display:flex; align-items:center; margin-bottom:6px;'>
                    <div style='width:140px; font-size:12px; color:#7a8faa;'>{status}</div>
                    <div style='flex:1; background:#1a2540; border-radius:4px; height:20px; overflow:hidden; margin:0 10px;'>
                        <div style='width:{pct}%; height:100%; background:linear-gradient(90deg, #6366f1, #22d3a5); border-radius:4px;'></div>
                    </div>
                    <div style='font-size:12px; font-family:JetBrains Mono,monospace; color:#e2e8f0; width:30px; text-align:right;'>{count}</div>
                </div>""", unsafe_allow_html=True)

        with col_stats:
            avg_score = int(sum(a.get("match_score") or 0 for a in all_apps) / max(total, 1))
            portals = {}
            for a in all_apps:
                p = a.get("portal", "other")
                portals[p] = portals.get(p, 0) + 1
            best_portal = max(portals, key=portals.get) if portals else "—"

            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{avg_score}%</div>
                <div class="metric-label">Avg Match Score</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value" style="font-size:18px;">{best_portal.title()}</div>
                <div class="metric-label">Most Active Platform</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value" style="color:{'#22d3a5' if int_rate >= 15 else '#f59e0b'}">{int_rate}%</div>
                <div class="metric-label">Interview Rate</div>
            </div>""", unsafe_allow_html=True)

        # Weekly performance
        st.markdown('<div class="section-header">THIS WEEK\'S PERFORMANCE</div>', unsafe_allow_html=True)
        from datetime import timedelta
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        weekly = [a for a in all_apps if (a.get("applied_at") or a.get("created_at", ""))[:10] >= str(week_start)]
        weekly_interviews = len([a for a in weekly if "Interview" in a.get("status", "")])
        weekly_score = min(100, len(weekly) * 7 + weekly_interviews * 15)
        score_color = "#22d3a5" if weekly_score >= 70 else ("#f59e0b" if weekly_score >= 40 else "#f87171")

        st.markdown(f"""<div style='background:#0c1020; border:1px solid #1a2540; border-radius:10px; padding:18px 22px; display:flex; align-items:center; gap:24px;'>
            <div style='text-align:center;'>
                <div style='font-size:40px; font-weight:800; color:{score_color}; font-family:JetBrains Mono,monospace;'>{weekly_score}</div>
                <div style='font-size:11px; color:#4a6080;'>Weekly Score</div>
            </div>
            <div>
                <div style='font-size:14px; color:#e2e8f0; font-weight:600; margin-bottom:6px;'>
                    {len(weekly)} applications this week · {weekly_interviews} interviews
                </div>
                <div style='font-size:13px; color:#7a8faa;'>
                    {'🔥 Excellent pace! Keep it up.' if weekly_score >= 70 else '📈 Increase your weekly application volume to 10-15 for faster results.' if weekly_score >= 40 else '⚡ Start logging applications to build momentum.'}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


def _merge(tracker, applied):
    merged = list(tracker)
    existing_ids = {t.get("id") for t in tracker}
    for a in applied:
        if a.get("id") not in existing_ids:
            a_copy = dict(a)
            if "result" in a_copy and "status" not in a_copy:
                a_copy["status"] = "Applied" if a_copy["result"] == "applied" else "Rejected"
            merged.append(a_copy)
    return merged


def _update_app(app_id, new_status, notes, tracker, applied):
    for t in tracker:
        if t.get("id") == app_id:
            t["status"] = new_status
            t["notes"] = notes
            t["last_updated"] = datetime.now().isoformat()
    save_tracker(tracker)
    for a in applied:
        if a.get("id") == app_id:
            a["status"] = new_status
            a["notes"] = notes
            a["last_updated"] = datetime.now().isoformat()
    save_applied(applied)
