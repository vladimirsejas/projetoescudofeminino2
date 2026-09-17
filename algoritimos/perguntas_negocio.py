import sqlite3

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

print("\n=== ESCUDO FEMININO - CONSULTAS ===\n")

print("1 - Qual câncer merece mais atenção?")
print("2 - Quais são as 3 maiores prioridades?")
print("3 - Qual câncer está mais acima da tendência estadual?")
print("4 - Existem anomalias?")
print("5 - Mostrar relatório executivo")

opcao = input("\nEscolha uma opção: ")

if opcao == "1":

    resultado = cursor.execute("""
        SELECT
            tipo_cancer,
            pontuacao_final,
            nivel_prioridade
        FROM priorizacao_executiva
        ORDER BY pontuacao_final DESC
        LIMIT 1
    """).fetchone()

    print("\nResposta:\n")

    print(
        f"O câncer que merece maior atenção é "
        f"{resultado[0]}."
    )

    print(
        f"Pontuação: {resultado[1]:.2f}"
    )

    print(
        f"Classificação: {resultado[2]}"
    )

elif opcao == "2":

    resultado = cursor.execute("""
        SELECT
            tipo_cancer,
            pontuacao_final
        FROM priorizacao_executiva
        ORDER BY pontuacao_final DESC
        LIMIT 3
    """).fetchall()

    print("\nTOP 3 PRIORIDADES\n")

    for i, linha in enumerate(resultado, start=1):

        print(
            f"{i}º {linha[0]} "
            f"({linha[1]:.2f})"
        )

elif opcao == "3":

    resultado = cursor.execute("""
        SELECT
            tipo_cancer,
            desvio
        FROM tendencia_estadual
        ORDER BY desvio DESC
        LIMIT 1
    """).fetchone()

    print("\nResposta:\n")

    print(
        f"{resultado[0]} apresentou desvio de "
        f"{resultado[1]:.2f}% acima da tendência estadual."
    )

elif opcao == "4":

    resultado = cursor.execute("""
        SELECT
            tipo_cancer,
            situacao
        FROM anomalias
        WHERE situacao <> 'NORMAL'
    """).fetchall()

    print("\nResultado:\n")

    if len(resultado) == 0:

        print("Nenhuma anomalia identificada.")

    else:

        for linha in resultado:

            print(
                f"{linha[0]} - {linha[1]}"
            )

elif opcao == "5":

    with open(
        "relatorio_executivo.txt",
        "r",
        encoding="utf-8"
    ) as arquivo:

        print("\n")
        print(arquivo.read())

else:

    print("Opção inválida.")

conn.close()