"""
Database seeding and data migration script.
Migrates data from CSV files and legacy configs to the new database.

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --tenant-id=my-company
    python scripts/seed_database.py --skip-applications
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.database import init_db, get_db_session, engine, Base
from backend.core.models import Tenant, User, JobApplication, QuestionBank, BotRunLog
from backend.core.encryption_service import EncryptionService
from backend.core.config_service import ConfigService


def create_default_tenant(db, tenant_id: str = "default") -> Tenant:
    """
    Create or get the default tenant.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        
    Returns:
        Tenant: Created or existing tenant
    """
    print(f"\n🏢 Setting up tenant: {tenant_id}")
    
    # Check if tenant exists
    existing = db.query(Tenant).filter(Tenant.slug == tenant_id).first()
    if existing:
        print(f"   ✅ Tenant already exists: {existing.name}")
        return existing
    
    # Create new tenant
    tenant = Tenant(
        slug=tenant_id,
        name="LinkedIn Job Bot" if tenant_id == "default" else tenant_id.replace('-', ' ').title(),
        branding={
            "logo_url": "",
            "company_name": "LinkedIn Job Bot",
            "colors": {
                "primary": "#0077B5",
                "secondary": "#00A0DC",
                "accent": "#313335"
            },
            "theme": "light"
        },
        features={
            "max_users": 100,
            "max_applications_per_day": 200,
            "ai_enabled": True,
            "custom_domain": False
        },
        settings={
            "timezone": "America/Sao_Paulo",
            "language": "pt-BR",
            "notification_email": ""
        },
        billing_plan="free",
        status="active"
    )
    
    db.add(tenant)
    db.flush()  # Get the ID
    
    print(f"   ✅ Created tenant: {tenant.name} (ID: {tenant.id})")
    return tenant


def create_default_user(
    db,
    tenant: Tenant,
    config: ConfigService,
    encryption: EncryptionService
) -> User:
    """
    Create default user from legacy config.
    
    Args:
        db: Database session
        tenant: Parent tenant
        config: ConfigService instance
        encryption: EncryptionService instance
        
    Returns:
        User: Created or existing user
    """
    print(f"\n👤 Setting up default user...")
    
    # Get credentials
    email, password = config.get_linkedin_credentials()
    
    if not email:
        print("   ⚠️  No LinkedIn email found in config")
        email = "user@example.com"
    
    # Check if user exists
    existing = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.email == email
    ).first()
    
    if existing:
        print(f"   ✅ User already exists: {existing.email}")
        return existing
    
    # Get personal info
    personal = config.get_personal_info()
    search = config.get_search_preferences()
    settings = config.get_settings()
    
    # Encrypt LinkedIn password
    encrypted_credentials = {
        "email": email,
        "password": encryption.encrypt(password) if password else ""
    }
    
    # Create user
    user = User(
        tenant_id=tenant.id,
        email=email,
        personal_info=personal.to_dict(),
        linkedin_credentials=encrypted_credentials,
        search_preferences=search.to_dict(),
        question_answers={
            "experience_by_technology": config.get_experience_map(),
            "years_of_experience": "5"
        },
        resume_config=config.get_resume_paths(),
        bot_settings=settings.to_dict(),
        status="active",
        is_admin=True
    )
    
    db.add(user)
    db.flush()
    
    print(f"   ✅ Created user: {user.email} (ID: {user.id})")
    print(f"      Name: {personal.full_name}")
    print(f"      City: {personal.current_city}")
    
    return user


def migrate_applications_from_csv(
    db,
    user: User,
    tenant: Tenant,
    csv_path: Path
) -> int:
    """
    Migrate job applications from CSV file.
    
    Args:
        db: Database session
        user: User to associate applications with
        tenant: Tenant
        csv_path: Path to CSV file
        
    Returns:
        int: Number of applications migrated
    """
    print(f"\n📄 Migrating applications from: {csv_path.name}")
    
    if not csv_path.exists():
        print(f"   ⚠️  File not found: {csv_path}")
        return 0
    
    # Set larger field size limit for CSV
    csv.field_size_limit(1000000)
    
    count = 0
    skipped = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    job_id = row.get('Job ID', '')
                    
                    # Skip if already exists
                    if job_id:
                        existing = db.query(JobApplication).filter(
                            JobApplication.linkedin_job_id == job_id,
                            JobApplication.user_id == user.id
                        ).first()
                        
                        if existing:
                            skipped += 1
                            continue
                    
                    # Parse date
                    date_str = row.get('Date Applied', '')
                    applied_at = None
                    if date_str and date_str != 'Pending':
                        try:
                            applied_at = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                applied_at = datetime.strptime(date_str, '%Y-%m-%d')
                            except ValueError:
                                applied_at = datetime.utcnow()
                    
                    # Determine application type
                    external_link = row.get('External Job link', '')
                    app_type = "easy_apply" if external_link == "Easy Applied" else "external"
                    
                    # Create application record
                    application = JobApplication(
                        user_id=user.id,
                        tenant_id=tenant.id,
                        linkedin_job_id=job_id,
                        title=row.get('Title', '')[:500] if row.get('Title') else None,
                        company=row.get('Company', '')[:255] if row.get('Company') else None,
                        location=row.get('Location', '')[:255] if row.get('Location') else None,
                        job_link=row.get('Job Link', ''),
                        external_job_link=external_link if external_link != "Easy Applied" else None,
                        hr_name=row.get('HR Name', ''),
                        hr_link=row.get('HR Link', ''),
                        status="applied",
                        application_type=app_type,
                        applied_at=applied_at or datetime.utcnow(),
                        extra_data={
                            "migrated_from": "csv",
                            "original_date": date_str
                        }
                    )
                    
                    db.add(application)
                    count += 1
                    
                    # Commit in batches
                    if count % 100 == 0:
                        db.flush()
                        print(f"      Processed {count} applications...")
                        
                except Exception as e:
                    print(f"   ⚠️  Error processing row: {e}")
                    continue
        
        db.flush()
        print(f"   ✅ Migrated {count} applications ({skipped} skipped as duplicates)")
        
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
        return 0
    
    return count


def migrate_failed_applications(
    db,
    user: User,
    tenant: Tenant,
    csv_path: Path
) -> int:
    """
    Migrate failed job applications from CSV file.
    
    Args:
        db: Database session
        user: User to associate applications with
        tenant: Tenant
        csv_path: Path to failed applications CSV
        
    Returns:
        int: Number of failed applications migrated
    """
    print(f"\n📄 Migrating failed applications from: {csv_path.name}")
    
    if not csv_path.exists():
        print(f"   ⚠️  File not found: {csv_path}")
        return 0
    
    csv.field_size_limit(1000000)
    count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    job_id = row.get('Job ID', '')
                    
                    # Parse date
                    date_str = row.get('Date Tried', '')
                    tried_at = None
                    if date_str:
                        try:
                            tried_at = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            tried_at = datetime.utcnow()
                    
                    application = JobApplication(
                        user_id=user.id,
                        tenant_id=tenant.id,
                        linkedin_job_id=job_id,
                        title=row.get('Title', '')[:500] if row.get('Title') else None,
                        company=row.get('Company', '')[:255] if row.get('Company') else None,
                        job_link=row.get('Job Link', ''),
                        status="failed",
                        application_type="easy_apply",
                        error_message=row.get('Fail Reason', ''),
                        applied_at=tried_at or datetime.utcnow(),
                        extra_data={
                            "migrated_from": "failed_csv"
                        }
                    )
                    
                    db.add(application)
                    count += 1
                    
                    if count % 100 == 0:
                        db.flush()
                        
                except Exception as e:
                    continue
        
        db.flush()
        print(f"   ✅ Migrated {count} failed applications")
        
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
        return 0
    
    return count


def migrate_questions_bank(db, json_path: Path) -> int:
    """
    Migrate questions from questions_bank.json.
    
    Args:
        db: Database session
        json_path: Path to questions_bank.json
        
    Returns:
        int: Number of questions migrated
    """
    print(f"\n❓ Migrating questions bank from: {json_path.name}")
    
    if not json_path.exists():
        print(f"   ⚠️  File not found: {json_path}")
        return 0
    
    count = 0
    skipped = 0
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        for q_hash, q_data in questions.items():
            # Check if exists
            existing = db.query(QuestionBank).filter(
                QuestionBank.question_hash == q_hash
            ).first()
            
            if existing:
                # Update times_seen
                existing.times_seen = max(existing.times_seen, q_data.get('times_seen', 1))
                existing.last_seen_at = datetime.utcnow()
                skipped += 1
                continue
            
            # Create new question
            question = QuestionBank(
                question_hash=q_hash,
                label=q_data.get('label', ''),
                normalized_label=q_data.get('normalized_label', ''),
                question_type=q_data.get('type', 'text'),
                default_answer=q_data.get('answer', ''),
                options=q_data.get('options', []),
                times_seen=q_data.get('times_seen', 1),
                verified=q_data.get('verified', False)
            )
            
            # Parse dates
            if q_data.get('first_seen'):
                try:
                    question.first_seen_at = datetime.fromisoformat(q_data['first_seen'])
                except:
                    pass
            
            if q_data.get('last_seen'):
                try:
                    question.last_seen_at = datetime.fromisoformat(q_data['last_seen'])
                except:
                    pass
            
            db.add(question)
            count += 1
            
            if count % 500 == 0:
                db.flush()
                print(f"      Processed {count} questions...")
        
        db.flush()
        print(f"   ✅ Migrated {count} questions ({skipped} updated)")
        
    except Exception as e:
        print(f"   ❌ Error migrating questions: {e}")
        return 0
    
    return count


def run_seed(
    tenant_id: str = "default",
    skip_applications: bool = False,
    skip_questions: bool = False
) -> bool:
    """
    Run the complete database seeding process.
    
    Args:
        tenant_id: Tenant identifier
        skip_applications: Skip migrating job applications
        skip_questions: Skip migrating questions bank
        
    Returns:
        bool: True if successful
    """
    print("=" * 60)
    print("🌱 LinkedIn Bot - Database Seeding")
    print("=" * 60)
    print(f"\nTenant ID: {tenant_id}")
    print(f"Skip applications: {skip_applications}")
    print(f"Skip questions: {skip_questions}")
    
    # Initialize database
    print("\n📦 Initializing database...")
    init_db()
    print("   ✅ Database tables created")
    
    # Setup services
    encryption = EncryptionService()
    config = ConfigService(tenant_id=tenant_id)
    
    # Paths
    excels_path = PROJECT_ROOT / "all excels"
    data_path = PROJECT_ROOT / "data"
    
    with get_db_session() as db:
        try:
            # Create tenant
            tenant = create_default_tenant(db, tenant_id)
            
            # Create user
            user = create_default_user(db, tenant, config, encryption)
            
            # Migrate applications
            if not skip_applications:
                # Applied applications
                applied_csv = excels_path / "all_applied_applications_history.csv"
                applied_count = migrate_applications_from_csv(db, user, tenant, applied_csv)
                
                # Failed applications
                failed_csv = excels_path / "all_failed_applications_history.csv"
                failed_count = migrate_failed_applications(db, user, tenant, failed_csv)
                
                # Update user stats
                user.total_applications = applied_count + failed_count
            
            # Migrate questions
            if not skip_questions:
                questions_json = data_path / "questions_bank.json"
                migrate_questions_bank(db, questions_json)
            
            # Commit all changes
            db.commit()
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 Seeding Summary")
            print("=" * 60)
            
            tenant_count = db.query(Tenant).count()
            user_count = db.query(User).count()
            app_count = db.query(JobApplication).count()
            question_count = db.query(QuestionBank).count()
            
            print(f"  Tenants: {tenant_count}")
            print(f"  Users: {user_count}")
            print(f"  Job Applications: {app_count}")
            print(f"  Questions: {question_count}")
            
            print("\n✅ Database seeding completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            db.rollback()
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Seed database with initial data"
    )
    parser.add_argument(
        '--tenant-id',
        default='default',
        help='Tenant identifier (default: default)'
    )
    parser.add_argument(
        '--skip-applications',
        action='store_true',
        help='Skip migrating job applications from CSV'
    )
    parser.add_argument(
        '--skip-questions',
        action='store_true',
        help='Skip migrating questions bank'
    )
    
    args = parser.parse_args()
    
    success = run_seed(
        tenant_id=args.tenant_id,
        skip_applications=args.skip_applications,
        skip_questions=args.skip_questions
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
