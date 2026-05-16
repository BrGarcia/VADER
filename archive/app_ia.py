import os, streamlit as st, pandas as pd
from src.data.data_loader import DataLoader
from src.ui.plots import TimelinePlotter
from src.ui.components import AttitudeBox, TimeController, SubsystemCards

st.set_page_config(page_title="VADER", layout="wide", initial_sidebar_state="collapsed")
_L, _P = DataLoader(), TimelinePlotter()

@st.cache_data(show_spinner="Processing...")
def ingest(f_bytes: bytes, fname: str) -> pd.DataFrame:
    p = os.path.join(DataLoader.RAW_DIR, fname)
    os.makedirs(DataLoader.RAW_DIR, exist_ok=True)
    os.makedirs(DataLoader.PROCESSED_DIR, exist_ok=True)
    with open(p, "wb") as f: f.write(f_bytes)
    return _L.ingest(p)

def get_recent() -> list[str]:
    if not os.path.exists(DataLoader.RAW_DIR): return []
    fs = [f for f in os.listdir(DataLoader.RAW_DIR) if f.endswith(".csv")]
    fs.sort(key=lambda x: os.path.getmtime(os.path.join(DataLoader.RAW_DIR, x)), reverse=True)
    return fs

def render_landing():
    recents = get_recent()
    st.title("V.A.D.E.R.")
    c1, c2, c3 = st.columns(3)

    with c1.container(border=True):
        st.subheader("VADR Mode")
        sel_rec = st.selectbox("History", ["-- Select --"] + recents, key="l_hist") if recents else None
        up_csv = st.file_uploader("Upload CSV", type=["csv"], key="l_up")
        rdy = up_csv or (sel_rec and sel_rec != "-- Select --")
        if st.button("START VADR", disabled=not rdy, use_container_width=True):
            if up_csv:
                st.session_state.current_df, st.session_state.current_filename = ingest(up_csv.getvalue(), up_csv.name), up_csv.name
                st.rerun()
            elif sel_rec:
                st.session_state.current_df, st.session_state.current_filename = _L.ingest(os.path.join(DataLoader.RAW_DIR, sel_rec)), sel_rec
                st.rerun()

    with c2.container(border=True):
        st.subheader("DTC Mode")
        up_dmps = st.file_uploader("Upload DMP", type=["dmp","txt","csv"], accept_multiple_files=True, key="l_dtc")
        if st.button("START DTC", disabled=not up_dmps, use_container_width=True):
            from src.data.dtc_parser import DtcParser
            df = DtcParser.ingest_files(up_dmps)
            if not df.empty:
                st.session_state.dtc_df, st.session_state.modo_app = df, "dtc"
                st.rerun()

    with c3.container(border=True):
        st.subheader("COMPLETA Mode")
        from src.utils.local_scanner import get_available_flights, scan_flight_folder
        v = get_available_flights()
        sel_v = st.selectbox("Flight", v, key="l_comp") if v else None
        if st.button("START COMPLETA", disabled=not v, use_container_width=True):
            map_ = scan_flight_folder(sel_v)
            st.session_state.completa_map = map_
            if map_.get("vadr_csv_path"):
                st.session_state.current_df = _L.ingest(str(map_["vadr_csv_path"]))
                st.session_state.current_filename = map_["vadr_csv_path"].name
            if map_.get("dtc_files_paths"):
                from src.data.dtc_parser import DtcParser
                st.session_state.dtc_df = DtcParser.processar_diretorio(str(map_["dtc_files_paths"][0].parent))
            st.session_state.modo_app = "completa"
            st.rerun()

def render_bottom_panel(df):
    st.divider()
    with st.container(border=True):
        c_f, c_i, c_b = st.columns([2, 1.5, 1])
        with c_f:
            sel = st.selectbox("Switch File", ["-- Current --"] + get_recent())
            if sel != "-- Current --" and st.button("Load", use_container_width=True):
                st.session_state.current_df, st.session_state.current_filename = _L.ingest(os.path.join(DataLoader.RAW_DIR, sel)), sel
                st.rerun()
        with c_i:
            st.write(f"File: {st.session_state.get('current_filename')} | Rows: {len(df)} | Time: {df['TIME'].max() if 'TIME' in df.columns else 0:.1f}s")
        with c_b:
            if st.button("NEW ANALYSIS", use_container_width=True):
                for k in ["current_df","current_filename","last_y_col",TimeController.SESSION_KEY]: st.session_state.pop(k, None)
                st.rerun()

def render_main(df, show_meta=True):
    ctrl, att_box, sub_cards, f_cols = TimeController(df), AttitudeBox(), SubsystemCards(), _L.get_fault_columns(df)
    if show_meta and (m := df.attrs.get("metadata", {})):
        with st.container(border=True): st.write(m)
    t_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snap = ctrl.get_snapshot(t_idx)
    num_cols = _L.get_numeric_columns(df)
    if "last_y_cols" not in st.session_state:
        st.session_state.last_y_cols = [next((c for c in ("BALT","MACH","APA","NZ") if c in num_cols), num_cols[:1])]
    
    y_cols = st.multiselect("Vars", num_cols, default=[c for c in st.session_state.last_y_cols if c in num_cols] or num_cols[:1]) or st.session_state.last_y_cols or num_cols[:1]
    st.session_state.last_y_cols, y_col = y_cols, y_cols[0] if y_cols else None
    
    fig = _P.plot(df, y_cols)
    fig = _P.add_phase_bands(fig, df)
    fig = _P.add_fault_markers(fig, df, f_cols, y_column=y_cols)
    if "TIME" in snap: fig.add_vline(x=float(snap["TIME"]), line=dict(color="red", width=2, dash="dash"))
    st.plotly_chart(fig, use_container_width=True, key=f"p_{y_col}")
    ctrl.render_slider()
    st.divider()
    att_box.render(snap, f_cols)
    sub_cards.render_all(snap)
    render_bottom_panel(df)

def render_dtc(df):
    meta = df.attrs.get("metadata", {})
    st.header(f"DTC Analysis: {meta.get('Status', 'N/A')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Files", meta.get("Total de Arquivos", 0))
    c2.metric("Rows", meta.get("Total de Registros", 0))
    c3.metric("Threshold", f"{meta.get('Threshold (ms)', 0)} ms")
    c_a, c_e = st.columns(2)
    c_a.metric("Aileron Alerts", meta.get("Disparos Aileron", 0))
    c_e.metric("Elevator Alerts", meta.get("Disparos Elevator", 0))
    
    def apply_style(d):
        s = d.style
        m = s.map if hasattr(s, "map") else s.applymap
        c_t = [c for c in ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"] if c in df.columns]
        c_1 = [c for c in ["Aileron_Test", "Elevator_Test"] if c in df.columns]
        m(lambda v: 'background: orange' if str(v).strip().upper() == "T" else '', subset=c_t)
        m(lambda v: 'background: red' if str(v).strip() == "1" else '', subset=c_1)
        return s

    d_df = df[(df.get("Aileron_Test")==1)|(df.get("Elevator_Test")==1)]
    if not d_df.empty:
        st.subheader("Triggers")
        st.dataframe(apply_style(d_df), hide_index=True)
    st.subheader("Full History")
    st.dataframe(apply_style(df), hide_index=True)
    if st.button("BACK"):
        st.session_state.pop("dtc_df", None); st.session_state.modo_app = None; st.rerun()

def _convert_btn(label, vids, key, rot):
    if st.button(label, key=key):
        from src.utils.video_converter import convert_video
        from pathlib import Path
        with st.spinner("Converting..."):
            err = sum(1 for v in vids if str(v).lower().endswith(('.mpg','.mpeg')) and not Path(str(v)).with_suffix('.mp4').exists() and not convert_video(str(v), Path(str(v)).with_suffix('.mp4'), rotate=rot))
            if err == 0: st.success("Done!")
            else: st.error("Errors occurred.")

def render_completa():
    m = st.session_state.get("completa_map", {})
    st.header("Integrated Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("VADR", "OK" if m.get("vadr_csv_path") else "X")
    c2.metric("DTC", len(m.get("dtc_files_paths",[])))
    c3.metric("CHVC", len(m.get("chvc_video_paths",[])))
    c4.metric("EICAS", len(m.get("eicas_video_paths",[])))
    
    cv1, cv2 = st.columns([3, 5.2])
    with cv1:
        st.subheader("EICAS")
        v_e = m.get("eicas_video_paths", [])
        if v_e:
            sel = st.selectbox("EICAS", {f.name: str(f) for f in v_e})
            if sel.lower().endswith(('.mpg','.mpeg')):
                _convert_btn("Convert Single", [sel], "c_e", True)
                _convert_btn("Convert All", v_e, "c_a_e", True)
            else: st.video(sel)
    with cv2:
        st.subheader("CHVC")
        v_c = m.get("chvc_video_paths", [])
        if v_c:
            sel = st.selectbox("CHVC", {f.name: str(f) for f in v_c})
            if sel.lower().endswith(('.mpg','.mpeg')):
                _convert_btn("Convert Single", [sel], "c_c", False)
                _convert_btn("Convert All", v_c, "c_a_c", False)
            else: st.video(sel)

    df_dtc = st.session_state.get("dtc_df")
    if df_dtc is not None and not df_dtc.empty:
        c_a, c_e = st.columns(2)
        c_a.write(f"Aileron: {df_dtc.attrs.get('metadata',{}).get('Disparos Aileron',0)}")
        c_e.write(f"Elevator: {df_dtc.attrs.get('metadata',{}).get('Disparos Elevator',0)}")
        d_df = df_dtc[(df_dtc.get("Aileron_Test")==1)|(df_dtc.get("Elevator_Test")==1)]
        if not d_df.empty:
            with st.expander("Triggers", expanded=True): st.dataframe(d_df)
        with st.expander("Full DTC History"): st.dataframe(df_dtc)

    df_v = st.session_state.get("current_df")
    if df_v is not None: render_main(df_v, False)

    if st.button("END INSPECTION"):
        for k in ["completa_map","dtc_df","current_df","modo_app"]: st.session_state.pop(k, None)
        st.rerun()

def main():
    df, mode = st.session_state.get("current_df"), st.session_state.get("modo_app")
    if mode == "dtc": render_dtc(st.session_state.get("dtc_df")) if st.session_state.get("dtc_df") is not None else st.rerun()
    elif mode == "completa": render_completa()
    elif df is not None: render_main(df)
    else: render_landing()

if __name__ == "__main__": main()
