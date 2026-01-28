"""
Sistema de Respostas Inteligentes e Variadas para Automação de Candidaturas
Desenvolvido para aumentar taxa de conversão e evitar detecção

Melhorias implementadas:
- Variação de respostas numéricas (±10-20%)
- Validação de idade de tecnologias
- Respostas contextualizadas por nível da vaga
- Sistema anti-detecção com randomização
- Keywords otimizadas para ATS
"""

import random
from datetime import datetime

# =====================================================
# SISTEMA DE VARIAÇÃO DE RESPOSTAS NUMÉRICAS
# =====================================================

def vary_numeric_answer(base_value, variation_percent=15):
    """
    Adiciona variação natural a respostas numéricas
    Evita respostas sempre iguais que parecem robotizadas
    
    Args:
        base_value: Valor base (int ou str)
        variation_percent: Percentual de variação (padrão 15%)
    
    Returns:
        String com valor variado
    """
    try:
        base = int(base_value)
        variation = int(base * variation_percent / 100)
        
        # 70% retorna valor base, 30% adiciona variação
        if random.random() < 0.7:
            return str(base)
        else:
            varied = base + random.randint(-variation, variation)
            return str(max(0, varied))  # Nunca negativo
    except:
        return str(base_value)


def vary_salary(base_salary, contract_type='CLT', job_level='pleno'):
    """
    Varia salário baseado no tipo de contrato e nível da vaga
    
    Args:
        base_salary: Salário base
        contract_type: 'CLT', 'PJ', 'contractor'
        job_level: 'junior', 'pleno', 'senior'
    
    Returns:
        String com salário ajustado
    """
    base = int(base_salary)
    
    # Ajustes por nível
    level_multipliers = {
        'junior': 0.8,
        'júnior': 0.8,
        'jr': 0.8,
        'pleno': 1.0,
        'mid': 1.0,
        'senior': 1.3,
        'sênior': 1.3,
        'sr': 1.3,
        'specialist': 1.4,
        'especialista': 1.4
    }
    
    # Ajustes por tipo de contrato
    contract_multipliers = {
        'CLT': 1.0,
        'PJ': 1.4,  # PJ geralmente 40% maior que CLT
        'contractor': 1.4,
        'pessoa jurídica': 1.4,
        'pessoa juridica': 1.4
    }
    
    level_mult = level_multipliers.get(job_level.lower(), 1.0)
    contract_mult = contract_multipliers.get(contract_type, 1.0)
    
    adjusted = int(base * level_mult * contract_mult)
    
    # Adiciona variação de ±8%
    variation = int(adjusted * 0.08)
    final = adjusted + random.randint(-variation, variation)
    
    # Arredonda para centenas
    final = round(final / 100) * 100
    
    return str(max(1000, final))


# =====================================================
# VALIDAÇÃO DE IDADE DE TECNOLOGIAS
# =====================================================

def validate_tech_age(tech_name, years_claimed):
    """
    Valida se os anos de experiência são realistas baseado na idade da tecnologia
    
    Args:
        tech_name: Nome da tecnologia
        years_claimed: Anos de experiência reivindicados
    
    Returns:
        Anos validados (ajustados se necessário)
    """
    # Idade máxima de tecnologias (ano atual - ano de lançamento)
    current_year = 2026
    tech_release_years = {
        'swift': 2014,
        'swiftui': 2019,
        'kotlin': 2011,
        'rust': 2015,
        'go': 2009,
        'golang': 2009,
        'typescript': 2012,
        'react': 2013,
        'react native': 2015,
        'vue': 2014,
        'angular': 2016,  # Angular 2+
        'docker': 2013,
        'kubernetes': 2014,
        'k8s': 2014,
        'graphql': 2015,
        'mongodb': 2009,
        'redis': 2009,
        'node.js': 2009,
        'nodejs': 2009,
        'fastapi': 2018,
        'next.js': 2016,
        'nextjs': 2016,
    }
    
    tech_lower = tech_name.lower()
    years = int(years_claimed)
    
    # Procura por match parcial
    for tech, release_year in tech_release_years.items():
        if tech in tech_lower:
            max_age = current_year - release_year
            if years > max_age:
                # Ajusta para 70% da idade máxima (mais realista)
                adjusted = int(max_age * 0.7)
                print(f"⚠️ Ajustado {tech_name}: {years} → {adjusted} anos (tech max: {max_age})")
                return str(adjusted)
    
    return str(years)


# =====================================================
# SISTEMA DE RESPOSTAS CONTEXTUALIZADAS
# =====================================================

def get_contextual_yes_no(question_text, confidence='high'):
    """
    Retorna Yes/No contextualizado baseado na confiança
    Adiciona variação para não parecer robô
    
    Args:
        question_text: Texto da pergunta
        confidence: 'high', 'medium', 'low'
    
    Returns:
        'Yes' ou 'No' baseado em probabilidade
    """
    # Keywords que indicam pergunta técnica importante
    important_keywords = [
        'requirement', 'required', 'obrigatório', 'mandatory',
        'must have', 'essential', 'critical', 'necessary'
    ]
    
    is_important = any(kw in question_text.lower() for kw in important_keywords)
    
    if confidence == 'high' or is_important:
        # 95% Yes, 5% No (variação para parecer humano)
        return 'Yes' if random.random() < 0.95 else 'No'
    elif confidence == 'medium':
        # 80% Yes, 20% No
        return 'Yes' if random.random() < 0.80 else 'No'
    else:  # low
        # 60% Yes, 40% No
        return 'Yes' if random.random() < 0.60 else 'No'


def generate_motivation_text(job_title='', company_name='', variation=1):
    """
    Gera texto de motivação variado para perguntas de "Por que você?"
    
    Args:
        job_title: Título da vaga
        company_name: Nome da empresa
        variation: Número da variação (1-5)
    
    Returns:
        Texto de motivação personalizado
    """
    variations = [
        f"Tenho grande interesse em fazer parte da equipe e contribuir com minhas habilidades em desenvolvimento Full Stack, especialmente Python e React.",
        
        f"Minha experiência com automações e APIs RESTful se alinha perfeitamente aos desafios desta posição. Estou entusiasmado para aplicar meus conhecimentos técnicos.",
        
        f"Como desenvolvedor Full Stack com foco em soluções escaláveis, vejo esta oportunidade como ideal para crescimento mútuo. Minha expertise em Python, Django e React pode agregar valor imediato.",
        
        f"Tenho sólida experiência em desenvolvimento web e automações, áreas que considero estratégicas para inovação. Busco desafios que permitam aplicar boas práticas e metodologias ágeis.",
        
        f"Minha trajetória em desenvolvimento Full Stack, combinando gestão de TI com expertise técnica, me preparou para contribuir efetivamente. Valorizo ambientes colaborativos e orientados a resultados."
    ]
    
    return variations[variation % len(variations)]


def add_ats_keywords(base_text):
    """
    Adiciona keywords otimizadas para ATS (Applicant Tracking Systems)
    
    Args:
        base_text: Texto base
    
    Returns:
        Texto com keywords adicionadas
    """
    keyword_pool = [
        'proativo', 'autodidata', 'team player',
        'problem solving', 'analytical thinking',
        'continuous improvement', 'melhoria contínua',
        'attention to detail', 'atenção aos detalhes',
        'agile methodologies', 'metodologias ágeis',
        'collaborative', 'colaborativo'
    ]
    
    # Adiciona 2-3 keywords aleatórias
    num_keywords = random.randint(2, 3)
    selected = random.sample(keyword_pool, num_keywords)
    
    enhanced = f"{base_text} Destaco características como: {', '.join(selected)}."
    return enhanced


# =====================================================
# SISTEMA ANTI-DETECÇÃO
# =====================================================

def get_humanized_delay():
    """
    Retorna delay variável para simular comportamento humano
    
    Returns:
        Float com segundos de delay
    """
    # Delay entre 0.8 e 2.5 segundos
    return round(random.uniform(0.8, 2.5), 2)


def should_make_typo():
    """
    Decide se deve simular um "typo" e correção (comportamento humano)
    
    Returns:
        Boolean
    """
    # 5% de chance de simular typo e correção
    return random.random() < 0.05


# =====================================================
# FUNÇÕES DE DETECÇÃO DE CONTEXTO
# =====================================================

def detect_job_level(job_title='', job_description=''):
    """
    Detecta nível da vaga (júnior/pleno/sênior) baseado no título e descrição
    
    Args:
        job_title: Título da vaga
        job_description: Descrição da vaga
    
    Returns:
        'junior', 'pleno' ou 'senior'
    """
    combined = (job_title + ' ' + job_description).lower()
    
    # Ordem importa: verificar sênior primeiro, depois pleno, depois júnior
    if any(word in combined for word in ['senior', 'sênior', 'sr ', 'sr.', 'specialist', 'especialista', 'tech lead', 'architect']):
        return 'senior'
    elif any(word in combined for word in ['pleno', 'mid-level', 'mid level', 'midlevel', 'intermediário', 'intermediate']):
        return 'pleno'
    elif any(word in combined for word in ['junior', 'júnior', 'jr ', 'jr.', 'trainee', 'estagiário', 'entry level', 'entry-level']):
        return 'junior'
    else:
        # Default para pleno se não detectar
        return 'pleno'


def detect_location_match(job_location='', user_city='Rio de Janeiro'):
    """
    Detecta se a localização da vaga é próxima do usuário
    
    Args:
        job_location: Localização da vaga
        user_city: Cidade do usuário
    
    Returns:
        Boolean indicando match
    """
    if not job_location:
        return True  # Se não especificado, assume remoto
    
    location_lower = job_location.lower()
    
    # Check por remoto
    if any(word in location_lower for word in ['remote', 'remoto', 'home office', 'anywhere']):
        return True
    
    # Check por cidade do usuário
    if user_city.lower() in location_lower:
        return True
    
    # Cidades próximas ao Rio de Janeiro
    nearby_cities = ['rio de janeiro', 'niterói', 'são gonçalo', 'duque de caxias']
    if any(city in location_lower for city in nearby_cities):
        return True
    
    return False


# =====================================================
# FUNÇÃO PRINCIPAL DE RESPOSTA INTELIGENTE
# =====================================================

def get_intelligent_answer(question_label, question_type, base_answer, 
                          job_title='', job_description='', job_location=''):
    """
    Retorna resposta inteligente e contextualizada
    
    Args:
        question_label: Texto da pergunta
        question_type: Tipo (text, select, radio, textarea)
        base_answer: Resposta base configurada
        job_title: Título da vaga (opcional)
        job_description: Descrição da vaga (opcional)
        job_location: Localização da vaga (opcional)
    
    Returns:
        Resposta otimizada
    """
    label_lower = question_label.lower()
    
    # Detectar contexto da vaga
    job_level = detect_job_level(job_title, job_description)
    is_location_match = detect_location_match(job_location)
    
    # 1. PERGUNTAS DE EXPERIÊNCIA (anos)
    if any(exp in label_lower for exp in ['anos de experiência', 'years of experience', 
                                            'há quantos anos', 'how many years',
                                            'quanto tempo', 'how long']):
        
        # Validar idade da tecnologia se for pergunta específica
        if any(tech in label_lower for tech in ['swift', 'kotlin', 'rust', 'go', 'golang', 
                                                  'react native', 'vue', 'angular']):
            base_answer = validate_tech_age(question_label, base_answer)
        
        # Adicionar variação
        return vary_numeric_answer(base_answer, variation_percent=10)
    
    # 2. PERGUNTAS DE SALÁRIO
    elif any(sal in label_lower for sal in ['pretensão salarial', 'salary expectation',
                                             'salário', 'remuneração', 'salary', 'compensation']):
        
        # Detectar tipo de contrato
        contract_type = 'CLT'
        if any(pj in label_lower for pj in ['pj', 'pessoa jurídica', 'contractor', 'freelance']):
            contract_type = 'PJ'
        
        return vary_salary(base_answer, contract_type, job_level)
    
    # 3. PERGUNTAS DE LOCALIZAÇÃO/PRESENCIAL
    elif any(loc in label_lower for loc in ['presencial', 'on-site', 'híbrido', 'hybrid',
                                             'localização', 'location']):
        
        if is_location_match:
            return 'Sim' if question_type == 'text' else 'Yes'
        else:
            # Preferir remoto se não for localização próxima
            return 'Remoto preferível' if question_type == 'text' else 'No'
    
    # 4. PERGUNTAS YES/NO TÉCNICAS
    elif question_type in ['select', 'radio'] and any(opt in str(base_answer).lower() for opt in ['yes', 'no']):
        
        # Detectar nível de confiança baseado na pergunta
        confidence = 'high'
        if any(word in label_lower for word in ['avançado', 'advanced', 'expert', 'proficient']):
            confidence = 'medium'  # Ser mais conservador com "avançado"
        elif any(word in label_lower for word in ['basic', 'básico', 'algum', 'some']):
            confidence = 'high'
        
        return get_contextual_yes_no(question_label, confidence)
    
    # 5. PERGUNTAS DE MOTIVAÇÃO (textarea)
    elif question_type in ['textarea', 'textarea-generic-fallback']:
        
        variation = random.randint(1, 5)
        base_text = generate_motivation_text(job_title, '', variation)
        
        # Adicionar keywords ATS
        if random.random() < 0.7:  # 70% das vezes adiciona keywords
            base_text = add_ats_keywords(base_text)
        
        return base_text
    
    # 6. RESPOSTA PADRÃO (com variação se numérica)
    else:
        if question_type == 'text' and str(base_answer).isdigit():
            return vary_numeric_answer(base_answer, variation_percent=15)
        else:
            return base_answer


# =====================================================
# ESTATÍSTICAS E LOGGING
# =====================================================

def log_answer_stats(question, answer, job_id):
    """
    Loga estatísticas de respostas para análise futura
    
    Args:
        question: Pergunta respondida
        answer: Resposta dada
        job_id: ID da vaga
    """
    # TODO: Implementar logging em arquivo CSV para análise
    pass


# =====================================================
# EXPORTAÇÕES
# =====================================================

__all__ = [
    'vary_numeric_answer',
    'vary_salary',
    'validate_tech_age',
    'get_contextual_yes_no',
    'generate_motivation_text',
    'add_ats_keywords',
    'get_humanized_delay',
    'detect_job_level',
    'detect_location_match',
    'get_intelligent_answer',
]
