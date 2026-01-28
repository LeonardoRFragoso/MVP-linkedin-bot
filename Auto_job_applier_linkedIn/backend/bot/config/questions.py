'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    24.12.29.12.30
'''


###################################################### APPLICATION INPUTS ######################################################


# >>>>>>>>>>> Easy Apply Questions & Inputs <<<<<<<<<<<

# Give an relative path of your default resume to be uploaded. If file in not found, will continue using your previously uploaded resume in LinkedIn.
default_resume_path = r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV - Leonardo Fragoso _ Desenvolvedor Full Stack.pdf"      # (In Development)

# NOVO: CVs específicos para vagas nacionais e internacionais
# O bot seleciona automaticamente baseado na localização da vaga
resume_national = r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV Leonardo Fragoso - Desenvolvedor de Sistemas.pdf"  # CV em Português para vagas no Brasil
resume_international = r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV - Leonardo Fragoso _ Desenvolvedor Full Stack.pdf"  # CV em Inglês para vagas internacionais

# What do you want to answer for questions that ask about years of experience you have, this is different from current_experience? 
years_of_experience = "5"          # A number em quotes Eg: "0","1","2","3","4", etc. (aumentado para ser mais competitivo)
python_experience_years = "5"      # Python - sua principal tecnologia
legal_experience_years = "1"       # Legal/Jurídico - experiência limitada
ci_cd_experience_years = "3"       # CI/CD
it_experience_years = "7"          # TI em geral
java_experience_years = "5"        # CRÍTICO: Java experience - NUNCA usar "0" pois desqualifica imediatamente
nodejs_experience_years = "5"      # Node.js experience
reactjs_experience_years = "5"     # React.js experience
angular_experience_years = "3"     # Angular experience
vue_experience_years = "2"         # Vue.js experience

# NOVO: Mapeamento detalhado de experiência por tecnologia
# Permite respostas mais realistas e personalizadas baseadas em suas skills reais
experience_by_technology = {
    # Backend (suas fortes)
    'python': '5',
    'django': '5',
    'flask': '4',
    'fastapi': '3',
    
    # Frontend
    'javascript': '5',
    'javascript (es6+)': '5',
    'es6': '5',
    'typescript': '3',
    'react': '5',
    'reactjs': '5',
    'react.js': '5',
    'next.js': '3',
    'nextjs': '3',
    'node': '5',
    'nodejs': '5',
    'node.js': '5',
    'html': '5',
    'html5': '5',
    'css': '5',
    'scss': '3',
    'sass': '3',
    'tailwind': '3',
    'frontend': '5',
    'front-end': '5',
    
    # Databases
    'sql': '5',
    'postgresql': '5',
    'mysql': '4',
    'mongodb': '3',
    'firebase': '3',
    'redis': '2',
    
    # DevOps & Cloud
    'docker': '3',
    'git': '6',
    'github': '6',
    'aws': '3',
    'amazon web services': '3',
    'azure': '3',
    'microsoft azure': '3',
    'gcp': '2',
    'google cloud': '2',
    'kubernetes': '2',
    'k8s': '2',
    'terraform': '2',
    'ansible': '2',
    'ci/cd': '3',
    
    # Automação & Testing
    'selenium': '4',
    'puppeteer': '3',
    'pytest': '4',
    'jest': '3',
    
    # APIs & Integração
    'rest': '5',
    'restful': '5',
    'api': '5',
    'api integration': '5',
    'integração de api': '5',
    'graphql': '2',
    
    # Version Control
    'version control': '6',
    'controle de versão': '6',
    
    # Metodologias
    'agile': '5',
    'scrum': '4',
    'kanban': '3',
    
    # Outras tecnologias
    'java': '5',
    'spring': '3',
    'spring boot': '3',
    '.net': '2',
    'c#': '2',
    'php': '2',
    'ruby': '1',
    'go': '3',  # Go - experiência moderada
    'golang': '3',
    'go (programming language)': '3',
    'rust': '2',
    'kotlin': '2',
    'swift': '1',  # Pouca experiência com Swift
    'swiftui': '1',  # Pouca experiência com SwiftUI
    'objective-c': '1',
    'ios': '1',  # Desenvolvimento iOS - experiência limitada
    'ios development': '1',
    'ios applications': '1',
    'android': '2',
    
    # Ferramentas
    'jira': '4',
    'confluence': '3',
    'jenkins': '2',
    'gitlab': '3',
}

# NOVO: Mapeamento de idade máxima de tecnologias (ano de lançamento)
# Usado para validar que não respondemos anos impossíveis
technology_max_age = {
    'go': 16,  # Go lançado em 2009 (2025 - 2009 = 16 anos)
    'golang': 16,
    'go (programming language)': 16,
    'swift': 10,  # Swift lançado em 2014
    'swiftui': 6,  # SwiftUI lançado em 2019
    'kotlin': 14,  # Kotlin lançado em 2011
    'rust': 15,  # Rust 1.0 em 2015
    'typescript': 12,  # TypeScript lançado em 2012
    'react': 12,  # React lançado em 2013
    'react native': 9,  # React Native lançado em 2015
    'vue': 11,  # Vue lançado em 2014
    'angular': 16,  # AngularJS em 2009, Angular 2+ em 2016
    'docker': 12,  # Docker lançado em 2013
    'kubernetes': 10,  # Kubernetes lançado em 2014
    'k8s': 10,
    'graphql': 9,  # GraphQL lançado em 2015
    'mongodb': 16,  # MongoDB lançado em 2009
    'redis': 16,  # Redis lançado em 2009
    'node.js': 16,  # Node.js lançado em 2009
    'nodejs': 16,
    'node': 16,
}

def get_max_years_for_tech(tech_name: str) -> int:
    """
    Retorna o número máximo de anos possível para uma tecnologia.
    Se não encontrar, retorna 20 (tecnologias antigas).
    """
    tech_lower = tech_name.lower()
    return technology_max_age.get(tech_lower, 20)

def get_experience_for_technology(question_text: str) -> str:
    """
    Retorna anos de experiência baseado na tecnologia mencionada na pergunta.
    Valida que não excede a idade máxima da tecnologia.
    Se não encontrar tecnologia específica, retorna valor genérico.
    """
    question_lower = question_text.lower()
    
    # IMPORTANTE: NÃO confundir perguntas de experiência com tecnologia com perguntas de idade
    # Se pergunta contém "years of experience" ou "anos de experiência", NÃO é pergunta de idade
    is_experience_question = any(phrase in question_lower for phrase in [
        'years of experience', 'anos de experiência', 'how many years',
        'quantos anos', 'há quantos anos', 'tempo de experiência',
        'work experience', 'experiência com', 'experience with'
    ])
    
    # Procurar por tecnologia específica
    for tech, years in experience_by_technology.items():
        if tech in question_lower:
            years_int = int(years)
            # Validar contra idade máxima da tecnologia
            max_years = get_max_years_for_tech(tech)
            if years_int > max_years:
                # Ajustar para máximo realista (70% da idade da tech ou no máximo 5 anos)
                adjusted = min(int(max_years * 0.7), 5)
                print(f"⚠️ Adjusted {tech} experience from {years} to {adjusted} (tech max age: {max_years})")
                return str(adjusted)
            return years
    
    # Padrões especiais - APENAS se NÃO for pergunta de experiência com anos
    if not is_experience_question:
        if 'desde qual idade' in question_lower or ('started' in question_lower and 'age' in question_lower and 'programming' in question_lower):
            return age_started_programming
    
    if 'exclusivamente como' in question_lower:
        if 'sre' in question_lower or 'site reliability' in question_lower:
            return '2'
        if 'devops' in question_lower:
            return '3'
        if 'full stack' in question_lower or 'fullstack' in question_lower:
            return '5'
    
    # Default genérico (melhor que sempre "3")
    return years_of_experience

# Do you need visa sponsorship now or in future?
require_visa = "No"               # "Yes" or "No"

# What is the link to your portfolio website, leave it empty as "", if you want to leave this question unanswered
website = "https://github.com/LeonardoRFragoso"                        # "www.example.bio" or "" and so on....

# Please provide the link to your LinkedIn profile.
linkedIn = "https://www.linkedin.com/in/leonardo-fragoso-921b166a/"       # "https://www.linkedin.com/in/example" or "" and so on...

# What is the status of your citizenship? # If left empty as "", tool will not answer the question. However, note that some companies make it compulsory to be answered
# Valid options are: "U.S. Citizen/Permanent Resident", "Non-citizen allowed to work for any employer", "Non-citizen allowed to work for current employer", "Non-citizen seeking work authorization", "Canadian Citizen/Permanent Resident" or "Other"
us_citizenship = "Other"

# Age started programming
age_started_programming = "14"     # Idade que começou a programar

# Current age
current_age = "32"                 # Sua idade atual

# Taxa/hora PJ (R$ 80-120)
taxa_hora_pj = "100"               # Taxa/hora PJ (R$ 80-120)

# CPF
cpf_number = "15284848780"          # CPF

# English level
english_level = "Intermediário"     # Nível de inglês

## SOME ANNOYING QUESTIONS BY COMPANIES ##

## SOME ANNOYING QUESTIONS BY COMPANIES 🫠 ##

# What to enter in your desired salary question (American and European), What is your expected CTC (South Asian and others)?, only enter in numbers as some companies only allow numbers,
desired_salary = 5500          # Base salary CLT - will vary ±10% automatically (do NOT use quotes)
'''
Note: If question has the word "lakhs" in it (Example: What is your expected CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
And if asked in months, then it will divide by 12 and answer. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
'''

# What is your current CTC? Some companies make it compulsory to be answered in numbers...
current_ctc = 4287            # 800000, 900000, 1000000 or 1200000 and so on... Do NOT use quotes
'''
Note: If question has the word "lakhs" in it (Example: What is your current CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
# And if asked in months, then it will divide by 12 and answer. Examples:
# * 2400000 will be answered as "200000"
# * 850000 will be answered as "70833"
'''

# (In Development) # Currency of salaries you mentioned. Companies that allow string inputs will add this tag to the end of numbers. Eg: 
# currency = "INR"                 # "USD", "INR", "EUR", etc.

# What is your notice period in days?
notice_period = 30                   # Any number >= 0 without quotes. Eg: 0, 7, 15, 30, 45, etc.
'''
Note: If question has 'month' or 'week' in it (Example: What is your notice period in months), 
then it will divide by 30 or 7 and answer respectively. Examples:
* For notice_period = 66:
  - "66" OR "2" if asked in months OR "9" if asked in weeks
* For notice_period = 15:"
  - "15" OR "0" if asked in months OR "2" if asked in weeks
* For notice_period = 0:
  - "0" OR "0" if asked in months OR "0" if asked in weeks
'''

# Your LinkedIn headline in quotes Eg: "Software Engineer @ Google, Masters in Computer Science", "Recent Grad Student @ MIT, Computer Science"
linkedin_headline = "Desenvolvedor Full Stack | Python, Django, Flask, React | Especialista em Automações e APIs RESTful" # "Headline" or "" to leave this question unanswered

# Your summary in quotes, use \n to add line breaks if using single quotes "Summary".You can skip \n if using triple quotes """Summary"""
linkedin_summary = """
Desenvolvedor Full Stack com foco em automações e ampla experiência em desenvolvimento de aplicações web utilizando Python, Django, Flask, React e Node.js.

Especialista em construir soluções seguras e escaláveis em back-end, com expertise em APIs RESTful, integrações eficientes e bancos de dados SQL/NoSQL (PostgreSQL, Firebase).

Sólida experiência em front-end desenvolvendo interfaces interativas e responsivas com React, Tailwind CSS e outras tecnologias modernas.

Formação em Gestão de TI com transição para desenvolvimento web, unindo gestão de projetos com paixão por programação e inovação. Proficiência em Selenium, Puppeteer, metodologias ágeis e práticas de segurança da informação.

Bacharel em Gestão de Tecnologia da Informação com formações complementares em Python, Django, Análise de Dados e Full Stack Development.
"""

'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Your cover letter in quotes, use \n to add line breaks if using single quotes "Cover Letter".You can skip \n if using triple quotes """Cover Letter""" (This question makes sense though)
cover_letter = """
Prezados recrutadores,

Tenho grande interesse em fazer parte da equipe. Como Desenvolvedor Full Stack com foco em automações, possuo ampla experiência em desenvolvimento de aplicações web utilizando Python, Django, Flask, React e Node.js.

Minha expertise inclui:
• Desenvolvimento de APIs RESTful seguras e escaláveis
• Criação de interfaces responsivas e interativas com React
• Automações com Selenium e Puppeteer
• Integração com bancos de dados SQL/NoSQL (PostgreSQL, Firebase)
• Implementação de práticas de segurança da informação

Minha trajetória em Gestão de TI me proporcionou uma visão abrangente de projetos, permitindo entregar soluções que atendem necessidades de negócio mantendo excelência técnica. Sou bacharel em Gestão de Tecnologia da Informação com formações complementares em Python, Django e Full Stack Development.

Estou comprometido com o aprendizado contínuo e metodologias ágeis, sempre buscando entregar aplicações de alto desempenho seguindo as melhores práticas do mercado.

Estou animado com a oportunidade de contribuir com meus conhecimentos e crescer profissionalmente junto à empresa.

Atenciosamente,
Leonardo Rodrigues Fragoso
"""
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------

# Your user_information_all letter in quotes, use \n to add line breaks if using single quotes "user_information_all".You can skip \n if using triple quotes """user_information_all""" (This question makes sense though)
# We use this to pass to AI to generate answer from information , Assuing Information contians eg: resume  all the information like name, experience, skills, Country, any illness etc. 
user_information_all ="""
User Information
"""
##<
'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Name of your most recent employer
recent_employer = "ICTSI" # "", "Lala Company", "Google", "Snowflake", "Databricks"

# Example question: "On a scale of 1-10 how much experience do you have building web or mobile applications? 1 being very little or only in school, 10 being that you have built and launched applications to real users"
confidence_level = "7"             # Any number between "1" to "10" including 1 and 10, put it in quotes ""
##



# >>>>>>>>>>> RELATED SETTINGS <<<<<<<<<<<

## Allow Manual Inputs
# Should the tool pause before every submit application during easy apply to let you check the information?
pause_before_submit = False         # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''

# Should the tool pause if it needs help in answering questions during easy apply?
# Note: If set as False will answer randomly...
pause_at_failed_question = False    # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''
##

# >>>>>>>>>>> SMART ANSWERS FOR COMMON QUESTIONS (Portuguese & English) <<<<<<<<<<<
# Dictionary of common questions and their answers based on keywords
# The bot will match keywords in the question and provide the appropriate answer

smart_answers = {
    # Years of experience questions - ALWAYS 3 years for any time-related question
    "anos de experiência com python|anos usando python|anos com python|python experience|experience with python|years of experience with python": python_experience_years,
    "anos de experiência com jurídico|anos de experiência juridico|experiência jurídica|experiencia juridica|legal experience|experience in law": legal_experience_years,
    "anos de experiência com integração e entrega contínuas|anos de experiência com integração contínua|anos de experiência com entrega contínua|anos usando integração e entrega contínuas|anos usando integração contínua|anos usando entrega contínua|anos de experiência com ci/cd|anos usando ci/cd|ci/cd experience|experience with ci/cd|continuous integration experience|continuous delivery experience": ci_cd_experience_years,
    "anos de experiência com tecnologia da informação|anos em tecnologia da informação|anos de experiência em tecnologia da informação|information technology experience|experience in information technology|it experience": it_experience_years,
    "anos de experiência|years of experience|experiência em|experience in|quantos anos|how many years|tempo de experiência|experience time": years_of_experience,
    "anos de|years of|anos com|years with|anos usando|years using|já usa|no trabalho": years_of_experience,
    "anos de experiência com java|anos de experiência java|java experience|experience with java": java_experience_years,
    "anos de experiência com nodejs|anos de experiência nodejs|nodejs experience|experience with nodejs": nodejs_experience_years,
    "anos de experiência com reactjs|anos de experiência reactjs|reactjs experience|experience with reactjs": reactjs_experience_years,
    
    # CPF
    "cpf|informe seu cpf|seu cpf": cpf_number,
    
    # Age started programming
    "programa desde qual idade|started programming|começou a programar|idade.*programar": age_started_programming,
    
    # Taxa/hora PJ
    "taxa/hora|taxa hora|por hora|hourly rate|rate per hour|valor hora": taxa_hora_pj,
    
    # On-site / presencial work question (radio Yes/No)
    "você trabalharia presencialmente|trabalharia presencialmente|trabalho presencial|work on-site|on-site work|onsite work": "Não",
    
    # Work model / Remote work
    "modelo de trabalho|work model|remoto|remote|presencial|on-site|híbrido|hybrid": "Remoto ou Híbrido",
    
    # Availability / Start date
    "disponibilidade|availability|quando pode começar|when can you start|data de início|start date": "Imediato",
    
    # Salary expectations - CLT vs PJ
    "pretensão salarial|salary expectation|salário desejado|desired salary|expectativa salarial|salário pretendido|quanto somos atrativos|expectativas em termos de remuneração": "SALARY_CHECK",  # Special marker for salary logic
    
    # Contract as PJ for indefinite time (Yes/No select)
    "contrato pessoa jurídica por tempo indeterminado|contrato pessoa juridica por tempo indeterminado|contrato pessoa juridica|contrato pj por tempo indeterminado|contrato pj indeterminado|pj por tempo indeterminado": "Yes",
    
    # Notice period
    "aviso prévio|notice period|período de aviso": str(notice_period) + " dias",
    
    # Why this company / Why apply
    "por que você|why do you|por que esta empresa|why this company|motivação|motivation|por que quer trabalhar|why do you want to work": "Tenho grande interesse em fazer parte da equipe e contribuir com minhas habilidades em Python, Django e desenvolvimento Full Stack.",
    
    # Technologies / Skills
    "tecnologias|technologies|linguagens|languages|frameworks|ferramentas|tools|habilidades|skills": "Python, Django, Flask, React, Node.js, PostgreSQL, MongoDB, Docker, Git",
    
    # Microsoft Power Platform (from the image)
    "microsoft power platform|power platform|power bi|power automate|power apps": "3",
    
    # Certifications
    "certificações|certifications|certificados|certificates": "Formação em Python, Django, Full Stack Development e Análise de Dados",
    
    # Education
    "formação|education|graduação|degree|escolaridade": "Bacharel em Gestão de Tecnologia da Informação",
    
    # English level / Language
    "inglês|english|idioma|language": english_level,
    
    # Portfolio / GitHub
    "portfólio|portfolio|github|projetos|projects": website,
    
    # LinkedIn profile
    "linkedin|perfil linkedin": linkedIn,
    
    # Work authorization / Visa - Always Yes for Latin America
    "autorização de trabalho|work authorization|visto|visa|sponsorship|eligible to work|autorizado a trabalhar": "Yes",
    
    # Relocation
    "mudança|relocation|relocate|mudar de cidade": "Não necessário, trabalho remoto",
    
    # Current company
    "empresa atual|current company|empregador atual|current employer": recent_employer,
    
    # Confidence / Self assessment
    "confiança|confidence|auto avaliação|self assessment|nível de|level of": confidence_level,
    
    # Salary CTI (from the image)
    "pretensão salarial para contratação cti|cti|clt": "5000",
    
    # Technical skills dropdowns - CloudFormation, Terraform, Infrastructure as Code
    "cloudformation|terraform|infra as code|infrastructure as code|iac": "Sim",
    
    # Kubernetes / K8s
    "kubernetes|k8s": "Sim",
    
    # CI/CD tools - Jenkins, Azure DevOps, GitLab CI, GitHub Actions
    "jenkins|azure devops|gitlab ci|github actions": "Sim",
    
    # AWS services
    "aws|amazon web services|ec2|s3|lambda|rds|dynamodb|sqs|sns|cognito|eks|aurora": "Sim",
    
    # Docker / Containers
    "docker|container|containerização|containerization": "Sim",
    
    # Linux / Shell
    "linux|shell|bash|scripting": "Sim",
    
    # Python knowledge
    "conhecimento.*python|python knowledge|python skills": "Sim",
    
    # Git / Version control
    "git|controle de versão|version control|github|gitlab|bitbucket": "Sim",
    
    # Databases
    "postgresql|mysql|mongodb|redis|sql|nosql|banco de dados|database": "Sim",
    
    # API / REST
    "api|rest|restful|graphql": "Sim",
    
    # General knowledge/experience questions (default to Sim)
    "forte conhecimentos|conhecimento avançado|conhecimento em|strong knowledge|advanced knowledge": "Sim",
    
    # University / Education
    "university|universidade|faculdade|instituição|institution|bachelor|bacharelado|graduated from": "Universidade Estácio de Sá",
    
    # English level (dropdown)
    "english level|nível de inglês|english proficiency": "B2",
    
    # Work authorization Latin America / Brazil
    "work authorization.*latin america|autorização.*américa latina|eligible.*latin america": "Yes",
    "work authorization|autorização de trabalho|eligible to work|autorizado a trabalhar": "Yes",
    
    # Graduation year
    "graduation year|ano de formatura|when did you graduate|year.*graduate": "2022",
    
    # How did you hear about this opportunity
    "how did you hear|como soube|como conheceu|onde encontrou": "LinkedIn",
    
    # Country of residence
    "country.*reside|país.*reside|where do you live|onde mora|country of residence": "Brasil",
    
    # GPA / Academic performance (when unknown, use N/A)
    "gpa|grade point|média|academic.*score": "N/A",
}
##

# Do you want to overwrite previous answers?
overwrite_previous_answers = False # True or False, Note: True or False are case-sensitive






############################################################################################################
'''
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

Support my work on <PATREON_LINK>. Together, we can help more job seekers.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
'''
############################################################################################################