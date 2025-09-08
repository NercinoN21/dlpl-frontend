import base64
import re
import time
from os import getenv
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from unidecode import unidecode
from utils.navigation import floating_reload_button

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    page_title='Inscrição | DLPL', page_icon='📝', layout='wide', initial_sidebar_state='expanded'
)

# Carrega as variáveis de ambiente e define a URL da API
floating_reload_button()
load_dotenv()
API_BASE_URL = getenv('API_URL', 'http://localhost:8000')


# --- FUNÇÕES HELPER ---
def remover_numeros_e_acentos_unidecode(text):
    """Limpa o texto, removendo números e acentos, e converte para maiúsculas."""
    text_sem_numeros = re.sub(r'\d+', '', text)
    text_limpa = unidecode(text_sem_numeros)
    return text_limpa.upper()


def load_image_as_base64(image_path):
    """Carrega uma imagem local e a converte para base64 para embutir no app."""
    try:
        with Path(image_path).open('rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None


def load_css():
    """
    Carrega e injeta um CSS customizado que se adapta automaticamente
    aos temas claro e escuro do Streamlit.
    """
    st.markdown(
        """
    <style>
        /* Remove a barra superior do Streamlit */
        header {visibility: hidden;}

        /* --- TIPOGRAFIA --- */
        h1, h2, h3 { color: var(--text-color); }
        h1 { font-weight: 600; padding-bottom: 1rem; text-align: center; }
        h2 { font-weight: 600; text-align: center;}
        h3 { font-weight: 500; opacity: 0.8; padding-bottom: 1rem; text-align: center;}

        /* --- "CARDS" / CONTAINERS --- */
        div[data-testid="stForm"] {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--border-color, rgba(128,128,128,0.2));
            border-radius: 18px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
            overflow: hidden;
            margin-bottom: 1.5rem;
        }
        div[data-testid="stForm"] > form {
            padding: 2rem 2.5rem;
        }

        /* --- WIDGETS (BOTÕES, INPUTS) --- */
        .stButton > button {
            border: none; border-radius: 12px; padding: 12px 24px;
            font-weight: 600; font-size: 15px; color: white;
            background-color: #4A7729; /* Verde do logo DLPL */
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #3b6021;
            transform: translateY(-2px);
        }
        .stButton > button:focus {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(74, 119, 41, 0.4);
        }

        /* Inputs de texto e Selectbox */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 12px !important;
            border: 1px solid var(--border-color, rgba(128,128,128,0.2)) !important;
            background-color: var(--background-color) !important;
            font-size: 16px !important;
        }
        .stTextInput input:focus, .stSelectbox > div > div:focus-within {
            border: 2px solid #4A7729 !important;
            box-shadow: 0 0 0 3px rgba(74, 119, 41, 0.4) !important;
        }

        /* --- LOGO --- */
        .logo-container {
            display: flex; justify-content: center;
            margin: 1rem 0 2rem 0;
        }
        .logo-img {
            max-width: 150px; height: 150px;
            filter: none !important; /* Impede que o tema escuro inverta as cores da logo */
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


# --- EXECUÇÃO PRINCIPAL ---

load_css()

# Adiciona a logo ao topo da página principal
logo_base64 = load_image_as_base64('logo.png')
if logo_base64:
    st.markdown(
        f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" class="logo-img"></div>',
        unsafe_allow_html=True,
    )

# Inicialização do estado da sessão
st.session_state.setdefault('is_verified', False)
st.session_state.setdefault('name', '')
st.session_state.setdefault('cpf', '')
st.session_state.setdefault('courses', [])
st.session_state.setdefault('turmas', [])
st.session_state.setdefault('semestre', [])

# Centraliza o conteúdo do formulário na tela
_, main_col, _ = st.columns([1, 1.5, 1])
with main_col:
    # --- ETAPA 1: VERIFICAÇÃO DE DADOS ---
    if not st.session_state.is_verified:
        st.title('Sistema de Inscrição')

        with st.form(key='form_verification'):
            st.header('Passo 1: Verificação de Dados')
            name = st.text_input('Nome Completo', placeholder='Digite seu nome completo')
            cpf = st.text_input('CPF', placeholder='Exemplo: 111.111.111-11')
            submit_button = st.form_submit_button(label='Verificar', use_container_width=True)

        if submit_button:
            if not name or not cpf:
                st.error('Por favor, preencha o nome e o CPF.')
            else:
                cleaned_name = remover_numeros_e_acentos_unidecode(name)
                with st.spinner('Verificando seus dados...'):
                    try:
                        response = requests.get(
                            f'{API_BASE_URL}/enrollment/verify-cpf-by-name',
                            params={'name': cleaned_name, 'cpf': cpf},
                        )
                        response.raise_for_status()
                        st.session_state.is_verified = True
                        st.session_state.name = cleaned_name
                        st.session_state.cpf = cpf
                        st.success('Dados verificados! Você pode prosseguir.')
                        time.sleep(1)
                        st.rerun()
                    except requests.exceptions.HTTPError as e:
                        msg = e.response.json()
                        st.error(f'Erro na verificação: {msg}')
                    except requests.exceptions.RequestException as e:
                        st.error(f'Erro ao conectar com a API: {e}')

    # --- ETAPA 2: INSCRIÇÃO ---
    if st.session_state.is_verified:
        st.title('Finalize sua Inscrição')

        # Obter cursos (se ainda não tiver)
        if not st.session_state.courses:
            with st.spinner('Buscando cursos...'):
                try:
                    response = requests.get(
                        f'{API_BASE_URL}/enrollment/courses',
                        params={'name': st.session_state.name, 'cpf': st.session_state.cpf},
                    )
                    response.raise_for_status()
                    st.session_state.courses = response.json().get('courses', [])
                except requests.exceptions.RequestException:
                    st.error('Erro ao buscar cursos.')

        if not st.session_state.courses:
            st.warning('Nenhum curso disponível para você no momento.')
            st.stop()

        with st.form(key='form_enrollment'):
            st.header('Passo 2: Seleção de Curso')
            st.info(f'Bem-vindo(a), {st.session_state.name}!')

            selected_course = st.selectbox('Selecione seu curso', st.session_state.courses)

            # Lógica para buscar informações do curso e turmas
            if selected_course:
                session_key = f'entry_info_{selected_course}'
                if session_key not in st.session_state:
                    try:
                        entry_info_resp = requests.get(
                            f'{API_BASE_URL}/enrollment/entry-info',
                            params={'name': st.session_state.name, 'cpf': st.session_state.cpf, 'course': selected_course},
                        )
                        entry_info_resp.raise_for_status()
                        st.session_state[session_key] = entry_info_resp.json()

                        if not st.session_state.turmas:
                            turmas_resp = requests.get(f'{API_BASE_URL}/turma/active')
                            turmas_resp.raise_for_status()
                            data = turmas_resp.json()
                            st.session_state.turmas = data.get('turmas', [])
                            st.session_state.semestre = [data.get('active_semester', 'N/A')]
                    except requests.exceptions.RequestException as e:
                        st.error(f'Erro ao buscar informações: {e}')

                entry_info = st.session_state.get(session_key)
                if entry_info:
                    st.write(f"Sua Nota Predita: **{entry_info.get('NOTA_PREDITA', 'N/A')}**")
                    selected_choice = st.selectbox('Escolha uma opção', entry_info.get('OPCOES', []))

            turma = st.selectbox('Turma', [t['name'] for t in st.session_state.get('turmas', [])])
            semester = st.selectbox('Semestre', st.session_state.get('semestre', []), disabled=True)

            submit_enrollment = st.form_submit_button('Finalizar Inscrição', use_container_width=True)

            if submit_enrollment:
                if not all([turma, semester, selected_choice]):
                    st.error('Por favor, selecione todas as opções.')
                else:
                    with st.spinner('Finalizando sua inscrição...'):
                        payload = {
                            'name': st.session_state.name, 'cpf': st.session_state.cpf,
                            'course': selected_course, 'choice': selected_choice,
                            'turma': turma, 'semester': semester,
                        }
                        try:
                            response = requests.post(f'{API_BASE_URL}/enrollment/', json=payload)
                            response.raise_for_status()
                            st.success('Inscrição finalizada com sucesso!')
                            st.balloons()
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            time.sleep(2)
                            st.rerun()
                        except requests.exceptions.HTTPError as e:
                            detail = e.response.json().get('detail', 'Ocorreu um erro.')
                            st.error(f'Erro ao finalizar: {detail}')
                        except requests.exceptions.RequestException as e:
                            st.error(f'Erro de conexão: {e}')