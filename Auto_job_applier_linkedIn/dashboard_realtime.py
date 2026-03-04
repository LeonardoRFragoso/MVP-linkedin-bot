import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
from collections import Counter
import time

st.set_page_config(
    page_title="LinkedIn Job Applications Dashboard",
    page_icon="💼",
    layout="wide"
)

# Session state para controlar auto-refresh
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

BASE_PATH = Path(__file__).parent
APPLIED_CSV = BASE_PATH / "all excels" / "all_applied_applications_history.csv"
FAILED_CSV = BASE_PATH / "all excels" / "all_failed_applications_history.csv"
LOG_FILE = BASE_PATH / "logs" / "log.txt"


def load_applied_data():
    """Carrega dados de candidaturas aplicadas sem cache"""
    try:
        df = pd.read_csv(APPLIED_CSV, encoding='utf-8')
        if 'Date Applied' in df.columns:
            df['Date Applied'] = pd.to_datetime(df['Date Applied'], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()


def load_failed_data():
    """Carrega dados de candidaturas falhadas sem cache"""
    try:
        df = pd.read_csv(FAILED_CSV, encoding='utf-8')
        if 'Date Tried' in df.columns:
            df['Date Tried'] = pd.to_datetime(df['Date Tried'], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()


def get_log_tail(lines=50):
    """Retorna as últimas linhas do log"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
        return ''.join(content[-lines:])
    except Exception as e:
        return f"Erro ao carregar log: {e}"


def load_log_summary():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        easy_applied = re.findall(r'Jobs Easy Applied:\s*(\d+)', content)
        failed = re.findall(r'Failed jobs:\s*(\d+)', content)
        skipped = re.findall(r'Irrelevant jobs skipped:\s*(\d+)', content)
        
        stats = {
            'easy_applied': sum(int(x) for x in easy_applied) if easy_applied else 0,
            'failed': sum(int(x) for x in failed) if failed else 0,
            'skipped': sum(int(x) for x in skipped) if skipped else 0,
        }
        return stats, content
    except Exception as e:
        return {}, ""


# Sidebar com controles
st.sidebar.title("⚙️ Controles")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Atualizar Agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    auto_refresh_enabled = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh_enabled

if st.session_state.auto_refresh:
    st.session_state.refresh_interval = st.sidebar.slider(
        "Intervalo (segundos)", 
        min_value=5, 
        max_value=60, 
        value=st.session_state.refresh_interval,
        step=5
    )
    
    # Verificar se deve atualizar baseado no tempo
    current_time = time.time()
    time_since_refresh = current_time - st.session_state.last_refresh
    
    if time_since_refresh >= st.session_state.refresh_interval:
        st.session_state.last_refresh = current_time
        st.rerun()
    else:
        # Mostrar contador de tempo até próxima atualização
        time_remaining = st.session_state.refresh_interval - time_since_refresh
        placeholder = st.sidebar.empty()
        placeholder.info(f"⏱️ Próxima atualização em {int(time_remaining)}s")
        
        # Usar time.sleep em vez de st.rerun() para evitar loop
        time.sleep(1)
        st.rerun()

# Título
st.title("📊 LinkedIn Job Applications Dashboard")
st.markdown("---")

# Carregar dados (sem cache para sempre ter dados atualizados)
df_applied = load_applied_data()
df_failed = load_failed_data()
log_stats, log_content = load_log_summary()

# Métricas principais
st.header("📈 Visão Geral")
col1, col2, col3, col4 = st.columns(4)

total_applied = len(df_applied) if not df_applied.empty else 0
total_failed = len(df_failed) if not df_failed.empty else 0
unique_applied = df_applied['Job ID'].nunique() if not df_applied.empty and 'Job ID' in df_applied.columns else 0
unique_failed = df_failed['Job ID'].nunique() if not df_failed.empty and 'Job ID' in df_failed.columns else 0

with col1:
    st.metric("✅ Candidaturas Aplicadas", total_applied, f"{unique_applied} únicas")
with col2:
    st.metric("❌ Candidaturas com Falha", total_failed, f"{unique_failed} únicas")
with col3:
    rate = (total_applied / (total_applied + total_failed) * 100) if (total_applied + total_failed) > 0 else 0
    st.metric("📊 Taxa de Sucesso", f"{rate:.1f}%")
with col4:
    st.metric("🔄 Total Tentativas", total_applied + total_failed)

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Aplicadas", "❌ Falhas", "📝 Log em Tempo Real", "📊 Análise"])

with tab1:
    st.subheader("Candidaturas Aplicadas")
    if not df_applied.empty:
        if 'Date Applied' in df_applied.columns:
            df_applied_sorted = df_applied.sort_values('Date Applied', ascending=False)
            df_applied_sorted['Date'] = df_applied_sorted['Date Applied'].dt.date
            daily = df_applied_sorted.groupby('Date').size().reset_index(name='Candidaturas')
            fig = px.bar(daily, x='Date', y='Candidaturas', title='Candidaturas por Dia', color_discrete_sequence=['#28a745'])
            st.plotly_chart(fig, use_container_width=True)
        
        if 'Company' in df_applied.columns:
            top_companies = df_applied['Company'].value_counts().head(10)
            fig2 = px.bar(x=top_companies.values, y=top_companies.index, orientation='h',
                         title='Top 10 Empresas', labels={'x': 'Qtd', 'y': 'Empresa'}, color_discrete_sequence=['#007bff'])
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
        
        cols = ['Title', 'Company', 'Date Applied', 'Job Link']
        avail = [c for c in cols if c in df_applied.columns]
        if avail:
            st.dataframe(df_applied[avail].sort_values('Date Applied', ascending=False) if 'Date Applied' in avail else df_applied[avail], use_container_width=True, height=400)
    else:
        st.warning("Nenhuma candidatura encontrada.")

with tab2:
    st.subheader("Candidaturas com Falha")
    if not df_failed.empty:
        if 'Assumed Reason' in df_failed.columns:
            reasons = df_failed['Assumed Reason'].value_counts()
            fig = px.pie(values=reasons.values, names=reasons.index, title='Motivos de Falha')
            st.plotly_chart(fig, use_container_width=True)
        
        cols = ['Job ID', 'Job Link', 'Date Tried', 'Assumed Reason']
        avail = [c for c in cols if c in df_failed.columns]
        if avail:
            st.dataframe(df_failed[avail].sort_values('Date Tried', ascending=False) if 'Date Tried' in avail else df_failed[avail], use_container_width=True, height=400)
    else:
        st.success("Nenhuma falha registrada!")

with tab3:
    st.subheader("📝 Log em Tempo Real")
    
    # Controles de log
    col1, col2 = st.columns([3, 1])
    with col1:
        log_lines = st.slider("Número de linhas do log", 10, 200, 50)
    with col2:
        if st.button("🔄 Atualizar Log"):
            st.rerun()
    
    # Exibir log
    log_content = get_log_tail(log_lines)
    st.code(log_content, language="text")
    
    # Auto-scroll info
    if st.session_state.auto_refresh:
        st.info("✅ Auto-refresh ativado - Log será atualizado automaticamente")

with tab4:
    st.subheader("📊 Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Vagas Únicas", unique_applied + unique_failed)
        if not df_applied.empty and 'Company' in df_applied.columns:
            st.metric("Empresas Diferentes", df_applied['Company'].nunique())
    
    with col2:
        st.metric("Taxa de Sucesso", f"{rate:.1f}%")
        if not df_applied.empty and 'Date Applied' in df_applied.columns:
            days_active = (df_applied['Date Applied'].max() - df_applied['Date Applied'].min()).days
            st.metric("Dias Ativos", max(1, days_active))
    
    # Estatísticas por hora (se disponível)
    if not df_applied.empty and 'Date Applied' in df_applied.columns:
        df_applied_copy = df_applied.copy()
        df_applied_copy['Hour'] = df_applied_copy['Date Applied'].dt.hour
        hourly = df_applied_copy.groupby('Hour').size().reset_index(name='Candidaturas')
        fig = px.bar(hourly, x='Hour', y='Candidaturas', title='Candidaturas por Hora do Dia')
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption(f"Última atualização: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
