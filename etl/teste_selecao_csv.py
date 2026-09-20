import os
import tempfile

from carga_todas_bases import selecionar_csv_unico


def main():
    with tempfile.TemporaryDirectory() as pasta:
        assert selecionar_csv_unico(pasta, "cancer_mama_rio_claro") is None

        caminho_unico = os.path.join(pasta, "A123456780191307.csv")
        open(caminho_unico, "w").close()
        assert (
            selecionar_csv_unico(pasta, "cancer_mama_rio_claro")
            == caminho_unico
        )

        caminho_novo = os.path.join(
            pasta, "cancer_mama_mulheres_rio_claro_2013_2025.csv"
        )
        open(caminho_novo, "w").close()

        try:
            selecionar_csv_unico(pasta, "cancer_mama_rio_claro")
        except RuntimeError as erro:
            assert "mais de um CSV" in str(erro)
        else:
            raise AssertionError(
                "Duas CSVs na mesma pasta deveriam falhar, "
                "não escolher uma sozinha"
            )

    print("Todas as checagens de seleção de CSV único passaram.")


if __name__ == "__main__":
    main()
