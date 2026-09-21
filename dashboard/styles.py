import streamlit as st


def aplicar_estilos():
    st.markdown(
        """
        <style>
        :root {
            --escudo-texto: #18333f;
            --escudo-subtexto: #5b6d75;
            --escudo-superficie: #ffffff;
            --escudo-fundo: #f5f7f8;
            --escudo-linha: #dce4e7;
            --escudo-acento: #2d6975;
            --escudo-acento-claro: #e8f1f3;
        }

        .stApp {
            background: var(--escudo-fundo);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.25rem;
            padding-bottom: 4rem;
        }

        [data-testid="stHeader"] {
            background: rgba(245, 247, 248, 0.92);
        }

        .ef-brand {
            display: flex;
            align-items: baseline;
            gap: .65rem;
            margin: .2rem 0 .85rem;
        }

        .ef-brand-name {
            font-size: 1.55rem;
            font-weight: 700;
            color: var(--escudo-texto);
        }

        .ef-brand-context {
            color: var(--escudo-subtexto);
            font-size: .9rem;
        }

        .ef-hero {
            background: var(--escudo-superficie);
            border: 1px solid var(--escudo-linha);
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            margin: .75rem 0 1rem;
        }

        .ef-overline {
            text-transform: uppercase;
            letter-spacing: .08em;
            font-size: .72rem;
            font-weight: 700;
            color: var(--escudo-acento);
            margin-bottom: .35rem;
        }

        .ef-title {
            color: var(--escudo-texto);
            font-size: clamp(1.65rem, 4vw, 2.55rem);
            line-height: 1.08;
            font-weight: 750;
            margin: 0;
        }

        .ef-subtitle {
            color: var(--escudo-subtexto);
            margin: .55rem 0 0;
            font-size: 1rem;
        }

        .ef-card {
            background: var(--escudo-superficie);
            border: 1px solid var(--escudo-linha);
            border-radius: 16px;
            padding: 1rem;
            min-height: 100%;
        }

        .ef-card-title {
            color: var(--escudo-texto);
            font-weight: 700;
            margin-bottom: .25rem;
        }

        .ef-card-text {
            color: var(--escudo-subtexto);
            font-size: .9rem;
            line-height: 1.45;
        }

        .ef-note {
            background: var(--escudo-acento-claro);
            border-left: 4px solid var(--escudo-acento);
            border-radius: 10px;
            padding: .9rem 1rem;
            color: var(--escudo-texto);
            margin: .75rem 0;
        }

        div[data-testid="stMetric"] {
            background: var(--escudo-superficie);
            border: 1px solid var(--escudo-linha);
            border-radius: 14px;
            padding: .7rem .8rem;
        }

        @media (max-width: 800px) {
            .block-container {
                padding: .7rem .75rem 5rem;
            }

            .ef-brand {
                flex-direction: column;
                gap: .1rem;
                margin-bottom: .65rem;
            }

            .ef-card {
                padding: .9rem;
            }

            button[kind="secondary"] {
                min-height: 2.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def marca(contexto=None):
    cidade = contexto or ""
    st.markdown(
        f"""
        <div class="ef-brand">
            <span class="ef-brand-name">Escudo Feminino</span>
            <span class="ef-brand-context">{cidade}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
