from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from rich.console import Console

console = Console()

def recover_from_error(driver, base_url, wait):
    """Tenta recuperar de um erro."""
    try:
        driver.refresh()
        wait_for_page_load(driver, wait)
    except:
        try:
            driver.get(base_url)
            wait_for_page_load(driver, wait)
        except Exception as e:
            console.print(f"[red]❌ Falha na recuperação: {str(e)}[/]")
            raise

def wait_for_selenium(driver, condition, timeout=10, error_msg="Timeout waiting for condition"):
    """
    Aguarda uma condição do Selenium com tratamento de exceções.

    Args:
        driver: WebDriver em uso.
        condition: Condição do WebDriverWait (ex: EC.presence_of_element_located).
        timeout (int): Tempo máximo de espera.
        error_msg (str): Mensagem de erro personalizada.
    
    Returns:
        O resultado da condição esperada.
    """
    try:
        return WebDriverWait(driver, timeout).until(condition)
    except TimeoutException:
        console.print(f"[bold yellow]⚠ {error_msg}[/]")
        raise

def wait_for_page_load(driver, wait):
    """Espera até que a página tenha terminado de carregar completamente."""
    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
