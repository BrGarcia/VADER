"""
test_time_controller.py — Testa a lógica de reprodução automática (RF05.1).

Os métodos de callback do TimeController só manipulam `st.session_state` e o
tamanho do DataFrame, então podem ser testados sem runtime do Streamlit
substituindo `session_state` por um dicionário simples.
"""
from unittest.mock import patch

import pandas as pd
import pytest

from src.ui.components import TimeController


@pytest.fixture
def df_voo() -> pd.DataFrame:
    """DataFrame mínimo com 1000 amostras."""
    return pd.DataFrame({"TIME": range(1000)})


@pytest.fixture
def controller(df_voo):
    """TimeController com session_state substituído por um dict."""
    fake_state: dict = {}
    with patch("src.ui.components.st") as fake_st:
        fake_st.session_state = fake_state
        ctrl = TimeController(df_voo)
        yield ctrl, fake_state


def test_state_keys_cobrem_todas_as_chaves_usadas():
    """STATE_KEYS deve listar tudo que precisa ser limpo ao trocar de voo."""
    assert TimeController.SESSION_KEY in TimeController.STATE_KEYS
    assert f"{TimeController.SESSION_KEY}_widget" in TimeController.STATE_KEYS
    assert TimeController.PLAY_KEY in TimeController.STATE_KEYS


def test_init_state_inicializa_indices_zerados(controller):
    ctrl, state = controller
    assert state[TimeController.SESSION_KEY] == 0
    assert state[f"{TimeController.SESSION_KEY}_widget"] == 0
    assert state[TimeController.PLAY_KEY] is False


def test_init_state_corrige_indice_fora_da_faixa(df_voo):
    """Voo novo menor que o anterior não pode deixar o slider fora da faixa."""
    fake_state = {
        TimeController.SESSION_KEY: 5000,
        f"{TimeController.SESSION_KEY}_widget": 5000,
        TimeController.PLAY_KEY: False,
    }
    with patch("src.ui.components.st") as fake_st:
        fake_st.session_state = fake_state
        TimeController(df_voo)  # n = 1000, índice salvo = 5000

    assert fake_state[f"{TimeController.SESSION_KEY}_widget"] == 0
    assert fake_state[TimeController.SESSION_KEY] == 0


def test_playback_step_cobre_o_voo_no_tempo_alvo(controller):
    """O passo deve percorrer o voo inteiro em ~_PLAYBACK_TARGET_SEC segundos."""
    ctrl, _ = controller
    n = len(ctrl.df)
    step = ctrl._playback_step(n)

    quadros = n / step
    duracao_s = quadros / TimeController._PLAYBACK_FPS
    assert step >= 1
    assert duracao_s == pytest.approx(TimeController._PLAYBACK_TARGET_SEC, rel=0.5)


def test_playback_step_nunca_zero_em_voo_curto(df_voo):
    """Arquivos pequenos ainda precisam avançar pelo menos 1 índice por quadro."""
    fake_state: dict = {}
    with patch("src.ui.components.st") as fake_st:
        fake_st.session_state = fake_state
        ctrl = TimeController(pd.DataFrame({"TIME": range(5)}))
        assert ctrl._playback_step(5) == 1


def test_toggle_play_liga_e_desliga(controller):
    ctrl, state = controller

    ctrl._toggle_play()
    assert state[TimeController.PLAY_KEY] is True

    ctrl._toggle_play()
    assert state[TimeController.PLAY_KEY] is False


def test_toggle_play_no_fim_reinicia_do_comeco(controller):
    """RF05.1 — dar Play parado no último quadro deve reiniciar a reprodução."""
    ctrl, state = controller
    ultimo = len(ctrl.df) - 1
    state[TimeController.SESSION_KEY] = ultimo
    state[f"{TimeController.SESSION_KEY}_widget"] = ultimo

    ctrl._toggle_play()

    assert state[TimeController.SESSION_KEY] == 0
    assert state[f"{TimeController.SESSION_KEY}_widget"] == 0
    assert state[TimeController.PLAY_KEY] is True


def test_pause_no_fim_nao_reinicia(controller):
    """Pausar no último quadro deve manter a posição, não voltar ao início."""
    ctrl, state = controller
    ultimo = len(ctrl.df) - 1
    state[TimeController.SESSION_KEY] = ultimo
    state[TimeController.PLAY_KEY] = True

    ctrl._toggle_play()

    assert state[TimeController.PLAY_KEY] is False
    assert state[TimeController.SESSION_KEY] == ultimo


def test_mover_slider_pausa_reproducao(controller):
    """RF05.1 — interação manual com o slider interrompe o playback."""
    ctrl, state = controller
    state[TimeController.PLAY_KEY] = True
    state[f"{TimeController.SESSION_KEY}_widget"] = 42

    ctrl._sync_slider_state()

    assert state[TimeController.SESSION_KEY] == 42
    assert state[TimeController.PLAY_KEY] is False
