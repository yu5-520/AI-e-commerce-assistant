from pathlib import Path
import json, os, urllib.request

TRUE_VALUES={'1','true','yes','on'}

def llm_enabled():
    return os.getenv('LLM_ENABLED','').lower() in TRUE_VALUES

def load_provider():
    cfg=json.loads(Path('config/model_providers.json').read_text(encoding='utf-8'))
    name=os.getenv('LLM_PROVIDER','custom')
    p=cfg.get(name) or cfg['custom']
    base=os.getenv('LLM_BASE_URL') or p.get('base_url') or os.getenv(p.get('base_url_env',''), '')
    key=os.getenv('LLM_API_KEY') or os.getenv(p.get('api_key_env',''), '')
    model=os.getenv('LLM_MODEL') or p.get('default_model') or os.getenv(p.get('default_model_env',''), '')
    return name, base.rstrip('/'), key, model

def chat(system_prompt, user_prompt):
    if not llm_enabled():
        return None
    provider, base_url, api_key, model = load_provider()
    if not base_url or not api_key or not model:
        return None
    url=base_url + '/chat/completions'
    data={
        'model': model,
        'messages': [
            {'role':'system','content':system_prompt},
            {'role':'user','content':user_prompt}
        ],
        'temperature': float(os.getenv('LLM_TEMPERATURE','0.3'))
    }
    body=json.dumps(data, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type','application/json')
    req.add_header('Authorization','Bearer '+api_key)
    timeout=int(os.getenv('LLM_TIMEOUT','60'))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw=r.read().decode('utf-8')
    obj=json.loads(raw)
    return obj['choices'][0]['message']['content']
