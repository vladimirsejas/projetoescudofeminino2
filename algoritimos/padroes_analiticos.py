import pandas as pd


def gerar_padroes_analiticos(conn, municipio, nome_municipio):
    """
    Produz achados descritivos para a camada de IA.
    Não altera nenhum indicador existente e não calcula score novo.
    """
    volume = pd.read_sql(
        """
        SELECT
            tipo_cancer,
            COUNT(*) AS internacoes,
            SUM(obito) AS obitos
        FROM internacoes
        WHERE municipio = ?
        GROUP BY tipo_cancer
        """,
        conn,
        params=(municipio,),
    )

    if volume.empty:
        return {
            "municipio": nome_municipio,
            "padroes": [],
            "evidencias": [],
        }

    volume["obitos"] = volume["obitos"].fillna(0)
    volume["taxa_mortalidade_hospitalar"] = (
        volume["obitos"] / volume["internacoes"] * 100
    )

    padroes = []
    evidencias = []

    top_volume = volume.sort_values("internacoes", ascending=False).iloc[0]
    top_mortalidade = volume.sort_values(
        "taxa_mortalidade_hospitalar", ascending=False
    ).iloc[0]

    padroes.append(
        {
            "tipo": "MAIOR_VOLUME",
            "cancer": top_volume["tipo_cancer"],
            "descricao": (
                f"{top_volume['tipo_cancer']} possui o maior volume "
                f"de internações hospitalares em {nome_municipio}."
            ),
        }
    )

    padroes.append(
        {
            "tipo": "MAIOR_MORTALIDADE_HOSPITALAR",
            "cancer": top_mortalidade["tipo_cancer"],
            "descricao": (
                f"{top_mortalidade['tipo_cancer']} apresenta a maior "
                f"taxa de mortalidade hospitalar entre os cânceres "
                f"monitorados em {nome_municipio}."
            ),
        }
    )

    top3_volume = set(
        volume.nlargest(3, "internacoes")["tipo_cancer"]
    )
    top3_mortalidade = set(
        volume.nlargest(3, "taxa_mortalidade_hospitalar")["tipo_cancer"]
    )

    cruzamentos = sorted(top3_volume & top3_mortalidade)

    for cancer in cruzamentos:
        linha = volume[volume["tipo_cancer"] == cancer].iloc[0]
        padroes.append(
            {
                "tipo": "CRUZAMENTO_VOLUME_MORTALIDADE",
                "cancer": cancer,
                "descricao": (
                    f"{cancer} está simultaneamente entre os três "
                    f"maiores volumes de internações e as três maiores "
                    f"taxas de mortalidade hospitalar."
                ),
            }
        )
        evidencias.append(
            {
                "tipo_cancer": cancer,
                "internacoes": int(linha["internacoes"]),
                "obitos": int(linha["obitos"]),
                "taxa_mortalidade_hospitalar": round(
                    float(linha["taxa_mortalidade_hospitalar"]), 2
                ),
            }
        )

    try:
        tendencia = pd.read_sql(
            """
            SELECT
                tipo_cancer,
                variacao_municipio,
                variacao_sp,
                desvio,
                evento
            FROM tendencia_estadual
            WHERE municipio = ?
            """,
            conn,
            params=(municipio,),
        )
    except Exception:
        tendencia = pd.DataFrame()

    if not tendencia.empty:
        acima = tendencia[
            tendencia["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL"
        ]
        for _, row in acima.iterrows():
            padroes.append(
                {
                    "tipo": "ACIMA_DA_TENDENCIA_ESTADUAL",
                    "cancer": row["tipo_cancer"],
                    "descricao": (
                        f"{row['tipo_cancer']} apresenta crescimento "
                        f"municipal acima da referência estadual, "
                        f"com desvio de {row['desvio']:.2f} pontos percentuais."
                    ),
                }
            )

    try:
        anomalias = pd.read_sql(
            """
            SELECT tipo_cancer, valor_2025, desvio_percentual, situacao
            FROM anomalias
            WHERE municipio = ?
              AND situacao != 'NORMAL'
            """,
            conn,
            params=(municipio,),
        )
    except Exception:
        anomalias = pd.DataFrame()

    if not anomalias.empty:
        for _, row in anomalias.iterrows():
            detalhe = (
                f"desvio de {row['desvio_percentual']:.2f}%"
                if pd.notna(row["desvio_percentual"])
                else "desvio percentual não calculável"
            )
            padroes.append(
                {
                    "tipo": "ANOMALIA",
                    "cancer": row["tipo_cancer"],
                    "descricao": (
                        f"{row['tipo_cancer']} apresenta {row['situacao']} "
                        f"em 2025 ({detalhe})."
                    ),
                }
            )

    try:
        prioridades = pd.read_sql(
            """
            SELECT tipo_cancer, nivel_prioridade, pontuacao_final
            FROM priorizacao_executiva
            WHERE municipio = ?
              AND nivel_prioridade IN ('CRITICA', 'ALTA')
            ORDER BY pontuacao_final DESC
            """,
            conn,
            params=(municipio,),
        )
    except Exception:
        prioridades = pd.DataFrame()

    for _, row in prioridades.iterrows():
        padroes.append(
            {
                "tipo": "PRIORIDADE_ALTA_OU_CRITICA",
                "cancer": row["tipo_cancer"],
                "descricao": (
                    f"{row['tipo_cancer']} está classificado como "
                    f"{row['nivel_prioridade']} na priorização do Escudo, "
                    f"com pontuação final de {row['pontuacao_final']:.2f}."
                ),
            }
        )

    return {
        "municipio": nome_municipio,
        "padroes": padroes,
        "evidencias": evidencias,
    }


def formatar_contexto_padroes(resultado):
    """Transforma os achados em contexto legível para a IA."""
    linhas = [
        "CAMADA DE PADRÕES ANALÍTICOS",
        f"MUNICÍPIO: {resultado['municipio']}",
        "",
        "ACHADOS CALCULADOS PELO ESCUDO:",
    ]

    if not resultado["padroes"]:
        linhas.append("- Nenhum padrão adicional identificado.")
    else:
        for padrao in resultado["padroes"]:
            linhas.append(f"- [{padrao['tipo']}] {padrao['descricao']}")

    if resultado["evidencias"]:
        linhas.extend(["", "EVIDÊNCIAS NUMÉRICAS DOS CRUZAMENTOS:"])
        for evidencia in resultado["evidencias"]:
            linhas.append(
                f"- {evidencia['tipo_cancer']}: "
                f"{evidencia['internacoes']} internações; "
                f"{evidencia['obitos']} óbitos; "
                f"{evidencia['taxa_mortalidade_hospitalar']:.2f}% "
                f"de mortalidade hospitalar."
            )

    linhas.extend(
        [
            "",
            "REGRA: estes achados são descritivos. "
            "Não representam causalidade nem previsão.",
        ]
    )

    return "\n".join(linhas)
