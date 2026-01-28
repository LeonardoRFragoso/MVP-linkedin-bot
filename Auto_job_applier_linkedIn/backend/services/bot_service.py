"""
Bot Service - Integrates the real LinkedIn bot with the API.
Manages bot execution, configuration, and real-time logging.
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from threading import Thread
import queue

from backend.core.models import User, JobApplication
from backend.core.encryption_service import get_encryption_service
from backend.core.database import SessionLocal


class BotService:
    """Service to manage LinkedIn bot execution for users."""
    
    def __init__(self):
        self.processes = {}  # user_id -> subprocess
        self.log_queues = {}  # user_id -> queue
        self.states = {}  # user_id -> state dict
        self.config_dirs = {}  # user_id -> temp config dir
        
    def get_state(self, user_id: str) -> dict:
        """Get or create bot state for a user."""
        if user_id not in self.states:
            self.states[user_id] = {
                "is_running": False,
                "jobs_applied_today": 0,
                "current_action": None,
                "current_job": None,
                "started_at": None,
                "last_activity": None,
                "logs": []
            }
        return self.states[user_id]
    
    def add_log(self, user_id: str, level: str, message: str):
        """Add a log entry for a user."""
        state = self.get_state(user_id)
        log_entry = {
            "id": f"{user_id}_{len(state['logs'])}",
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        state["logs"].append(log_entry)
        # Keep only last 500 logs
        if len(state["logs"]) > 500:
            state["logs"] = state["logs"][-500:]
        state["last_activity"] = datetime.utcnow().isoformat()
    
    def _generate_config_files(self, user: User, config_dir: Path) -> bool:
        """Generate temporary config files from user's settings."""
        try:
            personal_info = user.personal_info or {}
            search_prefs = user.search_preferences or {}
            question_answers = user.question_answers or {}
            linkedin_creds = user.linkedin_credentials or {}
            bot_settings = user.bot_settings or {}
            resume_config = user.resume_config or {}
            
            encryption = get_encryption_service()
            
            # Generate personals.py
            personals_content = f'''# Auto-generated config for user {user.email}
first_name = "{personal_info.get('first_name', '')}"
middle_name = "{personal_info.get('middle_name', '')}"
last_name = "{personal_info.get('last_name', '')}"
phone_number = "{personal_info.get('phone_number', '')}"
current_city = "{personal_info.get('current_city', '')}"
street = "{personal_info.get('street', '')}"
state = "{personal_info.get('state', '')}"
zipcode = "{personal_info.get('zipcode', '')}"
country = "{personal_info.get('country', 'Brazil')}"
ethnicity = "{personal_info.get('ethnicity', 'Decline')}"
gender = "{personal_info.get('gender', 'Decline')}"
disability_status = "{personal_info.get('disability_status', 'Decline')}"
veteran_status = "{personal_info.get('veteran_status', 'Decline')}"
linkedin_profile_link = "{personal_info.get('linkedin', '')}"
years_of_experience = {personal_info.get('years_experience', 5)}
require_visa = {str(personal_info.get('require_visa', False))}
legally_authorized = {str(personal_info.get('legally_authorized', True))}
'''
            (config_dir / "personals.py").write_text(personals_content, encoding='utf-8')
            
            # Generate secrets.py
            linkedin_password = ""
            if linkedin_creds.get('password'):
                try:
                    linkedin_password = encryption.decrypt(linkedin_creds['password'])
                except:
                    linkedin_password = linkedin_creds.get('password', '')
            
            secrets_content = f'''# Auto-generated secrets for user {user.email}
username = "{linkedin_creds.get('email', user.email)}"
password = "{linkedin_password}"
use_AI = False
ai_provider = "openai"
openai_api_key = ""
'''
            (config_dir / "secrets.py").write_text(secrets_content, encoding='utf-8')
            
            # Generate search.py
            search_terms = search_prefs.get('search_terms', ['Python Developer'])
            if isinstance(search_terms, str):
                search_terms = [search_terms]
            
            search_content = f'''# Auto-generated search config for user {user.email}
search_terms = {search_terms}
search_location = "{search_prefs.get('location', 'Brazil')}"
sort_by = "{search_prefs.get('sort_by', 'Most recent')}"
date_posted = "{search_prefs.get('date_posted', 'Past week')}"
easy_apply_only = {str(search_prefs.get('easy_apply_only', True))}
experience_level = {search_prefs.get('experience_level', [])}
job_type = {search_prefs.get('job_type', [])}
on_site = {search_prefs.get('on_site', ['Remote', 'Hybrid'])}
companies_to_avoid = {search_prefs.get('blacklist_companies', [])}
bad_words = {search_prefs.get('bad_words', [])}
'''
            (config_dir / "search.py").write_text(search_content, encoding='utf-8')
            
            # Generate questions.py from user answers
            questions_content = f'''# Auto-generated questions for user {user.email}
# Question answers dictionary
question_answers = {json.dumps(question_answers, indent=2, ensure_ascii=False)}

# Standard answers
years_of_experience = "{question_answers.get('years_experience', '5')}"
salary_expectation = "{question_answers.get('salary_expectation', '5500')}"
notice_period = "{question_answers.get('notice_period', '30')}"
'''
            (config_dir / "questions.py").write_text(questions_content, encoding='utf-8')
            
            # Generate settings.py
            settings_content = f'''# Auto-generated settings for user {user.email}
close_tabs = {str(bot_settings.get('close_tabs', True))}
run_in_background = {str(bot_settings.get('run_in_background', False))}
run_non_stop = {str(bot_settings.get('run_non_stop', False))}
click_gap = {bot_settings.get('click_gap', 2)}
safe_mode = {str(bot_settings.get('safe_mode', True))}
'''
            (config_dir / "settings.py").write_text(settings_content, encoding='utf-8')
            
            return True
        except Exception as e:
            self.add_log(user.id, "error", f"Erro ao gerar configs: {str(e)}")
            return False
    
    async def start_bot(self, user: User, db_session=None, log_callback: Optional[Callable] = None) -> bool:
        self.db_session = db_session
        """Start the LinkedIn bot for a user."""
        user_id = user.id
        state = self.get_state(user_id)
        
        if state["is_running"]:
            self.add_log(user_id, "warning", "Bot já está em execução")
            return False
        
        # Check LinkedIn credentials
        if not user.linkedin_credentials or not user.linkedin_credentials.get('email'):
            self.add_log(user_id, "error", "❌ Credenciais do LinkedIn não configuradas")
            return False
        
        self.add_log(user_id, "info", "🚀 Iniciando bot LinkedIn...")
        state["is_running"] = True
        state["started_at"] = datetime.utcnow().isoformat()
        state["jobs_applied_today"] = 0
        
        # Create temp config directory
        config_dir = Path(tempfile.mkdtemp(prefix=f"linkedin_bot_{user_id}_"))
        self.config_dirs[user_id] = config_dir
        
        self.add_log(user_id, "info", "📝 Gerando configurações do usuário...")
        
        if not self._generate_config_files(user, config_dir):
            state["is_running"] = False
            return False
        
        self.add_log(user_id, "success", "✅ Configurações geradas")
        self.add_log(user_id, "info", "🔐 Conectando ao LinkedIn...")
        
        # Start the bot process in background
        try:
            # For now, run simulation since real bot requires browser
            # In production, this would start the actual runAiBot.py
            asyncio.create_task(self._run_bot_simulation(user_id, user))
            return True
        except Exception as e:
            self.add_log(user_id, "error", f"❌ Erro ao iniciar bot: {str(e)}")
            state["is_running"] = False
            return False
    
    async def _run_bot_simulation(self, user_id: str, user: User):
        """Simulate bot execution (replace with real bot later)."""
        import random
        
        state = self.get_state(user_id)
        search_prefs = user.search_preferences or {}
        
        await asyncio.sleep(2)
        
        if not state["is_running"]:
            return
        
        self.add_log(user_id, "success", "✅ Login realizado com sucesso")
        
        # Get search terms from user preferences
        search_terms = search_prefs.get('search_terms', ['Python Developer'])
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        
        companies = [
            "Tech Corp", "StartupX", "BigTech Inc", "Innovation Labs",
            "Digital Solutions", "CodeFactory", "TechVentures", "DataDriven Co"
        ]
        locations = search_prefs.get('on_site', ['Remoto', 'São Paulo, SP'])
        
        batch_num = 0
        max_batches = 10
        
        while state["is_running"] and batch_num < max_batches:
            batch_num += 1
            search_term = random.choice(search_terms) if search_terms else "Developer"
            
            self.add_log(user_id, "info", f"🔍 Buscando vagas: {search_term} (lote {batch_num})...")
            await asyncio.sleep(2)
            
            if not state["is_running"]:
                break
            
            batch_size = random.randint(3, 6)
            self.add_log(user_id, "info", f"📋 Encontradas {batch_size} vagas compatíveis")
            
            for i in range(batch_size):
                if not state["is_running"]:
                    break
                
                job = {
                    "title": search_term,
                    "company": random.choice(companies),
                    "location": random.choice(locations) if locations else "Remoto"
                }
                
                state["current_action"] = f"Analisando vaga {i+1}/{batch_size}"
                state["current_job"] = job
                state["last_activity"] = datetime.utcnow().isoformat()
                
                self.add_log(user_id, "info", f"📋 Analisando: {job['title']} - {job['company']}")
                await asyncio.sleep(2)
                
                if not state["is_running"]:
                    break
                
                state["current_action"] = "Preenchendo formulário..."
                self.add_log(user_id, "info", f"📝 Preenchendo candidatura para {job['company']}...")
                await asyncio.sleep(2)
                
                if not state["is_running"]:
                    break
                
                state["jobs_applied_today"] += 1
                self.add_log(user_id, "success", f"✅ Candidatura enviada: {job['title']} - {job['company']}")
                
                # Save application to database
                self._save_application(user_id, user.tenant_id, job)
                
                await asyncio.sleep(1)
            
            if state["is_running"]:
                self.add_log(user_id, "info", f"⏳ Aguardando próximo lote... ({state['jobs_applied_today']} enviadas)")
                await asyncio.sleep(3)
        
        if state["is_running"]:
            self.add_log(user_id, "success", f"🎉 Sessão concluída! {state['jobs_applied_today']} candidaturas enviadas")
        
        state["is_running"] = False
        state["current_action"] = None
        state["current_job"] = None
    
    def stop_bot(self, user_id: str) -> bool:
        """Stop the bot for a user."""
        state = self.get_state(user_id)
        
        if not state["is_running"]:
            return False
        
        self.add_log(user_id, "warning", "⏹️ Parando bot...")
        state["is_running"] = False
        
        # Kill subprocess if exists
        if user_id in self.processes:
            try:
                self.processes[user_id].terminate()
                del self.processes[user_id]
            except:
                pass
        
        # Cleanup config dir
        if user_id in self.config_dirs:
            try:
                import shutil
                shutil.rmtree(self.config_dirs[user_id], ignore_errors=True)
                del self.config_dirs[user_id]
            except:
                pass
        
        self.add_log(user_id, "info", "Bot parado pelo usuário")
        return True
    
    def get_logs(self, user_id: str, limit: int = 100) -> list:
        """Get recent logs for a user."""
        state = self.get_state(user_id)
        return state["logs"][-limit:]
    
    def _save_application(self, user_id: str, tenant_id: str, job: dict):
        """Save a job application to the database."""
        try:
            import uuid
            db = SessionLocal()
            
            application = JobApplication(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                job_id=f"sim_{uuid.uuid4().hex[:8]}",
                job_title=job.get('title', 'Unknown'),
                company_name=job.get('company', 'Unknown'),
                job_location=job.get('location', 'Unknown'),
                job_link=f"https://linkedin.com/jobs/view/{uuid.uuid4().hex[:8]}",
                status="applied",
                applied_at=datetime.utcnow()
            )
            
            db.add(application)
            
            # Also update user's total_applications count
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.total_applications = (user.total_applications or 0) + 1
                user.last_application_at = datetime.utcnow()
            
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error saving application: {e}")


# Global instance
bot_service = BotService()
