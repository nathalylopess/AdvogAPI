import json
from pathlib import Path
from typing import List, Dict
from rich.table import Table
from rich.console import Console

console = Console()

class DataService:
    def __init__(self, data_file: str = None, auto_load: bool = False):
        """
        Inicializa o serviço de dados
        
        Args:
            data_file: Caminho customizado para o arquivo de dados
            auto_load: Se True, carrega os dados automaticamente na inicialização
        """
        # Define o caminho base relativo ao arquivo atual
        base_dir = Path(__file__).parent.parent.parent  # Ajusta para a raiz do projeto

        # Define o caminho padrão se não for fornecido
        self.data_file = base_dir / "data" / "dados_tjrn.json" if data_file is None else Path(data_file)
        
        # Converte para caminho absoluto e resolve qualquer ./
        self.data_file = self.data_file.resolve()
        
        self.data = []
        if auto_load:
            self.load_data()
        
        self.debug_file_path()  # Mostra informações de debug ao inicializar
    
    def load_data(self) -> List[Dict]:
        """Carrega os dados do arquivo JSON"""
        try:
            if not self.data_file.exists():
                console.print(f"[yellow]⚠ Arquivo não encontrado: {self.data_file}[/]")
                self.data = []
                return self.data
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    console.print("[yellow]⚠ Arquivo vazio ou sem dados válidos[/]")
                self.data = data
                return self.data
                
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Erro ao decodificar JSON: {str(e)}[/]")
            self.data = []
            return self.data
        except Exception as e:
            console.print(f"[red]❌ Erro inesperado: {str(e)}[/]")
            self.data = []
            return self.data
    
    def save_data(self, data: List[Dict], auto_load: bool = True):
        """
        Salva os dados no arquivo JSON
        
        Args:
            data: Dados a serem salvos
            auto_load: Se True, carrega os dados após salvar
        """
        try:
            # Cria o diretório se não existir
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            console.print(f"[green]✓ Dados salvos em: {self.data_file}[/]")
            
            if auto_load:
                self.data = data  # Atualiza os dados em memória sem ler do arquivo
                # Alternativa: self.load_data() se quiser ler do arquivo
                
        except Exception as e:
            console.print(f"[red]❌ Falha ao salvar dados: {str(e)}[/]")
            raise
    
    def display_data_table(self):
        if not self.data:
            console.print("[red]Nenhum dado disponível para exibição[/]")
            return
            
        table = Table(title="📊 Resultados da Coleta")
        table.add_column("ID", justify="right")
        table.add_column("Unidade", justify="left")
        table.add_column("Acervo Total", justify="right")
        
        for item in self.data:
            table.add_row(
                str(item["id"]),
                item["unidade"],
                item["acervo_total"]
            )
        
        console.print(table)

    def debug_file_path(self):
        """Exibe informações detalhadas sobre o arquivo de dados"""
        console.print(f"\n[bold]DEBUG - Caminho do arquivo:[/]")
        console.print(f"• Relativo: [cyan]{self.data_file}[/]")
        console.print(f"• Absoluto: [cyan]{self.data_file.absolute()}[/]")
        console.print(f"• Existe? [{'green' if self.data_file.exists() else 'red'}]{self.data_file.exists()}[/]")
        
        if self.data_file.exists():
            console.print(f"• Tamanho: {self.data_file.stat().st_size} bytes")
            console.print(f"• Última modificação: {self.data_file.stat().st_mtime}")