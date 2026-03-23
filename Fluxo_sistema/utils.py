import yaml
import os
import re

def load_config(config_path="config.yml"):
    """
    Carrega o arquivo YAML e resolve variáveis de ambiente ${VAR} ou $VAR.
    """
    with open(config_path, "r") as f:
        content = f.read()
    
    # Regex para encontrar ${VAR} ou $VAR
    pattern = re.compile(r'\${(\w+)}|\$(\w+)')
    
    def replacer(match):
        var_name = match.group(1) or match.group(2)
        # Fallback para os valores padrão se não encontrar no ambiente
        defaults = {
            'DB_USER': 'myuser',
            'DB_PASS': 'mypassword',
            'DB_PORT': '1111'
        }
        return os.getenv(var_name, defaults.get(var_name, match.group(0)))

    # Substitui variáveis no texto bruto do YAML antes do parse
    resolved_content = pattern.sub(replacer, content)
    return yaml.safe_load(resolved_content)
