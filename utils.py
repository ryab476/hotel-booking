# === МОДУЛЬ УТИЛИТ === 

def sanitize_miniapp_data_universal(data: dict) -> dict:
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = value.strip()
        elif value is None:
            safe_data[key] = ''
        else:
            safe_data[key] = value
    return safe_data