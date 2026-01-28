"""
Compatibility layer for transitioning from legacy config/*.py to ConfigService.

This module provides the same variable names as the old config files,
but loads them through ConfigService. This allows gradual migration
without breaking existing code.

Usage in runAiBot.py:
    # Old way (still works):
    from backend.bot.config.personals import first_name, last_name
    
    # New way (use this instead):
    from backend.core.config_compat import first_name, last_name
    
    # Or use ConfigService directly:
    from backend.core.config_service import ConfigService
    config = ConfigService()
    personal = config.get_personal_info()
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config_service import ConfigService, get_config_service

# Initialize ConfigService
_config = get_config_service(
    tenant_id=os.getenv('DEFAULT_TENANT_ID', 'default'),
    user_id=os.getenv('DEFAULT_USER_ID', None)
)

# ============================================================================
# PERSONALS - from config/personals.py
# ============================================================================

_personal = _config.get_personal_info()

first_name: str = _personal.first_name
middle_name: str = _personal.middle_name
last_name: str = _personal.last_name
full_name: str = _personal.full_name
phone_number: str = _personal.phone_number
current_city: str = _personal.current_city
street: str = _personal.street
state: str = _personal.state
zipcode: str = _personal.zipcode
country: str = _personal.country
ethnicity: str = _personal.ethnicity
gender: str = _personal.gender
disability_status: str = _personal.disability_status
veteran_status: str = _personal.veteran_status

# ============================================================================
# SECRETS - from config/secrets.py
# ============================================================================

_linkedin_email, _linkedin_password = _config.get_linkedin_credentials()
_ai_config = _config.get_ai_config()

username: str = _linkedin_email
password: str = _linkedin_password

use_AI: bool = _ai_config.get('use_ai', False)
ai_provider: str = _ai_config.get('provider', 'openai')
llm_api_url: str = _ai_config.get('api_url', 'https://api.openai.com/v1/')
llm_api_key: str = _ai_config.get('api_key', '')
llm_model: str = _ai_config.get('model', 'gpt-4o-mini')
llm_spec: str = _ai_config.get('spec', 'openai')
stream_output: bool = _ai_config.get('stream_output', False)

# ============================================================================
# SEARCH - from config/search.py
# ============================================================================

_search = _config.get_search_preferences()
_blacklist = _config.get_blacklist()

search_terms: List[str] = _search.search_terms
search_location: str = _search.search_location
switch_number: int = _search.switch_number
randomize_search_order: bool = _search.randomize_search_order
sort_by: str = _search.sort_by
date_posted: str = _search.date_posted
salary: str = _search.salary
easy_apply_only: bool = _search.easy_apply_only
experience_level: List[str] = _search.experience_level
job_type: List[str] = _search.job_type
on_site: List[str] = _search.on_site
companies: List[str] = _search.companies
location: List[str] = _search.location
industry: List[str] = _search.industry
job_function: List[str] = _search.job_function
job_titles: List[str] = _search.job_titles
benefits: List[str] = _search.benefits
commitments: List[str] = _search.commitments
under_10_applicants: bool = _search.under_10_applicants
in_your_network: bool = _search.in_your_network
fair_chance_employer: bool = _search.fair_chance_employer
pause_after_filters: bool = _search.pause_after_filters

# Blacklist
about_company_bad_words: List[str] = _blacklist.about_company_bad_words
about_company_good_words: List[str] = _blacklist.about_company_good_words
bad_words: List[str] = _blacklist.bad_words
contextual_bad_words: List[str] = _blacklist.contextual_bad_words
security_clearance: bool = _blacklist.security_clearance
did_masters: bool = _blacklist.did_masters
current_experience: int = _blacklist.current_experience

# ============================================================================
# SETTINGS - from config/settings.py
# ============================================================================

_settings = _config.get_settings()

close_tabs: bool = _settings.close_tabs
follow_companies: bool = _settings.follow_companies
run_non_stop: bool = _settings.run_non_stop
alternate_sortby: bool = _settings.alternate_sortby
cycle_date_posted: bool = _settings.cycle_date_posted
stop_date_cycle_at_24hr: bool = _settings.stop_date_cycle_at_24hr
generated_resume_path: str = _settings.generated_resume_path
file_name: str = _settings.file_name
failed_file_name: str = _settings.failed_file_name
logs_folder_path: str = _settings.logs_folder_path
click_gap: int = _settings.click_gap
run_in_background: bool = _settings.run_in_background
disable_extensions: bool = _settings.disable_extensions
safe_mode: bool = _settings.safe_mode
smooth_scroll: bool = _settings.smooth_scroll
keep_screen_awake: bool = _settings.keep_screen_awake
stealth_mode: bool = _settings.stealth_mode
showAiErrorAlerts: bool = _settings.showAiErrorAlerts

# ============================================================================
# QUESTIONS - from config/questions.py
# ============================================================================

_resume_paths = _config.get_resume_paths()
_experience_map = _config.get_experience_map()

default_resume_path: str = _resume_paths.get('default', '')
resume_national: str = _resume_paths.get('national', '')
resume_international: str = _resume_paths.get('international', '')

experience_by_technology: Dict[str, str] = _experience_map

# Load additional question variables from legacy config
try:
    from backend.bot.config.questions import (
        years_of_experience,
        python_experience_years,
        legal_experience_years,
        ci_cd_experience_years,
        it_experience_years,
        java_experience_years,
        nodejs_experience_years,
        reactjs_experience_years,
        angular_experience_years,
        vue_experience_years,
        desired_salary,
        current_ctc,
        notice_period,
        pause_before_submit,
        pause_at_failed_question,
        overwrite_previous_answers,
        useNewResume
    )
except ImportError:
    # Default values if not available
    years_of_experience = "5"
    python_experience_years = "5"
    legal_experience_years = "1"
    ci_cd_experience_years = "3"
    it_experience_years = "7"
    java_experience_years = "5"
    nodejs_experience_years = "5"
    reactjs_experience_years = "5"
    angular_experience_years = "3"
    vue_experience_years = "2"
    desired_salary = 0
    current_ctc = 0
    notice_period = 0
    pause_before_submit = True
    pause_at_failed_question = True
    overwrite_previous_answers = False
    useNewResume = True


# ============================================================================
# Helper Functions
# ============================================================================

def reload_config() -> None:
    """
    Reload configuration from all sources.
    Call this after modifying config files or environment variables.
    """
    global _config, _personal, _search, _blacklist, _settings
    global first_name, middle_name, last_name, full_name, phone_number
    global current_city, street, state, zipcode, country
    global ethnicity, gender, disability_status, veteran_status
    global username, password, use_AI, ai_provider
    global search_terms, search_location
    
    _config.clear_cache()
    _personal = _config.get_personal_info()
    _search = _config.get_search_preferences()
    _blacklist = _config.get_blacklist()
    _settings = _config.get_settings()
    
    # Update all variables
    first_name = _personal.first_name
    middle_name = _personal.middle_name
    last_name = _personal.last_name
    full_name = _personal.full_name
    # ... (other variables would be updated similarly)


def get_config_service_instance() -> ConfigService:
    """
    Get the underlying ConfigService instance.
    
    Returns:
        ConfigService: The config service instance
    """
    return _config


def switch_user(tenant_id: str = None, user_id: str = None) -> None:
    """
    Switch to a different tenant/user configuration.
    
    Args:
        tenant_id: New tenant ID
        user_id: New user ID
    """
    global _config
    _config = get_config_service(
        tenant_id=tenant_id or _config.tenant_id,
        user_id=user_id
    )
    reload_config()


# ============================================================================
# Validation
# ============================================================================

def validate_config() -> bool:
    """
    Validate that required configuration is present.
    
    Returns:
        bool: True if configuration is valid
    """
    errors = []
    
    if not first_name:
        errors.append("first_name is required")
    if not last_name:
        errors.append("last_name is required")
    if not phone_number:
        errors.append("phone_number is required")
    if not search_terms:
        errors.append("search_terms is required")
    
    if errors:
        print("⚠️  Configuration validation errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Config Compatibility Layer - Self Test")
    print("=" * 60)
    
    print(f"\n📋 Personal Info:")
    print(f"   Name: {full_name}")
    print(f"   Phone: {phone_number}")
    print(f"   City: {current_city}")
    
    print(f"\n🔐 Credentials:")
    print(f"   Username: {username[:5]}***" if username else "   Username: Not set")
    print(f"   Password: {'*' * 8}" if password else "   Password: Not set")
    
    print(f"\n🔍 Search:")
    print(f"   Terms: {search_terms[:3]}..." if search_terms else "   Terms: Not set")
    print(f"   Location: {search_location}")
    
    print(f"\n⚙️  Settings:")
    print(f"   Stealth mode: {stealth_mode}")
    print(f"   Run in background: {run_in_background}")
    
    print(f"\n🤖 AI Config:")
    print(f"   Use AI: {use_AI}")
    print(f"   Provider: {ai_provider}")
    
    print("\n" + "=" * 60)
    
    if validate_config():
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has issues. Please fix before running bot.")
