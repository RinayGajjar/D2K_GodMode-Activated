from .agent import FinanceAnalyzer

# Define agent manifest for the registry
AGENT_MANIFEST = {
    "id": "finance",
    "name": "Stock Analyzer",
    "description": "Analyze stocks and get investment recommendations",
    "version": "1.0.0",
    "input_types": ["csv", "txt"],
    "output_type": "json",
    "icon": "📈",
    "category": "Finance",
    "parameters": [],
}

__all__ = ["FinanceAnalyzer", "AGENT_MANIFEST"]
