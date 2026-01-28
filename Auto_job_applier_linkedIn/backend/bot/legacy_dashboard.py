import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import re
from collections import Counter
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="LinkedIn Job Applications Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


def extract_keywords_from_titles(df):
    """Extrai palavras-chave mais comuns dos títulos de vagas"""
    if df.empty or 'Title' not in df.columns:
        return Counter()
    
    # Palavras a ignorar
    stop_words = {'de', 'da', 'do', 'para', 'em', 'e', 'a', 'o', 'que', 'na', 'no', 'se', 'os', 'as', 'dos', 'das',
                  'um', 'uma', 'the', 'and', 'or', 'in', 'at', 'to', 'for', 'of', 'on', 'with', 'is', 'are', 'was', 'were'}
    
    all_words = []
    for title in df['Title'].dropna():
        words = re.findall(r'\b\w+\b', str(title).lower())
        all_words.extend([w for w in words if len(w) > 2 and w not in stop_words])
    
    return Counter(all_words)


def calculate_time_metrics(df):
    """Calcula métricas de tempo entre candidaturas"""
    if df.empty or 'Date Applied' not in df.columns:
        return {}
    
    df_sorted = df.sort_values('Date Applied')
    dates = pd.to_datetime(df_sorted['Date Applied'], errors='coerce').dropna()
    
    if len(dates) < 2:
        return {}
    
    time_diffs = dates.diff().dropna()
    
    return {
        'avg_time_between': time_diffs.mean(),
        'min_time_between': time_diffs.min(),
        'max_time_between': time_diffs.max(),
        'total_days': (dates.max() - dates.min()).days
    }


def get_hourly_distribution(df):
    """Analisa distribuição de candidaturas por hora do dia"""
    if df.empty or 'Date Applied' not in df.columns:
        return pd.DataFrame()
    
    df['hour'] = pd.to_datetime(df['Date Applied'], errors='coerce').dt.hour
    return df['hour'].value_counts().sort_index()


def normalize_work_style(work_style_value):
    """Normaliza e valida valores de modalidade de trabalho"""
    if pd.isna(work_style_value) or not work_style_value:
        return None
    
    value = str(work_style_value).lower().strip()
    
    # Remoto / Remote
    if any(word in value for word in ['remoto', 'remote', 'remotely']):
        return '🏠 Remoto'
    
    # Híbrido / Hybrid
    if any(word in value for word in ['híbrido', 'hibrido', 'hybrid']):
        return '🔀 Híbrido'
    
    # Presencial / On-site
    if any(word in value for word in ['presencial', 'on-site', 'onsite', 'office', 'escritório']):
        return '🏢 Presencial'
    
    # Se não reconhecer e for muito longo (provavelmente é nome de empresa/localização incorreto)
    if len(value) > 20:
        return None
    
    return None


def get_valid_work_styles(df):
    """Extrai e normaliza modalidades de trabalho válidas"""
    if df.empty or 'Work Style' not in df.columns:
        return pd.Series(dtype='object')
    
    # Aplicar normalização
    normalized = df['Work Style'].apply(normalize_work_style)
    
    # Filtrar apenas valores válidos (não None)
    return normalized.dropna()


# Título
st.title("📊 LinkedIn Job Applications Dashboard")
st.markdown("---")

# Carregar dados
df_applied = load_applied_data()
df_failed = load_failed_data()
log_stats, log_content = load_log_summary()

# Calcular métricas de tempo
time_metrics = calculate_time_metrics(df_applied)

# Sidebar com filtros
with st.sidebar:
    st.header("🔍 Filtros Globais")
    
    # Filtro de data
    if not df_applied.empty and 'Date Applied' in df_applied.columns:
        min_date = pd.to_datetime(df_applied['Date Applied']).min().date()
        max_date = pd.to_datetime(df_applied['Date Applied']).max().date()
        
        date_range = st.date_input(
            "Período de Análise",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_filter"
        )
        
        # Aplicar filtro de data
        if len(date_range) == 2:
            mask = (pd.to_datetime(df_applied['Date Applied']).dt.date >= date_range[0]) & \
                   (pd.to_datetime(df_applied['Date Applied']).dt.date <= date_range[1])
            df_applied_filtered = df_applied[mask]
        else:
            df_applied_filtered = df_applied
    else:
        df_applied_filtered = df_applied
    
    st.markdown("---")
    
    # Botão para exportar dados
    st.header("📥 Exportar Dados")
    if st.button("💾 Baixar CSV de Candidaturas"):
        if not df_applied.empty:
            csv = df_applied.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"candidaturas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

# Métricas principais
st.header("📈 Visão Geral")
col1, col2, col3, col4, col5 = st.columns(5)

total_applied = len(df_applied_filtered) if not df_applied_filtered.empty else 0
total_failed = len(df_failed) if not df_failed.empty else 0
unique_applied = df_applied_filtered['Job ID'].nunique() if not df_applied_filtered.empty and 'Job ID' in df_applied_filtered.columns else 0
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
with col5:
    if time_metrics and 'total_days' in time_metrics:
        avg_per_day = total_applied / max(time_metrics['total_days'], 1)
        st.metric("📅 Média/Dia", f"{avg_per_day:.1f}")
    else:
        st.metric("📅 Média/Dia", "N/A")

# Métricas de tempo
if time_metrics:
    st.markdown("### ⏱️ Métricas de Tempo")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'avg_time_between' in time_metrics:
            avg_minutes = time_metrics['avg_time_between'].total_seconds() / 60
            st.metric("⏰ Tempo Médio Entre Candidaturas", f"{avg_minutes:.1f} min")
    
    with col2:
        if 'min_time_between' in time_metrics:
            min_minutes = time_metrics['min_time_between'].total_seconds() / 60
            st.metric("⚡ Menor Intervalo", f"{min_minutes:.1f} min")
    
    with col3:
        if 'max_time_between' in time_metrics:
            max_minutes = time_metrics['max_time_between'].total_seconds() / 60
            if max_minutes > 60:
                st.metric("🐌 Maior Intervalo", f"{max_minutes/60:.1f} hrs")
            else:
                st.metric("🐌 Maior Intervalo", f"{max_minutes:.1f} min")
    
    with col4:
        if 'total_days' in time_metrics and time_metrics['total_days'] > 0:
            st.metric("📆 Período Total", f"{time_metrics['total_days']} dias")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 Aplicadas", 
    "🔍 Detalhes das Vagas", 
    "📊 Análises Avançadas",
    "🌍 Localização & Modalidade",
    "❌ Falhas", 
    "❓ Perguntas", 
    "📈 Tendências",
    "📝 Logs"
])

with tab1:
    st.subheader("Candidaturas Aplicadas")
    if not df_applied_filtered.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Date Applied' in df_applied_filtered.columns:
                df_temp = df_applied_filtered.copy()
                df_temp['Date'] = pd.to_datetime(df_temp['Date Applied']).dt.date
                daily = df_temp.groupby('Date').size().reset_index(name='Candidaturas')
                fig = px.bar(daily, x='Date', y='Candidaturas', title='📅 Candidaturas por Dia', 
                           color_discrete_sequence=['#28a745'])
                fig.update_layout(xaxis_title="Data", yaxis_title="Quantidade")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'Company' in df_applied_filtered.columns:
                top_companies = df_applied_filtered['Company'].value_counts().head(10)
                fig2 = px.bar(x=top_companies.values, y=top_companies.index, orientation='h',
                             title='🏢 Top 10 Empresas', labels={'x': 'Qtd', 'y': 'Empresa'}, 
                             color_discrete_sequence=['#007bff'])
                fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig2, use_container_width=True)
        
        # Resumo adicional
        st.markdown("### 📊 Resumo Rápido")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'Company' in df_applied_filtered.columns:
                unique_companies = df_applied_filtered['Company'].nunique()
                st.metric("🏢 Empresas Únicas", unique_companies)
        
        with col2:
            if 'Work Style' in df_applied_filtered.columns:
                remote_count = df_applied_filtered[df_applied_filtered['Work Style'].str.contains('Remote|remoto', case=False, na=False)].shape[0]
                st.metric("🏠 Vagas Remotas", remote_count)
        
        with col3:
            if 'Re-posted' in df_applied_filtered.columns:
                reposted = df_applied_filtered['Re-posted'].sum() if df_applied_filtered['Re-posted'].dtype == 'bool' else 0
                st.metric("🔄 Vagas Repostadas", reposted)
        
        with col4:
            if 'Questions Found' in df_applied_filtered.columns:
                with_questions = df_applied_filtered['Questions Found'].notna().sum()
                st.metric("❓ Com Perguntas", with_questions)
        
        # Tabela de candidaturas
        st.markdown("### 📋 Lista de Candidaturas")
        cols = ['Title', 'Company', 'Work Location', 'Work Style', 'Date Applied', 'Job Link']
        avail = [c for c in cols if c in df_applied_filtered.columns]
        if avail:
            display_df = df_applied_filtered[avail].copy()
            if 'Date Applied' in display_df.columns:
                display_df = display_df.sort_values('Date Applied', ascending=False)
            st.dataframe(display_df, use_container_width=True, height=400)
    else:
        st.warning("Nenhuma candidatura encontrada no período selecionado.")

with tab2:
    st.subheader("🔍 Detalhes Completos das Vagas Aplicadas")
    if not df_applied_filtered.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            companies_list = ['Todas'] + sorted(df_applied_filtered['Company'].dropna().unique().tolist()) if 'Company' in df_applied_filtered.columns else ['Todas']
            selected_company = st.selectbox("Filtrar por Empresa", companies_list, key="detail_company")
        with col2:
            search_term = st.text_input("🔎 Buscar por título ou descrição", key="search_job")
        
        # Aplicar filtros
        filtered = df_applied_filtered.copy()
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
    st.subheader("📊 Análises Avançadas")
    if not df_applied_filtered.empty:
        
        # Análise de Palavras-Chave nos Títulos
        st.markdown("### 🔤 Palavras-Chave Mais Comuns nos Títulos")
        keywords = extract_keywords_from_titles(df_applied_filtered)
        if keywords:
            top_keywords = dict(keywords.most_common(20))
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_keywords = px.bar(
                    x=list(top_keywords.values()),
                    y=list(top_keywords.keys()),
                    orientation='h',
                    title='Top 20 Palavras-Chave',
                    labels={'x': 'Frequência', 'y': 'Palavra'},
                    color_discrete_sequence=['#8e44ad']
                )
                fig_keywords.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                st.plotly_chart(fig_keywords, use_container_width=True)
            
            with col2:
                st.markdown("#### 📋 Top 10")
                for i, (word, count) in enumerate(keywords.most_common(10), 1):
                    st.markdown(f"{i}. **{word}** ({count}x)")
        
        st.markdown("---")
        
        # Análise de Experiência Requerida
        if 'Experience required' in df_applied_filtered.columns:
            st.markdown("### 🎓 Análise de Experiência Requerida")
            
            exp_data = df_applied_filtered['Experience required'].dropna()
            exp_data = exp_data[exp_data != 'Unknown']
            
            if len(exp_data) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    exp_counts = exp_data.value_counts()
                    fig_exp = px.pie(
                        values=exp_counts.values,
                        names=exp_counts.index,
                        title='Distribuição de Experiência',
                        hole=0.4
                    )
                    st.plotly_chart(fig_exp, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📊 Estatísticas")
                    st.metric("Total Vagas com Info", len(exp_data))
                    
                    # Tentar converter para numérico
                    try:
                        exp_numeric = pd.to_numeric(exp_data, errors='coerce').dropna()
                        if len(exp_numeric) > 0:
                            st.metric("Média de Anos", f"{exp_numeric.mean():.1f}")
                            st.metric("Mediana", f"{exp_numeric.median():.1f}")
                            st.metric("Máximo", f"{int(exp_numeric.max())}")
                    except:
                        pass
        
        st.markdown("---")
        
        # Análise de Currículo Usado
        if 'Resume' in df_applied_filtered.columns:
            st.markdown("### 📄 Currículos Utilizados")
            resume_counts = df_applied_filtered['Resume'].value_counts()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_resume = px.pie(
                    values=resume_counts.values,
                    names=resume_counts.index,
                    title='Distribuição de Currículos',
                    hole=0.3
                )
                st.plotly_chart(fig_resume, use_container_width=True)
            
            with col2:
                st.markdown("#### 📋 Detalhes")
                for resume, count in resume_counts.items():
                    percentage = (count / len(df_applied_filtered)) * 100
                    st.markdown(f"**{resume}**: {count} ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Análise de HR/Recrutadores
        if 'HR Name' in df_applied_filtered.columns:
            st.markdown("### 👤 Recrutadores")
            hr_data = df_applied_filtered[df_applied_filtered['HR Name'] != 'Unknown']['HR Name'].dropna()
            
            if len(hr_data) > 0:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    hr_counts = hr_data.value_counts().head(15)
                    fig_hr = px.bar(
                        x=hr_counts.values,
                        y=hr_counts.index,
                        orientation='h',
                        title='Top 15 Recrutadores',
                        labels={'x': 'Vagas', 'y': 'Recrutador'},
                        color_discrete_sequence=['#e74c3c']
                    )
                    fig_hr.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig_hr, use_container_width=True)
                
                with col2:
                    st.metric("Total com Info", len(hr_data))
                    st.metric("Recrutadores Únicos", hr_data.nunique())
                    most_common_hr = hr_data.value_counts().iloc[0]
                    st.metric("Mais Frequente", most_common_hr)
    else:
        st.warning("Nenhum dado disponível para análise.")

with tab4:
    st.subheader("🌍 Análise de Localização e Modalidade de Trabalho")
    if not df_applied_filtered.empty:
        
        # Análise de Localização
        if 'Work Location' in df_applied_filtered.columns:
            st.markdown("### 📍 Localizações")
            location_data = df_applied_filtered['Work Location'].dropna()
            location_data = location_data[location_data != 'Não informado']
            
            if len(location_data) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    location_counts = location_data.value_counts().head(15)
                    fig_location = px.bar(
                        x=location_counts.values,
                        y=location_counts.index,
                        orientation='h',
                        title='Top 15 Localizações',
                        labels={'x': 'Quantidade', 'y': 'Localização'},
                        color_discrete_sequence=['#3498db']
                    )
                    fig_location.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig_location, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📊 Resumo")
                    st.metric("Localizações Únicas", location_data.nunique())
                    st.metric("Total com Info", len(location_data))
                    
                    st.markdown("#### 🏆 Top 3")
                    for i, (loc, count) in enumerate(location_counts.head(3).items(), 1):
                        st.markdown(f"{i}. **{loc}** ({count})")
        
        st.markdown("---")
        
        # Análise de Modalidade (Work Style)
        if 'Work Style' in df_applied_filtered.columns:
            st.markdown("### 💼 Modalidade de Trabalho")
            
            # Usar função de normalização
            work_style_data = get_valid_work_styles(df_applied_filtered)
            
            if len(work_style_data) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    style_counts = work_style_data.value_counts()
                    fig_style = px.pie(
                        values=style_counts.values,
                        names=style_counts.index,
                        title='Distribuição de Modalidades',
                        hole=0.4,
                        color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c']
                    )
                    st.plotly_chart(fig_style, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📋 Detalhamento")
                    for style, count in style_counts.items():
                        percentage = (count / len(work_style_data)) * 100
                        st.markdown(f"**{style}**: {count} vagas ({percentage:.1f}%)")
                    
                    st.markdown("---")
                    st.metric("Total com Info Válida", len(work_style_data))
                    
                    # Mostrar quantas foram filtradas
                    total_rows = len(df_applied_filtered)
                    invalid_count = total_rows - len(work_style_data)
                    if invalid_count > 0:
                        st.caption(f"⚠️ {invalid_count} registros com dados inválidos foram filtrados")
            else:
                st.warning("⚠️ Nenhuma modalidade válida encontrada nos dados. O bot pode estar extraindo incorretamente as informações de modalidade de trabalho.")
        
        st.markdown("---")
        
        # Cruzamento Localização x Modalidade
        if 'Work Location' in df_applied_filtered.columns and 'Work Style' in df_applied_filtered.columns:
            st.markdown("### 🔀 Cruzamento: Localização × Modalidade")
            
            df_cross = df_applied_filtered[['Work Location', 'Work Style']].dropna()
            if len(df_cross) > 0:
                # Top 10 localizações
                top_locations = df_cross['Work Location'].value_counts().head(10).index
                df_cross_filtered = df_cross[df_cross['Work Location'].isin(top_locations)]
                
                cross_tab = pd.crosstab(df_cross_filtered['Work Location'], df_cross_filtered['Work Style'])
                
                fig_heatmap = px.imshow(
                    cross_tab,
                    labels=dict(x="Modalidade", y="Localização", color="Quantidade"),
                    title="Top 10 Localizações × Modalidade",
                    aspect="auto",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para análise.")

with tab5:
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

with tab6:
    st.subheader("❓ Perguntas Respondidas")
    if not df_applied_filtered.empty and 'Questions Found' in df_applied_filtered.columns:
        all_questions = []
        for _, row in df_applied_filtered.iterrows():
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

with tab7:
    st.subheader("📈 Análise de Tendências Temporais")
    if not df_applied_filtered.empty and 'Date Applied' in df_applied_filtered.columns:
        
        # Preparar dados temporais
        df_temp = df_applied_filtered.copy()
        df_temp['Date Applied'] = pd.to_datetime(df_temp['Date Applied'])
        df_temp['Date'] = df_temp['Date Applied'].dt.date
        df_temp['Hour'] = df_temp['Date Applied'].dt.hour
        df_temp['Day of Week'] = df_temp['Date Applied'].dt.day_name()
        df_temp['Week'] = df_temp['Date Applied'].dt.isocalendar().week
        
        # Candidaturas por dia da semana
        st.markdown("### 📅 Distribuição por Dia da Semana")
        col1, col2 = st.columns(2)
        
        with col1:
            # Ordenar dias da semana
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_pt = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 
                     'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
            
            day_counts = df_temp['Day of Week'].value_counts()
            day_counts_ordered = pd.Series({day_pt[day]: day_counts.get(day, 0) for day in day_order if day in day_counts.index})
            
            fig_days = px.bar(
                x=day_counts_ordered.values,
                y=day_counts_ordered.index,
                orientation='h',
                title='Candidaturas por Dia da Semana',
                labels={'x': 'Quantidade', 'y': 'Dia'},
                color=day_counts_ordered.values,
                color_continuous_scale='Viridis'
            )
            fig_days.update_layout(showlegend=False)
            st.plotly_chart(fig_days, use_container_width=True)
        
        with col2:
            # Distribuição por hora do dia
            hour_counts = df_temp['Hour'].value_counts().sort_index()
            
            fig_hours = px.bar(
                x=hour_counts.index,
                y=hour_counts.values,
                title='Candidaturas por Hora do Dia',
                labels={'x': 'Hora', 'y': 'Quantidade'},
                color=hour_counts.values,
                color_continuous_scale='Blues'
            )
            fig_hours.update_layout(showlegend=False)
            st.plotly_chart(fig_hours, use_container_width=True)
        
        st.markdown("---")
        
        # Tendência ao longo do tempo
        st.markdown("### 📊 Tendência Temporal")
        
        daily = df_temp.groupby('Date').size().reset_index(name='Candidaturas')
        daily['Date'] = pd.to_datetime(daily['Date'])
        daily['Média Móvel (7 dias)'] = daily['Candidaturas'].rolling(window=7, min_periods=1).mean()
        
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Bar(
            x=daily['Date'],
            y=daily['Candidaturas'],
            name='Candidaturas',
            marker_color='lightblue',
            opacity=0.6
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=daily['Date'],
            y=daily['Média Móvel (7 dias)'],
            name='Média Móvel (7 dias)',
            line=dict(color='red', width=3)
        ))
        
        fig_trend.update_layout(
            title='Tendência de Candidaturas ao Longo do Tempo',
            xaxis_title='Data',
            yaxis_title='Quantidade',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        st.markdown("---")
        
        # Estatísticas de produtividade
        st.markdown("### ⚡ Estatísticas de Produtividade")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_day = day_counts.idxmax()
            best_day_count = day_counts.max()
            st.metric("🏆 Melhor Dia da Semana", day_pt.get(best_day, best_day), f"{best_day_count} candidaturas")
        
        with col2:
            best_hour = hour_counts.idxmax()
            best_hour_count = hour_counts.max()
            st.metric("⏰ Hora Mais Produtiva", f"{best_hour}:00h", f"{best_hour_count} candidaturas")
        
        with col3:
            avg_daily = daily['Candidaturas'].mean()
            st.metric("📊 Média Diária", f"{avg_daily:.1f}")
        
        with col4:
            max_daily = daily['Candidaturas'].max()
            max_date = daily[daily['Candidaturas'] == max_daily]['Date'].iloc[0].strftime('%d/%m/%Y')
            st.metric("🚀 Recorde Diário", f"{max_daily}", f"em {max_date}")
        
        st.markdown("---")
        
        # Heatmap de atividade (Dia da Semana x Hora)
        st.markdown("### 🔥 Mapa de Calor de Atividade")
        
        heatmap_data = df_temp.groupby(['Day of Week', 'Hour']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='Day of Week', columns='Hour', values='count').fillna(0)
        
        # Reordenar dias da semana
        heatmap_pivot = heatmap_pivot.reindex([day for day in day_order if day in heatmap_pivot.index])
        heatmap_pivot.index = [day_pt.get(day, day) for day in heatmap_pivot.index]
        
        fig_heatmap = px.imshow(
            heatmap_pivot,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Candidaturas"),
            title="Atividade por Dia da Semana e Hora",
            aspect="auto",
            color_continuous_scale="YlOrRd"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
    else:
        st.warning("Nenhum dado temporal disponível.")

with tab8:
    st.subheader("📝 Resumo dos Logs")
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
