#!/usr/bin/env python3
"""
Script para execução manual do scraper
"""
from rich.console import Console
from app.services.scraper import TJRNScraper
from app.services.data_service import DataService

console = Console()

def main():
    console.print("[bold cyan]🚀 Iniciando coleta de dados do TJRN[/]")
    
    try:
        scraper = TJRNScraper(headless=False) # "False" para DEBUG
        data = scraper.fetch_data()  # Coleta todas as unidades
        
        data_service = DataService()
        data_service.save_data(data)
        data_service.display_data_table()
        
        console.print("[bold green]✅ Coleta concluída com sucesso![/]")
    except Exception as e:
        console.print(f"[bold red]❌ Erro durante a coleta: {str(e)}[/]")
        raise

if __name__ == "__main__":
    main()