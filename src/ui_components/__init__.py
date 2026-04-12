"""
ui_components.py
Componentes visuais Streamlit do V.A.D.E.R.

Fase 1: TimeController, AttitudeBox
Fase 2: EICASPanel (gauges), SubsystemCards
Fase 3: EICASPanel (CAS window), fault markers
"""

from __future__ import annotations

import json
import os
import streamlit as st
import pandas as pd

from src.plots import EngineGaugePlotter, AttitudeIndicator, NZ_ALERT_THRESHOLD, ENGINE_LIMITS, COLORS
from .fault_panel import FaultPanel

# -----------------------------------------------------------------------
# S-02: Cache de alertas.json — carregado UMA VEZ no nível de módulo
# -----------------------------------------------------------------------

_ALERTAS_PATH = os.path.join(os.path.dirname(__file__), "alertas.json")
try:
    with open(_ALERTAS_PATH, "r", encoding="utf-8") as _fh:
        _ALERT_DEFS_RAW: list[dict] = json.load(_fh)
except Exception:
    _ALERT_DEFS_RAW = []

# Pré-ordena por prioridade (Warning > Caution > Advisory) — imutável
_PRIORITY = {"Warning": 0, "Caution": 1, "Advisory": 2}
_ALERT_DEFS: list[dict] = sorted(
    _ALERT_DEFS_RAW, key=lambda x: _PRIORITY.get(x.get("categoria", ""), 3)
)


# -----------------------------------------------------------------------
# Dicionário de tradução MWC_DATA → (texto EICAS, severidade)
# -----------------------------------------------------------------------

@st.cache_data
def get_mwc_translation() -> dict[int, tuple[str, str]]:
    _mwc_catalog_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "mwc_data_catalogo.json"))
    translation: dict[int, tuple[str, str]] = {0: ("", "normal")}
    try:
        with open(_mwc_catalog_path, "r", encoding="utf-8") as _fh:
            for _k, _v in json.load(_fh).items():
                _msg = _v.get("mensagem")
                _level = _v.get("categoria")
                if _msg and _level:
                    translation[int(_k)] = (_msg, _level.lower())
    except Exception as e:
        print(f"Erro ao carregar mwc_data_catalogo.json: {e}")
    return translation

# -----------------------------------------------------------------------
# Descrições humanas das colunas de falha MW* (Fase 3)
# -----------------------------------------------------------------------

FAULT_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    # MW1 — sensores de medição
    "MW1_FPS1":    ("FAIL PS1 SENSOR",        "caution"),
    "MW1_FPS1ADC": ("FAIL PS1 ADC",           "caution"),
    "MW1_FMNADC":  ("FAIL MN ADC",            "caution"),
    "MW1_FTPS1":   ("FAIL T PS1 SENSOR",      "caution"),
    "MW1_FT1":     ("FAIL T1 SENSOR",         "caution"),
    "MW1_FT5":     ("FAIL T5 SENSOR",         "caution"),
    "MW1_FTOTTQ":  ("FAIL TOT/TQ SENSOR",     "caution"),
    "MW1_FNG":     ("FAIL Ng SENSOR",         "caution"),
    "MW1_FNP":     ("FAIL Np SENSOR",         "caution"),
    "MW1_FQ":      ("FAIL TORQUE SENSOR",     "caution"),
    "MW1_SUBIDLE": ("SUB-IDLE DETECT",        "caution"),
    "MW1_FLUART1": ("FAIL UART1",             "caution"),
    "MW1_FLUART2": ("FAIL UART2",             "caution"),
    "MW1_FLARINC": ("FAIL ARINC LINK",        "caution"),
    "MW1_FOATADC": ("FAIL OAT ADC",           "caution"),
    "MW1_FRT5BT":  ("FAIL RT5 BATT",         "caution"),
    # MW2 — atuadores e discretos
    "MW2_FWF":     ("FAIL FUEL FLOW",         "caution"),
    "MW2_FPCL":    ("FAIL PCL SENSOR",        "caution"),
    "MW2_FAPCL":   ("FAIL ANALOG PCL",        "caution"),
    "MW2_FDCDIS":  ("FAIL DC DISCRETE",       "caution"),
    "MW2_FSTRTDIS":("FAIL START DISCRETE",    "caution"),
    "MW2_FRIGDIS": ("FAIL IGN DISCRETE",      "caution"),
    "MW2_FWOW":    ("FAIL WOW DISCRETE",      "caution"),
    "MW2_FPMADIS": ("FAIL PMA DISCRETE",      "caution"),
    "MW2_NOSMM":   ("NO SMM COMM",            "caution"),
    "MW2_FRCPLA":  ("FAIL RCPLA",             "caution"),
    "MW2_FCREEP":  ("CREEP DETECTED",         "caution"),
    "MW2_FDCU":    ("FAIL DCU COMM",          "caution"),
    "MW2_FRQGT":   ("FAIL RQ GROUND TEST",    "caution"),
    "MW2_FRQBT":   ("FAIL RQ BENCH TEST",     "caution"),
    "MW2_FLOWVOLT":("LOW VOLTAGE",            "warning"),
    "MW2_RORIGGNG":("RIG Ng OUT OF RANGE",    "caution"),
    # MW3 — loops e hardware PMU
    "MW3_FWFLOOP": ("FAIL WF LOOP",           "caution"),
    "MW3_FBALOOP": ("FAIL BA LOOP",           "caution"),
    "MW3_FPIUTM":  ("FAIL PIU TM",            "caution"),
    "MW3_FFMUSM":  ("FAIL FMU SM",            "caution"),
    "MW3_FPMUFDIS":("FAIL PMU F DISCRETE",    "caution"),
    "MW3_FPMUWDIS":("FAIL PMU W DISCRETE",    "caution"),
    "MW3_FIGNDIS": ("FAIL IGN DISCRETE",      "caution"),
    "MW3_FNPCSA":  ("FAIL Np CSA",            "caution"),
    "MW3_FNPRDIS": ("FAIL Np R DISCRETE",     "caution"),
    "MW3_FQBUGDIS":("FAIL Q BUG DISCRETE",    "caution"),
    "MW3_FTMWA":   ("FAIL TMW A",             "caution"),
    "MW3_FPMUHW":  ("FAIL PMU HARDWARE",      "warning"),
    "MW3_FAILEEWR":("FAIL EEPROM WRITE",      "caution"),
    "MW3_FTTCOAT": ("FAIL TTC OAT",           "caution"),
    "MW3_FTTCPS1": ("FAIL TTC PS1",           "caution"),
    "MW3_FSHUTDIS":("FAIL SHUTDOWN SOL",      "warning"),
}


# -----------------------------------------------------------------------
# Controlador de Tempo Global — Fase 1
# -----------------------------------------------------------------------

class TimeController:
    """Gerencia o estado temporal global via st.session_state."""

    SESSION_KEY: str = "current_time_index"

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Inicializa st.session_state.current_time_index e play_state na primeira execução."""
        if self.SESSION_KEY not in st.session_state:
            st.session_state[self.SESSION_KEY] = 0
        if "is_playing" not in st.session_state:
            st.session_state.is_playing = False

    def render_slider(self, time_column: str = "TIME") -> int:
        """Renderiza o slider de tempo com botão Play/Pause e retorna o índice selecionado."""
        n = len(self.df)
        if n == 0:
            return 0

        current_idx: int = st.session_state.get(self.SESSION_KEY, 0)
        current_idx = max(0, min(current_idx, n - 1))

        # Layout com Colunas: Play/Pause | Slider
        col_btn, col_sld = st.columns([1, 15])

        with col_btn:
            # Ícone dinâmico Play ou Pause
            btn_label = "⏸" if st.session_state.is_playing else "▶"
            if st.button(btn_label, use_container_width=True, key="play_pause_btn"):
                st.session_state.is_playing = not st.session_state.is_playing
                st.rerun()

        with col_sld:
            # Slider: a chave do widget agora é independente para evitar conflito de escrita
            idx: int = st.slider(
                "Linha do Tempo",
                min_value=0,
                max_value=n - 1,
                value=current_idx,
                key=f"{self.SESSION_KEY}_widget",
                label_visibility="collapsed",
            )
            # Sincroniza o valor do slider de volta para o estado global
            if idx != current_idx:
                st.session_state[self.SESSION_KEY] = idx
                st.rerun()

        # Lógica de Reprodução Automática
        if st.session_state.is_playing:
            import time
            if current_idx < n - 1:
                st.session_state[self.SESSION_KEY] = current_idx + 1
                time.sleep(0.05)
                st.rerun()
            else:
                st.session_state.is_playing = False
                st.rerun()

        return int(st.session_state[self.SESSION_KEY])

    def get_snapshot(self, time_index: int) -> pd.Series:
        """Retorna a linha do DataFrame no índice temporal atual."""
        idx = max(0, min(time_index, len(self.df) - 1))
        return self.df.iloc[idx]


# -----------------------------------------------------------------------
# Box Superior: Horizonte Artificial + Dados Críticos — Fase 1
# -----------------------------------------------------------------------

class AttitudeBox:
    """Renderiza o Box Superior com o horizonte artificial e dados críticos."""

    def __init__(self) -> None:
        self._attitude = AttitudeIndicator()
        self._fault_panel = FaultPanel()

    def render(self, snapshot: pd.Series, fault_columns: list[str] | None = None) -> None:
        """Renderiza painel de falhas (central) + box de motor (esquerda) + box de voo (direita)."""

        def _safe(key: str, fallback: float = 0.0) -> float:
            val = snapshot.get(key, fallback)
            try:
                f = float(val)
                return f if f == f else fallback  # NaN check
            except Exception:
                return fallback

        # Helper para cores de alerta de motor
        def _get_engine_color(val: float, var: str) -> str:
            lims = ENGINE_LIMITS.get(var)
            if not lims: return COLORS["normal"]
            caution, warning = lims["caution"], lims["warning"]
            if var == "OP": # Limite mínimo (Oil Press)
                if val <= warning: return COLORS["warning"]
                if val <= caution: return COLORS["caution"]
            else:
                if val >= warning: return COLORS["warning"]
                if val >= caution: return COLORS["caution"]
            return "#00FF88" # Verde normal se dentro dos limites

        # Dados de Voo
        pitch, roll, altitude, speed, nz, aoa = _safe("APA"), _safe("ARA"), _safe("BALT", _safe("PALT")), _safe("MACH", _safe("AS")), _safe("NZ"), _safe("AOA")
        
        # Dados de Motor
        q, itt, ng, np, ff, ot, op, pcl = _safe("Q"), _safe("ITT"), _safe("NG"), _safe("NP"), _safe("FF"), _safe("OT"), _safe("OP"), _safe("PCL")

        col_metrics, col_horizon, col_engine = st.columns([1, 2, 1])

        with col_metrics:
            nz_color = COLORS["warning"] if abs(nz) > NZ_ALERT_THRESHOLD else "#00FF88"
            html_metrics = (
                f'<div style="font-family: monospace; background: #0E1117; border: 1px solid #2D2D2D; border-radius: 8px; padding: 14px 10px; text-align: center; line-height: 1.3; height: 320px; display: flex; flex-direction: column; justify-content: center;">'
                f'<div style="font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ALTITUDE (BALT)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:#00FF88;">{altitude:,.0f} ft</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">VELOCIDADE (MACH)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:#00FF88;">{speed:.3f}</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ATITUDE (APA/ARA)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:#FFC107;">{pitch:+.1f}°/{roll:+.1f}°</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">CARGA (NZ)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:{nz_color};">{nz:+.2f}G</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ATAQUE (AOA)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:#FAFAFA;">{aoa:.1f}°</div>'
                f'</div>'
            )
            st.markdown(html_metrics, unsafe_allow_html=True)

        with col_horizon:
            # ── Painel de Alertas EICAS (FaultPanel) ──
            # NOTA: self._attitude (AttitudeIndicator) está preservado para uso futuro
            # no bloco de Análise de Atitude + Geolocalização (Google Maps API).
            # O toggle 🌐 Horizonte Artificial foi removido desta tela — S-03 suspensa.
            mwc_code = int(_safe("MWC_DATA"))
            mwc_text, _ = get_mwc_translation().get(mwc_code, ("", ""))

            status_list = []
            for alert in _ALERT_DEFS:
                is_active = False
                msg = alert["mensagem"]

                if msg in snapshot.index and snapshot.get(msg, 0) == 1:
                    is_active = True
                elif mwc_text and msg == mwc_text:
                    is_active = True

                status_list.append({
                    "name": msg,
                    "level": alert["categoria"].upper(),
                    "active": is_active,
                })

            self._fault_panel.render(status_list)

        with col_engine:
            # Lógica de cor para PCL
            if pcl < 0: pcl_color = "#4A90D9" # Idle
            elif pcl < 130: pcl_color = "#00FF88" # Cruise
            else: pcl_color = "#FF4B4B" # Max

            html_engine = (
                f'<div style="font-family: monospace; background: #0E1117; border: 1px solid #2D2D2D; border-radius: 8px; padding: 14px 10px; text-align: center; line-height: 1.3; height: 320px; display: flex; flex-direction: column; justify-content: center;">'
                f'<div style="font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">TORQUE (Q)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:{_get_engine_color(q, "Q")};">{q:.1f}%</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ITT</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:{_get_engine_color(itt, "ITT")};">{itt:.0f}°C</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">NG / NP (%)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold;"><span style="color:{_get_engine_color(ng, "NG")};">{ng:.1f}</span>/<span style="color:{_get_engine_color(np, "NP")};">{np:.1f}</span></div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">MANETE (PCL)</div>'
                f'<div style="font-size:1.4rem; font-weight:bold; color:{pcl_color};">{pcl:.1f}°</div>'
                f'<div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">OIL T / P</div>'
                f'<div style="font-size:1.4rem; font-weight:bold;"><span style="color:{_get_engine_color(ot, "OT")};">{ot:.0f}°</span>/<span style="color:{_get_engine_color(op, "OP")};">{op:.0f}P</span></div>'
                f'</div>'
            )
            st.markdown(html_engine, unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Painel EICAS Principal — Fase 2 (gauges) / Fase 3 (CAS — skeleton)
# -----------------------------------------------------------------------

class EICASPanel:
    """Renderiza o painel EICAS completo no layout Streamlit."""

    EICAS_STYLE: str = "background-color: #0E1117; border-radius: 8px; padding: 12px;"

    def __init__(self) -> None:
        self._gauge_plotter = EngineGaugePlotter()

    def render(self, snapshot: pd.Series, fault_columns: list[str]) -> None:
        """Ponto de entrada principal do painel EICAS para o snapshot atual."""
        # Gauges (linha completa)
        self.render_engine_gauges(snapshot)

        # CAS (Crew Alerting System)
        mwc_raw = snapshot.get("MWC_DATA", 0)
        try:
            mwc_code = int(float(mwc_raw)) if mwc_raw == mwc_raw else 0
        except Exception:
            mwc_code = 0

        mw_flags = {}
        for col in fault_columns:
            if col in snapshot.index:
                val = snapshot.get(col, 0)
                try:
                    fval = float(val)
                    mw_flags[col] = int(fval) if fval == fval else 0
                except (ValueError, TypeError):
                    mw_flags[col] = 0
        self.render_cas_window(mwc_code, mw_flags)

    def render_engine_gauges(self, snapshot: pd.Series) -> None:
        """Renderiza os 7 gauges do motor (Q, ITT, NP, NG, FF, OT, OP) em colunas."""
        st.markdown(
            "<div style='background:#0E1117; border:1px solid #2D2D2D; "
            "border-radius:8px; padding:6px 4px 0px 4px;'>",
            unsafe_allow_html=True,
        )

        figs = self._gauge_plotter.plot_all_engine_gauges(snapshot)
        cols = st.columns(7)
        for i, (col, fig) in enumerate(zip(cols, figs)):
            with col:
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False, "staticPlot": True},
                    key=f"gauge_{i}_{snapshot.name}" # snapshot.name é o índice da linha (tempo)
                )

        st.markdown("</div>", unsafe_allow_html=True)

    def render_cas_window(self, mwc_code: int, mw_flags: dict[str, int]) -> None:
        """Renderiza a janela CAS.

        - Sem alertas → painel preto com "VOO NORMAL" em cinza.
        - WARNINGS (vermelho) sempre acima dos CAUTIONS (amarelo).
        - Cada falha MW* ativa gera uma linha de CAUTION (ou WARNING se mapeado).
        """
        warnings: list[str] = []
        cautions: list[str] = []

        # 1. MWC_DATA → mensagem principal
        mwc_text, mwc_sev = self._translate_mwc_code(mwc_code)
        if mwc_text:
            (warnings if mwc_sev == "warning" else cautions).append(mwc_text)

        # 2. Flags MW* discretas
        for col, val in mw_flags.items():
            if val != 1:
                continue
            desc, sev = FAULT_DESCRIPTIONS.get(
                col,
                (col.split("_", 1)[-1].replace("_", " "), "caution"),
            )
            (warnings if sev == "warning" else cautions).append(desc)

        # 3. Renderiza painel
        if not warnings and not cautions:
            body = (
                "<div style='color:#2A2A2A; font-size:0.75rem; "
                "text-align:center; padding:6px 0; letter-spacing:2px;'>"
                "— VOO NORMAL —</div>"
            )
        else:
            rows = ""
            for msg in warnings:
                rows += (
                    f"<div style='color:#FF4B4B; font-weight:bold; "
                    f"font-size:0.85rem; padding:2px 6px; "
                    f"border-left:3px solid #FF4B4B; margin-bottom:2px;'>"
                    f"▶ {msg}</div>"
                )
            for msg in cautions:
                rows += (
                    f"<div style='color:#FFC107; font-size:0.82rem; "
                    f"padding:2px 6px; "
                    f"border-left:3px solid #FFC107; margin-bottom:2px;'>"
                    f"▶ {msg}</div>"
                )
            body = rows

        n_alerts = len(warnings) + len(cautions)
        header_color = "#FF4B4B" if warnings else "#FFC107" if cautions else "#333333"
        header_label = (
            f"CAS — {len(warnings)}W / {len(cautions)}C"
            if n_alerts
            else "CAS"
        )

        st.markdown(
            f"<div style='"
            f"background:#000000; border:1px solid {header_color}; "
            f"border-radius:6px; margin-top:6px; padding:6px 4px;'>"
            f"  <div style='font-size:0.6rem; color:{header_color}; "
            f"  letter-spacing:2px; padding:0 6px 4px 6px;'>{header_label}</div>"
            f"  {body}"
            f"</div>",
            unsafe_allow_html=True,
        )

    def _translate_mwc_code(self, code: int) -> tuple[str, str]:
        """Traduz código numérico MWC_DATA para (texto, severidade).

        Retorna ('', 'normal') para código 0 ou desconhecido.
        """
        translation = get_mwc_translation()
        if code in translation:
            return translation[code]
        if code != 0:
            return (f"MWC CODE {code}", "caution")
        return ("", "normal")

    def _collect_active_faults(
        self, snapshot: pd.Series, fault_columns: list[str]
    ) -> list[tuple[str, str, str]]:
        """Varre as colunas MW* e retorna lista de (coluna, descrição, severidade) ativas."""
        active = []
        for col in fault_columns:
            val = snapshot.get(col, 0)
            try:
                if float(val) == 1.0:
                    desc, sev = FAULT_DESCRIPTIONS.get(
                        col,
                        (col.split("_", 1)[-1].replace("_", " "), "caution"),
                    )
                    active.append((col, desc, sev))
            except Exception:
                pass
        return active


# -----------------------------------------------------------------------
# Cards de Subsistemas — Fase 2
# -----------------------------------------------------------------------

class SubsystemCards:
    """Renderiza os cards informativos do Box Inferior."""

    _CARD_BASE = (
        "background:#0E1117; border:1px solid #2D2D2D; border-radius:8px; "
        "padding:12px; text-align:center; font-family:monospace; "
        "height:130px; display:flex; flex-direction:column; justify-content:center; "
        "box-sizing:border-box;"
    )

    def render_all(self, snapshot: pd.Series) -> None:
        """Renderiza os quatro cards de subsistemas lado a lado."""

        def _safe(key: str, fallback: float = 0.0) -> float:
            val = snapshot.get(key, fallback)
            try:
                f = float(val)
                return f if f == f else fallback
            except Exception:
                return fallback

        ldg = int(_safe("LDG"))
        wow = int(_safe("WOW"))
        nz  = _safe("NZ")

        col_gear, col_nz, col_engine, col_pcl = st.columns(4)

        with col_gear:
            self.render_landing_gear_card(ldg, wow)
        with col_nz:
            self.render_structural_load_card(nz)
        with col_engine:
            self.render_engine_summary_card(snapshot)
        with col_pcl:
            self._render_pcl_card(_safe("PCL"))

    def render_landing_gear_card(self, ldg: int, wow: int) -> None:
        """Exibe o card do Trem de Pouso com identificação das variáveis."""
        gear_label = "ABAIXADO" if ldg == 0 else "RECOLHIDO"
        gear_color = "#00FF88" if ldg == 0 else "#FFC107"
        phase_label = "SOLO" if wow == 1 else "AR"
        phase_color = "#A07850" if wow == 1 else "#4A90D9"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>TREM DE POUSO</div>"
            f"  <div style='font-size:1.0rem;font-weight:bold;color:{gear_color}; margin-top:4px;'><span style='color: #888; font-size: 0.75rem;'>LDG:</span> {gear_label}</div>"
            f"  <div style='font-size:1.0rem;font-weight:bold;color:{phase_color}; margin-top:2px;'><span style='color: #888; font-size: 0.75rem;'>WOW:</span> {phase_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_structural_load_card(self, nz: float) -> None:
        """Exibe card de Carga Estrutural (Força G). Alerta visual se NZ > 4.0G."""
        alert = abs(nz) > NZ_ALERT_THRESHOLD
        nz_color = "#FF4B4B" if alert else "#00FF88"
        border_color = "#FF4B4B" if alert else "#2D2D2D"
        alert_text = "<div style='font-size:0.65rem;color:#FF4B4B;'>⚠ LIMITE ESTRUTURAL</div>" if alert else ""

        st.markdown(
            f"<div style='{self._CARD_BASE} border-color:{border_color};'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>CARGA ESTRUTURAL</div>"
            f"  <div style='font-size:1.6rem;font-weight:bold;color:{nz_color};'>{nz:+.2f} G</div>"
            f"  {alert_text}"
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_engine_summary_card(self, snapshot: pd.Series) -> None:
        """Exibe card resumido do motor: ITT, FF e status geral."""
        def _safe(k: str) -> float:
            v = snapshot.get(k, 0)
            try:
                f = float(v)
                return f if f == f else 0.0
            except Exception:
                return 0.0

        itt = _safe("ITT")
        ff  = _safe("FF")
        ng  = _safe("NG")

        itt_color = "#FF4B4B" if itt > 1000 else "#FFC107" if itt > 850 else "#00FF88"
        ff_color  = "#FF4B4B" if ff  > 480  else "#FFC107" if ff  > 420 else "#00FF88"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>MOTOR</div>"
            f"  <div style='font-size:0.8rem;margin-top:4px;'>"
            f"    <span style='color:#888;'>ITT </span>"
            f"    <span style='color:{itt_color};font-weight:bold;'>{itt:.0f}°C</span>"
            f"  </div>"
            f"  <div style='font-size:0.8rem;margin-top:2px;'>"
            f"    <span style='color:#888;'>FF &nbsp;</span>"
            f"    <span style='color:{ff_color};font-weight:bold;'>{ff:.0f} kg/h</span>"
            f"  </div>"
            f"  <div style='font-size:0.8rem;margin-top:2px;'>"
            f"    <span style='color:#888;'>Ng &nbsp;</span>"
            f"    <span style='color:#FAFAFA;'>{ng:.1f}%</span>"
            f"  </div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    def _render_pcl_card(self, pcl: float) -> None:
        """Exibe a posição da Manete de Potência (PCL)."""
        # PCL range operacional: -20 a +179°
        # Zonas aproximadas: < 0° = Ground Idle, 0-60° = Flight Idle→Cruise, > 130° = Max Power
        if pcl < 0:
            pcl_label, pcl_color = "GROUND IDLE", "#4A90D9"
        elif pcl < 60:
            pcl_label, pcl_color = "IDLE / CRUISE", "#00FF88"
        elif pcl < 130:
            pcl_label, pcl_color = "CRUISE / CLIMB", "#FFC107"
        else:
            pcl_label, pcl_color = "MAX POWER", "#FF4B4B"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>MANETE (PCL)</div>"
            f"  <div style='font-size:1.6rem;font-weight:bold;color:{pcl_color};'>{pcl:.1f}°</div>"
            f"  <div style='font-size:0.7rem;color:{pcl_color};margin-top:2px;'>{pcl_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
