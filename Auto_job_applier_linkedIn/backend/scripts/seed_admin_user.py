"""
Seed Admin User Script
Creates the admin user leonardorfragoso@gmail.com with all preferences from the old system.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.database import SessionLocal, init_db
from backend.core.models import User, Tenant
from backend.core.encryption_service import get_encryption_service
from backend.api.auth import get_password_hash

def create_admin_user():
    """Create admin user with preferences from old system."""
    
    init_db()
    db = SessionLocal()
    encryption_service = get_encryption_service()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "leonardorfragoso@gmail.com").first()
        if existing_user:
            print("⚠️ User leonardorfragoso@gmail.com already exists. Updating preferences...")
            user = existing_user
        else:
            # Get or create default tenant
            tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
            if not tenant:
                tenant = Tenant(
                    name="Default",
                    slug="default",
                    branding={},
                    features={"max_users": 100, "max_applications_per_day": 50, "ai_enabled": True},
                    settings={"timezone": "America/Sao_Paulo", "language": "pt-BR"},
                    status="active"
                )
                db.add(tenant)
                db.commit()
                db.refresh(tenant)
                print("✅ Created default tenant")
            
            # Create admin user
            user = User(
                tenant_id=tenant.id,
                email="leonardorfragoso@gmail.com",
                password_hash=get_password_hash("admin123"),  # Default password - should be changed
                is_admin=True,
                status="active"
            )
            db.add(user)
            print("✅ Created admin user leonardorfragoso@gmail.com")
        
        # Personal info from personals.py
        user.personal_info = {
            "first_name": "Leonardo",
            "middle_name": "Rodrigues",
            "last_name": "Fragoso",
            "full_name": "Leonardo Rodrigues Fragoso",
            "phone_number": "21980292791",
            "current_city": "Rio de Janeiro",
            "job_title": "Desenvolvedor de Sistemas",
            "street": "Rua Iaco 180, apt 306",
            "state": "RJ",
            "zipcode": "21921-640",
            "country": "Brasil",
            "ethnicity": "Decline",
            "gender": "Decline",
            "disability_status": "Decline",
            "veteran_status": "Decline",
            "linkedin_url": "https://www.linkedin.com/in/leonardo-fragoso-921b166a/",
            "website": "https://github.com/LeonardoRFragoso",
            "us_citizenship": "Other",
            "current_age": "32",
            "age_started_programming": "14",
        }
        
        # Search preferences from search.py
        user.search_preferences = {
            "search_terms": [
                "Desenvolvedor Python", "Python Developer", 
                "Desenvolvedor Django", "Django Developer",
                "Desenvolvedor Flask", "Flask Developer",
                "Full Stack Developer", "Desenvolvedor Full Stack",
                "Backend Developer", "Desenvolvedor Backend",
                "Node.js Developer", "Desenvolvedor Node.js",
                "Desenvolvedor de Automações", "RPA Developer",
                "API Developer", "Desenvolvedor de Sistemas"
            ],
            "search_location": "Brasil",
            "sort_by": "Most recent",
            "date_posted": "Past 24 hours",
            "easy_apply_only": True,
            "experience_level": ["Entry level", "Associate"],
            "on_site": ["Remote", "Hybrid"],
            "location": ["Rio de Janeiro", "Remote", "Brasil"],
            "current_experience": 8,
            "bad_words": ["US Citizen", "USA Citizen", "No C2C", "No Corp2Corp", "Embedded Programming", "CNC", "COBOL", "FORTRAN", "Mainframe", "AS/400"],
            "about_company_bad_words": ["Crossover"],
        }
        
        # Question answers from questions.py - This is the key data!
        user.question_answers = {
            # Basic info
            "years_of_experience": "5",
            "salary_expectation": "5500",
            "available_start": "Imediato",
            "work_model": "Remoto ou Híbrido",
            "willing_relocate": "Não necessário, trabalho remoto",
            "english_level": "Intermediário",
            "notice_period": "30 dias",
            
            # Experience by technology
            "python_experience": "5",
            "django_experience": "5",
            "flask_experience": "4",
            "fastapi_experience": "3",
            "javascript_experience": "5",
            "typescript_experience": "3",
            "react_experience": "5",
            "nodejs_experience": "5",
            "java_experience": "5",
            "sql_experience": "5",
            "postgresql_experience": "5",
            "mongodb_experience": "3",
            "docker_experience": "3",
            "git_experience": "6",
            "aws_experience": "3",
            "azure_experience": "3",
            "kubernetes_experience": "2",
            "ci_cd_experience": "3",
            "selenium_experience": "4",
            "agile_experience": "5",
            "scrum_experience": "4",
            
            # Technology experience mapping (for smart matching)
            "experience_by_technology": {
                "python": "5", "django": "5", "flask": "4", "fastapi": "3",
                "javascript": "5", "typescript": "3", "react": "5", "reactjs": "5",
                "node": "5", "nodejs": "5", "next.js": "3",
                "html": "5", "css": "5", "tailwind": "3",
                "sql": "5", "postgresql": "5", "mysql": "4", "mongodb": "3",
                "docker": "3", "git": "6", "aws": "3", "azure": "3",
                "kubernetes": "2", "ci/cd": "3", "selenium": "4",
                "java": "5", "spring": "3", "go": "3",
                "agile": "5", "scrum": "4", "kanban": "3",
                "rest": "5", "api": "5", "graphql": "2",
            },
            
            # Personal documents
            "cpf": "15284848780",
            "taxa_hora_pj": "100",
            
            # Why interested / Motivation
            "why_interested": "Tenho grande interesse em fazer parte da equipe e contribuir com minhas habilidades em Python, Django e desenvolvimento Full Stack.",
            
            # Skills
            "main_skills": "Python, Django, Flask, React, Node.js, PostgreSQL, MongoDB, Docker, Git",
            
            # Certifications
            "certifications": "Formação em Python, Django, Full Stack Development e Análise de Dados",
            
            # Education
            "education": "Bacharel em Gestão de Tecnologia da Informação",
            "university": "Universidade Estácio de Sá",
            "graduation_year": "2022",
            
            # Employer
            "recent_employer": "ICTSI",
            "confidence_level": "7",
            
            # Work authorization
            "require_visa": "No",
            "work_authorization": "Yes",
            
            # Cover letter
            "cover_letter": """Prezado(a) Recrutador(a),

Meu nome é Leonardo Rodrigues Fragoso, sou desenvolvedor Full Stack com sólida experiência em Python, Django, Flask, React e Node.js. Tenho trabalhado na criação de soluções web completas, desde a arquitetura backend até interfaces modernas e responsivas.

Ao longo da minha carreira, desenvolvi projetos utilizando PostgreSQL, MongoDB, Docker e integrações com APIs RESTful. Minha experiência inclui automação de processos, desenvolvimento de dashboards analíticos e implementação de sistemas escaláveis.

Destaco minha capacidade de trabalhar com equipes multidisciplinares, traduzindo necessidades de negócio mantendo excelência técnica. Sou bacharel em Gestão de Tecnologia da Informação com formações complementares em Python, Django e Full Stack Development.

Estou comprometido com o aprendizado contínuo e metodologias ágeis, sempre buscando entregar aplicações de alto desempenho seguindo as melhores práticas do mercado.

Estou animado com a oportunidade de contribuir com meus conhecimentos e crescer profissionalmente junto à empresa.

Atenciosamente,
Leonardo Rodrigues Fragoso""",

            # Smart answers (from the old system)
            "custom_how_did_you_hear": "LinkedIn",
            "custom_country_residence": "Brasil",
            "custom_contrato_pj": "Yes",
            "custom_trabalho_presencial": "Não",
            
            # Updated timestamp
            "updated_at": "2026-01-28T01:05:00Z",
            "migrated_from": "legacy_system",
        }
        
        # Resume config
        user.resume_config = {
            "default": r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV - Leonardo Fragoso _ Desenvolvedor Full Stack.pdf",
            "national": r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV Leonardo Fragoso - Desenvolvedor de Sistemas.pdf",
            "international": r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\CV - Leonardo Fragoso _ Desenvolvedor Full Stack.pdf",
        }
        
        # LinkedIn credentials (encrypted)
        user.linkedin_credentials = {
            "email": "leonardorfragoso@gmail.com",
            "password": encryption_service.encrypt("PLACEHOLDER_CHANGE_ME"),
            "updated_at": "2026-01-28T01:05:00Z",
        }
        
        # Bot settings
        user.bot_settings = {
            "pause_before_submit": False,
            "pause_at_failed_question": False,
            "switch_number": 20,
            "randomize_search_order": False,
            "pause_after_filters": True,
            "overwrite_previous_answers": False,
        }
        
        db.commit()
        db.refresh(user)
        
        print("\n" + "="*60)
        print("✅ ADMIN USER CREATED/UPDATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📧 Email: leonardorfragoso@gmail.com")
        print(f"🔑 Password: admin123 (CHANGE THIS!)")
        print(f"👤 Name: Leonardo Rodrigues Fragoso")
        print(f"💼 Job Title: Desenvolvedor de Sistemas")
        print(f"📍 Location: Rio de Janeiro, RJ")
        print(f"🔗 LinkedIn: https://www.linkedin.com/in/leonardo-fragoso-921b166a/")
        print(f"\n📊 Imported Data:")
        print(f"   - {len(user.question_answers)} question answers")
        print(f"   - {len(user.search_preferences.get('search_terms', []))} search terms")
        print(f"   - Experience mapping for {len(user.question_answers.get('experience_by_technology', {}))} technologies")
        print(f"\n⚠️  IMPORTANT: Update LinkedIn password in the profile page!")
        print("="*60)
        
        return user
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
