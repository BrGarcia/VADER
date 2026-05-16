"""
app.py
Ponto de entrada do V.A.D.E.R.
Execute com: streamlit run app.py
"""

from __future__ import annotations

import os
import streamlit as st
import pandas as pd

from src.data.data_loader import DataLoader
from src.ui.plots import TimelinePlotter
from src.ui.components import AttitudeBox, TimeController, EICASPanel, SubsystemCards

# -----------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------

st.set_page_config(
    page_title="V.A.D.E.R.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_LOADER = DataLoader()
_PLOTTER = TimelinePlotter()

# -----------------------------------------------------------------------
# Cache de ingestão
# -----------------------------------------------------------------------

@st.cache_data(show_spinner="Processando telemetria...")
def _ingest(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw_path = os.path.join(DataLoader.RAW_DIR, filename)
    os.makedirs(DataLoader.RAW_DIR, exist_ok=True)
    os.makedirs(DataLoader.PROCESSED_DIR, exist_ok=True)

    with open(raw_path, "wb") as fh:
        fh.write(file_bytes)

    return _LOADER.ingest(raw_path)

def _get_recent_files() -> list[str]:
    if not os.path.exists(DataLoader.RAW_DIR):
        return []
    files = [f for f in os.listdir(DataLoader.RAW_DIR) if f.endswith(".csv")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DataLoader.RAW_DIR, x)), reverse=True)
    return files


# -----------------------------------------------------------------------
# Landing Page
# -----------------------------------------------------------------------

def render_landing() -> None:
    """Landing page: cabeçalho + box de upload + botão ENVIAR."""

    recent_files = _get_recent_files()

    # ── Cabeçalho centralizado ──
    _, col_mid, _ = st.columns([2, 1, 2])
    with col_mid:
        st.image("assets/a29_sideview.png", use_container_width=True)
        st.markdown("<h1 style='text-align: center; margin-top: -20px;'>V.A.D.E.R.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic; color: #888; font-size: 0.9em;'>Visualizador Analítico de Dados de Engenharia e Rastreio — A-29</p>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Título dos Modos ──
    st.markdown("<h3 style='text-align: center; margin-bottom: 24px; color: #ddd;'>Selecione o Modo de Análise</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    # ── MODO VADR (Atual) ──
    with col1:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #4CAF50; margin-bottom: 5px;'>📊 Modo VADR</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Análise clássica focada no arquivo CSV de telemetria.</p>", unsafe_allow_html=True)
            st.markdown("---")

            # Histórico
            if recent_files:
                st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>📁 HISTÓRICO</p>", unsafe_allow_html=True)
                st.selectbox(
                    "Histórico",
                    options=["-- Selecione um voo recente --"] + recent_files,
                    index=0,
                    label_visibility="collapsed",
                    key="landing_history_select"
                )

            # Upload
            st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center; margin-top: 10px;'>⬆️ UPLOAD CSV</p>", unsafe_allow_html=True)
            st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
                key="landing_csv_uploader"
            )

            # Feedback de seleção
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            uploaded = st.session_state.get("landing_csv_uploader")
            selected_recent = st.session_state.get("landing_history_select")
            arquivo_pronto = uploaded is not None or (
                selected_recent and selected_recent != "-- Selecione um voo recente --"
            )

            if arquivo_pronto:
                nome = uploaded.name if uploaded else selected_recent
                st.markdown(f"<p style='font-size: 0.72rem; text-align: center; color: #4CAF50; margin-top: 2px;'>✅ {nome}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888; margin-top: 2px;'>Selecione um arquivo CSV.</p>", unsafe_allow_html=True)

            # ── Botão ENVIAR ──
            enviar = st.button(
                "▶  INICIAR VADR",
                type="primary",
                use_container_width=True,
                key="landing_submit_btn",
                disabled=not arquivo_pronto,
            )

            if enviar:
                if uploaded is not None:
                    new_df = _ingest(uploaded.getvalue(), uploaded.name)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = uploaded.name
                        st.rerun()
                    else:
                        st.error("❌ Falha ao processar o arquivo CSV.")
                elif selected_recent and selected_recent != "-- Selecione um voo recente --":
                    raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
                    new_df = _LOADER.ingest(raw_path)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = selected_recent
                        st.rerun()
                    else:
                        st.error("❌ Falha ao carregar o arquivo do histórico.")

    # ── MODO DTC (Ativo) ──
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #FF9800; margin-bottom: 5px;'>🛠️ Modo DTC</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Leitura e decodificação de arquivos TRIMM.DMP.</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Upload
            st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>⬆️ UPLOAD DMPs</p>", unsafe_allow_html=True)
            uploaded_dmps = st.file_uploader(
                "Upload DMP",
                type=["dmp", "txt", "csv"], # dmp is standard, mas as vezes o OS não reconhece a ext nativamente
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="landing_dmp_uploader"
            )
            
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if uploaded_dmps:
                st.markdown(f"<p style='font-size: 0.72rem; text-align: center; color: #FF9800; margin-top: 2px;'>✅ {len(uploaded_dmps)} arquivos</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888; margin-top: 2px;'>Selecione os arquivos .DMP</p>", unsafe_allow_html=True)

            iniciar_dtc = st.button("▶  INICIAR DTC", disabled=not uploaded_dmps, type="primary", use_container_width=True, key="btn_dtc_start")
            
            if iniciar_dtc:
                from src.data.dtc_parser import DtcParser
                with st.spinner("Processando arquivos TRIMM..."):
                    df_dtc = DtcParser.ingest_files(uploaded_dmps)
                    if not df_dtc.empty:
                        st.session_state.dtc_df = df_dtc
                        st.session_state.modo_app = "dtc"
                        st.rerun()
                    else:
                        st.error("❌ Falha ao processar arquivos DTC. Verifique se são DMPs válidos.")

    # ── MODO COMPLETO (Ativo) ──
    with col3:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #2196F3; margin-bottom: 5px;'>🦅 Modo COMPLETA</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Dashboard All-in-One Integrado (HUD, EICAS, CSV e DTC).</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            from src.utils.local_scanner import get_available_flights, scan_flight_folder
            voos = get_available_flights()
            
            if not voos:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888;'>Pasta 'Arquivos_para_analise/' vazia.</p>", unsafe_allow_html=True)
                st.button("▶  INICIAR COMPLETA", disabled=True, use_container_width=True, key="btn_completa_disabled")
            else:
                st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>📁 SELECIONE O VOO</p>", unsafe_allow_html=True)
                voo_selecionado = st.selectbox(
                    "Voo Local",
                    options=voos,
                    label_visibility="collapsed",
                    key="landing_completa_select"
                )
                
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                iniciar_completa = st.button("▶  INICIAR COMPLETA", type="primary", use_container_width=True, key="btn_completa_start")
                
                if iniciar_completa:
                    with st.spinner("Escaneando diretório e carregando módulos..."):
                        mapeamento = scan_flight_folder(voo_selecionado)
                        st.session_state.completa_map = mapeamento
                        
                        # Ingestão de VADR
                        if mapeamento.get("vadr_csv_path"):
                            df_vadr = _LOADER.ingest(str(mapeamento["vadr_csv_path"]))
                            st.session_state.current_df = df_vadr
                            st.session_state.current_filename = mapeamento["vadr_csv_path"].name
                        
                        # Ingestão de DTC
                        if mapeamento.get("dtc_files_paths"):
                            from src.data.dtc_parser import DtcParser
                            # Se os DMPs estiverem na pasta DTC, ou na raiz
                            dtc_pasta = str(mapeamento["dtc_files_paths"][0].parent)
                            df_dtc = DtcParser.processar_diretorio(dtc_pasta)
                            st.session_state.dtc_df = df_dtc
                            
                        st.session_state.modo_app = "completa"
                        st.rerun()


# -----------------------------------------------------------------------
# Menu compacto (página de análise)
# -----------------------------------------------------------------------

def render_bottom_panel(df: pd.DataFrame) -> None:
    """Painel inferior: troca de arquivo, info e botão Nova Análise."""

    recent_files = _get_recent_files()

    st.markdown("---")
    with st.container(border=True):
        st.markdown("<p style='font-weight: bold; margin-bottom: 4px; font-size: 0.8rem; text-align: center;'>🛠️ CONFIGURAÇÕES E DADOS DE VOO</p>", unsafe_allow_html=True)

        col_file, col_info, col_btn = st.columns([2, 1.5, 1], gap="small")

        # ── Troca rápida de arquivo ──
        with col_file:
            _l, _mid, _r = st.columns([0.05, 0.9, 0.05])
            with _mid:
                opcoes = ["── Arquivo atual ──"] + (recent_files if recent_files else [])
                sel = st.selectbox(
                    "Trocar arquivo",
                    options=opcoes,
                    index=0,
                    label_visibility="collapsed",
                    key="analysis_history_select"
                )
                if sel and sel != "── Arquivo atual ──":
                    if st.button("▶  Carregar", key="analysis_load_btn", use_container_width=True):
                        raw_path = os.path.join(DataLoader.RAW_DIR, sel)
                        new_df = _LOADER.ingest(raw_path)
                        if new_df is not None:
                            st.session_state.current_df = new_df
                            st.session_state.current_filename = sel
                            st.rerun()

        # ── Info do arquivo atual ──
        with col_info:
            st.markdown("<p style='font-size: 0.75rem; font-weight: bold; margin-bottom: -10px; text-align: center;'>ℹ️ INFO</p>", unsafe_allow_html=True)
            n_rows = len(df)
            duration = df["TIME"].max() if "TIME" in df.columns else 0
            fname = st.session_state.get("current_filename", "arquivo")
            st.markdown(f"<p style='font-size: 0.7rem; margin-bottom: 0px; text-align: center;'>📄 {fname[:24]}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.7rem; text-align: center;'>🔢 {n_rows:,} registros | ⏱ {duration:.1f}s</p>", unsafe_allow_html=True)

        # ── Botão Nova Análise ──
        with col_btn:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("🔄  NOVA ANÁLISE", key="btn_nova_analise", use_container_width=True):
                # Limpa o estado e retorna à landing page
                for key in ["current_df", "current_filename", "last_y_col",
                             TimeController.SESSION_KEY]:
                    st.session_state.pop(key, None)
                st.rerun()


# -----------------------------------------------------------------------
# Layout Principal (Análise)
# -----------------------------------------------------------------------

def render_main(df: pd.DataFrame) -> str | None:
    """Monta o layout sincronizado de análise. Retorna y_col selecionado."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    subsys_cards  = SubsystemCards()
    fault_columns = _LOADER.get_fault_columns(df)

    # Cabeçalho de Dados da Aeronave
    metadata = df.attrs.get("metadata", {})
    if metadata:
        with st.container(border=True):
            st.markdown("<p style='font-weight: bold; margin-bottom: 5px; font-size: 0.85rem; text-align: center;'>✈️ DADOS DA AERONAVE</p>", unsafe_allow_html=True)
            cols_meta = st.columns(len(metadata) if len(metadata) > 0 else 1)
            for i, (key, val) in enumerate(metadata.items()):
                with cols_meta[i % len(cols_meta)]:
                    st.markdown(f"<p style='font-size: 0.75rem; text-align: center;'><span style='color: #888;'>{key}:</span> <br><b>{val}</b></p>", unsafe_allow_html=True)

    time_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snapshot = controller.get_snapshot(time_idx)

    # Atitude e Dados Críticos
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot, fault_columns)

    st.markdown("---")

    # ── Análise Temporal: título + seletor de variáveis inline ──
    numeric_cols = _LOADER.get_numeric_columns(df)

    # Padrão inicial: primeira variável relevante disponível
    if "last_y_cols" not in st.session_state:
        default = next(
            (c for c in ("BALT", "MACH", "APA", "NZ") if c in numeric_cols),
            numeric_cols[:1]
        )
        st.session_state.last_y_cols = [default] if isinstance(default, str) else default

    col_titulo, col_sel = st.columns([2, 1], gap="small")
    with col_titulo:
        titulo_placeholder = st.empty()
    with col_sel:
        y_cols = st.multiselect(
            "Variáveis",
            options=numeric_cols,
            default=[c for c in st.session_state.last_y_cols if c in numeric_cols] or numeric_cols[:1],
            label_visibility="collapsed",
            placeholder="Selecione as variáveis...",
            key="main_y_axis_select"
        )
        # Garante ao menos uma variável selecionada
        if not y_cols:
            y_cols = st.session_state.last_y_cols or numeric_cols[:1]
        st.session_state.last_y_cols = y_cols
        # Compatibilidade com código que usa last_y_col (singular)
        y_col = y_cols[0] if y_cols else None
        st.session_state.last_y_col = y_col

    label_vars = " · ".join(f"`{c}`" for c in y_cols)
    titulo_placeholder.markdown(f"#### 📈 Análise Temporal — {label_vars}")

    fig = _PLOTTER.plot(df, y_cols)
    fig = _PLOTTER.add_phase_bands(fig, df)
    fig = _PLOTTER.add_fault_markers(fig, df, fault_columns, y_column=y_cols)


    t_cursor = float(snapshot["TIME"]) if "TIME" in snapshot else 0
    fig.add_vline(
        x=t_cursor,
        line=dict(color="#FF4B4B", width=2, dash="dash"),
        annotation_text=f"  t={t_cursor:.2f}s",
        annotation_font=dict(color="#FF4B4B", size=11),
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key=f"main_plot_{y_col}")

    # Slider de Tempo
    controller.render_slider()

    # Cards de Subsistemas
    st.markdown("#### 🔧 Subsistemas")
    subsys_cards.render_all(snapshot)

    # Painel inferior (configurações + nova análise)
    render_bottom_panel(df)

    return y_col


# -----------------------------------------------------------------------
# Layout DTC (Módulo de Falhas TRIMM)
# -----------------------------------------------------------------------

def render_dtc(df: pd.DataFrame) -> None:
    """Monta a visualização para os dados consolidados do DTC."""
    st.markdown("<h2 style='text-align: center; color: #FF9800;'>🛠️ Análise DTC (Pitch Trim Switch)</h2>", unsafe_allow_html=True)
    
    meta = df.attrs.get("metadata", {})
    status = meta.get("Status", "N/A")
    status_color = "#FF4B4B" if "SUSPEITA" in status else "#4CAF50"
    
    # Cabeçalho principal com Status fora da métrica para não cortar texto longo
    st.markdown(f"<h3 style='text-align: center; margin-top: 0px; color: {status_color};'>{status}</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.metric("Total de Arquivos", meta.get("Total de Arquivos", 0))
        with col_kpi2:
            st.metric("Total de Registros", meta.get("Total de Registros", 0))
        with col_kpi3:
            st.metric("Threshold Seguro (ms)", f"{meta.get('Threshold (ms)', 0)} ms")

    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Análise de Movimento Não Comandado</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #aaa;'>Um alerta ocorre quando a posição da superfície sofre um salto brusco (> 1 grau) num intervalo de tempo menor que o Threshold Seguro.</p>", unsafe_allow_html=True)

    col_a, col_e = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Superfície Aileron</h4>", unsafe_allow_html=True)
            v_a = meta.get("Disparos Aileron", 0)
            c_a = "#FF4B4B" if v_a > 0 else "#4CAF50"
            st.markdown(f"<h1 style='text-align: center; color: {c_a}; margin-top: -10px;'>{v_a} alertas</h1>", unsafe_allow_html=True)
            if v_a == 0:
                st.markdown("<p style='text-align: center; color: #aaa; font-size: 0.8rem;'>Nenhuma anomalia matemática detectada.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align: center; color: #FF4B4B; font-size: 0.8rem; font-weight: bold;'>⚠️ Requer investigação imediata.</p>", unsafe_allow_html=True)
        
    with col_e:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Superfície Elevator</h4>", unsafe_allow_html=True)
            v_e = meta.get("Disparos Elevator", 0)
            c_e = "#FF4B4B" if v_e > 0 else "#4CAF50"
            st.markdown(f"<h1 style='text-align: center; color: {c_e}; margin-top: -10px;'>{v_e} alertas</h1>", unsafe_allow_html=True)
            if v_e == 0:
                st.markdown("<p style='text-align: center; color: #aaa; font-size: 0.8rem;'>Nenhuma anomalia matemática detectada.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align: center; color: #FF4B4B; font-size: 0.8rem; font-weight: bold;'>⚠️ Requer investigação imediata.</p>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Configuração de Estilos para as Tabelas
    def highlight_status_t(val):
        if str(val).strip().upper() == "T":
            return 'background-color: rgba(255, 152, 0, 0.4); color: white; font-weight: bold;'
        return ''

    def highlight_test_1(val):
        if str(val).strip() == "1":
            return 'background-color: rgba(255, 75, 75, 0.5); color: white; font-weight: bold;'
        return ''

    cols_t = [c for c in ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"] if c in df.columns]
    cols_1 = [c for c in ["Aileron_Test", "Elevator_Test"] if c in df.columns]

    def aplicar_estilos(data_frame):
        styler = data_frame.style
        if hasattr(styler, "map"):
            styler = styler.map(highlight_status_t, subset=cols_t)
            styler = styler.map(highlight_test_1, subset=cols_1)
        else:
            styler = styler.applymap(highlight_status_t, subset=cols_t)
            styler = styler.applymap(highlight_test_1, subset=cols_1)
        return styler

    # Extrato Rápido (Apenas Disparos)
    disparos_df = df[(df.get("Aileron_Test") == 1) | (df.get("Elevator_Test") == 1)]
    if not disparos_df.empty:
        st.markdown("### 🚨 Ocorrências de Disparo (Extrato Rápido)")
        st.markdown("<p style='font-size: 0.85rem; color: #bbb;'>Esta tabela mostra <b>apenas</b> os instantes exatos onde os alertas foram disparados. Analise os estados dos interruptores (Emer_ON, Stick) nestes momentos.</p>", unsafe_allow_html=True)
        st.dataframe(aplicar_estilos(disparos_df), use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Tabela Completa
    st.markdown("### 📋 Histórico Completo de Voo")
    st.dataframe(aplicar_estilos(df), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🔄  VOLTAR AO MENU INICIAL", use_container_width=True):
            st.session_state.pop("dtc_df", None)
            st.session_state.modo_app = None
            st.rerun()


# -----------------------------------------------------------------------
# Layout COMPLETA (Dashboard Integrado)
# -----------------------------------------------------------------------

def render_completa() -> None:
    """Monta o esqueleto do Dashboard Integrado All-In-One."""
    st.markdown("<h2 style='text-align: center; color: #2196F3;'>🦅 Dashboard Integrado (All-In-One)</h2>", unsafe_allow_html=True)
    
    mapeamento = st.session_state.get("completa_map", {})
    
    # Barra de Ferramentas / Status
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Telemetria (VADR)", "✅ OK" if mapeamento.get("vadr_csv_path") else "❌ Ausente")
        c2.metric("Falhas (DTC)", f"✅ {len(mapeamento.get('dtc_files_paths', []))} arq." if mapeamento.get("dtc_files_paths") else "❌ Ausente")
        c3.metric("Vídeo HUD (CHVC)", "✅ OK" if mapeamento.get("chvc_video_path") else "❌ Ausente")
        c4.metric("Vídeo MFD (EICAS)", "✅ OK" if mapeamento.get("eicas_video_path") else "❌ Ausente")
        
    st.markdown("---")
    
    # Grid de Vídeos e DTC
    col_vid1, col_vid2, col_dtc = st.columns([2, 2, 1], gap="medium")
    
    with col_vid1:
        st.markdown("#### 🎥 EICAS")
        if mapeamento.get("eicas_video_path"):
            st.info(f"Vídeo detectado: {mapeamento['eicas_video_path'].name}\n\n*(Player HTML5 será injetado aqui na Fase 4)*")
        else:
            st.warning("Sem gravação do EICAS")
            
    with col_vid2:
        st.markdown("#### 🎥 CHVC (HUD)")
        if mapeamento.get("chvc_video_path"):
            st.info(f"Vídeo detectado: {mapeamento['chvc_video_path'].name}\n\n*(Player HTML5 será injetado aqui na Fase 4)*")
        else:
            st.warning("Sem gravação do HUD")
            
    with col_dtc:
        st.markdown("#### 🛠️ Alertas DTC")
        df_dtc = st.session_state.get("dtc_df")
        if df_dtc is not None and not df_dtc.empty:
            meta = df_dtc.attrs.get("metadata", {})
            st.error(f"**Aileron:** {meta.get('Disparos Aileron', 0)}")
            st.error(f"**Elevator:** {meta.get('Disparos Elevator', 0)}")
        else:
            st.success("Sem falhas detectadas ou dados DTC ausentes.")
            
    st.markdown("---")
    st.markdown("#### 📈 Telemetria Sincronizada")
    
    df_vadr = st.session_state.get("current_df")
    if df_vadr is not None:
        st.info("*(O gráfico interativo TimelinePlotter entrará aqui para controlar o tempo global)*")
        # Por enquanto vamos renderizar a interface de análise normal debaixo de tudo
        render_main(df_vadr)
    else:
        st.warning("Sem dados de telemetria VADR para plotar gráficos.")
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🔄  ENCERRAR INSPEÇÃO", use_container_width=True):
        st.session_state.pop("completa_map", None)
        st.session_state.pop("dtc_df", None)
        st.session_state.pop("current_df", None)
        st.session_state.modo_app = None
        st.rerun()


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    df_cached = st.session_state.get("current_df")
    modo = st.session_state.get("modo_app")

    if modo == "dtc":
        df_dtc = st.session_state.get("dtc_df")
        if df_dtc is not None:
            render_dtc(df_dtc)
        else:
            st.session_state.modo_app = None
            st.rerun()
    elif modo == "completa":
        render_completa()
    elif df_cached is not None and modo != "completa":
        # ── Página de Análise VADR ──
        render_main(df_cached)
    else:
        # ── Landing Page ──
        render_landing()


if __name__ == "__main__":
    main()
