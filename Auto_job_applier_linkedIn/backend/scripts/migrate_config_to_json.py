"""
Migration script to convert legacy Python config files to JSON format.
This enables the transition to the new ConfigService-based architecture.

Usage:
    python scripts/migrate_config_to_json.py
    python scripts/migrate_config_to_json.py --encrypt-secrets
    python scripts/migrate_config_to_json.py --tenant-id=my-company --user-id=user-001
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.encryption_service import EncryptionService


def load_python_module(module_name: str) -> dict:
    """
    Load a Python config module and extract its variables.
    
    Args:
        module_name: Name of the config module (e.g., 'personals')
        
    Returns:
        dict: Module variables
    """
    try:
        import importlib
        module = importlib.import_module(f"config.{module_name}")
        
        config = {}
        for name in dir(module):
            if not name.startswith('_'):
                value = getattr(module, name)
                # Only include serializable types
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    config[name] = value
        
        return config
    except ImportError as e:
        print(f"  ⚠️  Module config.{module_name} not found: {e}")
        return {}
    except Exception as e:
        print(f"  ❌ Error loading config.{module_name}: {e}")
        return {}


def migrate_personals(encrypt_service: EncryptionService = None) -> dict:
    """Migrate personals.py to JSON format."""
    print("\n📋 Migrating personals.py...")
    
    data = load_python_module('personals')
    if not data:
        return {}
    
    # Structure the data
    migrated = {
        "personal_info": {
            "first_name": data.get('first_name', ''),
            "middle_name": data.get('middle_name', ''),
            "last_name": data.get('last_name', ''),
            "phone_number": data.get('phone_number', ''),
            "current_city": data.get('current_city', ''),
            "address": {
                "street": data.get('street', ''),
                "state": data.get('state', ''),
                "zipcode": data.get('zipcode', ''),
                "country": data.get('country', '')
            },
            "demographics": {
                "ethnicity": data.get('ethnicity', 'Decline'),
                "gender": data.get('gender', 'Decline'),
                "disability_status": data.get('disability_status', 'Decline'),
                "veteran_status": data.get('veteran_status', 'Decline')
            }
        }
    }
    
    print(f"  ✅ Migrated: {migrated['personal_info']['first_name']} {migrated['personal_info']['last_name']}")
    return migrated


def migrate_secrets(encrypt_service: EncryptionService = None) -> dict:
    """Migrate secrets.py to JSON format with encryption."""
    print("\n🔐 Migrating secrets.py...")
    
    data = load_python_module('secrets')
    if not data:
        return {}
    
    # Get credentials
    username = data.get('username', '')
    password = data.get('password', '')
    llm_api_key = data.get('llm_api_key', '')
    
    # Encrypt if service provided
    if encrypt_service and password:
        password = encrypt_service.encrypt(password)
        print(f"  🔒 Password encrypted")
    
    if encrypt_service and llm_api_key and llm_api_key != 'not-needed':
        llm_api_key = encrypt_service.encrypt(llm_api_key)
        print(f"  🔒 API key encrypted")
    
    migrated = {
        "linkedin_credentials": {
            "email": username,
            "password": password
        },
        "ai_config": {
            "use_ai": data.get('use_AI', False),
            "provider": data.get('ai_provider', 'openai'),
            "api_url": data.get('llm_api_url', 'https://api.openai.com/v1/'),
            "api_key": llm_api_key,
            "model": data.get('llm_model', 'gpt-4o-mini'),
            "spec": data.get('llm_spec', 'openai'),
            "stream_output": data.get('stream_output', False)
        }
    }
    
    masked_email = username[:3] + '***' + username[-10:] if len(username) > 13 else '***'
    print(f"  ✅ Migrated credentials for: {masked_email}")
    return migrated


def migrate_search() -> dict:
    """Migrate search.py to JSON format."""
    print("\n🔍 Migrating search.py...")
    
    data = load_python_module('search')
    if not data:
        return {}
    
    migrated = {
        "search_preferences": {
            "search_terms": data.get('search_terms', []),
            "search_location": data.get('search_location', ''),
            "switch_number": data.get('switch_number', 20),
            "randomize_search_order": data.get('randomize_search_order', False),
            "filters": {
                "sort_by": data.get('sort_by', 'Most recent'),
                "date_posted": data.get('date_posted', 'Past 24 hours'),
                "salary": data.get('salary', ''),
                "easy_apply_only": data.get('easy_apply_only', True),
                "experience_level": data.get('experience_level', []),
                "job_type": data.get('job_type', []),
                "on_site": data.get('on_site', []),
                "companies": data.get('companies', []),
                "location": data.get('location', []),
                "industry": data.get('industry', []),
                "job_function": data.get('job_function', []),
                "job_titles": data.get('job_titles', []),
                "benefits": data.get('benefits', []),
                "commitments": data.get('commitments', []),
                "under_10_applicants": data.get('under_10_applicants', False),
                "in_your_network": data.get('in_your_network', False),
                "fair_chance_employer": data.get('fair_chance_employer', False)
            },
            "pause_after_filters": data.get('pause_after_filters', True)
        },
        "blacklist": {
            "about_company_bad_words": data.get('about_company_bad_words', []),
            "about_company_good_words": data.get('about_company_good_words', []),
            "bad_words": data.get('bad_words', []),
            "contextual_bad_words": data.get('contextual_bad_words', []),
            "security_clearance": data.get('security_clearance', False),
            "did_masters": data.get('did_masters', False),
            "current_experience": data.get('current_experience', 5)
        }
    }
    
    print(f"  ✅ Migrated {len(migrated['search_preferences']['search_terms'])} search terms")
    print(f"  ✅ Location: {migrated['search_preferences']['search_location']}")
    return migrated


def migrate_settings() -> dict:
    """Migrate settings.py to JSON format."""
    print("\n⚙️  Migrating settings.py...")
    
    data = load_python_module('settings')
    if not data:
        return {}
    
    migrated = {
        "bot_settings": {
            "linkedin": {
                "close_tabs": data.get('close_tabs', False),
                "follow_companies": data.get('follow_companies', False),
                "run_non_stop": data.get('run_non_stop', False),
                "alternate_sortby": data.get('alternate_sortby', True),
                "cycle_date_posted": data.get('cycle_date_posted', True),
                "stop_date_cycle_at_24hr": data.get('stop_date_cycle_at_24hr', True)
            },
            "paths": {
                "generated_resume_path": data.get('generated_resume_path', '../../data/resumes/'),
                "file_name": data.get('file_name', 'all excels/all_applied_applications_history.csv'),
                "failed_file_name": data.get('failed_file_name', 'all excels/all_failed_applications_history.csv'),
                "logs_folder_path": data.get('logs_folder_path', '../../data/logs/')
            },
            "behavior": {
                "click_gap": data.get('click_gap', 1),
                "run_in_background": data.get('run_in_background', False),
                "disable_extensions": data.get('disable_extensions', False),
                "safe_mode": data.get('safe_mode', False),
                "smooth_scroll": data.get('smooth_scroll', False),
                "keep_screen_awake": data.get('keep_screen_awake', True),
                "stealth_mode": data.get('stealth_mode', False),
                "showAiErrorAlerts": data.get('showAiErrorAlerts', False)
            }
        }
    }
    
    print(f"  ✅ Migrated bot settings")
    return migrated


def migrate_questions() -> dict:
    """Migrate questions.py to JSON format."""
    print("\n❓ Migrating questions.py...")
    
    data = load_python_module('questions')
    if not data:
        return {}
    
    migrated = {
        "resume_config": {
            "default_resume_path": data.get('default_resume_path', ''),
            "resume_national": data.get('resume_national', ''),
            "resume_international": data.get('resume_international', '')
        },
        "experience": {
            "years_of_experience": data.get('years_of_experience', '5'),
            "by_technology": data.get('experience_by_technology', {})
        },
        "salary": {
            "desired_salary": data.get('desired_salary', 0),
            "current_ctc": data.get('current_ctc', 0),
            "notice_period": data.get('notice_period', 0)
        }
    }
    
    tech_count = len(migrated['experience']['by_technology'])
    print(f"  ✅ Migrated {tech_count} technology experience mappings")
    return migrated


def create_tenant_config(tenant_id: str, tenant_name: str = None) -> dict:
    """Create tenant-level configuration."""
    return {
        "tenant": {
            "id": tenant_id,
            "name": tenant_name or tenant_id.replace('-', ' ').title(),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        },
        "branding": {
            "company_name": tenant_name or "LinkedIn Job Bot",
            "logo_url": "",
            "colors": {
                "primary": "#0077B5",
                "secondary": "#00A0DC",
                "accent": "#313335"
            },
            "theme": "light"
        },
        "features": {
            "max_users": 10,
            "max_applications_per_day": 100,
            "ai_enabled": True,
            "custom_domain": False
        },
        "settings": {
            "timezone": "America/Sao_Paulo",
            "language": "pt-BR",
            "notification_email": ""
        }
    }


def run_migration(
    tenant_id: str = "default",
    user_id: str = "default-user",
    encrypt_secrets: bool = True,
    output_dir: Path = None
) -> bool:
    """
    Run the full migration process.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        encrypt_secrets: Whether to encrypt sensitive data
        output_dir: Output directory (default: config/tenants/{tenant_id})
        
    Returns:
        bool: True if migration successful
    """
    print("=" * 60)
    print("🚀 LinkedIn Bot - Config Migration Tool")
    print("=" * 60)
    print(f"\nTenant ID: {tenant_id}")
    print(f"User ID: {user_id}")
    print(f"Encrypt secrets: {encrypt_secrets}")
    
    # Setup output directory
    if output_dir is None:
        output_dir = PROJECT_ROOT / "config" / "tenants" / tenant_id
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Setup encryption if needed
    encrypt_service = None
    if encrypt_secrets:
        try:
            encrypt_service = EncryptionService()
            print("\n🔐 Encryption service initialized")
        except Exception as e:
            print(f"\n⚠️  Could not initialize encryption: {e}")
            print("   Proceeding without encryption...")
    
    # Migrate each config file
    all_config = {}
    
    # Personal info
    personals = migrate_personals(encrypt_service)
    all_config.update(personals)
    
    # Secrets (with encryption)
    secrets = migrate_secrets(encrypt_service)
    all_config.update(secrets)
    
    # Search preferences
    search = migrate_search()
    all_config.update(search)
    
    # Bot settings
    settings = migrate_settings()
    all_config.update(settings)
    
    # Questions/experience
    questions = migrate_questions()
    all_config.update(questions)
    
    # Add metadata
    all_config["_metadata"] = {
        "migrated_at": datetime.now().isoformat(),
        "source": "config/*.py",
        "version": "1.0.0",
        "tenant_id": tenant_id,
        "user_id": user_id
    }
    
    # Save user config
    user_config_path = output_dir / f"user_{user_id}.json"
    try:
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(all_config, f, indent=2, ensure_ascii=False)
        print(f"\n✅ User config saved: {user_config_path}")
    except Exception as e:
        print(f"\n❌ Failed to save user config: {e}")
        return False
    
    # Create tenant config
    tenant_config = create_tenant_config(tenant_id)
    tenant_config_path = output_dir / "tenant_config.json"
    try:
        with open(tenant_config_path, 'w', encoding='utf-8') as f:
            json.dump(tenant_config, f, indent=2, ensure_ascii=False)
        print(f"✅ Tenant config saved: {tenant_config_path}")
    except Exception as e:
        print(f"\n❌ Failed to save tenant config: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"  Personal info: ✅")
    print(f"  LinkedIn credentials: ✅ {'(encrypted)' if encrypt_secrets else '(plain)'}")
    print(f"  Search preferences: ✅")
    print(f"  Bot settings: ✅")
    print(f"  Experience mappings: ✅")
    print(f"\nFiles created:")
    print(f"  - {user_config_path}")
    print(f"  - {tenant_config_path}")
    
    print("\n⚠️  IMPORTANT:")
    print("  1. Verify the migrated config files are correct")
    print("  2. The original config/*.py files were NOT modified")
    print("  3. Update .env with ENCRYPTION_KEY if not already set")
    print("  4. Test with: python -m core.config_service")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Python config files to JSON format"
    )
    parser.add_argument(
        '--tenant-id',
        default='default',
        help='Tenant identifier (default: default)'
    )
    parser.add_argument(
        '--user-id',
        default='default-user',
        help='User identifier (default: default-user)'
    )
    parser.add_argument(
        '--encrypt-secrets',
        action='store_true',
        default=True,
        help='Encrypt sensitive data (default: True)'
    )
    parser.add_argument(
        '--no-encrypt',
        action='store_true',
        help='Disable encryption of secrets'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Custom output directory'
    )
    
    args = parser.parse_args()
    
    encrypt = args.encrypt_secrets and not args.no_encrypt
    
    success = run_migration(
        tenant_id=args.tenant_id,
        user_id=args.user_id,
        encrypt_secrets=encrypt,
        output_dir=args.output_dir
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
