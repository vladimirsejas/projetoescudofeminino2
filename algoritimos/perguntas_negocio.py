import sqlite3

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

print("\n=== ESCUDO FEMININO - CONSULTAS ===\n")

print("1 - Qual cÃ¢ncer merece mais atenÃ§Ã£o?")
print("2 - Quais sÃ£o as 3 maiores prioridades?")
print("3 - Qual cÃ¢ncer estÃ¡ mais acima da tendÃªncia estadual?")
print("4 - Existem anomalias?")
print("5 - Mostrar relatÃ³rio executivo")

opcao = input("\nEscolha uma opÃ§Ã£o: ")

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
        f"O cÃ¢ncer que merece maior atenÃ§Ã£o Ã© "
        f"{resultado[0]}."
    )

    print(
        f"PontuaÃ§Ã£o: {resultado[1]:.2f}"
    )

    print(
        f"ClassificaÃ§Ã£o: {resultado[2]}"
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
            f"{i}Âº {linha[0]} "
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
        f"{resultado[1]:.2f}% acima da tendÃªncia estadual."
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

    print("OpÃ§Ã£o invÃ¡lida.")

conn.close()
