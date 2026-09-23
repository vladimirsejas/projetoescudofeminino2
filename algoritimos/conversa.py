"""Compatibilidade pública do chatbot.

O núcleo foi separado em chat_inteligente.py para permitir testes e evolução
sem misturar interface, cálculo e linguagem.
"""

from chat_inteligente import (
    entender,
    calcular,
    responder,
    registrar_pergunta,
    normalizar,
    detectar_cancer,
)

__all__ = [
    "entender",
    "calcular",
    "responder",
    "registrar_pergunta",
    "normalizar",
    "detectar_cancer",
]
