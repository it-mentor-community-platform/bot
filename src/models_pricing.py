from src.config.env import DEFAULT_LLM_MODEL, BIGGER_CONTEXT_LLM_MODEL


# Contains models prices for input/output in $ per 1M tokens
PRICING = {
    "gpt-5.2":        {"input": 1.75,  "output": 14.00},
    "gpt-5.2-pro":    {"input": 21.00, "output": 168.00},
    "gpt-5.4":        {"input": 2.50,  "output": 15.00},
    "gpt-5.4-pro":    {"input": 30.00, "output": 180.00},
    "gpt-5.4-mini":   {"input": 0.75,  "output": 4.50},
    "gpt-5.4-nano":   {"input": 0.20,  "output": 1.25},
    "gpt-5.5":        {"input": 5.00,  "output": 30.00},
    "gpt-5.5-pro":    {"input": 30.00, "output": 180.00},
    "gpt-5.6-sol":    {"input": 5.00,  "output": 30.00},
    "gpt-5.6-terra":  {"input": 2.00,  "output": 12.00},
    "gpt-5.6-luna":   {"input": 0.20,  "output": 1.20},
    "gpt-6-astra":    {"input": 10.00, "output": 50.00},
    "gpt-6-luna":     {"input": 0.10,  "output": 0.50},
    "gpt-6.1-sol":    {"input": 2.00,  "output": 10.00},
    "gpt-6.1-terra":  {"input": 1.00,  "output": 5.00},
}

def check_pricing_for_configured_models() -> None:
    if DEFAULT_LLM_MODEL not in PRICING:
        raise ValueError(f"Pricing for default LLM model {DEFAULT_LLM_MODEL} is not configured")
    if BIGGER_CONTEXT_LLM_MODEL not in PRICING:
        raise ValueError(f"Pricing for bigger LLM model {DEFAULT_LLM_MODEL} is not configured")
