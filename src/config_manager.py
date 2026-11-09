"""Módulo de gerenciamento de configurações e variáveis de ambiente."""

import json
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"

# Configurações padrão do sistema
DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "<f9>",
    "language": "pt",
    "model": "whisper-large-v3-turbo",
    "sample_rate": 16000,
    "channels": 1,
    "restore_clipboard": False,
}


class ConfigManager:
    """Gerencia a leitura e persistência das configurações da aplicação."""

    def __init__(self, config_path: Path = CONFIG_FILE, env_path: Path = ENV_FILE) -> None:
        self.config_path = config_path
        self.env_path = env_path
        self._load_env()
        self.config = self._load_config()

    def _load_env(self) -> None:
        """Carrega variáveis do arquivo .env."""
        if self.env_path.exists():
            load_dotenv(dotenv_path=self.env_path, override=True)
        else:
            load_dotenv()

    def _load_config(self) -> Dict[str, Any]:
        """Lê o arquivo config.json ou cria com valores padrão se não existir."""
        if not self.config_path.exists():
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Garante que chaves novas presentes no DEFAULT_CONFIG sejam adicionadas
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()

    def save_config(self, new_config: Dict[str, Any]) -> None:
        """Salva as configurações atualizadas no config.json."""
        self.config = new_config
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Retorna o valor de uma configuração."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Atualiza e salva uma chave de configuração."""
        self.config[key] = value
        self.save_config(self.config)

    @property
    def groq_api_key(self) -> str:
        """Retorna a chave da API da Groq definida nas variáveis de ambiente."""
        return os.getenv("GROQ_API_KEY", "").strip()


# Instância global reutilizável
config_manager = ConfigManager()

