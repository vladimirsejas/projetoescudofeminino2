import os
import subprocess
import sys

DIRETORIO = os.path.dirname(os.path.abspath(__file__))

CADEIA = [
    "mortalidade.py",
    "custos_hospitalares.py",
    "permanencia_hospitalar.py",
    "faixa_etaria.py",
    "score_epidemiologico.py",
    "tendencia_estadual.py",
    "anomalias.py",
    "priorizador.py",
    "perfil_epidemiologico.py",
    "base_conhecimento.py",
    "memoria_ia.py",
    "fichas_ia.py",
    "relatorio_executivo.py",
]


def executar(municipio):
    ambiente = os.environ.copy()
    ambiente["ESCUDO_MUNICIPIO"] = municipio

    resultados = []

    for nome in CADEIA:
        caminho = os.path.join(DIRETORIO, nome)
        resultado = subprocess.run(
            [sys.executable, caminho],
            cwd=DIRETORIO,
            env=ambiente,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        resultados.append({
            "arquivo": nome,
            "codigo": resultado.returncode,
            "saida": resultado.stdout,
            "erro": resultado.stderr,
        })

        if resultado.returncode != 0:
            raise RuntimeError(
                f"Falha em {nome}:\n{resultado.stderr or resultado.stdout}"
            )

    return resultados
