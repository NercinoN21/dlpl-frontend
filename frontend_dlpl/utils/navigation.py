import base64
from os import getenv
from pathlib import Path

import streamlit as st


# --- FUNÇÕES HELPER ---
def load_image_as_base64(image_path):
    """Carrega uma imagem local e a converte para base64 para embutir no app."""
    try:
        with Path(image_path).open('rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def floating_reload_button():
    """
    Cria um botão flutuante no canto inferior direito para recarregar a página,
    imitando o comportamento do F5 (hard reload).
    """
    st.markdown(
        """
    <style>
        .reload-button {
            position: fixed;
            bottom: 20px;
            right: 25px;
            background-color: #4A7729; /* Verde DLPL */
            color: white;
            border: none;
            border-radius: 50%;
            width: 55px;
            height: 55px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px M(0,0,0,0.2);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.2s ease-in-out;
        }
        .reload-button:hover {
            transform: scale(1.1) rotate(90deg);
            box-shadow: 0 6px 16px rgba(0,0,0,0.3);
        }
    </style>
    <a href="javascript:location.reload(true)" target="_self" class="reload-button">
        &#8635;
    </a>
    """,
        unsafe_allow_html=True,
    )
