"""
Trickee EV Intelligence Platform
=================================
Pitch Dashboard — powered by real Charge-Up BMS telemetry (chargeup.txt)
5 vehicles | Oct 24, 2025 | GreenFuel & Inverted e-rickshaw fleets

Run:  streamlit run chargeup_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import time
import os

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trickee — EV Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
TEAL   = "#00d4ff"
GREEN  = "#00c853"
ORANGE = "#ff6b35"
RED    = "#ff3b30"
GOLD   = "#ffd600"
BG     = "#0d1117"
CARD   = "#13203a"
BORDER = "#1f3a5f"
DIM    = "#7d9bbd"

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  .stApp {{ background-color: {BG} !important; }}

  /* Metric cards */
  div[data-testid="metric-container"] {{
      background: linear-gradient(135deg, {CARD} 0%, #1a2d4a 100%);
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 16px 20px;
      box-shadow: 0 4px 16px rgba(0,212,255,0.06);
  }}
  div[data-testid="metric-container"] label {{
      color: {DIM} !important; font-size: 11px !important;
      text-transform: uppercase; letter-spacing: 0.6px;
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
      background: {CARD}; border-radius: 10px; padding: 4px; gap: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
      color: {DIM}; border-radius: 8px; padding: 8px 18px; font-weight: 600;
  }}
  .stTabs [aria-selected="true"] {{
      background: {BORDER}; color: {TEAL} !important;
  }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
      background: {CARD} !important;
      border-right: 1px solid {BORDER};
  }}

  /* Typography helpers */
  .t-header {{
      font-size: 30px; font-weight: 900;
      background: linear-gradient(90deg, {TEAL}, {GREEN});
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .t-sub {{
      font-size: 13px; color: {DIM}; margin-bottom: 4px;
  }}
  .t-section {{
      font-size: 17px; font-weight: 700; color: {TEAL};
      border-left: 3px solid {TEAL}; padding-left: 10px;
      margin: 22px 0 10px 0;
  }}

  /* Status chips */
  .chip {{
      display: inline-block; padding: 4px 12px;
      border-radius: 12px; font-size: 12px; font-weight: 700;
  }}
  .chip-charging    {{ background: {GREEN};  color: #000; }}
  .chip-discharging {{ background: {ORANGE}; color: #fff; }}
  .chip-idle        {{ background: #455a64; color: #fff; }}
  .chip-fault       {{ background: {RED};    color: #fff; }}
  .chip-ok          {{ background: {GREEN};  color: #000; }}

  /* KPI card (custom, not metric widget) */
  .kpi-card {{
      background: {CARD}; border: 1px solid {BORDER};
      border-radius: 14px; padding: 14px 16px; text-align: center;
  }}
  .kpi-label {{ font-size: 11px; color: {DIM}; text-transform: uppercase; letter-spacing: 0.5px; }}
  .kpi-value {{ font-size: 34px; font-weight: 900; margin: 6px 0; }}
  .kpi-sub   {{ font-size: 11px; color: #aaa; margin-top: 4px; }}

  /* Live badge */
  .live-badge {{
      display: inline-block; background: {RED}; color: #fff;
      padding: 3px 10px; border-radius: 10px;
      font-size: 11px; font-weight: 700;
      animation: blink 1.2s infinite;
  }}
  @keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}

  /* Sidebar snapshot rows */
  .snap-row {{ display: flex; justify-content: space-between; margin: 3px 0; }}
  .snap-name {{ font-size: 12px; color: #c9d1d9; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  DATA LOADING & PARSING
# ─────────────────────────────────────────────────────────────────────────────
CHARGEUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chargeup.txt")

@st.cache_data
def load_data():
    def sf(v, d=0.0):
        try:
            s = str(v).strip().strip('"')
            return float(s) if s else d
        except:
            return d

    def si(v, d=0):
        try:
            s = str(v).strip().strip('"')
            return int(float(s)) if s else d
        except:
            return d

    records = []
    with open(CHARGEUP_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("Received message:"):
                continue
            try:
                data = json.loads(line[len("Received message:"):].strip())
            except:
                continue

            attr  = data.get("attributes", {})
            tags  = data.get("devicetags", [])
            tag   = tags[0] if isinstance(tags, list) and tags else "Unknown"
            state = si(attr.get("CharDischarState", 0))

            # Extract & normalise 16 cell voltages (Inverted FW reports mV)
            cells = {f"C{i}": sf(attr.get(f"C{i}", 0)) for i in range(1, 17)}
            if cells.get("C1", 0) > 10:
                cells = {k: v / 1000.0 for k, v in cells.items()}

            max_cv = sf(attr.get("maxCellVoltage", 0))
            min_cv = sf(attr.get("minCellVoltage", 0))
            if max_cv > 10: max_cv /= 1000
            if min_cv > 10: min_cv /= 1000

            rec = dict(
                vehicle_id     = data.get("name", "Unknown"),
                tag            = tag,
                time           = pd.to_datetime(data.get("lastupdate")),
                latitude       = sf(data.get("latitude")),
                longitude      = sf(data.get("longitude")),
                speed          = sf(data.get("speed")),
                motion         = int(bool(data.get("motion", False))),
                soc            = si(attr.get("SOC")),
                soh            = si(attr.get("SOH")),
                batt_voltage   = sf(attr.get("battVoltage")),
                batt_current   = sf(attr.get("battCurrent")),
                batt_energy    = sf(attr.get("battEnergy") or 0),
                cycle_count    = si(attr.get("cycleCount")),
                charge_state   = state,
                charge_label   = {0: "Idle", 1: "Charging", 2: "Discharging"}.get(state, "Idle"),
                char_mos       = si(attr.get("charMOS")),
                dis_char_mos   = si(attr.get("disCharMOS")),
                temp1          = sf(attr.get("temp1")),
                temp2          = sf(attr.get("temp2")),
                temp3          = sf(attr.get("temp3")),
                temp4          = sf(attr.get("temp4")),
                mos_temp       = sf(attr.get("mosTemp")),
                max_temp       = sf(attr.get("maxTemp")),
                max_cell_v     = max_cv,
                min_cell_v     = min_cv,
                cell_volt_diff = sf(attr.get("cellVoltDiff", 0)),
                odokm          = sf(attr.get("odokm")),
                fw_version     = attr.get("fwVersion", ""),
                # Fault flags
                f_cov          = si(attr.get("COV", 0)),
                f_cuv          = si(attr.get("CUV", 0)),
                f_therm        = si(attr.get("thermRA", 0)),
                f_celldiff     = si(attr.get("cellDiffFault", 0)),
                f_short        = si(attr.get("shortCircuit", 0)),
                f_char_oc      = si(attr.get("charOCA", 0)),
                f_dis_oc       = si(attr.get("disOCA", 0)),
            )
            rec.update(cells)
            rec["power_w"] = rec["batt_voltage"] * rec["batt_current"]
            records.append(rec)

    df = pd.DataFrame(records)
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["msg_index"] = df.index
    return df


df       = load_data()
VEHICLES = sorted(df["vehicle_id"].unique())
N_MSGS   = len(df)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [
    ("msg_step", N_MSGS - 1),
    ("playing",  False),
    ("role",     "fleet"),
    ("sel_veh",  VEHICLES[0]),
    ("play_spd", 1.0),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=CARD,
    font=dict(color="#c9d1d9", size=12),
    margin=dict(l=12, r=12, t=44, b=12),
)

def soc_color(soc):
    if soc >= 60: return GREEN
    if soc >= 25: return GOLD
    return RED

def state_chip(label):
    cls  = {"Charging": "chip-charging", "Discharging": "chip-discharging", "Idle": "chip-idle"}.get(label, "chip-idle")
    icon = {"Charging": "🔌", "Discharging": "🏃", "Idle": "💤"}.get(label, "")
    return f'<span class="chip {cls}">{icon} {label}</span>'

def get_state(step):
    """Latest record per vehicle up to and including `step`."""
    sub = df[df.msg_index <= step]
    if sub.empty:
        return pd.DataFrame()
    return sub.loc[sub.groupby("vehicle_id")["msg_index"].idxmax()].reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="t-header">⚡ Trickee</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#7d9bbd;font-size:12px;margin-bottom:18px;">EV Intelligence Platform</div>', unsafe_allow_html=True)
    st.divider()

    # Role selector
    st.markdown("**👤 Dashboard Mode**")
    role_pick = st.radio(
        "",
        ["🏢  Fleet Manager", "🚗  Driver"],
        index=0 if st.session_state.role == "fleet" else 1,
        label_visibility="collapsed",
    )
    st.session_state.role = "fleet" if "Fleet" in role_pick else "driver"

    if st.session_state.role == "driver":
        st.markdown("**🚗 Select Your Vehicle**")
        sel = st.selectbox("", VEHICLES,
                           index=VEHICLES.index(st.session_state.sel_veh),
                           label_visibility="collapsed")
        st.session_state.sel_veh = sel

    st.divider()

    # ── REPLAY CONTROLS ──
    st.markdown("**📡 Live Telemetry Replay**")
    st.caption(f"Oct 24, 2025 · 11:03–11:05 IST · {N_MSGS} messages")

    step = st.slider(
        "Message Timeline",
        min_value=0, max_value=N_MSGS - 1,
        value=st.session_state.msg_step,
        key="timeline_slider",
    )
    st.session_state.msg_step = step

    cur_msg = df.iloc[st.session_state.msg_step]
    st.markdown(
        f'<div style="font-size:11px;color:{DIM};">'
        f'▶ Msg {step+1}/{N_MSGS} &nbsp;·&nbsp; '
        f'<b style="color:#c9d1d9;">{cur_msg["vehicle_id"]}</b> &nbsp;·&nbsp; '
        f'{cur_msg["time"].strftime("%H:%M:%S")} UTC</div>',
        unsafe_allow_html=True,
    )

    ca, cb = st.columns(2)
    play_clicked = ca.button(
        "⏸ Pause" if st.session_state.playing else "▶ Play",
        use_container_width=True,
    )
    if cb.button("⏮ Reset", use_container_width=True):
        st.session_state.msg_step = 0
        st.session_state.playing  = False
        st.rerun()
    if play_clicked:
        st.session_state.playing = not st.session_state.playing
        st.rerun()

    spd = st.select_slider(
        "Replay Speed", options=[0.5, 1.0, 2.0, 3.0],
        value=st.session_state.play_spd,
    )
    st.session_state.play_spd = spd

    st.divider()

    # Fleet snapshot
    snap = get_state(st.session_state.msg_step)
    if not snap.empty:
        st.markdown("**📊 All Vehicles**")
        for _, r in snap.iterrows():
            sc = soc_color(r.soc)
            st.markdown(
                f'<div class="snap-row">'
                f'<span class="snap-name">{r.vehicle_id}</span>'
                f'<span style="font-size:12px;color:{sc};font-weight:700;">{r.soc}% '
                f'{"🔌" if r.charge_label=="Charging" else ("🏃" if r.charge_label=="Discharging" else "💤")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-PLAY ENGINE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.playing:
    time.sleep(1.0 / max(st.session_state.play_spd, 0.1))
    if st.session_state.msg_step < N_MSGS - 1:
        st.session_state.msg_step += 1
    else:
        st.session_state.playing = False
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  CURRENT SNAPSHOT
# ─────────────────────────────────────────────────────────────────────────────
cur_state = get_state(st.session_state.msg_step)
cur_msg   = df.iloc[st.session_state.msg_step]

# ═════════════════════════════════════════════════════════════════════════════
#  ███████  FLEET MANAGER VIEW
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.role == "fleet":

    # ── Header ──
    h1, h2, h3 = st.columns([4, 1, 1])
    with h1:
        live_txt = (
            '<span class="live-badge">● PLAYING</span>'
            if st.session_state.playing
            else f'<span style="color:{DIM};font-size:12px;">⏸ Step {step+1}/{N_MSGS}</span>'
        )
        st.markdown(
            f'<div class="t-header">🏢 Fleet Intelligence Dashboard</div>'
            f'<div class="t-sub">{live_txt} &nbsp;·&nbsp; 5 Vehicles &nbsp;·&nbsp; '
            f'Charge-Up Fleet &nbsp;·&nbsp; Oct 24, 2025 (IST)</div>',
            unsafe_allow_html=True,
        )
    if not cur_state.empty:
        with h2:
            st.metric("Vehicles Active", int(cur_state[cur_state.speed > 0].shape[0]))
        with h3:
            st.metric("Charging Now", int(cur_state[cur_state.charge_label == "Charging"].shape[0]))

    st.divider()

    # ── 5 KPI Cards ──
    if not cur_state.empty:
        cols = st.columns(5)
        for i, (_, r) in enumerate(cur_state.iterrows()):
            sc  = soc_color(r.soc)
            chp = state_chip(r.charge_label)
            cols[i].markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{r.vehicle_id}</div>
              <div class="kpi-value" style="color:{sc};">{r.soc}%</div>
              <div class="kpi-sub">SOC</div>
              <div style="margin-top:6px;">{chp}</div>
              <div class="kpi-sub">{r.speed:.1f} km/h &nbsp;·&nbsp; {r.batt_voltage:.1f} V</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ──
    tab_map, tab_bat, tab_therm, tab_cells, tab_fault = st.tabs([
        "🗺️ Fleet Map",
        "⚡ Battery Analysis",
        "🌡️ Thermal Monitor",
        "🔬 Cell Analysis",
        "🚨 Fault Monitor",
    ])

    # ── TAB 1 · FLEET MAP ──────────────────────────────────────────────────
    with tab_map:
        st.markdown('<div class="t-section">📍 Live Vehicle Positions — Indian Fleet</div>', unsafe_allow_html=True)
        if not cur_state.empty:
            map_df = cur_state.copy()
            fig_map = px.scatter_mapbox(
                map_df,
                lat="latitude", lon="longitude",
                color="soc",
                color_continuous_scale=[[0, RED], [0.25, GOLD], [1, GREEN]],
                size=[30] * len(map_df),
                hover_name="vehicle_id",
                hover_data={
                    "soc": True, "charge_label": True, "speed": True,
                    "odokm": True, "cycle_count": True,
                    "latitude": False, "longitude": False,
                },
                zoom=5.2,
                center={"lat": 27.0, "lon": 77.5},
                mapbox_style="open-street-map",
                height=460,
                title="Fleet Positions — SOC Color-coded (Green=High, Red=Low)",
            )
            fig_map.update_layout(**DARK_LAYOUT, coloraxis_colorbar=dict(title="SOC%"))
            st.plotly_chart(fig_map, use_container_width=True)

            # Status table
            st.markdown('<div class="t-section">📋 Vehicle Status Table</div>', unsafe_allow_html=True)
            tbl = cur_state[["vehicle_id","tag","soc","soh","batt_voltage","batt_current",
                              "speed","odokm","cycle_count","charge_label","max_temp"]].copy()
            tbl.columns = ["Vehicle","Fleet","SOC%","SOH%","Volts(V)","Amps(A)",
                           "Speed(km/h)","Odo(km)","Cycles","State","MaxTemp°C"]
            st.dataframe(tbl, use_container_width=True, hide_index=True)

    # ── TAB 2 · BATTERY ANALYSIS ──────────────────────────────────────────
    with tab_bat:
        if not cur_state.empty:
            c1, c2 = st.columns(2)

            # SOC comparison horizontal bar
            with c1:
                st.markdown('<div class="t-section">State of Charge</div>', unsafe_allow_html=True)
                fig_soc = go.Figure()
                for _, r in cur_state.sort_values("soc").iterrows():
                    fig_soc.add_trace(go.Bar(
                        x=[r.soc], y=[r.vehicle_id], orientation="h",
                        marker_color=soc_color(r.soc),
                        text=f"{r.soc}%", textposition="auto",
                        showlegend=False,
                        hovertemplate=f"<b>{r.vehicle_id}</b><br>SOC: {r.soc}%<br>{r.batt_voltage:.2f}V<extra></extra>",
                    ))
                fig_soc.add_vline(x=20, line_dash="dash", line_color=RED,
                                  annotation_text="Low Bat", annotation_font_color=RED)
                fig_soc.update_layout(
                    **DARK_LAYOUT, height=280,
                    xaxis=dict(range=[0, 108], title="SOC (%)", gridcolor=BORDER),
                    yaxis=dict(title=""),
                    title="Fleet SOC at Replay Step",
                )
                st.plotly_chart(fig_soc, use_container_width=True)

            # Cycle count (battery age)
            with c2:
                st.markdown('<div class="t-section">Battery Age — Charge Cycles</div>', unsafe_allow_html=True)
                fig_age = go.Figure()
                for _, r in cur_state.iterrows():
                    hc = GREEN if r.soh >= 95 else (GOLD if r.soh >= 85 else RED)
                    fig_age.add_trace(go.Bar(
                        x=[r.vehicle_id], y=[r.cycle_count],
                        marker_color=hc, showlegend=False,
                        text=f"{r.cycle_count}c", textposition="auto",
                        hovertemplate=f"<b>{r.vehicle_id}</b><br>Cycles: {r.cycle_count}<br>SOH: {r.soh}%<br>Odo: {r.odokm:.0f}km<extra></extra>",
                    ))
                fig_age.add_hline(y=500, line_dash="dash", line_color=ORANGE,
                                  annotation_text="500c Alert", annotation_font_color=ORANGE)
                fig_age.update_layout(
                    **DARK_LAYOUT, height=280,
                    yaxis=dict(title="Cycles Used", gridcolor=BORDER),
                    xaxis=dict(title=""),
                    title="Charge Cycles per Vehicle (Color = SOH)",
                )
                st.plotly_chart(fig_age, use_container_width=True)

            # Power flow
            st.markdown('<div class="t-section">⚡ Instantaneous Power Flow</div>', unsafe_allow_html=True)
            fig_pwr = go.Figure()
            for _, r in cur_state.iterrows():
                pc = GREEN if r.power_w >= 0 else ORANGE
                fig_pwr.add_trace(go.Bar(
                    x=[r.vehicle_id], y=[r.power_w],
                    marker_color=pc, showlegend=False,
                    text=f"{r.power_w:+.0f}W", textposition="auto",
                    hovertemplate=(
                        f"<b>{r.vehicle_id}</b><br>"
                        f"Power: {r.power_w:.1f}W<br>"
                        f"Voltage: {r.batt_voltage:.2f}V | Current: {r.batt_current:.2f}A<extra></extra>"
                    ),
                ))
            fig_pwr.add_hline(y=0, line_color="#ffffff", line_width=1)
            fig_pwr.update_layout(
                **DARK_LAYOUT, height=300,
                yaxis=dict(title="Power (W)   [+ Charging | − Discharging]", gridcolor=BORDER),
                xaxis=dict(title=""),
                title="Power Flow — Positive = Charging, Negative = Discharging",
            )
            st.plotly_chart(fig_pwr, use_container_width=True)

    # ── TAB 3 · THERMAL MONITOR ────────────────────────────────────────────
    with tab_therm:
        if not cur_state.empty:
            st.markdown('<div class="t-section">Sensor Readings per Vehicle</div>', unsafe_allow_html=True)

            temp_rows = []
            for _, r in cur_state.iterrows():
                for sensor, val in [("Sensor-1", r.temp1), ("Sensor-2", r.temp2),
                                     ("Sensor-3", r.temp3), ("Sensor-4", r.temp4),
                                     ("MOS Temp",  r.mos_temp)]:
                    if val and val > 1:
                        temp_rows.append({"Vehicle": r.vehicle_id, "Sensor": sensor, "Temp (°C)": val})
            temp_df = pd.DataFrame(temp_rows)

            if not temp_df.empty:
                fig_temp = px.bar(
                    temp_df, x="Sensor", y="Temp (°C)", color="Temp (°C)",
                    facet_col="Vehicle", facet_col_wrap=5,
                    color_continuous_scale=[[0, GREEN], [0.5, GOLD], [0.75, ORANGE], [1, RED]],
                    range_color=[20, 55],
                    height=380,
                    title="Temperature Sensors — Red ≥ 45°C = Danger Zone",
                )
                fig_temp.add_hline(y=45, line_dash="dash", line_color=RED,
                                   annotation_text="45°C threshold")
                fig_temp.update_layout(**DARK_LAYOUT)
                st.plotly_chart(fig_temp, use_container_width=True)

            # ── Thermal × Current abuse scatter (like ev_pitch_dashboard Tab2) ──
            st.markdown('<div class="t-section">🔥 Thermal Abuse Monitor — Temp vs Load</div>', unsafe_allow_html=True)
            st.caption("High current at high temperature = battery damage. Trickee flags this in real-time before the BMS catches it.")

            fig_abuse = px.scatter(
                cur_state,
                x="max_temp", y="batt_current",
                color="soc",
                color_continuous_scale=[[0, RED], [0.5, GOLD], [1, GREEN]],
                size="cycle_count", size_max=50,
                text="vehicle_id",
                hover_data=["soh", "charge_label", "speed", "batt_voltage"],
                labels={"max_temp": "Max Cell Temperature (°C)",
                        "batt_current": "Battery Current (A)", "soc": "SOC%"},
                title="Thermal vs Load Matrix — All Vehicles",
                height=400,
            )
            fig_abuse.update_traces(textposition="top center")
            # Danger zone overlay
            fig_abuse.add_hrect(
                y0=25, y1=200, x0=42, x1=60,
                fillcolor=RED, opacity=0.08,
                annotation_text="⚠️ Warranty Risk Zone",
                annotation_font_color=RED, annotation_font_size=13,
            )
            fig_abuse.update_layout(
                **DARK_LAYOUT,
                xaxis=dict(gridcolor=BORDER),
                yaxis=dict(gridcolor=BORDER),
            )
            st.plotly_chart(fig_abuse, use_container_width=True)

    # ── TAB 4 · CELL ANALYSIS ──────────────────────────────────────────────
    with tab_cells:
        if not cur_state.empty:
            st.markdown('<div class="t-section">🔬 16-Cell Voltage Heatmap — All Vehicles</div>', unsafe_allow_html=True)
            st.caption("Each row = one vehicle | Each column = one cell (C1–C16) | Target LFP voltage ≈ 3.30 V | Colour deviation = imbalance")

            cell_cols = [f"C{i}" for i in range(1, 17)]
            heat_z, heat_y = [], []
            for _, r in cur_state.iterrows():
                vals = [float(r.get(c, 0) or 0) for c in cell_cols]
                if any(v > 0 for v in vals):
                    heat_z.append(vals)
                    heat_y.append(r.vehicle_id)

            if heat_z:
                fig_heat = go.Figure(data=go.Heatmap(
                    z=heat_z, x=cell_cols, y=heat_y,
                    colorscale=[
                        [0.0, RED],    # < 3.20 V (very low)
                        [0.35, GOLD],  # ~3.24 V
                        [0.55, GREEN], # ~3.30 V (ideal LFP)
                        [0.75, GOLD],  # ~3.36 V
                        [1.0,  RED],   # > 3.40 V (too high)
                    ],
                    zmin=3.18, zmax=3.42,
                    colorbar=dict(
                        title="Volts",
                        tickfont=dict(color="#c9d1d9"),
                        tickvals=[3.20, 3.25, 3.30, 3.35, 3.40],
                    ),
                    hovertemplate="<b>%{y}</b> · %{x}: <b>%{z:.4f} V</b><extra></extra>",
                ))
                fig_heat.update_layout(
                    **DARK_LAYOUT, height=310,
                    xaxis=dict(title="Cell Number", tickfont=dict(color="#c9d1d9")),
                    yaxis=dict(title="", tickfont=dict(color="#c9d1d9")),
                    title="Cell Voltage Heatmap — Green = Balanced | Red = Deviation",
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            # Pack imbalance bar
            st.markdown('<div class="t-section">📊 Pack Imbalance (Max − Min Cell Voltage)</div>', unsafe_allow_html=True)
            st.caption("< 20 mV = Healthy &nbsp;·&nbsp; 20–50 mV = Monitor &nbsp;·&nbsp; > 50 mV = Requires Action")

            imbal = cur_state[["vehicle_id", "cell_volt_diff"]].copy()
            imbal["mV"]     = imbal["cell_volt_diff"] * 1000
            imbal["Status"] = imbal["mV"].apply(
                lambda x: "Critical" if x > 50 else ("Monitor" if x > 20 else "Healthy")
            )
            color_map = {"Critical": RED, "Monitor": GOLD, "Healthy": GREEN}

            fig_imbal = px.bar(
                imbal.sort_values("mV"),
                x="mV", y="vehicle_id", orientation="h",
                color="Status", color_discrete_map=color_map,
                text="mV",
                labels={"mV": "Imbalance (mV)", "vehicle_id": ""},
                title="Cell Voltage Spread per Vehicle",
                height=280,
            )
            fig_imbal.update_traces(texttemplate="%{text:.1f} mV", textposition="auto")
            fig_imbal.add_vline(x=20, line_dash="dash", line_color=GOLD,
                                annotation_text="Monitor", annotation_font_color=GOLD)
            fig_imbal.add_vline(x=50, line_dash="dash", line_color=RED,
                                annotation_text="Action!", annotation_font_color=RED)
            fig_imbal.update_layout(**DARK_LAYOUT, xaxis=dict(gridcolor=BORDER))
            st.plotly_chart(fig_imbal, use_container_width=True)

    # ── TAB 5 · FAULT MONITOR ─────────────────────────────────────────────
    with tab_fault:
        if not cur_state.empty:
            st.markdown('<div class="t-section">🚨 BMS Fault Flag Grid — Real-time</div>', unsafe_allow_html=True)
            st.caption("All GREEN = healthy fleet. Trickee detects faults 30 s after BMS triggers — before the driver notices.")

            FLAG_MAP = {
                "Cell OV":   "f_cov",
                "Cell UV":   "f_cuv",
                "Therm RA":  "f_therm",
                "Cell Diff": "f_celldiff",
                "Short Ckt": "f_short",
                "Charge OC": "f_char_oc",
                "Disch OC":  "f_dis_oc",
            }

            z, y_lbls = [], []
            for _, r in cur_state.iterrows():
                row_vals = [int(r.get(col, 0) or 0) for col in FLAG_MAP.values()]
                z.append(row_vals)
                y_lbls.append(r.vehicle_id)

            fig_flt = go.Figure(data=go.Heatmap(
                z=z, x=list(FLAG_MAP.keys()), y=y_lbls,
                colorscale=[[0, GREEN], [0.01, GREEN], [0.99, RED], [1, RED]],
                zmin=0, zmax=1, showscale=False,
                hovertemplate="<b>%{y}</b> · %{x}: %{z}<extra></extra>",
            ))
            for i, veh in enumerate(y_lbls):
                for j, flag in enumerate(FLAG_MAP.keys()):
                    val = z[i][j]
                    fig_flt.add_annotation(
                        x=flag, y=veh,
                        text="✓" if val == 0 else "⚠",
                        showarrow=False,
                        font=dict(color="#000", size=18),
                    )
            fig_flt.update_layout(
                **DARK_LAYOUT, height=290,
                xaxis=dict(title="", tickfont=dict(color="#c9d1d9")),
                yaxis=dict(title="", tickfont=dict(color="#c9d1d9")),
                title="Fault Status — Green ✓ = Clear | Red ⚠ = Active Fault",
            )
            st.plotly_chart(fig_flt, use_container_width=True)

            total_faults = sum(sum(row) for row in z)
            if total_faults == 0:
                st.success("✅ All systems nominal — Zero active faults across the entire fleet.")
            else:
                st.error(f"⚠️ {total_faults} active fault(s) detected. Investigate immediately.")


# ═════════════════════════════════════════════════════════════════════════════
#  ████████  DRIVER VIEW
# ═════════════════════════════════════════════════════════════════════════════
else:
    sel_veh  = st.session_state.sel_veh
    veh_rows = cur_state[cur_state.vehicle_id == sel_veh]

    if veh_rows.empty:
        st.info(f"No data yet for **{sel_veh}** at this replay step — advance the slider ▶")
        st.stop()

    r = veh_rows.iloc[0]

    # ── Header ──
    live_txt = ('↻ LIVE' if st.session_state.playing else f'Step {step+1}/{N_MSGS}')
    chp = state_chip(r.charge_label)
    st.markdown(
        f'<div class="t-header">🚗 My Dashboard — {sel_veh}</div>'
        f'<div class="t-sub">{chp} &nbsp;·&nbsp; '
        f'{r.odokm:.1f} km total &nbsp;·&nbsp; '
        f'{r.cycle_count} charge cycles &nbsp;·&nbsp; SOH {r.soh}% &nbsp;·&nbsp; {live_txt}</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── FOUR GAUGES ──────────────────────────────────────────────────────────
    g1, g2, g3, g4 = st.columns(4)

    # SOC gauge
    with g1:
        fig_g_soc = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=r.soc,
            delta={"reference": 100, "decreasing": {"color": RED}},
            gauge={
                "axis":      {"range": [0, 100], "tickcolor": DIM},
                "bar":       {"color": soc_color(r.soc)},
                "bgcolor":   CARD,
                "steps": [
                    {"range": [0, 20],  "color": "#2a1010"},
                    {"range": [20, 60], "color": "#1a2010"},
                    {"range": [60,100], "color": "#102010"},
                ],
                "threshold": {"line": {"color": RED, "width": 3}, "thickness": 0.75, "value": 20},
            },
            title={"text": "STATE OF CHARGE", "font": {"color": DIM, "size": 12}},
        ))
        fig_g_soc.update_layout(**DARK_LAYOUT, height=240)
        st.plotly_chart(fig_g_soc, use_container_width=True)

    # Voltage gauge
    with g2:
        fig_g_v = go.Figure(go.Indicator(
            mode="gauge+number",
            value=r.batt_voltage,
            gauge={
                "axis":    {"range": [44, 58], "tickcolor": DIM},
                "bar":     {"color": TEAL},
                "bgcolor": CARD,
            },
            title={"text": "PACK VOLTAGE (V)", "font": {"color": DIM, "size": 12}},
        ))
        fig_g_v.update_layout(**DARK_LAYOUT, height=240)
        st.plotly_chart(fig_g_v, use_container_width=True)

    # Current gauge
    with g3:
        cur_col = GREEN if r.batt_current > 0 else ORANGE
        cur_lbl = "CHARGING (A)" if r.batt_current > 0 else "DISCHARGE (A)"
        fig_g_c = go.Figure(go.Indicator(
            mode="gauge+number",
            value=abs(r.batt_current),
            gauge={
                "axis":    {"range": [0, 50], "tickcolor": DIM},
                "bar":     {"color": cur_col},
                "bgcolor": CARD,
            },
            title={"text": cur_lbl, "font": {"color": DIM, "size": 12}},
        ))
        fig_g_c.update_layout(**DARK_LAYOUT, height=240)
        st.plotly_chart(fig_g_c, use_container_width=True)

    # Temperature gauge
    with g4:
        t_col = GREEN if r.temp1 < 38 else (GOLD if r.temp1 < 45 else RED)
        fig_g_t = go.Figure(go.Indicator(
            mode="gauge+number",
            value=r.temp1,
            gauge={
                "axis": {"range": [0, 60], "tickcolor": DIM},
                "bar":  {"color": t_col},
                "bgcolor": CARD,
                "steps": [
                    {"range": [0, 38],  "color": "#102010"},
                    {"range": [38, 45], "color": "#201510"},
                    {"range": [45, 60], "color": "#2a1010"},
                ],
                "threshold": {"line": {"color": RED, "width": 3}, "thickness": 0.75, "value": 45},
            },
            title={"text": "CELL TEMP (°C)", "font": {"color": DIM, "size": 12}},
        ))
        fig_g_t.update_layout(**DARK_LAYOUT, height=240)
        st.plotly_chart(fig_g_t, use_container_width=True)

    # ── KPI METRIC ROW ───────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # Power
    pwr_delta = "Charging" if r.power_w > 0 else ("-Discharging" if r.power_w < 0 else "Idle")
    pwr_color = "normal" if r.power_w != 0 else "off"
    m1.metric("⚡ Power", f"{abs(r.power_w):.0f} W", delta=pwr_delta, delta_color=pwr_color)
    
    # Speed
    m2.metric("🛣️ Speed", f"{r.speed:.1f} km/h")
    
    # SOH 
    soh_delta = f"-{100-r.soh:.0f}% from new" if r.soh < 100 else "Brand new"
    soh_color = "normal" if r.soh < 100 else "off"
    m3.metric("🔋 SOH", f"{r.soh}%", delta=soh_delta, delta_color=soh_color)
    
    # Odo
    m4.metric("📍 Odometer", f"{r.odokm:.1f} km")
    
    # Pack Imbalance
    imb_delta = "Healthy" if r.cell_volt_diff * 1000 < 20 else "-Monitor"
    m5.metric("🔌 Pack Imbal", f"{r.cell_volt_diff*1000:.1f} mV", delta=imb_delta)

    st.divider()

    # ── LOWER PANELS ─────────────────────────────────────────────────────────
    p1, p2 = st.columns(2)

    # My 16-cell breakdown
    with p1:
        st.markdown('<div class="t-section">🔬 My Battery Cells (C1–C16)</div>', unsafe_allow_html=True)
        cell_cols = [f"C{i}" for i in range(1, 17)]
        cell_vals = [float(r.get(c, 0) or 0) for c in cell_cols]
        active    = [v for v in cell_vals if v > 0]

        if active:
            avg_v   = np.mean(active)
            bar_clr = [
                GREEN  if abs(v - avg_v) < 0.010 else
                (GOLD  if abs(v - avg_v) < 0.025 else RED)
                for v in cell_vals
            ]
            fig_cells = go.Figure(go.Bar(
                x=cell_cols, y=cell_vals,
                marker_color=bar_clr,
                text=[f"{v:.3f}" for v in cell_vals],
                textposition="auto",
                hovertemplate="%{x}: <b>%{y:.4f} V</b><extra></extra>",
            ))
            fig_cells.add_hline(
                y=avg_v, line_dash="dot", line_color=TEAL,
                annotation_text=f"Avg {avg_v:.4f}V", annotation_font_color=TEAL,
            )
            fig_cells.update_layout(
                **DARK_LAYOUT, height=310,
                yaxis=dict(range=[3.15, 3.45], title="Voltage (V)", gridcolor=BORDER),
                xaxis=dict(title=""),
                title=f"Cell Breakdown — Spread: {r.cell_volt_diff*1000:.1f} mV",
            )
            st.plotly_chart(fig_cells, use_container_width=True)
        else:
            st.info("Cell-level data not available for this vehicle/step.")

    # My SOC vs fleet
    with p2:
        st.markdown('<div class="t-section">📊 My SOC vs Fleet</div>', unsafe_allow_html=True)
        if not cur_state.empty:
            cmp = cur_state[["vehicle_id", "soc"]].sort_values("soc").copy()
            fig_cmp = go.Figure()
            for _, rr in cmp.iterrows():
                is_me = rr.vehicle_id == sel_veh
                fig_cmp.add_trace(go.Bar(
                    x=[rr.soc], y=[rr.vehicle_id], orientation="h",
                    marker_color=TEAL if is_me else BORDER,
                    marker_line=dict(color=TEAL, width=2 if is_me else 0),
                    text=f"{rr.soc}%", textposition="auto",
                    showlegend=False,
                    hovertemplate=f"<b>{rr.vehicle_id}</b><br>SOC: {rr.soc}%<extra></extra>",
                ))
            fig_cmp.update_layout(
                **DARK_LAYOUT, height=310,
                xaxis=dict(range=[0, 108], title="SOC (%)", gridcolor=BORDER),
                yaxis=dict(title=""),
                title=f"Your Position in the Fleet (highlighted)",
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

    # Temperature sensor cards
    st.markdown('<div class="t-section">🌡️ My Temperature Sensors</div>', unsafe_allow_html=True)
    sensors = {"Cell 1": r.temp1, "Cell 2": r.temp2, "Cell 3": r.temp3,
               "Cell 4": r.temp4, "MOS": r.mos_temp}
    active_s = {k: v for k, v in sensors.items() if v and v > 1}
    if active_s:
        tcols = st.columns(len(active_s))
        for i, (name, val) in enumerate(active_s.items()):
            col_t = GREEN if val < 38 else (GOLD if val < 45 else RED)
            tcols[i].markdown(f"""
            <div style="background:{CARD};border:1px solid {col_t};
                        border-radius:10px;padding:12px;text-align:center;">
              <div style="font-size:11px;color:{DIM};">{name}</div>
              <div style="font-size:28px;font-weight:800;color:{col_t};">{val:.1f}°C</div>
            </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  SHARED BOTTOM · TELEMETRY REPLAY TIMELINE
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<div class="t-section">📡 Telemetry Message Replay Timeline</div>', unsafe_allow_html=True)
st.caption("Each ● = one live BMS ping received from the vehicle. The red NOW line tracks your replay position.")

fig_tl = go.Figure()
pal = [TEAL, GREEN, GOLD, ORANGE, "#c084fc"]  # one colour per vehicle

for idx, veh in enumerate(VEHICLES):
    vdf = df[df.vehicle_id == veh]
    # Convert to HH:MM:SS strings — avoids Plotly Timestamp arithmetic bug in add_vline
    x_strs = vdf["time"].dt.strftime("%H:%M:%S").tolist()
    fig_tl.add_trace(go.Scatter(
        x=x_strs,
        y=[veh] * len(vdf),
        mode="markers",
        marker=dict(
            size=16, color=pal[idx % len(pal)],
            symbol="circle", opacity=0.9,
            line=dict(color="#ffffff", width=1),
        ),
        name=veh,
        customdata=vdf[["soc", "charge_label", "speed"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Time (UTC): %{x}<br>"
            "SOC: %{customdata[0]}% | %{customdata[1]} | %{customdata[2]:.1f} km/h"
            "<extra></extra>"
        ),
    ))

# Moving NOW line — use add_shape + add_annotation with string x
# (add_vline with Timestamp raises arithmetic error in pandas 2.x + Plotly)
now_time_str = df.iloc[st.session_state.msg_step]["time"].strftime("%H:%M:%S")
fig_tl.add_shape(
    type="line",
    x0=now_time_str, x1=now_time_str,
    y0=0, y1=1, yref="paper",
    line=dict(color=RED, width=2),
)
fig_tl.add_annotation(
    x=now_time_str, y=1.04, yref="paper",
    text="▶ NOW",
    showarrow=False,
    font=dict(color=RED, size=12),
)

fig_tl.update_layout(
    **DARK_LAYOUT, height=210,
    xaxis=dict(title="Time (UTC)", gridcolor=BORDER),
    yaxis=dict(title="", gridcolor=BORDER),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(color="#c9d1d9")),
)
st.plotly_chart(fig_tl, use_container_width=True)

st.markdown(
    f'<div style="text-align:center;color:{DIM};font-size:11px;padding:8px 0;">'
    f'Trickee EV Intelligence &nbsp;·&nbsp; Real Charge-Up Fleet Data &nbsp;·&nbsp; '
    f'Oct 24, 2025 &nbsp;·&nbsp; Confidential</div>',
    unsafe_allow_html=True,
)
