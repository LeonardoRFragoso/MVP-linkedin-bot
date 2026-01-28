"""
Configuration Service for LinkedIn Bot White Label MVP.
Centralizes configuration loading from multiple sources with tenant/user isolation.

Priority order:
1. Environment variables (highest)
2. JSON config files (tenant-specific)
3. Legacy Python config files (fallback for migration)
4. Default values (lowest)
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from dotenv import load_dotenv

from .encryption_service import EncryptionService, get_encryption_service

logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()


@dataclass
class PersonalInfo:
    """User personal information for job applications."""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    current_city: str = ""
    street: str = ""
    state: str = ""
    zipcode: str = ""
    country: str = ""
    ethnicity: str = "Decline"
    gender: str = "Decline"
    disability_status: str = "Decline"
    veteran_status: str = "Decline"
    
    @property
    def full_name(self) -> str:
        """Get full name combining first, middle, and last names."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "current_city": self.current_city,
            "address": {
                "street": self.street,
                "state": self.state,
                "zipcode": self.zipcode,
                "country": self.country
            },
            "demographics": {
                "ethnicity": self.ethnicity,
                "gender": self.gender,
                "disability_status": self.disability_status,
                "veteran_status": self.veteran_status
            }
        }


@dataclass
class SearchPreferences:
    """Job search preferences and filters."""
    search_terms: List[str] = field(default_factory=list)
    search_location: str = ""
    switch_number: int = 20
    randomize_search_order: bool = False
    sort_by: str = "Most recent"
    date_posted: str = "Past 24 hours"
    salary: str = ""
    easy_apply_only: bool = True
    experience_level: List[str] = field(default_factory=list)
    job_type: List[str] = field(default_factory=list)
    on_site: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    location: List[str] = field(default_factory=list)
    industry: List[str] = field(default_factory=list)
    job_function: List[str] = field(default_factory=list)
    job_titles: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    commitments: List[str] = field(default_factory=list)
    under_10_applicants: bool = False
    in_your_network: bool = False
    fair_chance_employer: bool = False
    pause_after_filters: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "search_terms": self.search_terms,
            "search_location": self.search_location,
            "switch_number": self.switch_number,
            "randomize_search_order": self.randomize_search_order,
            "filters": {
                "sort_by": self.sort_by,
                "date_posted": self.date_posted,
                "salary": self.salary,
                "easy_apply_only": self.easy_apply_only,
                "experience_level": self.experience_level,
                "job_type": self.job_type,
                "on_site": self.on_site,
                "companies": self.companies,
                "location": self.location,
                "industry": self.industry,
                "job_function": self.job_function,
                "job_titles": self.job_titles,
                "benefits": self.benefits,
                "commitments": self.commitments,
                "under_10_applicants": self.under_10_applicants,
                "in_your_network": self.in_your_network,
                "fair_chance_employer": self.fair_chance_employer
            },
            "pause_after_filters": self.pause_after_filters
        }


@dataclass
class BlacklistConfig:
    """Blacklist configuration for filtering jobs."""
    about_company_bad_words: List[str] = field(default_factory=list)
    about_company_good_words: List[str] = field(default_factory=list)
    bad_words: List[str] = field(default_factory=list)
    contextual_bad_words: List[str] = field(default_factory=list)
    security_clearance: bool = False
    did_masters: bool = False
    current_experience: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "about_company_bad_words": self.about_company_bad_words,
            "about_company_good_words": self.about_company_good_words,
            "bad_words": self.bad_words,
            "contextual_bad_words": self.contextual_bad_words,
            "security_clearance": self.security_clearance,
            "did_masters": self.did_masters,
            "current_experience": self.current_experience
        }


@dataclass 
class BotSettings:
    """Bot behavior settings."""
    close_tabs: bool = False
    follow_companies: bool = False
    run_non_stop: bool = False
    alternate_sortby: bool = True
    cycle_date_posted: bool = True
    stop_date_cycle_at_24hr: bool = True
    generated_resume_path: str = "../../data/resumes/"
    file_name: str = "all excels/all_applied_applications_history.csv"
    failed_file_name: str = "all excels/all_failed_applications_history.csv"
    logs_folder_path: str = "../../data/logs/"
    click_gap: int = 1
    run_in_background: bool = False
    disable_extensions: bool = False
    safe_mode: bool = False
    smooth_scroll: bool = False
    keep_screen_awake: bool = True
    stealth_mode: bool = False
    showAiErrorAlerts: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "close_tabs": self.close_tabs,
            "follow_companies": self.follow_companies,
            "run_non_stop": self.run_non_stop,
            "alternate_sortby": self.alternate_sortby,
            "cycle_date_posted": self.cycle_date_posted,
            "stop_date_cycle_at_24hr": self.stop_date_cycle_at_24hr,
            "paths": {
                "generated_resume_path": self.generated_resume_path,
                "file_name": self.file_name,
                "failed_file_name": self.failed_file_name,
                "logs_folder_path": self.logs_folder_path
            },
            "behavior": {
                "click_gap": self.click_gap,
                "run_in_background": self.run_in_background,
                "disable_extensions": self.disable_extensions,
                "safe_mode": self.safe_mode,
                "smooth_scroll": self.smooth_scroll,
                "keep_screen_awake": self.keep_screen_awake,
                "stealth_mode": self.stealth_mode,
                "showAiErrorAlerts": self.showAiErrorAlerts
            }
        }


class ConfigService:
    """
    Centralized configuration service for multi-tenant support.
    
    Loads configuration from multiple sources in priority order:
    1. Environment variables
    2. JSON config files (tenant/user specific)
    3. Legacy Python config files (for migration)
    4. Default values
    
    Usage:
        config = ConfigService(tenant_id="default", user_id="user-001")
        personal = config.get_personal_info()
        email, password = config.get_linkedin_credentials()
    """
    
    # Base paths
    PROJECT_ROOT = Path(__file__).parent.parent
    CONFIG_DIR = PROJECT_ROOT / "config"
    TENANTS_DIR = CONFIG_DIR / "tenants"
    
    def __init__(
        self,
        tenant_id: str = "default",
        user_id: Optional[str] = None,
        encryption_service: Optional[EncryptionService] = None
    ):
        """
        Initialize ConfigService.
        
        Args:
            tenant_id: Tenant identifier (for multi-tenant support)
            user_id: User identifier within tenant
            encryption_service: Optional custom encryption service
        """
        self.tenant_id = tenant_id or os.getenv('DEFAULT_TENANT_ID', 'default')
        self.user_id = user_id
        self._encryption = encryption_service or get_encryption_service()
        
        # Config cache
        self._config_cache: Dict[str, Any] = {}
        self._loaded = False
        
        # Paths
        self.tenant_dir = self.TENANTS_DIR / self.tenant_id
        self.user_config_path = self.tenant_dir / f"user_{user_id}.json" if user_id else None
        self.tenant_config_path = self.tenant_dir / "tenant_config.json"
        
        logger.info(f"ConfigService initialized for tenant={tenant_id}, user={user_id}")
    
    def _ensure_tenant_dir(self) -> None:
        """Create tenant directory if it doesn't exist."""
        self.tenant_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_json_file(self, path: Path) -> Dict[str, Any]:
        """Load JSON configuration file."""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
        return {}
    
    def _save_json_file(self, path: Path, data: Dict[str, Any]) -> bool:
        """Save configuration to JSON file."""
        try:
            self._ensure_tenant_dir()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")
            return False
    
    def _load_legacy_python_config(self, module_name: str) -> Dict[str, Any]:
        """
        Load configuration from legacy Python config files.
        Used for migration from old config/*.py format.
        
        Args:
            module_name: Name of config module (e.g., 'personals', 'secrets')
            
        Returns:
            dict: Module variables as dictionary
        """
        try:
            import importlib
            module = importlib.import_module(f"config.{module_name}")
            
            # Extract public variables (not starting with _)
            config = {}
            for name in dir(module):
                if not name.startswith('_'):
                    value = getattr(module, name)
                    # Only include simple types
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        config[name] = value
            
            return config
        except ImportError as e:
            logger.debug(f"Legacy config module {module_name} not found: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Error loading legacy config {module_name}: {e}")
            return {}
    
    def _get_env_value(self, key: str, default: Any = None) -> Any:
        """Get value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        
        # Type conversion based on default value type
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes')
        if isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        if isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default
        if isinstance(default, list):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.split(',') if value else default
        
        return value
    
    def load_all_config(self) -> Dict[str, Any]:
        """
        Load all configuration from all sources.
        
        Returns:
            dict: Merged configuration from all sources
        """
        if self._loaded and self._config_cache:
            return self._config_cache
        
        config = {}
        
        # 1. Load legacy Python configs (lowest priority)
        legacy_modules = ['personals', 'secrets', 'search', 'settings', 'questions']
        for module in legacy_modules:
            legacy_config = self._load_legacy_python_config(module)
            config[module] = legacy_config
        
        # 2. Load tenant JSON config
        tenant_config = self._load_json_file(self.tenant_config_path)
        if tenant_config:
            self._deep_merge(config, tenant_config)
        
        # 3. Load user JSON config
        if self.user_config_path:
            user_config = self._load_json_file(self.user_config_path)
            if user_config:
                self._deep_merge(config, user_config)
        
        # 4. Override with environment variables
        env_overrides = self._load_env_overrides()
        self._deep_merge(config, env_overrides)
        
        self._config_cache = config
        self._loaded = True
        
        return config
    
    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides = {}
        
        # Map environment variables to config structure
        env_mappings = {
            'LINKEDIN_EMAIL': ('secrets', 'username'),
            'LINKEDIN_PASSWORD': ('secrets', 'password'),
            'OPENAI_API_KEY': ('secrets', 'llm_api_key'),
            'DEFAULT_AI_PROVIDER': ('secrets', 'ai_provider'),
            'SEARCH_LOCATION': ('search', 'search_location'),
            'MAX_APPLICATIONS_PER_DAY': ('settings', 'max_applications'),
        }
        
        for env_key, (section, config_key) in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                if section not in overrides:
                    overrides[section] = {}
                overrides[section][config_key] = value
        
        return overrides
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict (in-place)."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    # ==================== Public API ====================
    
    def get_personal_info(self) -> PersonalInfo:
        """
        Get user personal information.
        
        Returns:
            PersonalInfo: Dataclass with personal information
        """
        config = self.load_all_config()
        personals = config.get('personals', {})
        
        return PersonalInfo(
            first_name=personals.get('first_name', ''),
            middle_name=personals.get('middle_name', ''),
            last_name=personals.get('last_name', ''),
            phone_number=personals.get('phone_number', ''),
            current_city=personals.get('current_city', ''),
            street=personals.get('street', ''),
            state=personals.get('state', ''),
            zipcode=personals.get('zipcode', ''),
            country=personals.get('country', ''),
            ethnicity=personals.get('ethnicity', 'Decline'),
            gender=personals.get('gender', 'Decline'),
            disability_status=personals.get('disability_status', 'Decline'),
            veteran_status=personals.get('veteran_status', 'Decline')
        )
    
    def get_linkedin_credentials(self) -> Tuple[str, str]:
        """
        Get decrypted LinkedIn credentials.
        
        Returns:
            tuple: (email, password) - password is decrypted
        """
        config = self.load_all_config()
        secrets = config.get('secrets', {})
        
        email = secrets.get('username', '')
        password = secrets.get('password', '')
        
        # Decrypt if encrypted
        if self._encryption.is_encrypted(password):
            password = self._encryption.decrypt(password)
        
        return email, password
    
    def get_search_preferences(self) -> SearchPreferences:
        """
        Get job search preferences and filters.
        
        Returns:
            SearchPreferences: Dataclass with search preferences
        """
        config = self.load_all_config()
        search = config.get('search', {})
        
        return SearchPreferences(
            search_terms=search.get('search_terms', []),
            search_location=search.get('search_location', ''),
            switch_number=search.get('switch_number', 20),
            randomize_search_order=search.get('randomize_search_order', False),
            sort_by=search.get('sort_by', 'Most recent'),
            date_posted=search.get('date_posted', 'Past 24 hours'),
            salary=search.get('salary', ''),
            easy_apply_only=search.get('easy_apply_only', True),
            experience_level=search.get('experience_level', []),
            job_type=search.get('job_type', []),
            on_site=search.get('on_site', []),
            companies=search.get('companies', []),
            location=search.get('location', []),
            industry=search.get('industry', []),
            job_function=search.get('job_function', []),
            job_titles=search.get('job_titles', []),
            benefits=search.get('benefits', []),
            commitments=search.get('commitments', []),
            under_10_applicants=search.get('under_10_applicants', False),
            in_your_network=search.get('in_your_network', False),
            fair_chance_employer=search.get('fair_chance_employer', False),
            pause_after_filters=search.get('pause_after_filters', True)
        )
    
    def get_experience_map(self) -> Dict[str, str]:
        """
        Get technology experience mapping.
        
        Returns:
            dict: Technology name -> years of experience
        """
        config = self.load_all_config()
        questions = config.get('questions', {})
        return questions.get('experience_by_technology', {})
    
    def get_blacklist(self) -> BlacklistConfig:
        """
        Get blacklist configuration for job filtering.
        
        Returns:
            BlacklistConfig: Dataclass with blacklist settings
        """
        config = self.load_all_config()
        search = config.get('search', {})
        
        return BlacklistConfig(
            about_company_bad_words=search.get('about_company_bad_words', []),
            about_company_good_words=search.get('about_company_good_words', []),
            bad_words=search.get('bad_words', []),
            contextual_bad_words=search.get('contextual_bad_words', []),
            security_clearance=search.get('security_clearance', False),
            did_masters=search.get('did_masters', False),
            current_experience=search.get('current_experience', 5)
        )
    
    def get_settings(self) -> BotSettings:
        """
        Get bot behavior settings.
        
        Returns:
            BotSettings: Dataclass with bot settings
        """
        config = self.load_all_config()
        settings = config.get('settings', {})
        
        return BotSettings(
            close_tabs=settings.get('close_tabs', False),
            follow_companies=settings.get('follow_companies', False),
            run_non_stop=settings.get('run_non_stop', False),
            alternate_sortby=settings.get('alternate_sortby', True),
            cycle_date_posted=settings.get('cycle_date_posted', True),
            stop_date_cycle_at_24hr=settings.get('stop_date_cycle_at_24hr', True),
            generated_resume_path=settings.get('generated_resume_path', '../../data/resumes/'),
            file_name=settings.get('file_name', 'all excels/all_applied_applications_history.csv'),
            failed_file_name=settings.get('failed_file_name', 'all excels/all_failed_applications_history.csv'),
            logs_folder_path=settings.get('logs_folder_path', '../../data/logs/'),
            click_gap=settings.get('click_gap', 1),
            run_in_background=settings.get('run_in_background', False),
            disable_extensions=settings.get('disable_extensions', False),
            safe_mode=settings.get('safe_mode', False),
            smooth_scroll=settings.get('smooth_scroll', False),
            keep_screen_awake=settings.get('keep_screen_awake', True),
            stealth_mode=settings.get('stealth_mode', False),
            showAiErrorAlerts=settings.get('showAiErrorAlerts', False)
        )
    
    def get_ai_config(self) -> Dict[str, Any]:
        """
        Get AI/LLM configuration.
        
        Returns:
            dict: AI configuration with decrypted API keys
        """
        config = self.load_all_config()
        secrets = config.get('secrets', {})
        
        api_key = secrets.get('llm_api_key', '')
        if self._encryption.is_encrypted(api_key):
            api_key = self._encryption.decrypt(api_key)
        
        return {
            "use_ai": secrets.get('use_AI', False),
            "provider": secrets.get('ai_provider', 'openai'),
            "api_url": secrets.get('llm_api_url', 'https://api.openai.com/v1/'),
            "api_key": api_key,
            "model": secrets.get('llm_model', 'gpt-4o-mini'),
            "spec": secrets.get('llm_spec', 'openai'),
            "stream_output": secrets.get('stream_output', False)
        }
    
    def get_resume_paths(self) -> Dict[str, str]:
        """
        Get resume file paths.
        
        Returns:
            dict: Resume path configurations
        """
        config = self.load_all_config()
        questions = config.get('questions', {})
        
        return {
            "default": questions.get('default_resume_path', ''),
            "national": questions.get('resume_national', ''),
            "international": questions.get('resume_international', '')
        }
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary.
        Sensitive values are masked.
        
        Returns:
            dict: Complete configuration (passwords masked)
        """
        personal = self.get_personal_info()
        search = self.get_search_preferences()
        blacklist = self.get_blacklist()
        settings = self.get_settings()
        ai = self.get_ai_config()
        
        # Mask sensitive values
        ai_masked = ai.copy()
        if ai_masked.get('api_key'):
            ai_masked['api_key'] = ai_masked['api_key'][:8] + '...' if len(ai_masked.get('api_key', '')) > 8 else '***'
        
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "personal_info": personal.to_dict(),
            "search_preferences": search.to_dict(),
            "blacklist": blacklist.to_dict(),
            "settings": settings.to_dict(),
            "ai_config": ai_masked,
            "resume_paths": self.get_resume_paths(),
            "experience_map": self.get_experience_map()
        }
    
    # ==================== Save Methods ====================
    
    def save_user_config(self, config: Dict[str, Any]) -> bool:
        """
        Save user configuration to JSON file.
        Encrypts sensitive fields before saving.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            bool: True if saved successfully
        """
        if not self.user_config_path:
            logger.error("Cannot save config: user_id not set")
            return False
        
        # Encrypt sensitive fields
        sensitive_keys = ['password', 'llm_api_key', 'api_key']
        encrypted_config = self._encryption.encrypt_dict(config, keys_to_encrypt=sensitive_keys)
        
        return self._save_json_file(self.user_config_path, encrypted_config)
    
    def update_credentials(self, email: str, password: str) -> bool:
        """
        Update LinkedIn credentials (encrypted).
        
        Args:
            email: LinkedIn email
            password: LinkedIn password (will be encrypted)
            
        Returns:
            bool: True if saved successfully
        """
        encrypted_credentials = self._encryption.encrypt_credentials(email, password)
        
        # Load existing config
        config = self.load_all_config()
        if 'secrets' not in config:
            config['secrets'] = {}
        
        config['secrets']['username'] = encrypted_credentials['email']
        config['secrets']['password'] = encrypted_credentials['password']
        
        # Clear cache to reload
        self._config_cache = {}
        self._loaded = False
        
        return self.save_user_config(config)
    
    def clear_cache(self) -> None:
        """Clear configuration cache to force reload."""
        self._config_cache = {}
        self._loaded = False


# Singleton instance
_config_service: Optional[ConfigService] = None


def get_config_service(
    tenant_id: str = "default",
    user_id: Optional[str] = None
) -> ConfigService:
    """
    Get ConfigService instance.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        
    Returns:
        ConfigService: Service instance
    """
    global _config_service
    
    # Return cached if same tenant/user
    if _config_service and _config_service.tenant_id == tenant_id and _config_service.user_id == user_id:
        return _config_service
    
    _config_service = ConfigService(tenant_id=tenant_id, user_id=user_id)
    return _config_service


if __name__ == "__main__":
    # Quick test
    print("Testing ConfigService...")
    print("=" * 50)
    
    config = ConfigService(tenant_id="default")
    
    # Test personal info
    personal = config.get_personal_info()
    print(f"\nPersonal Info:")
    print(f"  Name: {personal.full_name}")
    print(f"  Phone: {personal.phone_number}")
    print(f"  City: {personal.current_city}")
    
    # Test search preferences
    search = config.get_search_preferences()
    print(f"\nSearch Preferences:")
    print(f"  Terms: {search.search_terms[:3]}...")
    print(f"  Location: {search.search_location}")
    
    # Test credentials (masked)
    email, password = config.get_linkedin_credentials()
    print(f"\nLinkedIn Credentials:")
    print(f"  Email: {email}")
    print(f"  Password: {'*' * len(password) if password else 'Not set'}")
    
    # Test AI config
    ai = config.get_ai_config()
    print(f"\nAI Config:")
    print(f"  Provider: {ai['provider']}")
    print(f"  Model: {ai['model']}")
    
    print("\n" + "=" * 50)
    print("ConfigService test complete!")
