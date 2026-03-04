import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
from collections import Counter
import time

# Configuração da página
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

# Caminhos dos arquivos
BASE_PATH = Path(__file__).parent
APPLIED_CSV = BASE_PATH / "all excels" / "all_applied_applications_history.csv"
FAILED_CSV = BASE_PATH / "all excels" / "all_failed_applications_history.csv"
LOG_FILE = BASE_PATH / "logs" / "log.txt"


@st.cache_data
def load_applied_data():
    try:
        df = pd.read_csv(APPLIED_CSV, encoding='utf-8')
        if 'Date Applied' in df.columns:
            df['Date Applied'] = pd.to_datetime(df['Date Applied'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de candidaturas: {e}")
        return pd.DataFrame()


@st.cache_data
def load_failed_data():
    try:
        df = pd.read_csv(FAILED_CSV, encoding='utf-8')
        if 'Date Tried' in df.columns:
            df['Date Tried'] = pd.to_datetime(df['Date Tried'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de falhas: {e}")
        return pd.DataFrame()


@st.cache_data
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


def parse_questions(questions_str):
    if pd.isna(questions_str) or not questions_str:
        return []
    questions = []
    pattern = r"\('([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'?([^']*)'?\)"
    matches = re.findall(pattern, str(questions_str))
    for match in matches:
        questions.append({
            'pergunta': match[0][:80] + '...' if len(match[0]) > 80 else match[0],
            'resposta': match[1],
            'tipo': match[2],
        })
    return questions


# Título
st.title("📊 LinkedIn Job Applications Dashboard")
st.markdown("---")

# Carregar dados
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Aplicadas", "🔍 Detalhes das Vagas", "❌ Falhas", "❓ Perguntas", "📝 Logs"])

with tab1:
    st.subheader("Candidaturas Aplicadas")
    if not df_applied.empty:
        if 'Date Applied' in df_applied.columns:
            df_applied['Date'] = df_applied['Date Applied'].dt.date
            daily = df_applied.groupby('Date').size().reset_index(name='Candidaturas')
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
    st.subheader("🔍 Detalhes Completos das Vagas Aplicadas")
    if not df_applied.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            companies_list = ['Todas'] + sorted(df_applied['Company'].dropna().unique().tolist()) if 'Company' in df_applied.columns else ['Todas']
            selected_company = st.selectbox("Filtrar por Empresa", companies_list, key="detail_company")
        with col2:
            search_term = st.text_input("🔎 Buscar por título ou descrição", key="search_job")
        
        # Aplicar filtros
        filtered = df_applied.copy()
        if selected_company != 'Todas':
            filtered = filtered[filtered['Company'] == selected_company]
        if search_term:
            mask = filtered.apply(lambda row: search_term.lower() in str(row.get('Title', '')).lower() or 
                                              search_term.lower() in str(row.get('About Job', '')).lower(), axis=1)
            filtered = filtered[mask]
        
        st.info(f"📌 Mostrando {len(filtered)} vagas")
        
        # Exibir cada vaga com detalhes
        for idx, row in filtered.iterrows():
            job_title = row.get('Title', 'Sem título')
            company = row.get('Company', 'Empresa não informada')
            date_applied = row.get('Date Applied', 'N/A')
            
            with st.expander(f"💼 {job_title} - {company}", expanded=False):
                # Info básica
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**🏢 Empresa:** {company}")
                    st.markdown(f"**📍 Local:** {row.get('Work Location', 'Não informado')}")
                with col2:
                    st.markdown(f"**💼 Modalidade:** {row.get('Work Style', 'Não informado')}")
                    st.markdown(f"**📅 Data Aplicação:** {date_applied}")
                with col3:
                    st.markdown(f"**📊 Experiência:** {row.get('Experience required', 'Não informado')}")
                    st.markdown(f"**📄 Currículo:** {row.get('Resume', 'Não informado')}")
                
                st.markdown("---")
                
                # HR Info
                hr_name = row.get('HR Name', 'Unknown')
                hr_link = row.get('HR Link', '')
                if hr_name and hr_name != 'Unknown':
                    st.markdown(f"**👤 Recrutador:** {hr_name}")
                    if hr_link:
                        st.markdown(f"[Ver perfil do recrutador]({hr_link})")
                
                # Descrição completa da vaga
                st.markdown("### 📝 Descrição da Vaga")
                about_job = row.get('About Job', 'Descrição não disponível')
                if about_job and str(about_job) != 'nan':
                    st.text_area("Descrição", about_job, height=300, key=f"about_{idx}", disabled=True, label_visibility="collapsed")
                else:
                    st.warning("Descrição não disponível")
                
                # Skills
                skills = row.get('Skills required', '')
                if skills and str(skills) != 'nan' and skills != 'Needs an AI':
                    st.markdown("### 🛠️ Skills Requeridas")
                    st.write(skills)
                
                # Perguntas respondidas
                questions = row.get('Questions Found', '')
                if questions and str(questions) != 'nan':
                    st.markdown("### ❓ Perguntas Respondidas")
                    parsed_qs = parse_questions(questions)
                    if parsed_qs:
                        for q in parsed_qs:
                            st.markdown(f"- **{q['pergunta']}**")
                            st.markdown(f"  - Resposta: `{q['resposta']}` ({q['tipo']})")
                
                # Link da vaga
                job_link = row.get('Job Link', '')
                if job_link:
                    st.markdown("---")
                    st.markdown(f"🔗 [**Abrir vaga no LinkedIn**]({job_link})")
    else:
        st.warning("Nenhuma candidatura encontrada.")

with tab3:
    st.subheader("Análise de Falhas")
    if not df_failed.empty:
        if 'Assumed Reason' in df_failed.columns:
            reasons = df_failed['Assumed Reason'].value_counts()
            fig = px.pie(values=reasons.values, names=reasons.index, title='Motivos de Falha', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Detalhamento")
            reason_df = pd.DataFrame({'Motivo': reasons.index, 'Quantidade': reasons.values, '%': (reasons.values / reasons.sum() * 100).round(1)})
            st.dataframe(reason_df, use_container_width=True)
        
        # Bad Words
        st.subheader("🚫 Bad Words Detectadas")
        bad_words = []
        if 'Stack Trace' in df_failed.columns:
            for trace in df_failed['Stack Trace'].dropna():
                matches = re.findall(r'Contains bad word "([^"]+)"', str(trace))
                bad_words.extend(matches)
        
        if bad_words:
            bw_counts = Counter(bad_words)
            bw_df = pd.DataFrame({'Bad Word': list(bw_counts.keys()), 'Ocorrências': list(bw_counts.values())}).sort_values('Ocorrências', ascending=False)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(bw_df, use_container_width=True)
            with col2:
                fig3 = px.bar(bw_df, x='Bad Word', y='Ocorrências', title='Bad Words', color_discrete_sequence=['#ffc107'])
                st.plotly_chart(fig3, use_container_width=True)
        
        cols = ['Job ID', 'Assumed Reason', 'Date Tried', 'Job Link']
        avail = [c for c in cols if c in df_failed.columns]
        if avail:
            st.dataframe(df_failed[avail].drop_duplicates(), use_container_width=True, height=400)
    else:
        st.warning("Nenhuma falha encontrada.")

with tab4:
    st.subheader("Perguntas Respondidas")
    if not df_applied.empty and 'Questions Found' in df_applied.columns:
        all_questions = []
        for _, row in df_applied.iterrows():
            qs = parse_questions(row.get('Questions Found', ''))
            for q in qs:
                q['vaga'] = row.get('Title', 'N/A')
                q['empresa'] = row.get('Company', 'N/A')
                all_questions.append(q)
        
        if all_questions:
            qdf = pd.DataFrame(all_questions)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Perguntas", len(qdf))
            with col2:
                st.metric("Perguntas Únicas", qdf['pergunta'].nunique())
            with col3:
                st.metric("Tipos", qdf['tipo'].nunique())
            
            if 'tipo' in qdf.columns:
                types = qdf['tipo'].value_counts()
                fig = px.pie(values=types.values, names=types.index, title='Tipos de Perguntas', hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
            
            top_qs = qdf['pergunta'].value_counts().head(15)
            fig2 = px.bar(x=top_qs.values, y=top_qs.index, orientation='h', title='Top 15 Perguntas', labels={'x': 'Freq', 'y': 'Pergunta'}, color_discrete_sequence=['#17a2b8'])
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
            st.plotly_chart(fig2, use_container_width=True)
            
            st.dataframe(qdf[['pergunta', 'resposta', 'tipo', 'vaga', 'empresa']].drop_duplicates(), use_container_width=True, height=400)
        else:
            st.info("Nenhuma pergunta encontrada.")
    else:
        st.warning("Dados não disponíveis.")

with tab5:
    st.subheader("Resumo dos Logs")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Easy Applied (Log)", log_stats.get('easy_applied', 0))
    with col2:
        st.metric("Failed (Log)", log_stats.get('failed', 0))
    with col3:
        st.metric("Skipped (Log)", log_stats.get('skipped', 0))
    
    st.subheader("Últimas Linhas do Log")
    if log_content:
        last_lines = '\n'.join(log_content.split('\n')[-100:])
        st.text_area("Log", last_lines, height=400)
    else:
        st.warning("Log vazio ou não encontrado.")

st.markdown("---")
st.caption("Dashboard LinkedIn Job Applications - Auto Job Applier")
