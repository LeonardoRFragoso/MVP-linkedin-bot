'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    24.12.29.12.30
'''


# Imports
import os
import csv
import re
import pyautogui

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

from backend.bot.config.personals import *
from backend.bot.config.questions import *
from backend.bot.config.search import *
from backend.bot.config.secrets import use_AI, username, password, ai_provider
from backend.bot.config.settings import *

from backend.bot.modules.open_chrome import *
from backend.bot.modules.helpers import *
from backend.bot.modules.clickers_and_finders import *
from backend.bot.modules.validator import validate_config
from backend.bot.modules.questions_bank import get_questions_bank

if use_AI:
    from backend.bot.modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
    from backend.bot.modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
    from backend.bot.modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

from typing import Literal


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
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
        if easy_apply_only:
            try:
                easy_apply_pill = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '//*[@id="searchFilter_applyWithLinkedin"]'
                        ' | //button[contains(@aria-label, "Candidatura simplificada") or contains(@aria-label, "Easy Apply") or contains(normalize-space(), "Candidatura simplificada")]'
                    ))
                )
                aria_checked = (easy_apply_pill.get_attribute("aria-checked") or "").lower()
                if aria_checked != "true":
                    scroll_to_view(driver, easy_apply_pill)
                    easy_apply_pill.click()
                    print_lg('Clicked top-bar "Candidatura simplificada" filter pill')
            except Exception as e:
                # Se falhar, continuamos usando o comportamento antigo via modal "Todos os filtros"
                print_lg('Failed to click top-bar "Candidatura simplificada" filter pill, falling back to All filters modal', e)

        # Em PT-BR o botão é "Todos os filtros". Em EN-US é "All filters".
        wait.until(EC.presence_of_element_located((
            By.XPATH,
            '//button[normalize-space()="All filters" or normalize-space()="Todos os filtros"]'
        ))).click()
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel_noWait(driver, experience_level) 
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies: buffer(recommended_wait)

        multi_sel_noWait(driver, job_type)
        multi_sel_noWait(driver, on_site)
        if job_type or on_site: buffer(recommended_wait)

        if easy_apply_only: boolean_button_click(driver, actions, "Easy Apply")
        
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

        show_results_button: WebElement = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]')
        show_results_button.click()
        
        # CRÍTICO: Aguardar página recarregar após aplicar filtros
        print_lg("⏳ Aguardando página recarregar após filtros...")
        buffer(5)  # Dar tempo para a página recarregar
        
        # Aguardar jobs aparecerem
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
            print_lg("✅ Jobs carregados após aplicar filtros")
        except:
            print_lg("⚠️ Timeout esperando jobs após filtros, continuando...")
        
        buffer(2)  # Buffer adicional de segurança

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        # print_lg(e)



def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Function to get pagination element and current page number
    '''
    try:
        pagination_element = try_find_by_classes(driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//button[contains(@class, 'active')]").text)
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
    # Primeiro pegar job_id (mais estável)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    
    # Depois pegar outros elementos com retry
    job_details_button = job.find_element(By.TAG_NAME, 'a')
    scroll_to_view(driver, job_details_button, True)
    buffer(0.5)  # Pequeno delay após scroll
    
    title = job_details_button.text
    title = title[:title.find("\n")] if "\n" in title else title
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    
    # CORREÇÃO: Extração robusta de work_style com validação
    work_style = 'Não informado'
    if '(' in work_location and ')' in work_location:
        potential_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
        work_location_clean = work_location[:work_location.rfind('(')].strip()
        
        # VALIDAR se é realmente uma modalidade reconhecida
        potential_style_lower = potential_style.lower()
        if 'remote' in potential_style_lower or 'remoto' in potential_style_lower:
            work_style = 'Remoto'
        elif 'hybrid' in potential_style_lower or 'híbrido' in potential_style_lower or 'hibrido' in potential_style_lower:
            work_style = 'Híbrido'
        elif 'on-site' in potential_style_lower or 'presencial' in potential_style_lower or 'onsite' in potential_style_lower or 'on site' in potential_style_lower:
            work_style = 'Presencial'
        else:
            # Se não for modalidade reconhecida, é provavelmente texto incorreto
            work_style = 'Não informado'
            print_lg(f"⚠️ Work style não reconhecido: '{potential_style}' - Salvando como 'Não informado'")
        
        work_location = work_location_clean
    else:
        # Tentar encontrar modalidade no texto completo se não houver parênteses
        location_lower = work_location.lower()
        if 'remote' in location_lower or 'remoto' in location_lower:
            work_style = 'Remoto'
        elif 'hybrid' in location_lower or 'híbrido' in location_lower or 'hibrido' in location_lower:
            work_style = 'Híbrido'
        elif 'on-site' in location_lower or 'presencial' in location_lower:
            work_style = 'Presencial'
    
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
            buffer(0.5)  # Delay antes de clicar
            job_details_button.click()
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
        # print_lg(e)
        discard_job()
        buffer(1)  # Delay antes de retry
        job_details_button.click() # To pass the error outside
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
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        
        # NOVO: Verificar se vaga é 100% presencial em outra cidade (não RJ)
        if not skip:
            is_presential = any(word in jobDescriptionLow for word in ['100% presencial', 'presencial', 'on-site', 'escritório', 'office'])
            cities_not_rj = ['brasília', 'brasilia', 'são paulo', 'sao paulo', 'belo horizonte', 'curitiba', 
                            'porto alegre', 'salvador', 'fortaleza', 'recife', 'manaus', 'goiânia']
            
            if is_presential:
                # Verificar se menciona cidade que não é Rio
                for city in cities_not_rj:
                    if city in jobDescriptionLow and 'rio de janeiro' not in jobDescriptionLow and 'rio' not in work_location.lower():
                        skipMessage = f'\n{jobDescription}\n\nVaga presencial em {city.title()}, fora do Rio de Janeiro. Skipping!\n'
                        skipReason = "Presencial em outra cidade (não RJ)"
                        skip = True
                        print_lg(f"⚠️ Pulando vaga presencial em {city.title()} (você está no Rio)")
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


# Function to select correct resume based on job location
def select_resume_by_location(work_location: str) -> str:
    """
    Seleciona o CV correto baseado na localização da vaga.
    - Vagas no Brasil: CV em Português
    - Vagas internacionais: CV em Inglês
    """
    from backend.bot.config.questions import resume_national, resume_international
    
    location_lower = work_location.lower()
    
    # Lista de indicadores de vaga brasileira
    brazil_indicators = [
        'brasil', 'brazil', 'são paulo', 'sao paulo', 'rio de janeiro',
        'belo horizonte', 'brasília', 'brasilia', 'curitiba', 'porto alegre',
        'recife', 'salvador', 'fortaleza', 'manaus', 'goiânia', 'goiania',
        'campinas', 'florianópolis', 'florianopolis', 'vitória', 'vitoria',
        'paraná', 'parana', 'santa catarina', 'rio grande do sul', 'minas gerais',
        'pernambuco', 'bahia', 'ceará', 'ceara', 'amazonas', 'distrito federal'
    ]
    
    # Detectar se é vaga no Brasil
    is_brazil = any(indicator in location_lower for indicator in brazil_indicators)
    
    if is_brazil:
        print_lg(f"🇧🇷 Vaga nacional detectada ({work_location}) - Usando CV em Português")
        return resume_national
    else:
        print_lg(f"🌎 Vaga internacional detectada ({work_location}) - Usando CV em Inglês")
        return resume_international

# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(resume)
    except:
        return False, "Previous resume"


# Function to answer common questions for Easy Apply using smart answers
def answer_common_questions(label: str, answer: str) -> str:
    '''
    Intelligently answers questions based on keywords in the label
    Supports both Portuguese and English
    Special logic for salary: CLT = 5000, PJ = 7000
    PRIORITY ORDER: Time/experience questions > Salary > Other smart answers
    '''
    import re
    from backend.bot.config.questions import smart_answers, years_of_experience, age_started_programming, current_age, taxa_hora_pj, cpf_number, english_level, get_experience_for_technology
    
    # Convert label to lowercase for matching
    label_lower = label.lower()
    
    # PRIORITY 1: Time/duration questions - these ALWAYS need numeric answers
    # Check for "há quanto tempo", "how long", "quanto tempo", "há quantos anos" patterns
    time_indicators = ['há quanto tempo', 'how long', 'quanto tempo', 'há quantos anos', 
                       'quantos anos', 'how many years', 'years of experience', 
                       'anos de experiência', 'experiência com', 'experience with',
                       'já usa', 'you have been using', 'work experience']
    
    is_time_question = any(indicator in label_lower for indicator in time_indicators)
    
    if is_time_question:
        # NOVO: Usa função inteligente que mapeia 50+ tecnologias diferentes
        experience_answer = get_experience_for_technology(label)
        print_lg(f"✨ Time question detected: '{label[:60]}...' -> {experience_answer} years")
        return str(experience_answer)
    
    # PRIORITY 2: CPF question
    if 'cpf' in label_lower:
        print_lg(f"CPF question detected: '{label}' -> {cpf_number}")
        return str(cpf_number)
    
    # PRIORITY 3: Current age question
    if any(k in label_lower for k in ['sua idade', 'tu edad', 'your age', 'qual é sua idade', 'cuál es tu edad', 'how old are you', 'idade atual', 'current age']):
        print_lg(f"Current age question: '{label}' -> {current_age}")
        return str(current_age)
    
    # PRIORITY 4: Age started programming
    if any(k in label_lower for k in ['programa desde qual idade', 'started programming', 'começou a programar', 'age.*programming']):
        print_lg(f"Age started programming question: '{label}' -> {age_started_programming}")
        return str(age_started_programming)
    
    # PRIORITY 4: Taxa/hora PJ
    if any(k in label_lower for k in ['taxa/hora', 'taxa hora', 'por hora', 'hourly rate', 'rate per hour', '/hora', '/h']):
        print_lg(f"Taxa/hora PJ question: '{label}' -> {taxa_hora_pj}")
        return str(taxa_hora_pj)
    
    # PRIORITY 5: English level
    if any(k in label_lower for k in ['nível de inglês', 'english level', 'proficiency in english', 'inglês', 'english']):
        if 'fluent' in label_lower or 'fluente' in label_lower:
            print_lg(f"English fluency question: '{label}' -> No (Intermediário)")
            return "No"  # User is intermediate, not fluent
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
def answer_questions(modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None, job_id: str | None = None, job_title: str | None = None ) -> set:
    # Get all questions from the page
    
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    all_legacy_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    all_questions = all_questions + all_list_questions + all_single_line_questions + all_legacy_questions
    
    # NOVO: Track de perguntas já processadas para evitar duplicatas
    processed_questions = set()
    
    # NOVO: Get questions bank instance
    questions_bank = get_questions_bank()

    for Question in all_questions:
        try:
            # Criar ID único para esta pergunta (para evitar processar duplicatas)
            try:
                question_id = Question.get_attribute('data-test-form-element') or Question.get_attribute('id') or Question.text[:100]
                
                # Se já processamos esta pergunta, pular
                if question_id in processed_questions:
                    continue
                    
                processed_questions.add(question_id)
            except:
                pass  # Se falhar, continuar normalmente
            
            # Texto completo do bloco da pergunta (caso o label seja difícil de capturar)
            question_block_text = (Question.text or "").strip()
            question_block_lower = question_block_text.lower()
        except StaleElementReferenceException:
            print_lg("Stale element in question, skipping...")
            continue

        # Tratamento direto para perguntas de pretensão salarial que podem fugir da lógica normal de label
        if any(word in question_block_lower for word in ['pretensão', 'pretensao', 'salário', 'salario', 'remuneração', 'remuneracao', 'expectativas em termos de remuneração', 'salary expectation', 'salary expectations', 'compensation']):
            try:
                input_or_textarea = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number'] | .//textarea", False)
            except Exception:
                input_or_textarea = None

            if input_or_textarea:
                current_value = input_or_textarea.get_attribute("value") or ""
                if not current_value.strip() or overwrite_previous_answers:
                    smart_answer = answer_common_questions(question_block_lower, "")
                    answer_value = smart_answer if smart_answer else "5000"
                    # DEBUG: print_lg(f"Direct salary handler for block '{question_block_text[:80]}', answering: '{answer_value}'")
                    input_or_textarea.clear()
                    input_or_textarea.send_keys(str(answer_value))
                    questions_list.add(("direct-salary:" + question_block_lower, str(answer_value), "text-or-textarea", current_value))
                    continue

        # Tratamento direto para perguntas de anos de experiência específicas (CI/CD, TI)
        # Útil quando o label do input não é associado corretamente, mas o texto do bloco contém a pergunta.
        ci_cd_keywords = ['integração e entrega contínuas', 'integração contínua', 'entrega contínua', 'ci/cd', 'continuous integration', 'continuous delivery']
        it_keywords = ['tecnologia da informação', 'information technology', 'it experience']

        if any(k in question_block_lower for k in ci_cd_keywords):
            try:
                exp_input = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number']", False)
            except Exception:
                exp_input = None
            if exp_input:
                current_value = exp_input.get_attribute("value") or ""
                if not current_value.strip() or overwrite_previous_answers:
                    answer_value = ci_cd_experience_years
                    # DEBUG: print_lg(f"Direct CI/CD experience handler for block '{question_block_text[:80]}', answering: '{answer_value}'")
                    exp_input.clear()
                    exp_input.send_keys(str(answer_value))
                    questions_list.add(("direct-cicd:" + question_block_lower, str(answer_value), "text", current_value))
                    continue

        if any(k in question_block_lower for k in it_keywords):
            try:
                exp_input = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number']", False)
            except Exception:
                exp_input = None
            if exp_input:
                current_value = exp_input.get_attribute("value") or ""
                if not current_value.strip() or overwrite_previous_answers:
                    answer_value = it_experience_years
                    # DEBUG: print_lg(f"Direct IT experience handler for block '{question_block_text[:80]}', answering: '{answer_value}'")
                    exp_input.clear()
                    exp_input.send_keys(str(answer_value))
                    questions_list.add(("direct-it:" + question_block_lower, str(answer_value), "text", current_value))
                    continue

        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            try:
                label_org = "Unknown"
                try:
                    label = Question.find_element(By.TAG_NAME, "label")
                    label_org = label.find_element(By.TAG_NAME, "span").text
                except: pass
                answer = 'Yes'
                label = label_org.lower()
                select = Select(select)
                selected_option = select.first_selected_option.text
                optionsText = []
                options = '"List of phone country codes"'
                if label != "phone country code":
                    optionsText = [option.text for option in select.options]
                    options = "".join([f' "{option}",' for option in optionsText])
                prev_answer = selected_option
                
                # NOVO: Consultar banco de perguntas primeiro
                stored_answer = questions_bank.get_answer(label_org, "select")
                if stored_answer and not overwrite_previous_answers:
                    answer = stored_answer
                    print_lg(f"💾 Using stored answer from bank for SELECT: '{label_org[:50]}...' -> '{answer}'")
                elif overwrite_previous_answers or selected_option == "Select an option" or selected_option == "Selecionar opção" or selected_option == "Selecciona una opción" or "selecionar" in selected_option.lower() or "selecciona" in selected_option.lower():
                    ##> ------ WINDY_WINDWARD Email:karthik.sarode23@gmail.com - Added fuzzy logic to answer location based questions ------
                    if 'email' in label or 'phone' in label: 
                        answer = prev_answer
                    elif 'gender' in label or 'sex' in label: 
                        answer = gender
                    elif 'disability' in label: 
                        answer = disability_status
                    # Acceptance questions (Aceita remuneração, aceita benefícios, etc.) - Yes/No dropdowns
                    elif any(accept_word in label for accept_word in ['aceita', 'accept', 'concorda', 'agree', 'toparia', 'gostaria']):
                        answer = 'Yes'
                        print_lg(f"Detected acceptance question, answering: Yes")
                    # English/Language proficiency questions - match available options
                    elif ('inglês' in label or 'ingles' in label or 'english' in label) and ('nível' in label or 'nivel' in label or 'level' in label or 'proficiência' in label or 'proficiency' in label):
                        # Try to find appropriate option based on available choices
                        options_lower = [opt.lower() for opt in optionsText]
                        if any('conversação' in opt or 'conversacao' in opt for opt in options_lower):
                            answer = 'Conversação'
                        elif any('intermediário' in opt or 'intermediario' in opt for opt in options_lower):
                            answer = 'Intermediário'
                        elif any('b2' in opt for opt in options_lower):
                            answer = 'B2'
                        elif any('proficiente' in opt or 'proficient' in opt for opt in options_lower):
                            answer = 'Proficiente'
                        else:
                            answer = 'Conversação'  # Default fallback
                        print_lg(f"Detected English level question, answering: {answer}")
                    elif 'proficiency' in label: 
                        answer = 'Professional'
                    # Availability questions (disponibilidade)
                    elif 'disponibilidade' in label or 'availability' in label or 'disponível' in label or 'available' in label:
                        answer = 'Sim'  # Default to Yes for availability
                        print_lg(f"Detected availability question, answering: Sim")
                    # Add location handling
                    elif any(loc_word in label for loc_word in ['location', 'city', 'state', 'country']):
                        if 'country' in label:
                            answer = country 
                        elif 'state' in label:
                            answer = state
                        elif 'city' in label or 'cidade' in label:
                            answer = current_city  # SEMPRE usar sua cidade, não da vaga
                            print_lg(f"📍 Detected city question, answering: {answer}")
                        else:
                            answer = current_city  # Default para sua cidade
                    # Work authorization Latin America - Yes
                    elif 'work authorization' in label or 'autorização' in label or 'eligible to work' in label:
                        if 'latin america' in label or 'américa latina' in label or 'latam' in label:
                            answer = 'Yes'
                            print_lg(f"Detected Latin America work auth question, answering: Yes")
                        else:
                            answer = 'Yes'
                            print_lg(f"Detected work authorization question, answering: Yes")
                    # How did you hear about this opportunity - LinkedIn
                    elif 'how did you hear' in label or 'como soube' in label or 'como conheceu' in label or 'hear about' in label:
                        answer = 'LinkedIn'
                        print_lg(f"Detected referral source question, answering: LinkedIn")
                    # Graduation year - try to find 2022 in options
                    elif ('graduation' in label and 'year' in label) or ('year' in label and ('graduate' in label or 'bachelor' in label)) or ('ano' in label and ('formatura' in label or 'graduação' in label)):
                        # Try to find 2022 in options
                        if any('2022' in opt for opt in optionsText):
                            answer = '2022'
                        else:
                            answer = '2022'
                        print_lg(f"Detected graduation year question, answering: 2022")
                    # GPA / Academic score questions - answer N/A
                    elif 'gpa' in label or 'grade point' in label or label == 'unknown':
                        # Check if N/A is an option
                        if any('n/a' in opt.lower() for opt in optionsText):
                            answer = 'N/A'
                        else:
                            answer = 'N/A'
                        print_lg(f"Detected GPA question, answering: N/A")
                    # LOCALIZAÇÃO - Verificar cidade/estado específico (SELECT)
                    elif any(loc_word in label for loc_word in ['reside', 'mora', 'live in', 'located in', 'você está em', 'atualmente em', 'currently in']):
                        # Verificar se menciona Rio de Janeiro
                        if 'rio de janeiro' in label or ' rio ' in label or ' rj ' in label:
                            answer = 'Yes'
                            print_lg(f"✅ Location SELECT (Rio de Janeiro), answering: Yes")
                        # Verificar se menciona Brasil sem cidade específica
                        elif ('brasil' in label or 'brazil' in label) and 'brasília' not in label and 'brasilia' not in label:
                            answer = 'Yes'
                            print_lg(f"✅ Location SELECT (Brasil), answering: Yes")
                        # Se menciona Brasília, São Paulo ou outra cidade
                        else:
                            answer = 'No'
                            print_lg(f"❌ Location SELECT (outra cidade em '{label_org[:50]}...'), answering: No")
                    # Vaga 100% presencial em outra cidade
                    elif ('100% presencial' in label or 'presencial' in label) and 'tudo certo' in label:
                        # Verificar se menciona Rio
                        if 'rio de janeiro' in label or 'rio' in label or ' rj' in label:
                            answer = 'Yes'
                            print_lg(f"✅ On-site work in Rio, answering: Yes")
                        else:
                            answer = 'No'
                            print_lg(f"❌ On-site work in other city ('{label_org[:40]}'), answering: No")
                    # Technical skills questions - default to Sim (Yes)
                    elif any(tech in label for tech in ['cloudformation', 'terraform', 'infra as code', 'kubernetes', 'k8s', 
                        'jenkins', 'azure devops', 'ci/cd', 'cicd', 'gitlab', 'github', 'docker', 'container',
                        'aws', 'amazon', 'ec2', 's3', 'lambda', 'linux', 'shell', 'python', 'git', 
                        'postgresql', 'mysql', 'mongodb', 'sql', 'nosql', 'api', 'rest', 'graphql',
                        'version control', 'controle de versão', 'api integration', 'integração de api',
                        'css', 'scss', 'sass', 'html', 'html5', 'javascript', 'typescript', 'react', 'next.js', 'nextjs',
                        'frontend', 'front-end', 'backend', 'back-end', 'fullstack', 'full-stack', 'full stack',
                        'forte conhecimentos', 'conhecimento avançado', 'conhecimento em']):
                        answer = 'Yes'
                        print_lg(f"Detected technical skill question, answering: Yes")
                    # Experience questions with Yes/No options (Possui experiência, Você tem, Já trabalhou, etc.)
                    elif any(exp_word in label for exp_word in ['possui', 'você tem', 'ja teve', 'já teve', 'já trabalhou', 'ja trabalhou', 'experience', 'experiência', 'trabalharia', 'topa', 'toparia', 'negociável', 'negociavel']):
                        answer = 'Yes'
                        print_lg(f"Detected experience/acceptance question, answering: Yes")
                    else: 
                        answer = answer_common_questions(label,answer)
                    try: 
                        select.select_by_visible_text(answer)
                    except NoSuchElementException as e:
                        # Define similar phrases for common answers
                        possible_answer_phrases = []
                        if answer == 'Decline':
                            possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"]
                        elif 'yes' in answer.lower() or answer.lower() == 'sim':
                            possible_answer_phrases = ["Yes", "Agree", "I do", "I have", "Sim", "sim", "Tenho", "Aceito"]
                        elif 'no' in answer.lower() or answer.lower() == 'não' or answer.lower() == 'nao':
                            possible_answer_phrases = ["No", "Disagree", "I don't", "I do not", "Não", "não", "Nao", "nao"]
                        else:
                            # Try partial matching for any answer
                            possible_answer_phrases = [answer]
                            # Add lowercase and uppercase variants
                            possible_answer_phrases.append(answer.lower())
                            possible_answer_phrases.append(answer.upper())
                            # Try without special characters
                            possible_answer_phrases.append(''.join(c for c in answer if c.isalnum()))
                        ##<
                        foundOption = False
                        for phrase in possible_answer_phrases:
                            for option in optionsText:
                                # Check if phrase is in option or option is in phrase (bidirectional matching)
                                if phrase.lower() in option.lower() or option.lower() in phrase.lower():
                                    select.select_by_visible_text(option)
                                    answer = option
                                    foundOption = True
                                    break
                        if not foundOption:
                            #TODO: Use AI to answer the question need to be implemented logic to extract the options for the question
                            print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                            select.select_by_index(randint(1, len(select.options)-1))
                            answer = select.first_selected_option.text
                            randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
                
                # NOVO: Salvar pergunta no banco
                questions_bank.add_question(
                    label=label_org,
                    answer=answer,
                    question_type="select",
                    options=optionsText,
                    prev_answer=prev_answer,
                    job_id=job_id,
                    job_title=job_title
                )
                questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            except StaleElementReferenceException:
                print_lg("Stale element in select dropdown, skipping...")
            continue
        
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
            
            # NOVO: Consultar banco de perguntas primeiro
            stored_answer = questions_bank.get_answer(label_org.rstrip(' [,'), "radio")
            if stored_answer and not overwrite_previous_answers:
                answer = stored_answer
                print_lg(f"💾 Using stored answer from bank for RADIO: '{label_org[:50]}...' -> '{answer}'")
            elif overwrite_previous_answers or prev_answer is None:
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
                # Disponibilidade para trabalhar presencialmente em cidade específica
                elif 'presencial' in label or 'on-site' in label or 'escritório' in label or 'office' in label:
                    # Apenas se for Rio de Janeiro
                    if 'rio de janeiro' in label or 'rio' in label or ' rj' in label:
                        answer = 'Yes'
                        print_lg(f"✅ On-site work in Rio, answering: Yes")
                    # Se for remoto/híbrido, aceitar
                    elif 'remoto' in label or 'remote' in label or 'híbrido' in label or 'hybrid' in label:
                        answer = 'Yes'
                        print_lg(f"✅ Remote/Hybrid work, answering: Yes")
                    # Se for outra cidade
                    else:
                        answer = 'No'
                        print_lg(f"❌ On-site work in other city ('{label_org[:40]}...'), answering: No")
                # English confidence - Yes
                elif 'confident' in label and 'english' in label:
                    answer = 'Yes'
                    print_lg(f"✅ Detected English confidence radio, answering: Yes")
                # Perguntas sobre LOCALIZAÇÃO - Verificar cidade/estado específico
                elif 'reside' in label or 'mora' in label or 'live in' in label or 'located in' in label or 'você está em' in label or 'atualmente em' in label or 'currently in' in label:
                    # Verificar se menciona sua cidade/estado
                    if 'rio de janeiro' in label or ' rio ' in label or ' rj ' in label or label.startswith('rio '):
                        answer = 'Yes'
                        print_lg(f"✅ Location question (Rio de Janeiro), answering: Yes")
                    # Verificar se menciona Brasil (sem mencionar cidade específica)
                    elif 'brasil' in label or 'brazil' in label:
                        if 'brasília' not in label and 'brasilia' not in label:  # Excluir Brasília-DF
                            answer = 'Yes'
                            print_lg(f"✅ Location question (Brasil), answering: Yes")
                        else:
                            answer = 'No'
                            print_lg(f"❌ Location question (Brasília-DF), answering: No")
                    # Se menciona outra cidade/estado específico (São Paulo, Brasília, etc)
                    else:
                        answer = 'No'
                        print_lg(f"❌ Location question (outra cidade em '{label_org[:50]}...'), answering: No")
                # Perguntas de experiência com tecnologias - SEMPRE responder Yes
                # Nunca responder "No" pois desqualifica automaticamente (exceto localização)
                elif 'do you have experience' in label or 'você tem experiência' in label or 'experience with' in label or 'feel confident' in label:
                    answer = 'Yes'
                    print_lg(f"✅ Experience/confidence question detected, answering: Yes ('{label_org[:50]}...')")

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
            
            # NOVO: Salvar pergunta no banco
            questions_bank.add_question(
                label=label_org.rstrip(' [,') + " ]",
                answer=answer,
                question_type="radio",
                options=[opt.split('"')[1] if '"' in opt else opt for opt in options_labels],
                prev_answer=prev_answer,
                job_id=job_id,
                job_title=job_title
            )
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question (try multiple input types)
        text = try_xp(Question, ".//input[@type='text']", False)
        if not text:
            text = try_xp(Question, ".//input[not(@type) or @type='text' or @type='number' or @type='tel']", False)
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
                    span = try_xp(Question, ".//span", False)
                    if span and span.text:
                        label_org = span.text
                except: pass
            
            # Method 3: Try to get all text from the question container
            if not label_org or label_org == "Unknown" or label_org.strip() == "":
                try:
                    question_text = Question.text
                    if question_text and len(question_text) > 5:
                        label_org = question_text.split('\n')[0]  # Get first line
                except: pass
            
            # DEBUG: print_lg(f"Found text input, label: '{label_org[:80]}...'" if len(label_org) > 80 else f"Found text input, label: '{label_org}'")
            
            answer = "" # years_of_experience
            label = label_org.lower()
            
            # DEBUG: Log the question being processed
            # DEBUG: print_lg(f"Processing text question: '{label_org[:100]}...' " if len(label_org) > 100 else f"Processing text question: '{label_org}'")

            prev_answer = text.get_attribute("value")
            
            # NOVO: Consultar banco de perguntas primeiro
            stored_answer = questions_bank.get_answer(label_org, "text")
            if stored_answer and not overwrite_previous_answers:
                answer = stored_answer
                print_lg(f"💾 Using stored answer from bank for TEXT: '{label_org[:50]}...' -> '{answer}'")
            elif not prev_answer or overwrite_previous_answers:
                # Current age - CHECK FIRST
                if any(k in label for k in ['sua idade', 'tu edad', 'your age', 'qual é sua idade', 'cuál es tu edad', 'how old are you', 'idade atual', 'current age', 'what is your age']):
                    answer = current_age
                    print_lg(f"Detected current age question, answering: {answer}")
                # Age when started programming - MUST NOT trigger on experience questions
                elif ('desde qual idade' in label and 'programa' in label) or \
                   ('qual idade' in label and 'programa' in label and 'desde' in label) or \
                   ('age' in label and 'started' in label and 'programming' in label and 'experience' not in label and 'years' not in label):
                    answer = age_started_programming
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
                # Java experience - PRIORITY CHECK
                elif 'java' in label and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = java_experience_years
                    print_lg(f"Detected Java experience question, answering: {answer}")
                # Node.js experience
                elif ('node' in label or 'nodejs' in label or 'node.js' in label) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = nodejs_experience_years
                    print_lg(f"Detected Node.js experience question, answering: {answer}")
                # React experience
                elif ('react' in label or 'reactjs' in label or 'react.js' in label) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = reactjs_experience_years
                    print_lg(f"Detected React experience question, answering: {answer}")
                # Python experience
                elif 'python' in label and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = python_experience_years
                    print_lg(f"Detected Python experience question, answering: {answer}")
                # CI/CD experience questions
                elif (('ci/cd' in label) or ('integração e entrega contínuas' in label) or ('integração contínua' in label) or ('entrega contínua' in label) or ('continuous integration' in label) or ('continuous delivery' in label)) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = ci_cd_experience_years
                    print_lg(f"Detected CI/CD experience question, answering: {answer}")
                # Information Technology experience questions
                elif ('tecnologia da informação' in label or 'information technology' in label) and ('experience' in label or 'years' in label or 'anos' in label or 'experiência' in label):
                    answer = it_experience_years
                    print_lg(f"Detected IT experience question, answering: {answer}")
                elif 'jurídico' in label or 'juridico' in label:
                    answer = legal_experience_years
                    print_lg(f"Detected legal experience question, answering: {answer}")
                elif 'experience' in label or 'years' in label or 'anos' in label or 'experiência' in label:
                    answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label or 'endereço' in label or 'rua' in label: answer = street
                elif 'city' in label or 'cidade' in label:
                    answer = current_city  # SEMPRE usar sua cidade
                    print_lg(f"📍 City question in text field, answering: {answer}")
                    do_actions = True
                elif 'location' in label or 'localização' in label or 'address' in label:
                    answer = f"{current_city}, {state}, {country}"  # Endereço completo
                    print_lg(f"📍 Location/address question, answering: {answer}")
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
                # DEBUG: print_lg(f"Answering with: '{answer}'")
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            
            # NOVO: Salvar pergunta no banco
            questions_bank.add_question(
                label=label_org,
                answer=text.get_attribute("value"),
                question_type="text",
                prev_answer=prev_answer,
                job_id=job_id,
                job_title=job_title
            )
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
            
            # NOVO: Consultar banco de perguntas primeiro
            stored_answer = questions_bank.get_answer(label_org, "textarea")
            if stored_answer and not overwrite_previous_answers:
                answer = stored_answer
                print_lg(f"💾 Using stored answer from bank for TEXTAREA: '{label_org[:50]}...' -> '{answer[:80]}...'")
            elif not prev_answer or overwrite_previous_answers:
                # Detecção melhorada para Summary e Cover Letter
                if 'summary' in label or 'resumo' in label or 'sobre você' in label or 'about you' in label:
                    answer = linkedin_summary
                    print_lg(f"✍️ Preenchendo Summary: '{label_org}'")
                elif 'cover' in label or 'carta' in label or 'carta de apresentação' in label or 'cover letter' in label:
                    answer = cover_letter
                    print_lg(f"✍️ Preenchendo Cover Letter: '{label_org}'")

                # Tentar responder usando smart_answers e lógica semelhante à de perguntas de texto
                if answer == "":
                    answer = answer_common_questions(label, answer)

                # Se ainda não tem resposta, tentar respostas técnicas genéricas
                if answer == "":
                    label_full_lower = label_org.lower() if label_org else ""
                    
                    # Perguntas de salário
                    if any(word in label_full_lower for word in ['salário', 'salarial', 'remuneração', 'pretensão', 'expectativas', 'atrativos', 'salary', 'compensation', 'pay']):
                        if 'atual' in label_full_lower or 'current' in label_full_lower:
                            answer = current_ctc
                            print_lg(f"💰 Detectada pergunta de salário atual: {current_ctc}")
                        else:
                            answer = desired_salary
                            print_lg(f"💰 Detectada pergunta de salário desejado: {desired_salary}")
                    
                    # Perguntas técnicas sobre redes/protocolos
                    elif any(word in label_full_lower for word in ['network', 'protocol', 'rede', 'protocolo', 'fragmentation', 'fragmentação', 'multiplexing', 'multiplexação']):
                        answer = "I have hands-on experience with network protocols including TCP/IP, UDP, and HTTP/HTTPS. Regarding fragmentation, I understand it's the process of breaking large packets into smaller units to fit network MTU sizes. Multiplexing allows multiple data streams to share the same network connection efficiently. I've worked with these concepts in distributed systems and API integrations, ensuring reliable data transmission and optimal network performance."
                        print_lg(f"🌐 Pergunta técnica de redes detectada, respondendo...")
                    
                    # Perguntas sobre serialização/desserialização
                    elif any(word in label_full_lower for word in ['serialization', 'serialização', 'binary', 'binário', 'format', 'formato']):
                        answer = "I have experience with binary serialization using formats like JSON, Protocol Buffers, and MessagePack. I've used these for efficient data storage and transmission in APIs and microservices. My hands-on work includes implementing serialization for REST APIs, handling large datasets, and optimizing data transfer between services while maintaining compatibility and performance."
                        print_lg(f"📦 Pergunta sobre serialização detectada, respondendo...")
                    
                    # Perguntas sobre experiência hands-on genéricas
                    elif any(word in label_full_lower for word in ['hands-on', 'experience', 'experiência', 'describe', 'descreva', 'explain', 'explique']):
                        answer = "I have extensive hands-on experience working with Python, Django, Flask, React, and Node.js. My expertise includes building scalable web applications, RESTful APIs, database management (PostgreSQL, MongoDB), and implementing automated solutions. I've successfully delivered multiple projects involving full-stack development, system integrations, and continuous deployment practices."
                        print_lg(f"💼 Pergunta genérica de experiência detectada, respondendo...")
                    
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
                
                # FALLBACK FINAL: Se AI não respondeu e ainda não tem resposta
                if answer == "" or not answer:
                    answer = "Yes, I have experience with this technology and concept. Throughout my career as a Full Stack Developer, I've worked extensively with Python, Django, Flask, React, and Node.js, which has given me a solid foundation in various technical concepts and best practices. I'm comfortable learning and adapting to new technologies and methodologies as needed for the project requirements."
                    print_lg(f"⚠️ Usando resposta técnica genérica para: '{label_org[:60]}...'")
                    randomly_answered_questions.add((label_org, "textarea-generic-fallback"))
            
            text_area.clear()
            text_area.send_keys(answer)
            if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            
            # NOVO: Salvar pergunta no banco
            questions_bank.add_question(
                label=label_org,
                answer=text_area.get_attribute("value"),
                question_type="textarea",
                prev_answer=prev_answer,
                job_id=job_id,
                job_title=job_title
            )
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
def add_to_rejected_jobs(job_id: str, reason: str) -> None:
    '''
    NOVO: Adiciona job ID à lista de rejected jobs para evitar múltiplas tentativas
    '''
    try:
        rejected_jobs_file = "all excels/rejected_jobs.txt"
        with open(rejected_jobs_file, 'a', encoding='utf-8') as file:
            file.write(f"{job_id}|{reason}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print_lg(f"🚫 Job {job_id} adicionado à blacklist (Motivo: {reason})")
    except Exception as e:
        print_lg(f"⚠️ Erro ao adicionar job {job_id} à blacklist: {e}")


def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        # NOVO: Adicionar à blacklist para não tentar novamente
        add_to_rejected_jobs(job_id, error)
        
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Job Link':truncate_for_csv(job_link), 'Resume Tried':truncate_for_csv(resume), 'Date listed':truncate_for_csv(date_listed), 'Date Tried':datetime.now(), 'Assumed Reason':truncate_for_csv(error), 'Stack Trace':truncate_for_csv(exception), 'External Job link':truncate_for_csv(application_link), 'Screenshot Name':truncate_for_csv(screenshot_name)})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


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
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Function to discard the job application
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    buffer(0.5)
    
    # Try to find and click discard button in confirmation modal
    discard_buttons = [
        'Descartar', 'Descartar candidatura', 'Sair', 'Sair sem salvar',
        'Discard', 'Discard application', 'Exit', 'Leave', 
        'Cancelar', 'Cancel', 'Fechar', 'Close'
    ]
    
    if not click_button_multilang(driver, discard_buttons, 2):
        # Try clicking via aria-label for the discard confirmation modal
        try:
            discard_modal = driver.find_element(By.XPATH, "//div[@data-test-modal-id='data-test-easy-apply-discard-confirmation']")
            # Try primary/secondary buttons in the modal
            buttons_to_try = [
                ".//button[contains(@class, 'artdeco-button--primary')]",
                ".//button[contains(@class, 'artdeco-button--secondary')]",
                ".//button[@data-test-dialog-primary-btn]",
                ".//button[@data-test-dialog-secondary-btn]"
            ]
            for btn_xpath in buttons_to_try:
                try:
                    btn = discard_modal.find_element(By.XPATH, btn_xpath)
                    btn.click()
                    print_lg("✅ Closed discard confirmation modal")
                    buffer(0.5)
                    return
                except:
                    continue
        except:
            pass
        
        # Last resort: multiple ESC presses
        for _ in range(3):
            actions.send_keys(Keys.ESCAPE).perform()
            buffer(0.3)






# NOVA FUNÇÃO: Carregar jobs rejeitados/falhados do arquivo
def get_rejected_job_ids() -> set:
    '''
    Carrega IDs de jobs que falharam anteriormente para evitar múltiplas tentativas
    '''
    rejected_jobs = set()
    rejected_jobs_file = "all excels/rejected_jobs.txt"
    
    try:
        if os.path.exists(rejected_jobs_file):
            with open(rejected_jobs_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.strip():
                        # Formato: job_id|reason|date
                        parts = line.strip().split('|')
                        if parts:
                            rejected_jobs.add(parts[0])
            print_lg(f"✅ Carregados {len(rejected_jobs)} jobs na blacklist (já tentados e falharam)")
    except Exception as e:
        print_lg(f"⚠️ Erro ao carregar rejected jobs: {e}")
    
    return rejected_jobs


# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = get_rejected_job_ids()  # ATUALIZADO: Carregar de arquivo
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
                # Wait until job listings are loaded with more patience
                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
                except:
                    print_lg("⚠️ Timeout esperando jobs carregarem, tentando novamente...")
                    buffer(5)
                    continue

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(2)  # Reduzido de 3 para 2 (já temos wait antes)
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
                
                # NOVO: Validar se pegou jobs
                if not job_listings:
                    print_lg("⚠️ Nenhum job encontrado na página, aguardando...")
                    buffer(5)
                    continue

            
                for job_index, job in enumerate(job_listings):
                    try:
                        if keep_screen_awake: pyautogui.press('shiftright')
                        if current_count >= switch_number: break
                        print_lg("\n-@-\n")

                        # RETRY LOGIC: Tentar até 3x em caso de stale element
                        max_retries = 3
                        for retry in range(max_retries):
                            try:
                                # Re-buscar o elemento se for retry
                                if retry > 0:
                                    print_lg(f"🔄 Retry {retry}/{max_retries} para job #{job_index}...")
                                    buffer(2)
                                    job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
                                    if job_index >= len(job_listings):
                                        print_lg("⚠️ Job não existe mais na lista, pulando...")
                                        break
                                    job = job_listings[job_index]
                                
                                job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                                break  # Sucesso, sair do retry loop
                                
                            except StaleElementReferenceException as e:
                                if retry == max_retries - 1:
                                    print_lg(f"❌ Stale element após {max_retries} tentativas, pulando job...")
                                    raise  # Re-raise para ser pego pelo except externo
                                print_lg(f"⚠️ Stale element detectado, tentando novamente...")
                                buffer(1)
                                
                    except StaleElementReferenceException:
                        print_lg("⚠️ Job ficou stale mesmo após retries, pulando...")
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
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    questions_list = answer_questions(modal, questions_list, work_location, job_description=description, job_id=job_id, job_title=title)
                                    if useNewResume and not uploaded:
                                        # Selecionar CV correto baseado na localização da vaga
                                        selected_resume = select_resume_by_location(work_location)
                                        uploaded, resume = upload_resume(modal, selected_resume)
                                    try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Revisar"]') 
                                    except NoSuchElementException:  
                                        try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Rever"]')
                                        except NoSuchElementException:
                                            try: next_button = modal.find_element(By.XPATH, './/button[contains(span, "Avançar") or contains(span, "Próximo")]')
                                            except NoSuchElementException: next_button = modal.find_element(By.XPATH, './/button[@aria-label="Avançar para a próxima etapa" or contains(@aria-label, "Avançar")]')
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Happens when it tries to click Next button in About Company photos section
                                    except StaleElementReferenceException:
                                        print_lg("Stale element in next button, refreshing modal...")
                                        buffer(1)
                                        modal = find_by_class(driver, "jobs-easy-apply-modal")
                                        continue
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
                                # Try clicking Review/Revisar/Avançar button (final step before submit)
                                buffer(2)  # Wait a bit for the page to load
                                # Refresh modal reference to avoid stale elements
                                try:
                                    modal = find_by_class(driver, "jobs-easy-apply-modal")
                                except:
                                    print_lg("Modal not found, might have been closed")
                                # Try multiple times with different button texts - SEARCH IN MODAL, NOT DRIVER
                                if not click_button_multilang(modal, ["Revisar", "Rever"], 3):
                                    # Se Revisar não encontrado, tenta Avançar
                                    if not click_button_multilang(modal, ["Avançar", "Próximo"], 3):
                                        # If still not found, might already be on final screen
                                        print_lg("Review button not found, assuming already on final screen")
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    # try_xp(modal, ".//span[normalize-space(.)='Review']")
                                follow_company(modal)
                                # Try clicking Submit application/Enviar candidatura button
                                buffer(1)  # Wait a bit before submitting
                                
                                # SCROLL THE MODAL TO THE BOTTOM to ensure submit button is visible
                                # MELHORADO: Scroll múltiplas vezes para garantir chegar ao final
                                print_lg("⬇️ Scrolling modal to bottom...")
                                scroll_success = False
                                
                                try:
                                    # Strategy 1: Find scrollable container and scroll múltiplas vezes
                                    modal_content = modal.find_element(By.XPATH, ".//div[contains(@class, 'jobs-easy-apply-content') or contains(@class, 'artdeco-modal__content')]")
                                    
                                    # Scroll gradualmente até o final (máximo 5 tentativas)
                                    for scroll_attempt in range(5):
                                        last_height = driver.execute_script("return arguments[0].scrollTop", modal_content)
                                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal_content)
                                        buffer(0.3)  # Aguardar conteúdo carregar
                                        new_height = driver.execute_script("return arguments[0].scrollTop", modal_content)
                                        
                                        # Se não mudou, chegou ao final
                                        if last_height == new_height:
                                            break
                                    
                                    print_lg(f"✅ Scrolled modal content to bottom (após {scroll_attempt + 1} tentativas)")
                                    scroll_success = True
                                    buffer(0.5)
                                except:
                                    print_lg("⚠️ Falha ao scrollar modal content, tentando fallback...")
                                
                                # Fallback 1: Scroll o modal inteiro
                                if not scroll_success:
                                    try:
                                        for scroll_attempt in range(5):
                                            last_height = driver.execute_script("return arguments[0].scrollTop", modal)
                                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
                                            buffer(0.3)
                                            new_height = driver.execute_script("return arguments[0].scrollTop", modal)
                                            if last_height == new_height:
                                                break
                                        print_lg(f"✅ Scrolled modal to bottom (após {scroll_attempt + 1} tentativas)")
                                        scroll_success = True
                                        buffer(0.5)
                                    except:
                                        print_lg("⚠️ Falha ao scrollar modal, tentando footer...")
                                
                                # Fallback 2: Scroll até o footer
                                if not scroll_success:
                                    try:
                                        footer = modal.find_element(By.XPATH, ".//footer")
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'end', behavior: 'smooth'});", footer)
                                        buffer(0.8)
                                        print_lg("✅ Scrolled to modal footer")
                                        scroll_success = True
                                    except:
                                        print_lg("⚠️ Não conseguiu scrollar, tentando clicar mesmo assim...")
                                
                                # Extra: Scroll adicional para garantir que o botão está visível
                                if scroll_success:
                                    try:
                                        driver.execute_script("window.scrollBy(0, 200);")  # Scroll da página também
                                        buffer(0.3)
                                    except:
                                        pass
                                
                                # MELHORADO: Try multiple variations of submit button with retry logic
                                submitted = False
                                submit_attempts = 0
                                max_submit_attempts = 3
                                
                                while not submitted and submit_attempts < max_submit_attempts:
                                    submit_attempts += 1
                                    print_lg(f"🔄 Tentativa {submit_attempts} de {max_submit_attempts} para clicar em Submit...")
                                    
                                    # CRITICAL: Refresh modal reference to avoid stale element
                                    try:
                                        modal = find_by_class(driver, "jobs-easy-apply-modal")
                                        buffer(0.5)  # Wait for modal to be ready
                                    except Exception as e:
                                        print_lg(f"⚠️ Failed to refresh modal: {e}")
                                        break
                                    
                                    # Strategy 1: Find by aria-label in modal
                                    if not submitted:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//button[contains(@aria-label, 'Enviar candidatura') or contains(@aria-label, 'Submit application')]")
                                            scroll_to_view(driver, submit_btn)
                                            buffer(0.5)
                                            submit_btn.click()
                                            print_lg("✅ Clicked submit button via aria-label in modal")
                                            submitted = True
                                        except Exception as e:
                                            print_lg(f"Strategy 1 failed: {e}")
                                    
                                    # Strategy 2: Primary button in modal footer
                                    if not submitted:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//footer//button[contains(@class, 'artdeco-button--primary')]")
                                            scroll_to_view(driver, submit_btn)
                                            buffer(0.5)
                                            submit_btn.click()
                                            print_lg("✅ Clicked primary button in modal footer")
                                            submitted = True
                                        except Exception as e:
                                            print_lg(f"Strategy 2 failed: {e}")
                                    
                                    # Strategy 3: Find by span text inside modal
                                    if not submitted:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//button[.//span[contains(text(), 'Enviar candidatura') or contains(text(), 'Submit application')]]")
                                            scroll_to_view(driver, submit_btn)
                                            buffer(0.5)
                                            submit_btn.click()
                                            print_lg("✅ Clicked submit button via span text in modal")
                                            submitted = True
                                        except Exception as e:
                                            print_lg(f"Strategy 3 failed: {e}")
                                    
                                    # Strategy 4: JavaScript click as last resort
                                    if not submitted and submit_attempts == max_submit_attempts:
                                        try:
                                            submit_btn = modal.find_element(By.XPATH, ".//button[contains(@aria-label, 'Enviar candidatura') or contains(@aria-label, 'Submit application') or .//span[contains(text(), 'Enviar candidatura') or contains(text(), 'Submit application')]]")
                                            scroll_to_view(driver, submit_btn)
                                            buffer(0.5)
                                            driver.execute_script("arguments[0].click();", submit_btn)
                                            print_lg("✅ Clicked submit button via JavaScript (last resort)")
                                            submitted = True
                                        except Exception as e:
                                            print_lg(f"⚠️ JavaScript click failed: {e}")
                                    
                                    # Strategy 5: Fallback to multilang buttons
                                    if not submitted:
                                        if click_button_multilang(modal, ["Enviar candidatura", "Enviar"], 2):
                                            submitted = True
                                            print_lg("✅ Clicked via multilang (modal)")
                                        elif click_button_multilang(driver, ["Enviar candidatura", "Enviar"], 2):
                                            submitted = True
                                            print_lg("✅ Clicked via multilang (driver)")
                                    
                                    if not submitted:
                                        print_lg(f"❌ Tentativa {submit_attempts} falhou. Aguardando antes de tentar novamente...")
                                        buffer(2)
                                
                                if submitted: 
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
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    click_button_multilang(driver, ["Concluído", "Fechar"], 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    # if screenshot_name == "Not Available":  screenshot_name = screenshot(driver, job_id, "Failed to click Submit application")
                                    # else:   screenshot_name = [screenshot_name, screenshot(driver, job_id, "Failed to click Submit application")]
                                    if errored == "nose": raise Exception("Failed to click Submit application 😑")


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
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
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
            pyautogui.alert(text='Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), title="Missing Resume", button="OK")
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
        pyautogui.alert(e,alert_title)
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
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            pyautogui.alert(msg,"Info")
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
