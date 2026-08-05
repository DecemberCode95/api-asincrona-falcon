"""
Configuración centralizada de logging estructurado con JSON
Uso: from core.logging_config import logger
     logger.info("mensaje", extra={"datos": "adicionales"})
"""

import logging
import json
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatea logs en JSON estructurado"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Agregar datos adicionales si existen
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """
    Configura logging centralizado
    Crea logs en:
      • Consola (nivel INFO)
      • Archivo logs/api.log (nivel DEBUG)
    """
    logger = logging.getLogger("api")
    logger.setLevel(logging.DEBUG)
    
    # Limpiar handlers anteriores (si existen)
    logger.handlers = []
    
    # Crear carpeta logs si no existe
    log_file = Path("logs")
    log_file.mkdir(exist_ok=True)
    
    # ===== HANDLER A CONSOLA (Más legible) =====
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ===== HANDLER A ARCHIVO JSON (Estructurado) =====
    file_handler = logging.FileHandler("logs/api.log")
    file_handler.setLevel(logging.DEBUG)
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger


# Inicializar logger global
logger = setup_logging()
