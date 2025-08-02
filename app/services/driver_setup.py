import os
import shutil
import tempfile
import platform
from selenium import webdriver
from selenium.webdriver import Remote
from selenium.common.exceptions import WebDriverException
from rich.console import Console

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # pip install webdriver-manager


console = Console()

def setup_chrome_options(headless=True):
    """Configura e retorna as opções do Chrome."""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--remote-debugging-port=9222')
    return options

def cleanup_old_sessions():
    """Limpa sessões antigas do Chrome."""
    try:
        if platform.system() != "Windows":
            os.system("pkill -f chrome")
            os.system("pkill -f chromedriver")
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('chrome_'):
                try:
                    shutil.rmtree(os.path.join(temp_dir, item))
                except Exception as e:
                    console.print(f"[yellow]⚠️ Falha ao limpar {item}: {str(e)}[/]")
    except Exception as e:
        console.print(f"[red]❌ Erro durante a limpeza de sessões antigas: {str(e)}[/]")

def setup_temp_directory(options):
    """Cria e adiciona um diretório temporário às opções do Chrome."""
    user_data_dir = os.path.join(tempfile.gettempdir(), f'chrome_{os.getpid()}')
    cleanup_old_sessions()
    options.add_argument(f'--user-data-dir={user_data_dir}')
    return user_data_dir

def initialize_driver(options):
    """Inicializa e retorna o WebDriver com as opções fornecidas."""
    try:
        if os.getenv("SELENIUM_REMOTE_URL"):
            driver = Remote(
                command_executor=os.getenv("SELENIUM_REMOTE_URL"),
                options=options
            )
        else:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.set_page_load_timeout(30)
        return driver
    except WebDriverException as e:
        console.print(f"[bold red]❌ Falha ao iniciar o WebDriver: {str(e)}[/]")
        raise

def setup_driver(headless=True):
    """
    Executa o setup completo: opções do Chrome, diretório temporário e WebDriver.
    
    Returns:
        driver (Remote): WebDriver inicializado.
        options (ChromeOptions): As opções usadas.
        user_data_dir (str): Diretório temporário utilizado.
    """
    options = setup_chrome_options(headless)
    user_data_dir = setup_temp_directory(options)
    driver = initialize_driver(options)
    return driver, options, user_data_dir