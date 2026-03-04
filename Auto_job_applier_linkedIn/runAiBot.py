# Imports
import os
import csv
import re

# Try to import pyautogui, but handle headless environments gracefully
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    PYAUTOGUI_AVAILABLE = False
    print(f"Warning: pyautogui not available ({e}). GUI dialogs will use console instead.")

# Set CSV field size limit to prevent field size errors
csv.field_size_limit(1000000)  # Set to 1MB instead of default 131KB

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException, WebDriverException, StaleElementReferenceException

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password, ai_provider
from config.settings import *

# Explicit imports to ensure availability in all functions
from config.questions import cover_letter, linkedin_summary

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config

if use_AI:
    from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
    from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
    from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

from typing import Literal


if PYAUTOGUI_AVAILABLE:
    pyautogui.FAILSAFE = False

# Helper functions for GUI dialogs that work with or without display
def show_alert(text, title="Alert"):
    """Show an alert dialog, fallback to console if display unavailable"""
    if PYAUTOGUI_AVAILABLE:
        try:
            pyautogui.alert(text, title)
        except:
            print(f"\n[{title}]\n{text}\n")
    else:
        print(f"\n[{title}]\n{text}\n")

def show_confirm(text, title="Confirm", buttons=None):
    """Show a confirm dialog, fallback to console if display unavailable"""
    if buttons is None:
        buttons = ["Yes", "No"]
    
    if PYAUTOGUI_AVAILABLE:
        try:
            return pyautogui.confirm(text, title, buttons)
        except:
            pass
    
    print(f"\n[{title}]\n{text}")
    for i, btn in enumerate(buttons, 1):
        print(f"{i}. {btn}")
    
    while True:
        try:
            choice = input("Enter your choice (number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(buttons):
                return buttons[idx]
        except (ValueError, IndexError):
            pass
        print("Invalid choice. Please try again.")

# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Global Variables and logics

pause_at_failed_question = False
pause_before_submit = False

if run_in_background == True:
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
about_company_for_ai = None # TODO extract about company for AI
##<

#>

# Helper function to click buttons in both English and Portuguese
def click_button_multilang(element, button_texts: list[str], time: float=5.0) -> bool:
    '''
    Tries to click a button with text in multiple languages
    Returns True if clicked, False if not found
    '''
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    
    for text in button_texts:
        try:
            # Try span first (original method)
            if wait_span_click(element, text, time):
                print_lg(f"Clicked button (span): {text}")
                return True
        except:
            pass
        
        try:
            # Try button with aria-label
            button = WebDriverWait(element, time).until(
                EC.element_to_be_clickable((By.XPATH, f".//button[contains(@aria-label, '{text}')]"))
            )
            button.click()
            print_lg(f"Clicked button (aria-label): {text}")
            return True
        except:
            pass
            
        try:
            # Try button with text content
            button = WebDriverWait(element, time).until(
                EC.element_to_be_clickable((By.XPATH, f".//button[contains(., '{text}')]"))
            )
            button.click()
            print_lg(f"Clicked button (text): {text}")
            return True
        except:
            continue
    
    print_lg(f"Click Failed! Didn't find any of: {button_texts}")
    return False

#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    # Check if we're on a jobs search page while logged in
    if "/jobs/search" in driver.current_url and try_xp(driver, '//nav[@aria-label="Primary Navigation"]'): return True
    # If we can't determine, assume NOT logged in to force login attempt
    print_lg("Could not determine login status, will attempt login...")
    return False


def login_LN() -> None:
    '''
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from `secrets.py`
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    '''
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    
    # Wait a bit for page to load
    buffer(2)
    
    # Try to close any popups that might be blocking
    try:
        close_button = driver.find_element(By.XPATH, '//button[@aria-label="Dismiss" or @data-test-modal-close-btn]')
        close_button.click()
        print_lg("Closed popup")
        buffer(1)
    except:
        pass
    
    try:
        # Wait for login page to load
        buffer(2)
        
        # Try to find and fill username field
        try:
            username_field = driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            print_lg(f"Filled username: {username}")
        except:
            try:
                # Alternative selector for email field
                username_field = driver.find_element(By.XPATH, "//input[@name='session_key' or @autocomplete='username']")
                username_field.clear()
                username_field.send_keys(username)
                print_lg(f"Filled username (alternative): {username}")
            except Exception as e:
                print_lg(f"Couldn't find username field: {e}")
        
        # Try to find and fill password field
        try:
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            print_lg("Filled password")
        except:
            try:
                # Alternative selector for password field
                password_field = driver.find_element(By.XPATH, "//input[@name='session_password' or @type='password']")
                password_field.clear()
                password_field.send_keys(password)
                print_lg("Filled password (alternative)")
            except Exception as e:
                print_lg(f"Couldn't find password field: {e}")
        
        buffer(1)
        
        # Find and click the login button
        try:
            login_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Entrar")]')
            login_button.click()
            print_lg("Clicked login button")
        except:
            try:
                login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
                login_button.click()
                print_lg("Clicked login button (alternative)")
            except Exception as e:
                print_lg(f"Couldn't find login button: {e}")
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/")) # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)
#>



def get_applied_job_ids() -> set[str]:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids: set[str] = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



def set_search_location() -> None:
    '''
    Function to set search location
    '''
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False) #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!", e)


def apply_filters() -> None:
    '''
    Function to apply job search filters
    '''
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        # Garantir que o filtro "Candidatura simplificada" (Easy Apply) esteja ligado na barra superior
        # Esse botão existe fora do modal de "Todos os filtros". Em algumas contas não há o id fixo,
        # então tentamos por id OU por aria-label/texto, com espera explícita.
        def _dismiss_any_modal():
            try:
                overlay = driver.find_element(By.XPATH, '//div[@data-test-modal-container][@aria-hidden="false"]')
                try:
                    dismiss_btn = overlay.find_element(By.XPATH, './/button[@aria-label="Dismiss" or @aria-label="Fechar" or contains(@aria-label,"Descartar") or contains(@aria-label,"discard") or contains(@aria-label,"Close")]')
                    dismiss_btn.click()
                except Exception:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                buffer(1)
            except Exception:
                pass

        _dismiss_any_modal()

        if easy_apply_only:
            try:
                easy_apply_pill = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        '//button[@id="searchFilter_applyWithLinkedin" or contains(@aria-label, "Filtro Candidatura simplificada") or @aria-label="Filtro Candidatura simplificada."]'
                    ))
                )
                aria_pressed = (easy_apply_pill.get_attribute("aria-checked") or easy_apply_pill.get_attribute("aria-pressed") or "").lower()
                if aria_pressed != "true":
                    scroll_to_view(driver, easy_apply_pill)
                    easy_apply_pill.click()
                    buffer(1)
                    _dismiss_any_modal()
                    print_lg('Clicked top-bar "Candidatura simplificada" filter pill')
            except Exception as e:
                print_lg('Failed to click top-bar "Candidatura simplificada" filter pill, falling back to All filters modal', e)

        _dismiss_any_modal()

        # Em PT-BR o botão é "Todos os filtros". Em EN-US é "All filters".
        try:
            all_filters_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//button[normalize-space()="All filters" or normalize-space()="Todos os filtros"]'
            )))
            print_lg("✅ Found 'Todos os filtros' button, clicking...")
            all_filters_btn.click()
            print_lg("✅ Clicked 'Todos os filtros' button")
            buffer(2)  # Wait for modal to fully load
        except Exception as e:
            print_lg("❌ Failed to find/click 'Todos os filtros' button:", e)
            raise

        _ptbr = {
            "Most recent": "Mais recentes", "Most relevant": "Mais relevantes",
            "Any time": "A qualquer momento", "Past month": "Último mês",
            "Past week": "Última semana", "Past 24 hours": "Últimas 24 horas",
            "Internship": "Estágio", "Entry level": "Júnior",
            "Associate": "Analista", "Mid-Senior level": "Pleno-sênior",
            "Director": "Diretor", "Executive": "Executivo",
            "Full-time": "Tempo integral", "Part-time": "Meio período",
            "Contract": "Contrato", "Temporary": "Temporário",
            "Volunteer": "Voluntário", "Other": "Outro",
            "On-site": "Presencial", "Remote": "Remoto", "Hybrid": "Híbrido",
            "Easy Apply": "Candidatura simplificada",
            "Under 10 applicants": "Menos de 10 candidaturas",
            "In your network": "Na sua rede", "Fair Chance Employer": "Empresas que dão segundas chances",
        }
        def _loc(text): return _ptbr.get(text, text)
        def _loc_list(lst): return [_loc(t) for t in lst]

        print_lg(f"🔍 Applying filter: Sort by = {_loc(sort_by)}")
        wait_span_click(driver, _loc(sort_by))
        
        print_lg(f"🔍 Applying filter: Date posted = {_loc(date_posted)}")
        wait_span_click(driver, _loc(date_posted))
        buffer(recommended_wait)

        multi_sel_noWait(driver, _loc_list(experience_level))
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies: buffer(recommended_wait)

        multi_sel_noWait(driver, _loc_list(job_type))
        multi_sel_noWait(driver, _loc_list(on_site))
        if job_type or on_site: buffer(recommended_wait)
        
        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry: buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles: buffer(recommended_wait)

        if under_10_applicants: boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network: boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer: boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)
        
        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments: buffer(recommended_wait)

        # Apply Easy Apply filter LAST to ensure it stays active
        if easy_apply_only: 
            boolean_button_click(driver, actions, _loc("Easy Apply"))
            print_lg('✅ Easy Apply filter set LAST in modal')

        # Tenta encontrar o botão "Show results" / "Exibir resultados" com múltiplas estratégias
        show_results_button = None
        show_results_strategies = [
            # Strategy 1: aria-label (most reliable)
            '//button[contains(@aria-label, "Apply current filters") or contains(@aria-label, "Aplicar filtro") or contains(@aria-label, "Mostrar") or contains(@aria-label, "Show")]',
            # Strategy 2: span text inside button
            '//button[.//span[normalize-space()="Exibir resultados" or normalize-space()="Show results" or contains(normalize-space(), "Exibir") or contains(normalize-space(), "resultado")]]',
            # Strategy 3: Primary button in modal footer
            '//div[contains(@class, "reusable-search-filters-buttons")]//button[contains(@class, "artdeco-button--primary")]',
            # Strategy 4: Any primary button in filters panel
            '//div[contains(@class, "search-reusables-filters")]//button[contains(@class, "artdeco-button--primary")]',
            # Strategy 5: Button with specific data attributes
            '//button[@data-test-reusables-filters-modal-show-results-button]',
            # Strategy 6: Generic primary button at bottom of modal
            '//div[contains(@class, "artdeco-modal__actionbar")]//button[contains(@class, "artdeco-button--primary")]',
        ]
        
        for strategy in show_results_strategies:
            try:
                show_results_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, strategy))
                )
                print_lg(f"✅ Found 'Show results' button using strategy: {strategy[:60]}...")
                break
            except:
                continue
        
        if not show_results_button:
            print_lg("❌ Could not find 'Show results' button with any strategy")
            # Try pressing ESC to close modal and continue without applying filters
            actions.send_keys(Keys.ESCAPE).perform()
            buffer(1)
            raise Exception("Failed to find Show results button")
        
        # Final verification: ensure Easy Apply filter is still active
        if easy_apply_only:
            try:
                easy_apply_pill = driver.find_element(By.XPATH, '//button[@id="searchFilter_applyWithLinkedin" or contains(@aria-label, "Filtro Candidatura simplificada")]')
                aria_pressed = (easy_apply_pill.get_attribute("aria-checked") or easy_apply_pill.get_attribute("aria-pressed") or "").lower()
                if aria_pressed != "true":
                    print_lg('❌ Easy Apply filter was deactivated, reactivating...')
                    easy_apply_pill.click()
                    buffer(1)
                else:
                    print_lg('✅ Easy Apply filter confirmed active')
            except Exception as e:
                print_lg('Could not verify Easy Apply filter status:', e)
        
        show_results_button.click()
        buffer(3)
        
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@data-job-id]')))
        buffer(2)

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == show_confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        print_lg(e)



def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Function to get pagination element and current page number
    '''
    try:
        # Try multiple approaches to find pagination
        pagination_element = None
        
        # Method 1: Try by classes
        pagination_element = try_find_by_classes(driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
        
        # Method 2: Try by data-test-id (LinkedIn uses this)
        if not pagination_element:
            try:
                pagination_element = driver.find_element(By.XPATH, "//div[@data-test-pagination-page-container]")
            except:
                pass
        
        # Method 3: Try by aria-label containing page numbers
        if not pagination_element:
            try:
                pagination_element = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Paginação') or contains(@aria-label, 'Pagination')]")
            except:
                pass
        
        # Method 4: Try to find any button with page number
        if not pagination_element:
            try:
                page_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Página') or contains(@aria-label, 'Page')]")
                if page_buttons:
                    # Find the container that holds these buttons
                    pagination_element = page_buttons[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'pagination') or contains(@class, 'artdeco-pagination')]")
            except:
                pass
        
        if pagination_element:
            scroll_to_view(driver, pagination_element)
            # Try to find current page number
            try:
                active_button = pagination_element.find_element(By.XPATH, ".//button[contains(@class, 'active') or @aria-current='page']")
                current_page = int(active_button.text)
            except:
                try:
                    # Alternative: find button with aria-label indicating current page
                    active_button = pagination_element.find_element(By.XPATH, ".//button[contains(@aria-label, 'current') or contains(@aria-label, 'atual')]")
                    current_page = int(active_button.text)
                except:
                    # Fallback: assume page 1 if we can't determine
                    current_page = 1
        else:
            print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
            current_page = None
            
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page



def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    '''
    job_details_button = job.find_element(By.TAG_NAME, 'a')  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    title = job_details_button.text
    title = title[:title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
    work_location = work_location[:work_location.rfind('(')].strip()
    
    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except: pass
    try: 
        if not skip: 
            # First, ensure no modal is blocking
            close_discard_modal()
            job_details_button.click()
    except ElementClickInterceptedException as e:
        print_lg(f'Click intercepted for "{title} | {company}" job. Job ID: {job_id}! Trying to close blocking modal...')
        # Try to close any blocking modal
        discard_job()
        buffer(0.5)
        try:
            job_details_button.click()
        except Exception as retry_e:
            print_lg(f'Retry click also failed: {retry_e}')
            skip = True  # Mark as skip to avoid further errors
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
        # print_lg(e)
        discard_job()
        try:
            job_details_button.click()
        except:
            skip = True  # Mark as skip if click still fails
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words: 
            if word.lower() in about_company: 
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card



# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])


 
def get_job_description(
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''

    # Inicializa variáveis para garantir retorno seguro mesmo em caso de exceção
    jobDescription: str | Literal['Unknown'] = "Unknown"
    experience_required: int | Literal['Unknown'] | str = "Unknown"
    skip: bool = False
    skipReason: str | None = None
    skipMessage: str | None = None
    found_masters = 0

    try:
        ##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        ##<
        jobDescriptionLow = jobDescription.lower()
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        # Verificar clearance governamental (apenas contexto US/governamental, não cloud security)
        if not skip and security_clearance == False:
            # Palavras que indicam clearance governamental real
            gov_clearance_phrases = [
                'security clearance required',
                'active security clearance',
                'top secret clearance',
                'secret clearance required',
                'ts/sci clearance',
                'polygraph',
                'us security clearance',
                'government clearance',
                'dod clearance',
                'federal clearance'
            ]
            for phrase in gov_clearance_phrases:
                if phrase in jobDescriptionLow:
                    skipMessage = f'\n{jobDescription}\n\nFound "{phrase}". Skipping this job!\n'
                    skipReason = "Asking for Security clearance"
                    skip = True
                    break
        if not skip:
            if did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if current_experience > -1 and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":
            print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)

    return jobDescription, experience_required, skip, skipReason, skipMessage


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except:
        return False, "Previous resume"

# Function to upload profile image
def upload_profile_image(modal: WebElement, image_path: str = "perfil.jpeg") -> bool:
    '''
    Upload profile image when requested in Easy Apply forms
    '''
    try:
        # Try to find file input for profile image
        file_inputs = modal.find_elements(By.XPATH, ".//input[@type='file']")
        
        if not file_inputs:
            print_lg(f"No file input found for profile image")
            return False
        
        # Check if the image file exists
        full_path = os.path.abspath(image_path)
        if not os.path.exists(full_path):
            print_lg(f"Profile image not found at: {full_path}")
            return False
        
        # Try to upload to the first file input (usually profile image)
        for file_input in file_inputs:
            try:
                # Check if this input is for image/photo
                accept_attr = file_input.get_attribute("accept") or ""
                if "image" in accept_attr.lower() or accept_attr == "":
                    file_input.send_keys(full_path)
                    print_lg(f"✅ Profile image uploaded successfully: {image_path}")
                    buffer(1)
                    return True
            except Exception as e:
                print_lg(f"Failed to upload to this input: {e}")
                continue
        
        return False
    except Exception as e:
        print_lg(f"Failed to upload profile image: {e}")
        return False


# Function to answer common questions for Easy Apply using smart answers
def answer_common_questions(label: str, answer: str) -> str:
    '''
    Intelligently answers questions based on keywords in the label
    Supports both Portuguese and English
    Special logic for salary: CLT = 5000, PJ = 7000
    PRIORITY ORDER: Time/experience questions > Salary > Other smart answers
    '''
    import re
    from config.questions import smart_answers, years_of_experience, python_experience_years, ci_cd_experience_years, it_experience_years, legal_experience_years, java_experience_years, nodejs_experience_years, reactjs_experience_years, age_started_programming, taxa_hora_pj, cpf_number, english_level, cover_letter, linkedin_summary
    
    # Convert label to lowercase for matching
    label_lower = label.lower()
    
    # PRIORITY 0: Headline, Summary, Cover Letter - MUST be handled first
    if label_lower == 'headline' or label_lower.startswith('headline'):
        from config.questions import linkedin_headline
        print_lg(f"Headline question detected: '{label}' -> using linkedin_headline")
        return linkedin_headline if linkedin_headline else "Desenvolvedor Full Stack | Python, Django, Flask, React | Especialista em Automações e APIs RESTful"
    
    if label_lower == 'summary' or (label_lower.startswith('summary') and len(label_lower) < 30):
        print_lg(f"Summary question detected: '{label}' -> using linkedin_summary")
        return linkedin_summary.strip() if linkedin_summary else "Desenvolvedor Full Stack com 8+ anos de experiência em Python, Django, Flask, React e Node.js. Especialista em automações, APIs RESTful e integração de sistemas."
    
    if 'cover letter' in label_lower or 'carta de apresentação' in label_lower:
        print_lg(f"Cover letter question detected: '{label}' -> using cover_letter")
        return cover_letter.strip() if cover_letter else ""
    
    # PRIORITY 1: Time/duration questions - these ALWAYS need numeric answers
    # Check for "há quanto tempo", "how long", "quanto tempo", "há quantos anos" patterns
    time_indicators = ['há quanto tempo', 'how long', 'quanto tempo', 'há quantos anos', 
                       'quantos anos', 'how many years', 'years of experience', 
                       'anos de experiência', 'experiência com', 'experience with',
                       'já usa', 'you have been using', 'work experience']
    
    is_time_question = any(indicator in label_lower for indicator in time_indicators)
    
    if is_time_question:
        # Return appropriate experience years based on technology mentioned
        if 'python' in label_lower:
            print_lg(f"Time question detected (Python): '{label}' -> {python_experience_years}")
            return str(python_experience_years)
        elif any(k in label_lower for k in ['java', 'spring', 'spring boot', 'jboss', 'quarkus']):
            print_lg(f"Time question detected (Java): '{label}' -> {java_experience_years}")
            return str(java_experience_years)
        elif any(k in label_lower for k in ['node', 'nodejs', 'node.js']):
            print_lg(f"Time question detected (Node.js): '{label}' -> {nodejs_experience_years}")
            return str(nodejs_experience_years)
        elif any(k in label_lower for k in ['react', 'reactjs', 'react.js', 'react native']):
            print_lg(f"Time question detected (React.js): '{label}' -> {reactjs_experience_years}")
            return str(reactjs_experience_years)
        elif any(k in label_lower for k in ['ci/cd', 'cicd', 'integração contínua', 'entrega contínua', 'continuous integration', 'continuous delivery']):
            print_lg(f"Time question detected (CI/CD): '{label}' -> {ci_cd_experience_years}")
            return str(ci_cd_experience_years)
        elif any(k in label_lower for k in ['tecnologia da informação', 'information technology', ' ti ', ' it ']):
            print_lg(f"Time question detected (IT): '{label}' -> {it_experience_years}")
            return str(it_experience_years)
        elif any(k in label_lower for k in ['jurídico', 'juridico', 'legal', 'law']):
            print_lg(f"Time question detected (Legal): '{label}' -> {legal_experience_years}")
            return str(legal_experience_years)
        else:
            # Default years of experience for any other time question
            print_lg(f"Time question detected (General): '{label}' -> {years_of_experience}")
            return str(years_of_experience)
    
    # PRIORITY 2: CPF question
    if 'cpf' in label_lower:
        print_lg(f"CPF question detected: '{label}' -> {cpf_number}")
        return str(cpf_number)
    
    # PRIORITY 3: Age started programming
    if any(k in label_lower for k in ['programa desde qual idade', 'started programming', 'começou a programar', 'age.*programming']):
        print_lg(f"Age started programming question: '{label}' -> {age_started_programming}")
        return str(age_started_programming)
    
    # PRIORITY 4: Taxa/hora PJ
    if any(k in label_lower for k in ['taxa/hora', 'taxa hora', 'por hora', 'hourly rate', 'rate per hour', '/hora', '/h']):
        print_lg(f"Taxa/hora PJ question: '{label}' -> {taxa_hora_pj}")
        return str(taxa_hora_pj)
    
    # PRIORITY 5: English level
    if any(k in label_lower for k in ['nível de inglês', 'english level', 'proficiency in english', 'inglês', 'english']):
        if 'fluent' in label_lower or 'fluente' in label_lower or 'native' in label_lower or 'nativo' in label_lower:
            print_lg(f"English fluency/native question: '{label}' -> No (Intermediário)")
            return "No"  # User is intermediate, not fluent/native
        else:
            print_lg(f"English level question: '{label}' -> {english_level}")
            return str(english_level)
    
    # PRIORITY 6: Salary questions - special handling
    salary_indicators = ['pretensão', 'salário', 'salarial', 'remuneração', 'salary', 'compensation', 'ctc', 'pay']
    is_salary_question = any(indicator in label_lower for indicator in salary_indicators)
    
    if is_salary_question:
        # Check if it's current salary
        if 'atual' in label_lower or 'current' in label_lower:
            print_lg(f"Current salary question: '{label}' -> {current_ctc}")
            return str(current_ctc)
        # Check if it's CLT or PJ
        elif 'clt' in label_lower or 'carteira assinada' in label_lower or 'carteira' in label_lower:
            print_lg(f"Salary question (CLT): '{label}' -> {desired_salary}")
            return str(desired_salary)
        elif 'pj' in label_lower or 'pessoa jurídica' in label_lower or 'cnpj' in label_lower:
            print_lg(f"Salary question (PJ): '{label}' -> 7000")
            return "7000"
        else:
            # Default to desired salary
            print_lg(f"Salary question (default): '{label}' -> {desired_salary}")
            return str(desired_salary)
    
    # PRIORITY 7: Try to match with smart answers dictionary (excluding time/salary already handled)
    for keywords, smart_answer in smart_answers.items():
        # Skip time-related and salary entries (already handled above)
        if smart_answer == "SALARY_CHECK":
            continue
        if any(time_word in keywords for time_word in ['anos de experiência', 'years of experience', 'experience in', 'experiência em']):
            continue
            
        # Split keywords by | and check if any matches
        keyword_list = keywords.split('|')
        for keyword in keyword_list:
            if keyword.strip() in label_lower:
                print_lg(f"Smart answer matched for '{label}': {smart_answer}")
                return str(smart_answer)
    
    # Fallback to original logic
    if 'sponsorship' in label_lower or 'visa' in label_lower: 
        return require_visa
    
    # If no match found, return original answer
    return answer
def get_salary_by_job_level(job_description: str | None = None) -> str:
    '''
    Detecta o nível da vaga e tipo de contrato para retornar salário apropriado em REAIS
    CLT Junior/Pleno: R$ 6.000
    PJ Junior/Pleno: R$ 8.000
    CLT Senior/Engenheiro: R$ 8.000
    PJ Senior/Engenheiro: R$ 10.000
    '''
    default_salary = "6000"  # R$ 6.000 CLT padrão
    
    if not job_description:
        return default_salary
    
    job_desc_lower = job_description.lower()
    
    # Detectar nível da vaga
    is_senior = any(word in job_desc_lower for word in ['senior', 'sênior', 'senhor', 'lead', 'principal', 'staff', 'architect', 'arquiteto'])
    is_engineer = any(word in job_desc_lower for word in ['engenheiro', 'engineer', 'engineering'])
    is_junior_pleno = any(word in job_desc_lower for word in ['junior', 'júnior', 'pleno', 'mid-level', 'mid level', 'associate', 'analista'])
    
    # Detectar tipo de contrato
    is_pj = any(word in job_desc_lower for word in ['pj', 'pessoa jurídica', 'pessoa juridica', 'autônomo', 'autonomo', 'freelancer', 'contratado'])
    is_clt = any(word in job_desc_lower for word in ['clt', 'consolidada', 'consolidado', 'tempo integral', 'full-time', 'fulltime'])
    
    # Determinar salário baseado em nível e tipo (valores em R$)
    if is_senior or is_engineer:
        if is_pj:
            return "10000"  # R$ 10.000 PJ Senior
        else:
            return "8000"   # R$ 8.000 CLT Senior
    elif is_junior_pleno:
        if is_pj:
            return "8000"   # R$ 8.000 PJ Pleno
        else:
            return "6000"   # R$ 6.000 CLT Pleno
    
    # Se não conseguir detectar, retorna padrão
    return default_salary


def answer_questions(modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None ) -> set:
    # NOVA ABORDAGEM: Procurar por inputs/selects/textareas diretamente
    print_lg("🔍 Iniciando preenchimento de formulário...")
    
    # Aguardar um pouco para o modal carregar completamente
    buffer(1)
    
    # Encontrar todos os inputs, selects e textareas com múltiplas estratégias
    all_inputs = []
    
    # Estratégia 1: inputs padrão
    try:
        all_inputs.extend(modal.find_elements(By.XPATH, ".//input[@type='text' or @type='number' or @type='email' or @type='tel']"))
    except:
        pass
    
    # Estratégia 2: inputs sem type (geralmente text)
    try:
        inputs_no_type = modal.find_elements(By.XPATH, ".//input[not(@type) or @type='']")
        for inp in inputs_no_type:
            if inp not in all_inputs:
                all_inputs.append(inp)
    except:
        pass
    
    # Estratégia 3: inputs dentro de form-elements do LinkedIn
    try:
        form_inputs = modal.find_elements(By.XPATH, ".//div[contains(@class, 'fb-dash-form-element')]//input")
        for inp in form_inputs:
            if inp not in all_inputs:
                all_inputs.append(inp)
    except:
        pass
    
    # Estratégia 4: inputs com aria-label
    try:
        aria_inputs = modal.find_elements(By.XPATH, ".//input[@aria-label or @aria-describedby]")
        for inp in aria_inputs:
            if inp not in all_inputs and inp.get_attribute('type') not in ['hidden', 'file', 'checkbox', 'radio', 'submit', 'button']:
                all_inputs.append(inp)
    except:
        pass
    
    try:
        all_inputs.extend(modal.find_elements(By.XPATH, ".//textarea"))
    except:
        pass
    
    try:
        all_inputs.extend(modal.find_elements(By.XPATH, ".//select"))
    except:
        pass
    
    # Encontrar todos os containers de perguntas
    all_questions = []
    try:
        all_questions.extend(modal.find_elements(By.XPATH, ".//div[@data-test-form-element]"))
    except:
        pass
    
    try:
        all_questions.extend(modal.find_elements(By.XPATH, ".//div[contains(@class, 'artdeco-form-element')]"))
    except:
        pass
    
    # Remover duplicatas
    seen = set()
    unique_questions = []
    for q in all_questions:
        try:
            # Usa hash do objeto em vez de id() para evitar conflito com variável 'id'
            q_id = q.get_attribute('id') or str(hash(q))
            if q_id not in seen:
                seen.add(q_id)
                unique_questions.append(q)
        except:
            unique_questions.append(q)
    
    all_questions = unique_questions
    print_lg(f"✅ Encontrados {len(all_questions)} elementos de pergunta e {len(all_inputs)} inputs/selects")

    # Try to upload profile image if requested
    try:
        file_inputs = modal.find_elements(By.XPATH, ".//input[@type='file']")
        for file_input in file_inputs:
            try:
                accept_attr = (file_input.get_attribute("accept") or "").lower()
                label_text = ""
                
                # Try to find associated label
                try:
                    label_elem = file_input.find_element(By.XPATH, "./ancestor::div[@data-test-form-element]//label | ./ancestor::div[@data-test-form-element]//h3")
                    label_text = (label_elem.text or "").lower()
                except:
                    pass
                
                # Check if this is a profile/photo image field
                if "image" in accept_attr or "photo" in accept_attr or "profile" in label_text or "foto" in label_text or "imagem" in label_text:
                    if upload_profile_image(modal, "perfil.jpeg"):
                        print_lg("✅ Profile image uploaded in answer_questions")
                        questions_list.add(("profile-image", "perfil.jpeg", "file", ""))
                        break
            except Exception as e:
                print_lg(f"Error checking file input: {e}")
                continue
    except Exception as e:
        print_lg(f"Error processing file inputs: {e}")

    # Processa inputs diretamente
    processed_inputs = set()
    
    for input_elem in all_inputs:
        try:
            input_id = input_elem.get_attribute('id') or str(hash(input_elem))
            if input_id in processed_inputs:
                continue
            processed_inputs.add(input_id)
            
            # Pula inputs de arquivo
            if input_elem.get_attribute('type') == 'file':
                continue
            
            # Pula inputs já preenchidos (a menos que overwrite_previous_answers)
            current_value = input_elem.get_attribute('value') or ""
            if current_value and not overwrite_previous_answers:
                print_lg(f"⏭️ Input já preenchido, pulando: {current_value[:50]}")
                continue
            
            # Tenta encontrar o label
            label_org = "Unknown"
            try:
                # Procura por label associado
                label_id = input_elem.get_attribute('id')
                if label_id:
                    label = input_elem.find_element(By.XPATH, f"./ancestor::div//label[@for='{label_id}']")
                    label_org = label.text
            except:
                pass
            
            # Se não encontrou label, tenta pelo texto do container
            if label_org == "Unknown":
                try:
                    container = input_elem.find_element(By.XPATH, "./ancestor::div[@data-test-form-element or contains(@class, 'form-element')]")
                    label_org = container.text.split('\n')[0] if container.text else "Unknown"
                except:
                    pass
            
            # Pula se não conseguiu encontrar label
            if label_org == "Unknown" or not label_org.strip():
                continue
            
            label = label_org.lower()
            answer = ""
            is_location_field = False  # Inicializar variável
            
            # Determina a resposta baseado no label
            # IMPORTANTE: Verificar perguntas específicas ANTES de palavras-chave genéricas
            
            # HEADLINE - usar headline configurado
            if label == 'headline' or 'headline' in label:
                answer = "Desenvolvedor Full Stack | Python, Django, Flask, React | Especialista em Automações e APIs RESTful"
                print_lg(f"✅ Detectado: Headline, respondendo com título profissional")
            # SUMMARY - usar linkedin_summary
            elif label == 'summary' or (label.startswith('summary') and len(label) < 20):
                answer = linkedin_summary if linkedin_summary else "Desenvolvedor Full Stack com 8+ anos de experiência em Python, Django, Flask, React e Node.js. Especialista em automações, APIs RESTful e integração de sistemas."
                print_lg(f"✅ Detectado: Summary, respondendo com resumo profissional")
            # Perguntas "How many years of experience as [role]?" - NÚMERO, não Yes/No
            elif ('how many years' in label or 'years of experience' in label) and ('as a' in label or 'como' in label or 'developer' in label or 'engineer' in label):
                answer = years_of_experience
                print_lg(f"✅ Detectado: Anos de experiência como profissional, respondendo: {answer}")
            # Pergunta específica: "Is your résumé in English?" - espera número (escala)
            elif ('résumé' in label or 'resume' in label or 'cv' in label or 'currículo' in label) and ('english' in label or 'inglês' in label or 'ingles' in label):
                answer = "10"  # Escala máxima, indicando que sim, está em inglês
                print_lg(f"✅ Detectado: Pergunta sobre currículo em inglês (escala), respondendo: 10")
            # Pergunta específica: Salário em USD/Euros (atual ou desejado)
            elif ('salary' in label or 'salário' in label or 'expectation' in label or 'expectativa' in label or 'compensation' in label or 'ctc' in label) and ('usd' in label or 'dollar' in label or 'euro' in label or 'dólar' in label):
                # Detecta se é salário ATUAL ou DESEJADO
                is_current = 'current' in label or 'atual' in label or 'present' in label or 'last' in label or 'último' in label or 'previous' in label
                
                if 'hourly' in label or 'hour' in label or 'hora' in label:
                    # Taxa por hora
                    answer = "18"  # R$ 100/hora ÷ 5.5 = ~$18/hora
                    print_lg(f"✅ Detectado: Taxa horária em USD/EUR, respondendo: $18/hour")
                elif is_current:
                    # Salário ATUAL: R$ 4.287
                    if 'euro' in label or 'eur' in label or '€' in label:
                        answer = "715"  # R$ 4.287 ÷ 6.0 = €715
                        print_lg(f"✅ Detectado: Salário ATUAL em EUR, respondendo: €715")
                    else:
                        answer = "780"  # R$ 4.287 ÷ 5.5 = $780
                        print_lg(f"✅ Detectado: Salário ATUAL em USD, respondendo: $780")
                else:
                    # Salário DESEJADO: R$ 8.000
                    if 'euro' in label or 'eur' in label or '€' in label:
                        answer = "1330"  # R$ 8.000 ÷ 6.0 = €1.330
                        print_lg(f"✅ Detectado: Salário DESEJADO em EUR, respondendo: €1330")
                    else:
                        answer = "1450"  # R$ 8.000 ÷ 5.5 = $1.450
                        print_lg(f"✅ Detectado: Salário DESEJADO em USD, respondendo: $1450")
            # IMPORTANTE: Perguntas sobre ANOS de experiência com tecnologias (ANTES de Yes/No)
            elif ('how many years' in label or 'quantos anos' in label or 'years of experience' in label or 'anos de experiência' in label or 'years of work experience' in label) and ('with' in label or 'com' in label or 'in' in label or 'em' in label):
                # Perguntas sobre anos de experiência com tecnologias específicas
                answer = "3"  # Padrão: 3 anos
                
                # Tecnologias específicas com valores customizados
                if 'python' in label:
                    answer = python_experience_years
                elif 'java' in label and 'javascript' not in label:
                    answer = java_experience_years
                elif 'node' in label or 'nodejs' in label:
                    answer = nodejs_experience_years
                elif 'react' in label or 'reactjs' in label:
                    answer = reactjs_experience_years
                elif 'ci/cd' in label or 'cicd' in label:
                    answer = ci_cd_experience_years
                
                print_lg(f"✅ Detectado: Pergunta sobre ANOS de experiência com tecnologia, respondendo: {answer}")
            # Perguntas sobre experiência com tecnologia (Do you have experience with X?)
            elif ('do you have' in label or 'have you' in label or 'você tem' in label or 'possui' in label) and ('experience' in label or 'experiência' in label) and ('with' in label or 'com' in label or 'working with' in label):
                # Verificar se é um textarea (espera descrição) ou input (espera Yes/No)
                if input_elem.tag_name == 'textarea':
                    # Textarea espera descrição - fornecer resposta descritiva
                    answer = "Yes, I have professional experience working with this technology in production environments, including development, implementation and maintenance of solutions."
                    print_lg(f"✅ Detectado: Pergunta sobre experiência (textarea), respondendo com descrição")
                else:
                    # Input normal - responder Yes/No
                    answer = "Yes"
                    print_lg(f"✅ Detectado: Pergunta sobre experiência com tecnologia (Yes/No), respondendo: Yes")
            # Perguntas Yes/No genéricas
            elif any(word in label for word in ['sim', 'yes', 'agree', 'aceita', 'accept', 'eligible', 'autorização', 'are you', 'do you', 'have you', 'can you', 'will you', 'você é', 'você tem', 'você pode']):
                answer = "Yes"
            elif any(word in label for word in ['não', 'no', 'disagree', 'decline']):
                answer = "No"
            # Perguntas sobre salário
            elif any(word in label for word in ['salário', 'salary', 'remuneração', 'compensation', 'pay', 'hourly rate', 'taxa horária']):
                answer = desired_salary
            # Perguntas sobre experiência (anos)
            elif any(word in label for word in ['experiência', 'experience', 'anos', 'years']) and not ('english' in label or 'inglês' in label):
                answer = years_of_experience
            # Perguntas sobre nome
            elif any(word in label for word in ['nome', 'name']) and not ('company' in label or 'empresa' in label):
                answer = full_name
            # Email
            elif 'email' in label or 'e-mail' in label:
                answer = email
            # Telefone
            elif any(word in label for word in ['telefone', 'phone', 'celular', 'mobile']):
                answer = phone_number
            # Localização
            elif any(word in label for word in ['cidade', 'city', 'location', 'localização']) and not ('company' in label or 'empresa' in label):
                answer = current_city if current_city else work_location
                is_location_field = True
            else:
                answer = answer_common_questions(label, "")
                is_location_field = False
            
            # Preenche o input
            if answer:
                try:
                    input_elem.clear()
                    input_elem.send_keys(str(answer))
                    
                    # Para campos de localização com autocomplete, selecionar primeira opção
                    if is_location_field:
                        buffer(1.5)  # Aguardar dropdown aparecer
                        try:
                            # Tentar clicar na primeira opção do dropdown
                            first_option = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, 
                                    "//div[contains(@class, 'basic-typeahead__selectable') or contains(@class, 'typeahead-result')]"
                                ))
                            )
                            first_option.click()
                            print_lg(f"✅ Selecionado do dropdown: '{label_org[:60]}'")
                        except:
                            # Fallback: usar ARROW_DOWN + ENTER
                            actions.send_keys(Keys.ARROW_DOWN).perform()
                            buffer(0.3)
                            actions.send_keys(Keys.ENTER).perform()
                            print_lg(f"✅ Preenchido (com ENTER): '{label_org[:60]}' = '{str(answer)[:50]}'")
                    else:
                        print_lg(f"✅ Preenchido: '{label_org[:60]}' = '{str(answer)[:50]}'")
                    
                    questions_list.add((label_org, str(answer), "text", current_value))
                except Exception as e:
                    print_lg(f"❌ Erro ao preencher '{label_org}': {e}")
        except StaleElementReferenceException:
            print_lg("⚠️ Stale element, pulando...")
            continue
        except Exception as e:
            print_lg(f"⚠️ Erro processando input: {e}")
            continue
    
    # Processa selects
    for select_elem in [s for s in all_inputs if s.tag_name == 'select']:
        try:
            # Tenta encontrar o label
            label_org = "Unknown"
            try:
                label_id = select_elem.get_attribute('id')
                if label_id:
                    label = select_elem.find_element(By.XPATH, f"./ancestor::div//label[@for='{label_id}']")
                    label_org = label.text
            except:
                pass
            
            if label_org == "Unknown":
                try:
                    container = select_elem.find_element(By.XPATH, "./ancestor::div[@data-test-form-element]")
                    label_org = container.text.split('\n')[0] if container.text else "Unknown"
                except:
                    pass
            
            if label_org == "Unknown" or not label_org.strip():
                continue
            
            label = label_org.lower()
            answer = "Yes"
            
            # Determina resposta
            if any(word in label for word in ['sim', 'yes', 'agree', 'aceita']):
                answer = "Yes"
            elif any(word in label for word in ['não', 'no', 'disagree']):
                answer = "No"
            
            # Seleciona opção
            try:
                select = Select(select_elem)
                select.select_by_visible_text(answer)
                print_lg(f"✅ Select preenchido: '{label_org[:60]}' = '{answer}'")
                questions_list.add((label_org, answer, "select", ""))
            except:
                # Tenta por valor parcial
                for option in select.options:
                    if answer.lower() in option.text.lower():
                        select.select_by_visible_text(option.text)
                        print_lg(f"✅ Select preenchido (parcial): '{label_org[:60]}' = '{option.text}'")
                        questions_list.add((label_org, option.text, "select", ""))
                        break
        except Exception as e:
            print_lg(f"⚠️ Erro em select: {e}")
            continue
    
    # Processa questions containers (para elementos customizados que não foram processados)
    # SIMPLIFICADO: apenas processa elementos que não foram encontrados antes
    for Question in all_questions:
        try:
            # Pula se já foi processado
            question_id = Question.get_attribute('id') or str(hash(Question))
            if question_id in processed_inputs:
                continue
            
            # Texto completo do bloco da pergunta
            question_block_text = (Question.text or "").strip()
            question_block_lower = question_block_text.lower()
            
            if not question_block_text:
                continue
            
            print_lg(f"🔍 Processando pergunta customizada: '{question_block_text[:80]}'")
        except StaleElementReferenceException:
            print_lg("Stale element in question, skipping...")
            continue

        # Apenas processa elementos que não foram encontrados antes
        # Tenta encontrar inputs/selects dentro do container
        try:
            inputs_in_question = Question.find_elements(By.XPATH, ".//input[@type='text' or @type='number' or @type='email' or @type='tel' or not(@type)] | .//select | .//textarea")
            if inputs_in_question:
                for inp in inputs_in_question:
                    if inp.get_attribute('id') not in processed_inputs:
                        # Processa este input
                        label_org = question_block_text.split('\n')[0] if question_block_text else "Unknown"
                        current_value = inp.get_attribute('value') or ""
                        
                        if not current_value or overwrite_previous_answers:
                            # Determina resposta baseado no texto da pergunta
                            answer = ""
                            
                            # Pergunta específica: currículo em inglês - espera número (escala)
                            if ('résumé' in question_block_lower or 'resume' in question_block_lower or 'cv' in question_block_lower or 'currículo' in question_block_lower) and ('english' in question_block_lower or 'inglês' in question_block_lower or 'ingles' in question_block_lower):
                                answer = "10"  # Escala máxima
                                print_lg(f"✅ Detectado (customizado): Pergunta sobre currículo em inglês (escala), respondendo: 10")
                            # Pergunta específica: Salário em USD/Euros (atual ou desejado)
                            elif ('salary' in question_block_lower or 'salário' in question_block_lower or 'expectation' in question_block_lower or 'expectativa' in question_block_lower or 'compensation' in question_block_lower or 'ctc' in question_block_lower) and ('usd' in question_block_lower or 'dollar' in question_block_lower or 'euro' in question_block_lower or 'dólar' in question_block_lower):
                                # Detecta se é salário ATUAL ou DESEJADO
                                is_current = 'current' in question_block_lower or 'atual' in question_block_lower or 'present' in question_block_lower or 'last' in question_block_lower or 'último' in question_block_lower or 'previous' in question_block_lower
                                
                                if 'hourly' in question_block_lower or 'hour' in question_block_lower or 'hora' in question_block_lower:
                                    answer = "18"  # Taxa por hora
                                    print_lg(f"✅ Detectado (customizado): Taxa horária em USD/EUR, respondendo: $18/hour")
                                elif is_current:
                                    # Salário ATUAL: R$ 4.287
                                    if 'euro' in question_block_lower or 'eur' in question_block_lower or '€' in question_block_lower:
                                        answer = "715"  # €715
                                        print_lg(f"✅ Detectado (customizado): Salário ATUAL em EUR, respondendo: €715")
                                    else:
                                        answer = "780"  # $780
                                        print_lg(f"✅ Detectado (customizado): Salário ATUAL em USD, respondendo: $780")
                                else:
                                    # Salário DESEJADO: R$ 8.000
                                    if 'euro' in question_block_lower or 'eur' in question_block_lower or '€' in question_block_lower:
                                        answer = "1330"  # €1.330
                                        print_lg(f"✅ Detectado (customizado): Salário DESEJADO em EUR, respondendo: €1330")
                                    else:
                                        answer = "1450"  # $1.450
                                        print_lg(f"✅ Detectado (customizado): Salário DESEJADO em USD, respondendo: $1450")
                            # IMPORTANTE: Perguntas sobre ANOS de experiência com tecnologias (ANTES de Yes/No)
                            elif ('how many years' in question_block_lower or 'quantos anos' in question_block_lower or 'years of experience' in question_block_lower or 'anos de experiência' in question_block_lower or 'years of work experience' in question_block_lower) and ('with' in question_block_lower or 'com' in question_block_lower or 'in' in question_block_lower or 'em' in question_block_lower):
                                # Perguntas sobre anos de experiência com tecnologias específicas
                                answer = "3"  # Padrão: 3 anos
                                
                                # Tecnologias específicas
                                if 'python' in question_block_lower:
                                    answer = python_experience_years
                                elif 'java' in question_block_lower and 'javascript' not in question_block_lower:
                                    answer = java_experience_years
                                elif 'node' in question_block_lower or 'nodejs' in question_block_lower:
                                    answer = nodejs_experience_years
                                elif 'react' in question_block_lower or 'reactjs' in question_block_lower:
                                    answer = reactjs_experience_years
                                elif 'ci/cd' in question_block_lower or 'cicd' in question_block_lower:
                                    answer = ci_cd_experience_years
                                
                                print_lg(f"✅ Detectado (customizado): ANOS de experiência com tecnologia, respondendo: {answer}")
                            # Perguntas sobre experiência com tecnologia (Do you have experience with X?)
                            elif ('do you have' in question_block_lower or 'have you' in question_block_lower or 'você tem' in question_block_lower or 'possui' in question_block_lower) and ('experience' in question_block_lower or 'experiência' in question_block_lower) and ('with' in question_block_lower or 'com' in question_block_lower or 'working with' in question_block_lower):
                                # Perguntas "Do you have experience with [technology]?" → Sempre "Yes"
                                answer = "Yes"
                                print_lg(f"✅ Detectado (customizado): Experiência com tecnologia (Yes/No), respondendo: Yes")
                            # Perguntas Yes/No genéricas
                            elif any(word in question_block_lower for word in ['sim', 'yes', 'agree', 'aceita', 'accept', 'eligible', 'autorização', 'are you', 'do you', 'have you', 'can you', 'will you']):
                                answer = "Yes"
                            elif any(word in question_block_lower for word in ['não', 'no', 'disagree', 'decline']):
                                answer = "No"
                            # Salário
                            elif any(word in question_block_lower for word in ['salário', 'salary', 'remuneração', 'compensation', 'hourly rate']):
                                answer = desired_salary
                            # Experiência (evitar confusão com inglês)
                            elif any(word in question_block_lower for word in ['experiência', 'experience', 'anos', 'years']) and not ('english' in question_block_lower or 'inglês' in question_block_lower):
                                answer = years_of_experience
                            # Nome
                            elif any(word in question_block_lower for word in ['nome', 'name']) and not ('company' in question_block_lower):
                                answer = full_name
                            else:
                                answer = answer_common_questions(question_block_lower, "")
                            
                            if answer:
                                try:
                                    if inp.tag_name == 'select':
                                        select = Select(inp)
                                        select.select_by_visible_text(answer)
                                    else:
                                        inp.clear()
                                        inp.send_keys(str(answer))
                                    print_lg(f"✅ Preenchido (customizado): '{label_org[:60]}' = '{str(answer)[:50]}'")
                                    questions_list.add((label_org, str(answer), inp.tag_name, current_value))
                                    processed_inputs.add(inp.get_attribute('id'))
                                except Exception as e:
                                    print_lg(f"❌ Erro ao preencher customizado: {e}")
        except:
            pass
        
        # Código antigo removido para evitar loop infinito - foi substituído pelo novo código acima
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except: pass
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                # Work authorization in Latin America - Yes
                elif 'work authorization' in label or 'autorização' in label or 'eligible' in label:
                    answer = 'Yes'
                    print_lg(f"Detected work authorization radio, answering: Yes")
                # Bachelor's degree - Yes
                elif "bachelor" in label or "bacharelado" in label or "graduação" in label:
                    answer = 'Yes'
                    print_lg(f"Detected bachelor's degree radio, answering: Yes")
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption: 
                    actions.move_to_element(foundOption).click().perform()
                else:    
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    # if answer == 'Decline':
                    #     answer = options_labels[0]
                    #     for phrase in ["Prefer not", "not want", "not wish"]:
                    #         foundOption = try_xp(radio, f".//label[normalize-space()='{phrase}']", False)
                    #         if foundOption:
                    #             answer = f'Decline ({phrase})'
                    #             ele = foundOption
                    #             break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption: randomly_answered_questions.add((f'{label_org} ]',"radio"))
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question (try multiple input types)
        text = try_xp(Question, ".//input[@type='text']", False)
        if not text:
            text = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number' or @type='tel' or @type='email']", False)
        if not text:
            text = try_xp(Question, ".//textarea", False)
            
        if text: 
            do_actions = False
            label_org = "Unknown"
            
            # Try multiple ways to get the label
            # Method 1: label with for attribute
            label = try_xp(Question, ".//label[@for]", False)
            if label:
                try: 
                    hidden = label.find_element(By.CLASS_NAME,'visually-hidden')
                    label_org = hidden.text if hidden else label.text
                except: 
                    label_org = label.text if label.text else "Unknown"
            
            # Method 2: If still Unknown, try span with question text
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                try:
                    span = try_xp(Question, ".//span[not(contains(@class, 'visually-hidden'))]", False)
                    if span and span.text and len(span.text) > 3:
                        label_org = span.text
                except: pass
            
            # Method 3: Try to get all text from the question container
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                try:
                    question_text = Question.text
                    if question_text and len(question_text) > 5:
                        label_org = question_text.split('\n')[0]  # Get first line
                except: pass
            
            # Skip if label is still empty or too generic
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                continue
            
            answer = "" # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                # Age when started programming - CHECK FIRST (before other patterns)
                # Patterns: "desde qual idade", "qual idade", "programa desde", "age", etc.
                if ('idade' in label and ('programa' in label or 'desde' in label or 'qual' in label)) or \
                   ('age' in label and ('programming' in label or 'code' in label or 'coding' in label or 'started' in label)) or \
                   ('desde qual idade' in label) or ('qual idade' in label and 'programa' in label):
                    answer = "29"
                    print_lg(f"Detected programming age question, answering: {answer}")
                # University / Education institution questions
                elif 'university' in label or 'universidade' in label or 'faculdade' in label or 'institution' in label or 'instituição' in label or 'graduated from' in label or "bachelor's" in label or 'bachelor' in label:
                    answer = "Universidade Estácio de Sá"
                    print_lg(f"Detected university question, answering: {answer}")
                # Country of residence
                elif 'country' in label and ('reside' in label or 'live' in label or 'residence' in label):
                    answer = "Brasil"
                    print_lg(f"Detected country question, answering: {answer}")
                # English level with numbered options (1- Básico, 2- Intermediário, 3- Avançado)
                elif ('nível' in label or 'nivel' in label or 'level' in label) and ('inglês' in label or 'ingles' in label or 'english' in label):
                    # Check if it's asking for a number (1, 2, 3) or text
                    if '1-' in label or '2-' in label or '1 -' in label or '2 -' in label:
                        answer = "2"  # Intermediário (numbered option)
                        print_lg(f"Detected English level question (numbered), answering: 2")
                    else:
                        answer = "B2"  # Standard level
                        print_lg(f"Detected English level question, answering: B2")
                # "há quanto tempo" questions should always return years
                elif 'há quanto tempo' in label or 'how long' in label or 'quanto tempo' in label:
                    answer = years_of_experience
                    print_lg(f"Detected time experience question, answering: {answer}")
                # Python experience
                elif 'python' in label and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = python_experience_years
                # CI/CD experience questions
                elif (('ci/cd' in label) or ('integração e entrega contínuas' in label) or ('integração contínua' in label) or ('entrega contínua' in label) or ('continuous integration' in label) or ('continuous delivery' in label)) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = ci_cd_experience_years
                # Information Technology experience questions
                elif ('tecnologia da informação' in label or 'information technology' in label) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = it_experience_years
                elif 'jurídico' in label or 'juridico' in label:
                    answer = legal_experience_years
                elif 'experience' in label or 'years' in label or 'anos' in label or 'experiência' in label:
                    answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label or 'pretensão' in label or 'remuneração' in label or 'salarial' in label or 'expectativas' in label or 'quanto somos atrativos' in label: 
                    if 'current' in label or 'present' in label or 'atual' in label:
                        if 'month' in label or 'mês' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        # Check for CLT vs PJ in the label
                        if 'clt' in label or 'carteira' in label:
                            answer = "5000"
                            print_lg(f"Detected CLT salary question, answering: 5000")
                        elif 'pj' in label or 'pessoa jurídica' in label or 'cnpj' in label:
                            answer = "7000"
                            print_lg(f"Detected PJ salary question, answering: 7000")
                        elif 'month' in label or 'mês' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                            print_lg(f"Detected salary question (desired), answering: {desired_salary}")
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = linkedin_headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                else: answer = answer_common_questions(label,answer)
                
                # FALLBACK: If still no answer, check for salary-related keywords in the full label
                if answer == "":
                    label_full_lower = label_org.lower() if label_org else ""
                    if any(word in label_full_lower for word in ['salário', 'salarial', 'remuneração', 'pretensão', 'expectativas', 'atrativos', 'salary', 'compensation', 'pay']):
                        if 'atual' in label_full_lower or 'current' in label_full_lower:
                            answer = current_ctc
                            print_lg(f"FALLBACK: Detected CURRENT salary question, answering: {current_ctc}")
                        else:
                            answer = desired_salary
                            print_lg(f"FALLBACK: Detected DESIRED salary question, answering: {desired_salary}")
                    elif any(word in label_full_lower for word in ['ci/cd', 'integração e entrega contínuas', 'integração contínua', 'entrega contínua', 'continuous integration', 'continuous delivery']):
                        answer = ci_cd_experience_years
                        print_lg(f"FALLBACK: Detected CI/CD experience question from full label, answering: {answer}")
                    elif 'python' in label_full_lower:
                        answer = python_experience_years
                        print_lg(f"FALLBACK: Detected Python experience question from full label, answering: {answer}")
                    elif 'tecnologia da informação' in label_full_lower or 'information technology' in label_full_lower:
                        answer = it_experience_years
                        print_lg(f"FALLBACK: Detected IT/Technology experience question from full label, answering: {answer}")
                    elif any(word in label_full_lower for word in ['jurídico', 'juridico', 'legal']):
                        answer = legal_experience_years
                        print_lg(f"FALLBACK: Detected legal/jurídico experience question from full label, answering: {answer}")
                    elif any(word in label_full_lower for word in ['anos', 'years', 'experiência', 'experience', 'tempo', 'quanto tempo', 'quantos', 'how many']):
                        answer = years_of_experience
                        print_lg(f"FALLBACK: Detected experience/years question from full label, answering: {answer}")
                    elif label_full_lower == "" or label_full_lower == "unknown":
                        # If label is empty/unknown, default to 3 (common numeric answer)
                        answer = years_of_experience
                        print_lg(f"FALLBACK: Unknown question, defaulting to: {answer}")
                
                ##> ------ Yang Li : MARKYangL - Feature ------
                if answer == "":
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="text", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "text"))
                            answer = years_of_experience
                    else:
                        randomly_answered_questions.add((label_org, "text"))
                        answer = years_of_experience
                ##<
                # DEBUG: Log the answer being given
                print_lg(f"DEBUG: Answering with: '{answer}'")
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label_org = "Unknown"

            # Reutilizar a mesma lógica de extração de label das perguntas de texto
            # Method 1: label with for attribute
            label = try_xp(Question, ".//label[@for]", False)
            if label:
                try:
                    hidden = label.find_element(By.CLASS_NAME, 'visually-hidden')
                    label_org = hidden.text if hidden else label.text
                except:
                    label_org = label.text if label.text else "Unknown"

            # Method 2: If still Unknown, try span with question text
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                try:
                    span = try_xp(Question, ".//span", False)
                    if span and span.text:
                        label_org = span.text
                except:
                    pass

            # Method 3: Try to get all text from the question container
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                try:
                    question_text = Question.text
                    if question_text and len(question_text) > 5:
                        label_org = question_text.split('\n')[0]
                except:
                    pass

            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = linkedin_summary
                elif 'cover' in label: answer = cover_letter

                print_lg(f"DEBUG: Processing textarea question: '{label_org}'")

                # Tentar responder usando smart_answers e lógica semelhante à de perguntas de texto
                if answer == "":
                    answer = answer_common_questions(label, answer)

                if answer == "":
                    label_full_lower = label_org.lower() if label_org else ""
                    if any(word in label_full_lower for word in ['salário', 'salarial', 'remuneração', 'pretensão', 'expectativas', 'atrativos', 'salary', 'compensation', 'pay']):
                        if 'atual' in label_full_lower or 'current' in label_full_lower:
                            answer = current_ctc
                            print_lg(f"FALLBACK (textarea): Detected CURRENT salary question, answering: {current_ctc}")
                        else:
                            answer = desired_salary
                            print_lg(f"FALLBACK (textarea): Detected DESIRED salary question, answering: {desired_salary}")
                    elif 'python' in label_full_lower:
                        answer = python_experience_years
                        print_lg(f"FALLBACK (textarea): Detected Python experience question from full label, answering: {answer}")
                    elif any(word in label_full_lower for word in ['jurídico', 'juridico', 'legal']):
                        answer = legal_experience_years
                        print_lg(f"FALLBACK (textarea): Detected legal/jurídico experience question from full label, answering: {answer}")
                    elif any(word in label_full_lower for word in ['anos', 'years', 'experiência', 'experience', 'tempo', 'quanto tempo', 'quantos', 'how many']):
                        answer = years_of_experience
                        print_lg(f"FALLBACK (textarea): Detected experience/years question from full label, answering: {answer}")

                if answer == "":
                ##> ------ Yang Li : MARKYangL - Feature ------
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="textarea", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "textarea"))
                            answer = ""
                    else:
                        randomly_answered_questions.add((label_org, "textarea"))
            text_area.clear()
            text_area.send_keys(answer)
            if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            ##<
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e: 
                    print_lg("Checkbox click failed!", e)
                    pass
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list




def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            feedback_msg = driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text.lower()
            # Check for daily limit in English and Portuguese
            if any(phrase in feedback_msg for phrase in [
                "exceeded the daily application limit",
                "limitamos o número de envios diários",
                "limite diário",
                "daily limit",
                "candidate-se amanhã"
            ]): 
                dailyEasyApplyLimitReached = True
                print_lg("\n###############  Limite diário de candidaturas atingido!  ###############\n")
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        # Click Easy Apply button (supports English and Portuguese)
        easy_apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]")))
        easy_apply_btn.click()
        print_lg("Clicked Easy Apply button")
        buffer(1)
        # Try both "Continue" and "Continuar" for Portuguese
        try:
            wait_span_click(driver, "Continue", 1, True, False)
        except:
            wait_span_click(driver, "Continuar", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based om `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Job Link':truncate_for_csv(job_link), 'Resume Tried':truncate_for_csv(resume), 'Date listed':truncate_for_csv(date_listed), 'Date Tried':datetime.now(), 'Assumed Reason':truncate_for_csv(error), 'Stack Trace':truncate_for_csv(exception), 'External Job link':truncate_for_csv(application_link), 'Screenshot Name':truncate_for_csv(screenshot_name)})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        show_alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Title':truncate_for_csv(title), 'Company':truncate_for_csv(company), 'Work Location':truncate_for_csv(work_location), 'Work Style':truncate_for_csv(work_style), 
                            'About Job':truncate_for_csv(description), 'Experience required': truncate_for_csv(experience_required), 'Skills required':truncate_for_csv(skills), 
                                'HR Name':truncate_for_csv(hr_name), 'HR Link':truncate_for_csv(hr_link), 'Resume':truncate_for_csv(resume), 'Re-posted':truncate_for_csv(reposted), 
                                'Date Posted':truncate_for_csv(date_listed), 'Date Applied':truncate_for_csv(date_applied), 'Job Link':truncate_for_csv(job_link), 
                                'External Job link':truncate_for_csv(application_link), 'Questions Found':truncate_for_csv(questions_list), 'Connect Request':truncate_for_csv(connect_request)})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        show_alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Function to close any open discard confirmation modal
def close_discard_modal() -> bool:
    '''
    Closes the discard confirmation modal if it's open.
    Returns True if modal was found and closed, False otherwise.
    '''
    try:
        # Check if discard confirmation modal is open
        discard_modal = driver.find_element(By.XPATH, 
            '//div[@data-test-modal-id="data-test-easy-apply-discard-confirmation" and @aria-hidden="false"]'
        )
        
        # Strategy 1: Click "Descartar" button inside modal (confirms discard)
        discard_strategies = [
            './/button[.//span[normalize-space()="Descartar" or normalize-space()="Discard"]]',
            './/button[contains(@data-control-name, "discard")]',
            './/button[contains(@class, "artdeco-button--primary")]',  # Usually the confirm button
        ]
        
        for strategy in discard_strategies:
            try:
                btn = discard_modal.find_element(By.XPATH, strategy)
                btn.click()
                print_lg(f"✅ Clicked discard button in modal using: {strategy[:50]}")
                buffer(0.5)
                return True
            except:
                continue
        
        # Strategy 2: Press ESC to close modal
        actions.send_keys(Keys.ESCAPE).perform()
        print_lg("✅ Pressed ESC to close discard modal")
        buffer(0.5)
        return True
        
    except NoSuchElementException:
        return False
    except Exception as e:
        print_lg(f"⚠️ Error closing discard modal: {e}")
        return False

# Function to discard the job application
def discard_job() -> None:
    '''
    Discards the current job application by closing any open modals.
    Uses multiple strategies to ensure the modal is properly closed.
    '''
    # First, try to close any existing discard confirmation modal
    if close_discard_modal():
        buffer(0.5)
        return
    
    # Send ESC to trigger discard confirmation
    actions.send_keys(Keys.ESCAPE).perform()
    buffer(1)
    
    # Now try to confirm the discard
    discard_button_strategies = [
        # Strategy 1: Button with span text "Descartar"
        '//div[@data-test-modal-id="data-test-easy-apply-discard-confirmation"]//button[.//span[normalize-space()="Descartar" or normalize-space()="Discard"]]',
        # Strategy 2: Primary button in discard modal
        '//div[@data-test-modal-id="data-test-easy-apply-discard-confirmation"]//button[contains(@class, "artdeco-button--primary")]',
        # Strategy 3: Any button with discard text
        '//button[.//span[normalize-space()="Descartar" or normalize-space()="Discard"]]',
        # Strategy 4: Button with data-control-name
        '//button[contains(@data-control-name, "discard")]',
    ]
    
    for strategy in discard_button_strategies:
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, strategy))
            )
            btn.click()
            print_lg(f"✅ Clicked discard button: {strategy[:50]}...")
            buffer(0.5)
            return
        except:
            continue
    
    # Fallback: Try click_button_multilang
    if not click_button_multilang(driver, ['Descartar', 'Discard', 'Cancelar', 'Cancel'], 2):
        # Last resort: press ESC multiple times
        for _ in range(3):
            actions.send_keys(Keys.ESCAPE).perform()
            buffer(0.3)
        print_lg("⚠️ Used ESC fallback to close modals")






# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')

        apply_filters()

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
                
                if not job_listings:
                    print_lg("No job listings found on this page, moving to next...")
                    break

            
                for job_index in range(len(job_listings)):
                    try:
                        if keep_screen_awake and PYAUTOGUI_AVAILABLE:
                            try:
                                pyautogui.press('shiftright')
                            except:
                                pass
                        if current_count >= switch_number: break
                        print_lg("\n-@-\n")

                        # Re-fetch job listings to avoid stale elements
                        job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
                        if job_index >= len(job_listings):
                            print_lg("Job index out of range, skipping...")
                            break
                        
                        job = job_listings[job_index]
                        job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    except StaleElementReferenceException:
                        print_lg("Stale element in job listing, skipping to next job...")
                        continue
                    
                    if skip: continue
                    # Redundant fail safe check for applied jobs!
                    try:
                        if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                            continue
                    except Exception as e:
                        print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"
                    skills = "Needs an AI" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"
                    jobs_top_card = None  # Initialize to avoid UnboundLocalError

                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")
                        # Try to get jobs_top_card anyway for date calculation
                        try:
                            jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
                        except:
                            pass



                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                        # if connect_hr:
                        #     driver.switch_to.new_window('tab')
                        #     driver.get(hr_link)
                        #     wait_span_click("More")
                        #     wait_span_click("Connect")
                        #     wait_span_click("Add a note")
                        #     message_box = driver.find_element(By.XPATH, "//textarea")
                        #     message_box.send_keys(connect_request_message)
                        #     if close_tabs: driver.close()
                        #     driver.switch_to.window(linkedIn_tab) 
                        # def message_hr(hr_info_card):
                        #     if not hr_info_card: return False
                        #     hr_info_card.find_element(By.XPATH, ".//span[normalize-space()='Message']").click()
                        #     message_box = driver.find_element(By.XPATH, "//div[@aria-label='Write a message…']")
                        #     message_box.send_keys()
                        #     try_xp(driver, "//button[normalize-space()='Send']")        
                    except Exception as e:
                        print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                        # print_lg(e)


                    # Calculation of date posted
                    try:
                        # First, try the standard posted-date element (works for multiple languages)
                        try:
                            time_posted_text = find_by_class(driver, "jobs-unified-top-card__posted-date", 2).text
                        except Exception:
                            # Fallback: search inside the top card for any span that likely contains the date
                            if jobs_top_card:
                                time_posted_el = jobs_top_card.find_element(
                                    By.XPATH,
                                    './/span[contains(@class,"posted") or contains(@class,"listed") or contains(normalize-space(), " ago") or contains(normalize-space(), "há ")]'
                                )
                                time_posted_text = time_posted_el.text
                            else:
                                raise Exception("jobs_top_card not available")

                        print("Time Posted: " + time_posted_text)
                        if "Reposted" in time_posted_text:
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text.strip())
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!", e)


                    description, experience_required, skip, reason, message = get_job_description()
                    if skip:
                        print_lg(message)
                        failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    
                    if use_AI and description != "Unknown":
                        ##> ------ Yang Li : MARKYangL - Feature ------
                        try:
                            if ai_provider.lower() == "openai":
                                skills = ai_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "deepseek":
                                skills = deepseek_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "gemini":
                                skills = gemini_extract_skills(aiClient, description)
                            else:
                                skills = "In Development"
                            print_lg(f"Extracted skills using {ai_provider} AI")
                        except Exception as e:
                            print_lg("Failed to extract skills:", e)
                            skills = "Error extracting skills"
                        ##<

                    uploaded = False
                    # Case 1: Easy Apply Button (supports English and Portuguese)
                    if try_xp(driver, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and (contains(@aria-label, 'Easy') or contains(@aria-label, 'Candidatura simplificada') or contains(., 'Candidatura simplificada'))]"):
                        try: 
                            # Fechar modal de "Lembrete de segurança" se aparecer
                            try:
                                safety_modal = WebDriverWait(driver, 2).until(
                                    EC.presence_of_element_located((By.XPATH, 
                                        '//div[contains(@class, "artdeco-modal") and .//h2[contains(text(), "Lembrete") or contains(text(), "safety") or contains(text(), "Security")]]'
                                    ))
                                )
                                # Clicar em "Continuar candidatura" ou "Continue applying"
                                continue_btn = safety_modal.find_element(By.XPATH, 
                                    './/button[contains(@class, "artdeco-button--primary") or .//span[contains(text(), "Continuar") or contains(text(), "Continue")]]'
                                )
                                continue_btn.click()
                                print_lg("✅ Fechado modal de lembrete de segurança")
                                buffer(1)
                            except:
                                pass
                            
                            try: 
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                # Try clicking Next/Próximo/Avançar button
                                click_button_multilang(modal, ["Avançar", "Próximo"], 1)
                                # if description != "Unknown":
                                #     resume = create_custom_resume(description)
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                previous_questions_hash = None
                                same_questions_count = 0
                                while next_button:
                                    next_counter += 1
                                    
                                    if next_counter >= 20: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            show_alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed")
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    
                                    # NOVO: Fechar modal de descarte se estiver aberto
                                    try:
                                        discard_modal = driver.find_element(By.XPATH, '//div[@data-test-modal-id="data-test-easy-apply-discard-confirmation" and @aria-hidden="false"]')
                                        try:
                                            close_btn = discard_modal.find_element(By.XPATH, './/button[@aria-label="Dismiss" or @aria-label="Fechar" or contains(@aria-label, "Descartar")]')
                                            close_btn.click()
                                            print_lg("✅ Fechado modal de descarte que estava bloqueando")
                                            buffer(1)
                                        except:
                                            actions.send_keys(Keys.ESCAPE).perform()
                                            print_lg("✅ Pressionado ESC para fechar modal de descarte")
                                            buffer(1)
                                    except:
                                        pass
                                    # NOVO: Garantir que modal existe antes de usar
                                    try:
                                        modal = find_by_class(driver, "jobs-easy-apply-modal")
                                    except:
                                        print_lg("⚠️ Modal não encontrado, tentando continuar...")
                                        break
                                    
                                    questions_list = answer_questions(modal, questions_list, work_location, job_description=description)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    
                                    # Fechar qualquer dropdown de autocomplete aberto antes de clicar em Avançar
                                    try:
                                        open_dropdowns = driver.find_elements(By.XPATH, "//div[contains(@class, 'basic-typeahead__triggered-content') or contains(@class, 'typeahead-results')]")
                                        if open_dropdowns:
                                            actions.send_keys(Keys.ESCAPE).perform()
                                            buffer(0.5)
                                            print_lg("✅ Fechado dropdown de autocomplete aberto")
                                    except:
                                        pass
                                    
                                    # NOVO: Tentar encontrar botão Next com múltiplas estratégias
                                    next_button = None
                                    next_button_strategies = [
                                        './/span[normalize-space(.)="Revisar"]',
                                        './/span[normalize-space(.)="Rever"]',
                                        './/span[normalize-space(.)="Avançar"]',
                                        './/span[normalize-space(.)="Próximo"]',
                                        './/button[.//span[contains(text(), "Avançar") or contains(text(), "Próximo") or contains(text(), "Revisar")]]',
                                        './/button[@aria-label="Avançar para a próxima etapa" or contains(@aria-label, "Avançar") or contains(@aria-label, "Continue")]',
                                        './/footer//button[contains(@class, "artdeco-button--primary")]',
                                    ]
                                    
                                    for strategy in next_button_strategies:
                                        try:
                                            next_button = modal.find_element(By.XPATH, strategy)
                                            if next_button and next_button.is_displayed():
                                                print_lg(f"✅ Found next button: {strategy[:50]}")
                                                break
                                        except:
                                            continue
                                    else:
                                        next_button = None
                                    
                                    if next_button:
                                        try:
                                            # Se encontrou um span, clicar no botão pai
                                            if next_button.tag_name == 'span':
                                                parent_button = next_button.find_element(By.XPATH, './ancestor::button')
                                                parent_button.click()
                                            else:
                                                next_button.click()
                                        except ElementClickInterceptedException: 
                                            print_lg("⚠️ Click interceptado, saindo do loop...")
                                            break
                                        except StaleElementReferenceException:
                                            print_lg("Stale element in next button, refreshing modal...")
                                            buffer(1)
                                            try:
                                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                            except:
                                                break
                                            continue
                                    else:
                                        print_lg("⚠️ Botão Next não encontrado, assumindo fim do formulário")
                                        break
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            except StaleElementReferenceException as e:
                                print_lg("Stale element during question answering, retrying...", e)
                                buffer(1)
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                errored = "stale"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Answered the following questions...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                # NOVO: Fechar modal de descarte antes de continuar
                                try:
                                    discard_modal = driver.find_element(By.XPATH, '//div[@data-test-modal-id="data-test-easy-apply-discard-confirmation" and @aria-hidden="false"]')
                                    try:
                                        close_btn = discard_modal.find_element(By.XPATH, './/button[@aria-label="Dismiss" or @aria-label="Fechar"]')
                                        close_btn.click()
                                        print_lg("✅ Fechado modal de descarte antes de submit")
                                        buffer(1)
                                    except:
                                        actions.send_keys(Keys.ESCAPE).perform()
                                        buffer(1)
                                except:
                                    pass
                                
                                # Try clicking Review/Revisar/Avançar button (final step before submit)
                                buffer(2)  # Wait a bit for the page to load
                                # Refresh modal reference
                                try:
                                    modal = find_by_class(driver, "jobs-easy-apply-modal")
                                except:
                                    print_lg("⚠️ Modal não encontrado antes de submit, continuando...")
                                    modal = None
                                
                                if modal:
                                    # Try multiple times with different button texts - SEARCH IN MODAL, NOT DRIVER
                                    if not click_button_multilang(modal, ["Revisar", "Rever"], 3):
                                        # Se Revisar não encontrado, tenta Avançar
                                        if not click_button_multilang(modal, ["Avançar", "Próximo"], 3):
                                            # If still not found, might already be on final screen
                                            print_lg("Review button not found, assuming already on final screen")
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = show_confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    # try_xp(modal, ".//span[normalize-space(.)='Review']")
                                if modal:
                                    follow_company(modal)
                                # Try clicking Submit application/Enviar candidatura button
                                buffer(0.3)
                                
                                submitted = False
                                
                                if modal:
                                    # Strategy 1: Primary button in footer (fastest - usually the submit button)
                                    try:
                                        submit_btn = modal.find_element(By.XPATH, ".//footer//button[contains(@class, 'artdeco-button--primary')]")
                                        submit_btn.click()
                                        print_lg("✅ Clicked primary button in footer")
                                        submitted = True
                                    except:
                                        pass
                                    
                                    # Strategy 2: Direct click via aria-label
                                    if not submitted:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//button[contains(@aria-label, 'Enviar candidatura') or contains(@aria-label, 'Submit application')]")
                                            submit_btn.click()
                                            print_lg("✅ Clicked submit via aria-label")
                                            submitted = True
                                        except:
                                            pass
                                    
                                    # Strategy 3: Button by span text
                                    if not submitted:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//button[.//span[normalize-space()='Enviar candidatura' or normalize-space()='Submit application']]")
                                            submit_btn.click()
                                            print_lg("✅ Clicked submit via span text")
                                            submitted = True
                                        except:
                                            pass
                                
                                if submitted and modal: 
                                    date_applied = datetime.now()
                                    buffer(1.5)  # Wait for confirmation modal to appear
                                    # Try multiple variations for Done button
                                    done_clicked = False
                                    # Try specific XPath for done button
                                    try:
                                        done_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Fechar') or contains(@aria-label, 'Done')]")
                                        done_btn.click()
                                        done_clicked = True
                                        print_lg("Clicked Done button via aria-label")
                                    except:
                                        pass
                                    # Try button with span text
                                    if not done_clicked:
                                        try:
                                            done_btn = driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Concluído') or contains(text(), 'Done') or contains(text(), 'Fechar') or contains(text(), 'OK')]]")
                                            done_btn.click()
                                            done_clicked = True
                                            print_lg("Clicked Done button via span text")
                                        except:
                                            pass
                                    # Try artdeco-modal dismiss button
                                    if not done_clicked:
                                        try:
                                            done_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'artdeco-modal')]//button[contains(@class, 'artdeco-button--primary') or contains(@class, 'artdeco-modal__dismiss')]")
                                            done_btn.click()
                                            done_clicked = True
                                            print_lg("Clicked modal dismiss/primary button")
                                        except:
                                            pass
                                    # Fallback to click_button_multilang
                                    if not done_clicked and not click_button_multilang(driver, ["Concluído", "Fechar", "OK"], 2): 
                                        actions.send_keys(Keys.ESCAPE).perform()
                                        print_lg("Pressed ESC to close modal")
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in show_confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    click_button_multilang(driver, ["Concluído", "Fechar"], 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    # if screenshot_name == "Not Available":  screenshot_name = screenshot(driver, job_id, "Failed to click Submit application")
                                    # else:   screenshot_name = [screenshot_name, screenshot(driver, job_id, "Failed to click Submit application")]
                                    discard_job()
                                    failed_job(job_id, job_link, resume, date_listed, "Failed to submit application", "Modal not found or submit failed", application_link, screenshot_name)
                                    failed_count += 1
                                    continue  # Skip saving as success


                        except Exception as e:
                            print_lg("Failed to Easy apply!")
                            # print_lg(e)
                            critical_error_log("Somewhere in Easy Apply process",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                        if dailyEasyApplyLimitReached:
                            print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                            return
                        if skip: continue

                    submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                    if uploaded:   useNewResume = False

                    print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')
                    current_count += 1
                    if application_link == "Easy Applied": easy_applied_count += 1
                    else:   external_jobs_count += 1
                    applied_jobs.add(job_id)



                # Switching to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    next_page = current_page + 1
                    # Try multiple XPath patterns for next page button
                    next_page_button = None
                    
                    # Method 1: English aria-label
                    try:
                        next_page_button = pagination_element.find_element(By.XPATH, f".//button[@aria-label='Page {next_page}']")
                    except:
                        pass
                    
                    # Method 2: Portuguese aria-label
                    if not next_page_button:
                        try:
                            next_page_button = pagination_element.find_element(By.XPATH, f".//button[@aria-label='Página {next_page}']")
                        except:
                            pass
                    
                    # Method 3: Button with text equal to page number
                    if not next_page_button:
                        try:
                            next_page_button = pagination_element.find_element(By.XPATH, f".//button[normalize-space()='{next_page}']")
                        except:
                            pass
                    
                    # Method 4: Find by data-test-pagination-page
                    if not next_page_button:
                        try:
                            next_page_button = pagination_element.find_element(By.XPATH, f".//button[@data-test-pagination-page='{next_page}']")
                        except:
                            pass
                    
                    if next_page_button:
                        scroll_to_view(driver, next_page_button)
                        next_page_button.click()
                        print_lg(f"\n>-> Now on Page {next_page} \n")
                        buffer(2)  # Wait for page to load
                    else:
                        print_lg(f"\n>-> Didn't find Page {next_page}. Probably at the end page of results!\n")
                        break
                        
                except Exception as e:
                    print_lg(f"\n>-> Error navigating to Page {current_page+1}: {e}\n")
                    break

        except StaleElementReferenceException as e:
            print_lg("Stale element error - page DOM changed. Retrying search...", e)
            buffer(2)
            # Refresh the page and continue
            try:
                driver.refresh()
                buffer(3)
            except:
                pass
            continue  # Try next iteration
        except NoSuchWindowException as e:
            print_lg("Browser window closed. Ending application process.", e)
            raise e  # Re-raise to be caught by main
        except WebDriverException as e:
            # Check if it's actually a stale element hidden in WebDriverException
            if "stale element" in str(e).lower():
                print_lg("Stale element detected in WebDriverException. Retrying...", e)
                buffer(2)
                try:
                    driver.refresh()
                    buffer(3)
                except:
                    pass
                continue
            print_lg("Browser session is invalid. Ending application process.", e)
            raise e  # Re-raise to be caught by main
        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            try:
                print_lg(driver.page_source, pretty=True)
            except Exception as page_source_error:
                print_lg(f"Failed to get page source, browser might have crashed. {page_source_error}")
            # print_lg(e)

        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1        
        validate_config()
        
        if not os.path.exists(default_resume_path):
            show_alert('Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), "Missing Resume")
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            if ai_provider == "openai":
                aiClient = ai_create_openai_client()
            ##> ------ Yang Li : MARKYangL - Feature ------
            # Create DeepSeek client
            elif ai_provider == "deepseek":
                aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                aiClient = gemini_create_client()
            ##<

            try:
                about_company_for_ai = " ".join([word for word in (first_name+" "+last_name).split() if len(word) > 3])
                print_lg(f"Extracted about company info for AI: '{about_company_for_ai}'")
            except Exception as e:
                print_lg("Failed to extract about company info!", e)
        
        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except (NoSuchWindowException, WebDriverException) as e:
        print_lg("Browser window closed or session is invalid. Exiting.", e)
    except Exception as e:
        critical_error_log("In Applier Main", e)
        show_alert(str(e), alert_title)
    finally:
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        quote = choice([
            "You're one step closer than before.", 
            "All the best with your future interviews.", 
            "Keep up with the progress. You got this.", 
            "If you're tired, learn to take rest but never give up.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
            "Opportunities don't happen, you create them. - Chris Grosser",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
            ])
        msg = f"\n{quote}\n\n\nBest regards,\nSai Vignesh Golla\nhttps://www.linkedin.com/in/saivigneshgolla/\n\n"
        show_alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            show_alert(msg, "Info")
            print_lg("\n"+msg)
        ##> ------ Yang Li : MARKYangL - Feature ------
        if use_AI and aiClient:
            try:
                if ai_provider.lower() == "openai":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "deepseek":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "gemini":
                    pass # Gemini client does not need to be closed
                print_lg(f"Closed {ai_provider} AI client.")
            except Exception as e:
                print_lg("Failed to close AI client:", e)
        ##<
        try:
            if driver:
                driver.quit()
        except WebDriverException as e:
            print_lg("Browser already closed.", e)
        except Exception as e: 
            critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
