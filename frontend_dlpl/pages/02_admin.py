import base64
from datetime import datetime
from os import getenv
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from io import BytesIO

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(page_title='Admin | DLPL', page_icon='🔑', layout='wide', initial_sidebar_state="expanded")

# Carrega as variáveis de ambiente e define a URL da API
load_dotenv()
API_BASE_URL = getenv('API_URL', 'http://localhost:3001')


# --- FUNÇÕES HELPER ---
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
        h1 { font-weight: 600; padding-bottom: 1rem; }
        h2 { font-weight: 600; }
        h3 { font-weight: 500; opacity: 0.8; padding-bottom: 1rem; }

        /* --- ABAS (TABS) --- */
        div[data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 1px solid var(--border-color, rgba(128,128,128,0.2));
        }
        button[data-baseweb="tab"] {
            background-color: transparent; border-bottom: 2px solid transparent !important;
            font-weight: 500; color: var(--text-color); opacity: 0.7;
            transition: all 0.2s;
        }
        button[data-baseweb="tab"]:hover {
            background-color: var(--secondary-background-color); opacity: 1;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4A7729; /* Verde DLPL (cor da marca) */
            border-bottom: 2px solid #4A7729 !important; opacity: 1;
        }

        /* --- "CARDS" / CONTAINERS --- */
        div[data-testid="stExpander"], div[data-testid="stForm"] {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--border-color, rgba(128,128,128,0.2));
            border-radius: 18px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
            overflow: hidden; margin-bottom: 1.5rem;
        }
        div[data-testid="stExpander"] > details { padding: 1rem 1.25rem; }
        div[data-testid="stExpander"] > details > summary { font-weight: 600; color: var(--text-color); }
        div[data-testid="stForm"] > form { padding: 1.5rem 2rem; }

        /* --- WIDGETS (BOTÕES, INPUTS) --- */
        .stButton > button {
            border: none; border-radius: 12px; padding: 12px 24px;
            font-weight: 600; font-size: 15px; color: white;
            background-color: #4A7729; /* Verde do logo DLPL */
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #3b6021; transform: translateY(-2px);
        }
        .stButton > button:focus {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(74, 119, 41, 0.4);
        }

        /* Botão secundário/perigoso (Delete) */
        .stButton > button[kind="primary"] { background-color: #d93f3f; }
        .stButton > button[kind="primary"]:hover { background-color: #b32b2b; }

        /* Inputs de texto e Selectbox */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 12px !important;
            border: 1px solid var(--border-color, rgba(128,128,128,0.2)) !important;
            background-color: var(--background-color) !important; font-size: 16px !important;
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


def api_request(method, endpoint, params=None, json=None, data=None):
    """Função centralizada para fazer requisições autenticadas à API."""
    if (
        'access_token' not in st.session_state
        or not st.session_state.access_token
    ):
        return None
    try:
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        cookies = st.session_state.auth_cookies
        response = requests.request(
            method,
            f'{API_BASE_URL}{endpoint}',
            headers=headers,
            cookies=cookies,
            params=params,
            json=json,
            data=data,
        )
        response.raise_for_status()
        return response.json() if response.text else {}
    except requests.exceptions.HTTPError as e:
        error = e.response.json()
        st.error(f'Erro na API ({e.response.status_code}): {error}')
        return None
    except requests.exceptions.RequestException as e:
        st.error(f'Erro de conexão: {e}')
        return None


@st.cache_data(ttl=600)
def get_semesters():
    data = api_request('GET', '/turma/semesters')
    return data.get('semesters', []) if data else []


@st.cache_data(ttl=600)
def get_all_turmas():
    data = api_request('GET', '/turma/', params={'is_active': None})
    return data.get('turmas', []) if data else []


def display_login_form():
    """Mostra o formulário de login centralizado."""
    _, main_col, _ = st.columns([1, 1.5, 1])
    with main_col:
        st.title('Área de Administração DLPL')
        with st.form(key='login_form'):
            st.header('Login')
            username = st.text_input(
                'Nome de Usuário', placeholder='Digite seu nome de usuário'
            )
            password = st.text_input(
                'Senha', type='password', placeholder='Digite sua senha'
            )
            if st.form_submit_button('Entrar', width='stretch'):
                try:
                    session = requests.Session()
                    response = session.post(
                        f'{API_BASE_URL}/users/login',
                        data={'name': username, 'password': password},
                    )
                    response.raise_for_status()
                    access_token = response.json().get('token')
                    cookies = session.cookies.get_dict()
                    if access_token and 'session-token' in cookies:
                        st.session_state.access_token = access_token
                        st.session_state.auth_cookies = cookies
                        st.rerun()
                    else:
                        st.error('Credenciais inválidas.')
                except requests.exceptions.HTTPError:
                    st.error('Erro no login. Verifique suas credenciais.')
                except requests.exceptions.RequestException as e:
                    st.error(f'Erro de conexão com a API: {e}')


def display_enrollment_manager():
    st.subheader('Filtrar Inscrições')
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        nome_aluno = st.text_input('Filtrar por nome do aluno')
    with col2:
        semestres_disponiveis = ['Todos'] + get_semesters()
        semestre = st.selectbox('Filtrar por semestre', semestres_disponiveis)
    with col3:
        turmas_disponiveis = ['Todas'] + [t['name'] for t in get_all_turmas()]
        turma = st.selectbox('Filtrar por turma', turmas_disponiveis)
    with col4:
        pass # TODO Filtro por escolha

    params = {
        'query_nome': nome_aluno if nome_aluno else None,
        'query_semestre': semestre if semestre != 'Todos' else None,
        'query_turma': turma if turma != 'Todas' else None,
    }
    data = api_request('GET', '/enrollment/', params=params)
    if data:
        df_inscricoes = pd.DataFrame(data.get('data', []))
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_inscricoes.to_excel(writer, index=False, sheet_name='enrollments')

            for column in df_inscricoes:
                column_width = max(df_inscricoes[column].astype(str).map(len).max(), len(column))
                col_idx = df_inscricoes.columns.get_loc(column)
                writer.sheets['enrollments'].set_column(col_idx, col_idx, column_width)

        st.download_button(
            label='Download dos Dados em Excel',
            data=buffer.getvalue(),
            file_name=f'inscricoes_{nome_aluno or ""}_{semestre or ""}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


        st.dataframe(df_inscricoes, use_container_width=True, hide_index=True)



def display_user_manager():
    with st.expander('➕ Adicionar Novo Usuário'):
        with st.form('new_user_form', clear_on_submit=True):
            new_user_name = st.text_input('Nome do novo usuário')
            new_user_pass = st.text_input('Senha', type='password')
            if st.form_submit_button('Criar Usuário'):
                if new_user_name and new_user_pass:
                    if (
                        api_request(
                            'POST',
                            '/users/',
                            data={
                                'name': new_user_name,
                                'password': new_user_pass,
                            },
                        )
                        is not None
                    ):
                        st.success(f"Usuário '{new_user_name}' criado!")
                        st.rerun()
                else:
                    st.warning('Preencha o nome e a senha.')

    st.subheader('Lista de Usuários')
    data = api_request('GET', '/users/', params={'is_active': None})
    if data:
        df_users = pd.DataFrame(data.get('users', []))
        st.info(
            '💡 Edite o status de "ativo" ou "admin" diretamente na tabela.'
        )
        st.session_state.setdefault('original_users_df', df_users.copy())

        edited_df = st.data_editor(
            df_users, use_container_width=True, disabled=['name']
        )
        if (
            st.session_state.original_users_df
            and not st.session_state.original_users_df.equals(edited_df)
        ):
            diff = st.session_state.original_users_df.compare(
                edited_df, align_axis=0
            ).dropna()
            for idx in diff.index.get_level_values(0).unique():
                user_name = edited_df.loc[idx, 'name']
                if 'is_active' in diff.columns.get_level_values(1):
                    new_status = edited_df.loc[idx, 'is_active']
                    api_request(
                        'PUT',
                        '/users/update-active',
                        data={
                            'name': user_name,
                            'is_active': bool(new_status),
                        },
                    )
                elif 'admin' in diff.columns.get_level_values(1):
                    new_status = edited_df.loc[idx, 'admin']
                    api_request(
                        'PUT',
                        '/users/update-admin',
                        data={'name': user_name, 'admin': bool(new_status)},
                    )
            st.session_state.original_users_df = edited_df.copy()
            st.success('Alterações salvas.')
            st.rerun()


def display_class_manager():
    with st.expander('➕ Adicionar Nova Turma'):
        with st.form('new_class_form', clear_on_submit=True):
            turma_name = st.text_input('Nome da nova turma (ex: Turma A)')
            turma_semester = st.text_input('Semestre (ex: 2025.1)')
            if st.form_submit_button('Criar Turma'):
                if turma_name and turma_semester:
                    if (
                        api_request(
                            'POST',
                            '/turma/',
                            json={
                                'name': turma_name,
                                'semester': turma_semester,
                            },
                        )
                        is not None
                    ):
                        st.success(
                            f"Turma '{turma_name} - {turma_semester}' criada!"
                        )
                        st.cache_data.clear()
                        st.rerun()

    with st.expander('✏️ Editar ou Deletar Turma Existente'):
        turmas = get_all_turmas()
        if not turmas:
            st.warning('Nenhuma turma cadastrada.')
        else:
            turma_options = {
                f"{t['name']} - {t['semester']}": t for t in turmas
            }
            selected_turma_str = st.selectbox(
                'Selecione a turma', turma_options.keys()
            )
            if selected_turma_str:
                selected_turma_obj = turma_options[selected_turma_str]
                with st.form('edit_delete_turma'):
                    st.write(f'**Editando:** {selected_turma_str}')
                    new_name = st.text_input(
                        'Novo nome', value=selected_turma_obj['name']
                    )
                    new_semester = st.text_input(
                        'Novo semestre', value=selected_turma_obj['semester']
                    )
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.form_submit_button(
                            'Salvar Alterações', width='stretch'
                        ):
                            api_request(
                                'PUT',
                                '/turma/',
                                json={
                                    **selected_turma_obj,
                                    'new_name': new_name,
                                    'new_semester': new_semester,
                                },
                            )
                            st.cache_data.clear()
                            st.rerun()
                    with col2:
                        if st.form_submit_button(
                            'DELETAR', type='primary', width='stretch'
                        ):
                            api_request(
                                'DELETE', '/turma/', json=selected_turma_obj
                            )
                            st.cache_data.clear()
                            st.rerun()

    st.subheader('Lista de Turmas Cadastradas')
    if turmas := get_all_turmas():
        st.dataframe(pd.DataFrame(turmas), use_container_width=True)


def display_config_manager():
    config_data = api_request('GET', '/config/')
    if config_data:
        st.info(
            f"""**Configuração Atual:**
- Semestre Ativo: `{config_data.get('activeSemester', 'N/D')}`
- Início Inscrições: `{config_data.get('enrollmentStartDate', 'N/D')}`
- Fim Inscrições: `{config_data.get('enrollmentEndDate', 'N/D')}`
- Nota de corte: `{config_data.get('cutoffScore', 'N/D')}`"""
        )

    with st.form('config_form'):
        st.subheader('Definir Nova Configuração')
        active_semester = st.selectbox(
            'Selecione o semestre ativo', get_semesters()
        )

        cutoff_note = st.number_input(
            'Nota de corte para aprovação automática (0-10)',
            min_value=0.0,
            max_value=10.0,
            step=0.25,
            value=float(config_data.get('cutoffScore', 6.75))
        )
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input('Data de início', value=config_data.get('enrollmentStartDate', datetime.now().date()))
            end_date = st.date_input('Data de fim', value=config_data.get('enrollmentEndDate',  datetime.now().replace(year=datetime.now().year + 1).date()))
        with col2:
            start_time = st.time_input(
                'Hora de início', value=config_data.get('enrollmentStartDate', datetime.now().time())
            )
            end_time = st.time_input(
                'Hora de fim', value=config_data.get('enrollmentEndDate', datetime.now().replace(hour=datetime.now().hour + 1).time())
            )
        if st.form_submit_button(
            'Salvar Configurações', type='primary', width='stretch'
        ):
            payload = {
                'activeSemester': active_semester,
                'cutoffScore': cutoff_note,
                'enrollmentStartDate': datetime.combine(
                    start_date, start_time
                ).isoformat(),
                'enrollmentEndDate': datetime.combine(
                    end_date, end_time
                ).isoformat(),
            }
            if api_request('POST', '/config/', json=payload) is not None:
                st.success('Configurações salvas!')
                st.rerun()


# --- EXECUÇÃO PRINCIPAL ---
load_css()

st.session_state.setdefault('access_token', None)
st.session_state.setdefault('auth_cookies', None)
st.session_state.setdefault('original_users_df', None)

logo_base64 = load_image_as_base64('logo.png')
if logo_base64:
    st.markdown(
        f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" class="logo-img"></div>',
        unsafe_allow_html=True,
    )

if not st.session_state.access_token:
    display_login_form()
else:
    st.title('Painel Administrativo')

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            '📊 Gerenciar Inscrições',
            '👤 Gerenciar Usuários',
            '📚 Gerenciar Turmas',
            '⚙️ Configurações',
        ]
    )
    with tab1:
        display_enrollment_manager()
    with tab2:
        display_user_manager()
    with tab3:
        display_class_manager()
    with tab4:
        display_config_manager()
