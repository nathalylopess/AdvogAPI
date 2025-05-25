import pytest
from app.services.scraper import TJRNScraper
from app.services.data_service import DataService

@pytest.mark.integration
def test_scraper_integration():
    """Teste de integração do scraper (requer conexão com internet)"""
    scraper = TJRNScraper(headless=True)
    data = scraper.fetch_data(max_units=2)  # Testa com apenas 2 unidades
    
    assert len(data) > 0
    assert "unidade" in data[0]
    assert "processos_em_tramitacao" in data[0]
    
    # Teste de salvamento
    data_service = DataService()
    data_service.save_data(data)
    loaded_data = data_service.load_data()
    
    assert len(loaded_data) == len(data)