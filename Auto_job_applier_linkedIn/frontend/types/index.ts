export interface Tenant {
  id: string;
  slug: string;
  name: string;
  branding: {
    logo_url?: string;
    company_name?: string;
    colors: {
      primary: string;
      secondary: string;
      accent: string;
    };
    theme: string;
  };
  features: {
    max_users: number;
    max_applications_per_day: number;
    ai_enabled: boolean;
    custom_domain: boolean;
  };
  settings: {
    timezone: string;
    language: string;
    notification_email: string;
  };
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
}

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  personal_info: {
    first_name: string;
    middle_name?: string;
    last_name: string;
    full_name: string;
    phone_number: string;
    current_city: string;
  };
  search_preferences?: {
    search_terms: string[];
    location: string;
    experience_levels: string[];
  };
  status: 'active' | 'inactive' | 'suspended';
  is_admin: boolean;
  total_applications: number;
  last_application_at?: string;
  created_at: string;
}

export interface JobApplication {
  id: string;
  user_id: string;
  tenant_id: string;
  linkedin_job_id: string;
  title: string;
  company: string;
  location?: string;
  job_link: string;
  external_job_link?: string;
  hr_name?: string;
  hr_link?: string;
  status: 'applied' | 'failed' | 'skipped' | 'external';
  application_type: 'easy_apply' | 'external';
  error_message?: string;
  applied_at: string;
  created_at: string;
}

export interface QuestionStats {
  total_questions: number;
  verified_questions: number;
  unverified_questions: number;
  by_type: Record<string, number>;
}

export interface ApplicationStats {
  total_applications: number;
  successful_applications: number;
  failed_applications: number;
  success_rate: number;
  applications_today: number;
  applications_this_week: number;
  top_companies: Array<{ company: string; count: number }>;
}

export interface HealthStatus {
  status: string;
  database: {
    database_url: string;
    is_sqlite: boolean;
    connected: boolean;
    error?: string;
  };
  timestamp: string;
  version: string;
}
