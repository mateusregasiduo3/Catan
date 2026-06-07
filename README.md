# Catan
Como começar (ambiente Windows):

1. Ativa o ambiente virtual:

    windows: .\\venv\\Scripts\\Activate.ps1
    linux:
      python -m venv .venv 
      source .venv/bin/activate

2. Instale dependências:

   pip install -r requiriments.txt

3. Execute o jogo:

   python main.py

Para executar todos os testes:
   python -m pytest tests/ -v --tb=line

Para executar a suíte por grupos de casos com o driver:

    python drivers.py --list
    python drivers.py --group domain
    python drivers.py --group all -- --cov=. --cov-report=term-missing