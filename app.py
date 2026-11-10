import math
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ITI Trades Assistant", page_icon="🛠️", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1100px;}
    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.10);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        padding: 14px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cutting speed (m/min) ki typical range. Sirf reference, handbook se check karo.
SPEEDS = {
    "HSS": {"Mild Steel": (25, 35), "Aluminium": (70, 100), "Brass": (60, 90),
            "Cast Iron": (20, 30), "Stainless Steel": (15, 25)},
    "Carbide": {"Mild Steel": (100, 180), "Aluminium": (200, 400), "Brass": (150, 250),
                "Cast Iron": (80, 150), "Stainless Steel": (80, 140)},
}


def pair(label_a, val_a, label_b, val_b, **kw):
    c1, c2 = st.columns(2)
    a = c1.number_input(label_a, min_value=0.01, value=float(val_a), **kw)
    b = c2.number_input(label_b, min_value=0.01, value=float(val_b), **kw)
    return a, b


# ---------- Turner / Machinist ----------
def turning():
    c1, c2 = st.columns(2)
    tool = c1.selectbox("Tool", list(SPEEDS))
    mat = c2.selectbox("Material", list(SPEEDS[tool]))
    lo, hi = SPEEDS[tool][mat]
    st.info(f"Typical cutting speed: **{lo} - {hi} m/min**")
    vc = st.number_input("Cutting speed (m/min)", min_value=1.0,
                         value=float((lo + hi) / 2), key=f"vc{tool}{mat}")
    d, length = pair("Diameter (mm)", 50, "Length of cut (mm)", 100)
    feed, passes = pair("Feed (mm/rev)", 0.2, "Passes", 1, step=0.05)
    rate, mat_cost = pair("Machine + labour (₹/hr)", 400, "Material cost (₹)", 150)
    rpm = (1000 * vc) / (math.pi * d)
    t = length / (feed * rpm) * passes
    cost = t / 60 * rate + mat_cost
    msg = [("warning", "Cutting speed range se bahar hai.")] if not lo <= vc <= hi else \
          [("success", "Cutting speed sahi range me hai.")]
    return {"Spindle RPM": f"{rpm:,.0f}", "Machining time": f"{t:.2f} min",
            "Job cost": f"₹ {cost:,.0f}"}, msg


# ---------- Fitter ----------
def tap_drill():
    major, pitch = pair("Bolt/tap size M (mm)", 10, "Pitch (mm)", 1.5, step=0.25)
    if pitch >= major:
        return {}, [("error", "Pitch size se chhota hona chahiye.")]
    return {"Tap drill size": f"{major - pitch:.2f} mm"}, \
           [("info", "Tap drill = Major diameter - Pitch (metric thread).")]


# ---------- Electrician ----------
def ohm():
    find = st.radio("Kya nikalna hai?", ["Voltage (V)", "Current (A)", "Resistance (Ω)"],
                    horizontal=True)
    if find.startswith("Voltage"):
        i, r = pair("Current (A)", 2, "Resistance (Ω)", 50)
        v = i * r
    elif find.startswith("Current"):
        v, r = pair("Voltage (V)", 230, "Resistance (Ω)", 50)
        i = v / r
    else:
        v, i = pair("Voltage (V)", 230, "Current (A)", 2)
        r = v / i
    return {"Voltage": f"{v:.2f} V", "Current": f"{i:.2f} A",
            "Resistance": f"{r:.2f} Ω", "Power": f"{v * i:.1f} W"}, None


def power_bill():
    w, h = pair("Load (Watt)", 1500, "Roz ghante", 5)
    days, rate = pair("Din", 30, "Rate (₹/unit)", 7)
    units = w * h * days / 1000
    return {"Units (kWh)": f"{units:.1f}", "Bill": f"₹ {units * rate:,.0f}"}, \
           [("info", "Rate apne bijli bill se dekh kar daalo.")]


def three_phase():
    v, i = pair("Line voltage (V)", 415, "Current (A)", 10)
    pf = st.slider("Power factor", 0.1, 1.0, 0.8, 0.05)
    kva = math.sqrt(3) * v * i / 1000
    return {"Power (kW)": f"{kva * pf:.2f}", "Apparent (kVA)": f"{kva:.2f}"}, None


# ---------- Welder ----------
def heat_input():
    v, i = pair("Arc voltage (V)", 24, "Current (A)", 120)
    speed, eff = pair("Travel speed (mm/min)", 150, "Efficiency (0-1)", 0.8, step=0.05)
    hi = v * i * 60 / (speed * 1000) * min(eff, 1.0)
    return {"Heat input": f"{hi:.2f} kJ/mm"}, \
           [("info", "Efficiency process par depend karti hai. Apne WPS se check karo.")]


# ---------- Electronics Mechanic ----------
def led_resistor():
    vs, vf = pair("Supply (V)", 5, "LED voltage (V)", 2)
    ma = st.number_input("LED current (mA)", min_value=1.0, value=20.0)
    if vs <= vf:
        return {}, [("error", "Supply voltage LED voltage se zyada honi chahiye.")]
    r = (vs - vf) / (ma / 1000)
    return {"Resistor": f"{r:.0f} Ω", "Resistor power": f"{(ma / 1000) ** 2 * r * 1000:.0f} mW"}, \
           [("info", "Nearest higher standard value ka resistor lagao.")]


def series_parallel():
    txt = st.text_input("Resistor values (Ω), comma se alag", "100, 220, 330")
    try:
        vals = [float(x) for x in txt.split(",") if x.strip()]
        assert vals and all(v > 0 for v in vals)
    except Exception:
        return {}, [("error", "Sirf positive numbers likho, jaise 100, 220.")]
    return {"Series": f"{sum(vals):.1f} Ω",
            "Parallel": f"{1 / sum(1 / v for v in vals):.2f} Ω"}, None


# ---------- Refrigeration & AC ----------
def ac_size():
    area = st.number_input("Room area (sq ft)", min_value=10.0, value=150.0)
    tr = area / 110
    size = next((s for s in [0.75, 1, 1.5, 2, 3, 4, 5] if s >= tr), "5+")
    return {"Rough load": f"{tr:.2f} TR", "Suggested AC": f"{size} TR",
            "Cooling": f"{tr * 3.517:.1f} kW"}, \
           [("warning", "Yeh rough andaaza hai (1 TR = 110 sq ft). Dhoop, log aur machines se load badhta hai.")]


# ---------- Plumber ----------
def tank():
    shape = st.radio("Tank shape", ["Rectangle", "Cylinder"], horizontal=True)
    if shape == "Rectangle":
        a, b = pair("Length (cm)", 100, "Width (cm)", 80)
        h = st.number_input("Height (cm)", min_value=1.0, value=100.0)
        litres = a * b * h / 1000
    else:
        d, h = pair("Diameter (cm)", 90, "Height (cm)", 120)
        litres = math.pi / 4 * d * d * h / 1000
    return {"Capacity": f"{litres:,.0f} litres"}, None


# ---------- Carpenter ----------
def wood():
    length, width = pair("Length (feet)", 6, "Width (inch)", 8)
    thick, pcs = pair("Thickness (inch)", 2, "Pieces", 4)
    rate = st.number_input("Rate (₹/cft)", min_value=1.0, value=1500.0)
    cft = length * width * thick / 144 * pcs
    return {"Wood": f"{cft:.2f} cft", "Cost": f"₹ {cft * rate:,.0f}"}, None


# ---------- Mechanic Motor Vehicle / Diesel ----------
def engine():
    bore, stroke = pair("Bore (mm)", 86, "Stroke (mm)", 86)
    cyl, clear = pair("Cylinders", 4, "Clearance volume/cyl (cc)", 50)
    swept = math.pi / 4 * (bore / 10) ** 2 * (stroke / 10)
    return {"Engine size": f"{swept * cyl:,.0f} cc",
            "Compression ratio": f"{(swept + clear) / clear:.1f} : 1"}, None


TRADES = {
    "Turner / Machinist": {"Turning: RPM, time, cost": turning},
    "Fitter": {"Tap drill size": tap_drill},
    "Electrician": {"Ohm's Law": ohm, "Bijli bill": power_bill, "3-phase power": three_phase},
    "Welder": {"Heat input": heat_input},
    "Electronics Mechanic": {"LED resistor": led_resistor, "Series / Parallel": series_parallel},
    "Refrigeration & AC": {"AC size estimate": ac_size},
    "Plumber": {"Tank capacity": tank},
    "Carpenter": {"Wood (cft) aur cost": wood},
    "Mechanic Motor Vehicle / Diesel": {"Engine size aur compression ratio": engine},
}

if "jobs" not in st.session_state:
    st.session_state.jobs = []

st.title("🛠️ ITI Trades Assistant")
st.caption("ITI ke har trade ke liye kaam ke calculators, ek jagah.")

tab_calc, tab_hist = st.tabs(["🧮 Calculator", "📋 Job History"])

with tab_calc:
    c1, c2 = st.columns(2)
    trade = c1.selectbox("Trade", list(TRADES))
    calc = c2.selectbox("Calculator", list(TRADES[trade]))
    job = st.text_input("Job / kaam ka naam", "My job")
    st.divider()

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Input")
        results, msgs = TRADES[trade][calc]()
    with right:
        st.subheader("Result")
        if results:
            cols = st.columns(2)
            for n, (k, v) in enumerate(results.items()):
                cols[n % 2].metric(k, v)
        for level, text in msgs or []:
            getattr(st, level)(text)
        if results and st.button("➕ History me save karo", use_container_width=True):
            st.session_state.jobs.append({
                "Time": datetime.now().strftime("%d-%m %H:%M"),
                "Trade": trade, "Calculator": calc, "Job": job,
                "Result": " | ".join(f"{k}: {v}" for k, v in results.items()),
            })
            st.toast("Save ho gaya!")

with tab_hist:
    if not st.session_state.jobs:
        st.info("Abhi koi job save nahi hai.")
    else:
        df = pd.DataFrame(st.session_state.jobs)
        st.dataframe(df, use_container_width=True, hide_index=True)
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ CSV download", df.to_csv(index=False).encode("utf-8"),
                           "jobs.csv", "text/csv", use_container_width=True)
        if d2.button("🗑️ History saaf karo", use_container_width=True):
            st.session_state.jobs = []
            st.rerun()
