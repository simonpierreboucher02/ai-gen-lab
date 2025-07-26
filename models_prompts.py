# Configuration des modèles avec leurs tarifs API
# Tarifs en USD par million de tokens (juillet 2025)

PRICING_DATA = {
    # Claude (Anthropic)
    'claude-sonnet-4-20250514': {
        'name': 'Claude Sonnet 4',
        'provider': 'Anthropic',
        'input_cost': 3.0,   # $/1M tokens
        'output_cost': 15.0, # $/1M tokens
        'context_window': 64000
    },
    'claude-opus-4-20250514': {
        'name': 'Claude Opus 4',
        'provider': 'Anthropic', 
        'input_cost': 15.0,  # $/1M tokens
        'output_cost': 75.0, # $/1M tokens
        'context_window': 32000
    },
    'claude-3-7-sonnet-20250219': {
        'name': 'Claude 3.7 Sonnet',
        'provider': 'Anthropic',
        'input_cost': 3.0,   # $/1M tokens
        'output_cost': 15.0, # $/1M tokens
        'context_window': 128000
    },
    
    # OpenAI
    'gpt-4o': {
        'name': 'GPT-4o',
        'provider': 'OpenAI',
        'input_cost': 5.0,   # $/1M tokens
        'output_cost': 20.0, # $/1M tokens
        'context_window': 16000
    },
    'gpt-4o-mini': {
        'name': 'GPT-4o Mini',
        'provider': 'OpenAI',
        'input_cost': 0.6,   # $/1M tokens
        'output_cost': 2.4,  # $/1M tokens
        'context_window': 16000
    },
    'gpt-4.1': {
        'name': 'GPT-4.1',
        'provider': 'OpenAI',
        'input_cost': 2.0,   # $/1M tokens
        'output_cost': 8.0,  # $/1M tokens
        'context_window': 32000
    },
    'gpt-4.1-mini': {
        'name': 'GPT-4.1 Mini',
        'provider': 'OpenAI',
        'input_cost': 0.4,   # $/1M tokens
        'output_cost': 1.6,  # $/1M tokens
        'context_window': 32000
    },
    'gpt-4.1-nano': {
        'name': 'GPT-4.1 Nano',
        'provider': 'OpenAI',
        'input_cost': 0.1,   # $/1M tokens
        'output_cost': 0.4,  # $/1M tokens
        'context_window': 32000
    },
    
    # OpenAI O-Series (Reasoning Models) - Prix corrigés selon spécifications
    'o3': {
        'name': 'O3 (full)',
        'provider': 'OpenAI-Reasoning',
        'input_cost': 2000.0,   # $/1M tokens ($2 per 1K)
        'output_cost': 8000.0,  # $/1M tokens ($8 per 1K)
        'context_window': 200000
    },
    'o4-mini': {
        'name': 'O4 Mini',
        'provider': 'OpenAI-Reasoning',
        'input_cost': 150.0,    # $/1M tokens ($0.15 per 1K)
        'output_cost': 600.0,   # $/1M tokens ($0.60 per 1K)
        'context_window': 128000
    },
    'o1': {
        'name': 'O1 (full)',
        'provider': 'OpenAI-Reasoning',
        'input_cost': 15000.0,  # $/1M tokens ($15 per 1K)
        'output_cost': 60000.0, # $/1M tokens ($60 per 1K)
        'context_window': 200000
    },
    'o3-mini': {
        'name': 'O3 Mini',
        'provider': 'OpenAI-Reasoning',
        'input_cost': 1100.0,   # $/1M tokens ($1.1 per 1K)
        'output_cost': 1100.0,  # $/1M tokens ($1.1 per 1K) - coût identique input/output
        'context_window': 128000
    },
    
    # xAI Grok
    'grok-4-latest': {
        'name': 'Grok-4',
        'provider': 'xAI',
        'input_cost': 3.0,   # $/1M tokens
        'output_cost': 15.0, # $/1M tokens
        'context_window': 256000
    },
    'grok-3': {
        'name': 'Grok-3',
        'provider': 'xAI',
        'input_cost': 3.0,   # $/1M tokens
        'output_cost': 15.0, # $/1M tokens
        'context_window': 131072
    },
    'grok-3-mini': {
        'name': 'Grok-3 Mini',
        'provider': 'xAI',
        'input_cost': 0.3,   # $/1M tokens
        'output_cost': 0.5,  # $/1M tokens
        'context_window': 131072
    },
    'grok-3-fast': {
        'name': 'Grok-3 Fast',
        'provider': 'xAI',
        'input_cost': 5.0,   # $/1M tokens
        'output_cost': 25.0, # $/1M tokens
        'context_window': 131072
    }
}

def calculate_cost(model_id, input_tokens, output_tokens):
    """Calculer le coût d'une génération"""
    if model_id not in PRICING_DATA:
        return 0.0
    
    pricing = PRICING_DATA[model_id]
    input_cost = (input_tokens / 1_000_000) * pricing['input_cost']
    output_cost = (output_tokens / 1_000_000) * pricing['output_cost']
    
    return input_cost + output_cost

def get_model_pricing(model_id):
    """Obtenir les infos de tarification d'un modèle"""
    return PRICING_DATA.get(model_id, {})