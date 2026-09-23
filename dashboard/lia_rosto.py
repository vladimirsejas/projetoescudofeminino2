import base64

# ============================================================
# O ROSTO DA LIA (ilustração vetorial, ver docs/LIA.md)
#
# Mulher negra madura, cabelo crespo curto grisalho, óculos, blusa
# berinjela -- pesquisadora, não médica: sem jaleco, sem crachá, sem
# marca de instituição real. O mesmo desenho em 5 expressões; só
# mudam sobrancelhas, olhos, boca e o pequeno símbolo no canto, para
# o rosto ser o mesmo em todas e ficar nítido em qualquer tamanho.
# ============================================================

PELE = "#7a4a2e"
PELE_SOMBRA = "#643b23"
CABELO_ESCURO = "#3b3634"
CABELO_CINZA = "#9c9794"
CABELO_CLARO = "#cfcac6"
BLUSA = "#5b2a55"
GOLA = "#e9dff0"
ARMACAO = "#27212b"
FUNDO = "#efe9f7"

# (sobrancelha esquerda, sobrancelha direita, olhos, boca, símbolo)
EXPRESSOES = {
    "acolhedora": {
        "sobrancelhas": ("M71 78 Q80 74 89 77", "M111 77 Q120 74 129 78"),
        "olhos": "sorrindo",
        "boca": '<path d="M88 118 Q100 128 112 118" stroke="#3a1f14" stroke-width="3" fill="none" stroke-linecap="round"/>',
        "simbolo": None,
    },
    "explicando": {
        "sobrancelhas": ("M71 77 Q80 73 89 76", "M111 76 Q120 73 129 77"),
        "olhos": "abertos",
        "boca": '<path d="M89 118 Q100 125 111 118" stroke="#3a1f14" stroke-width="3" fill="none" stroke-linecap="round"/>',
        "simbolo": "grafico",
    },
    "atenta": {
        "sobrancelhas": ("M71 74 Q80 69 89 73", "M111 73 Q120 69 129 74"),
        "olhos": "abertos",
        "boca": '<ellipse cx="100" cy="120" rx="5" ry="4" fill="#3a1f14"/>',
        "simbolo": "lupa",
    },
    "cautelosa": {
        "sobrancelhas": ("M71 76 Q80 76 89 73", "M111 73 Q120 76 129 76"),
        "olhos": "abertos",
        "boca": '<path d="M90 121 L110 119" stroke="#3a1f14" stroke-width="3" fill="none" stroke-linecap="round"/>',
        "simbolo": "cuidado",
    },
    "pensativa": {
        "sobrancelhas": ("M71 77 Q80 73 89 76", "M111 72 Q120 68 129 72"),
        "olhos": "para_cima",
        "boca": '<path d="M91 120 Q101 123 110 117" stroke="#3a1f14" stroke-width="3" fill="none" stroke-linecap="round"/>',
        "simbolo": "pergunta",
    },
}

ROTULOS = {
    "acolhedora": "Lia, acolhedora",
    "explicando": "Lia explicando um dado",
    "atenta": "Lia atenta: encontrou um sinal",
    "cautelosa": "Lia cautelosa: este dado pede cuidado",
    "pensativa": "Lia pensativa: explicando como calculou",
}


def _cabelo():
    """Cabelo crespo curto, sal e pimenta: uma base escura com o
    formato do penteado e, por cima, cachos pequenos em posições
    variadas -- a maioria escuros, uns grisalhos e poucos claros.
    Posições pseudoaleatórias com semente fixa: o cabelo é o mesmo em
    todas as expressões."""
    import math
    import random
    rnd = random.Random(7)
    partes = [f'<ellipse cx="100" cy="80" rx="58" ry="52" fill="{CABELO_ESCURO}"/>']
    for _ in range(170):
        ang = rnd.uniform(math.pi * 0.88, math.pi * 2.12)
        raio = rnd.uniform(0.55, 1.0)
        x = 100 + 56 * raio * math.cos(ang)
        y = 80 + 50 * raio * math.sin(ang)
        if y > 104:  # não desce abaixo da orelha
            continue
        sorteio = rnd.random()
        cor = CABELO_ESCURO if sorteio < 0.55 else (CABELO_CINZA if sorteio < 0.88 else CABELO_CLARO)
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.uniform(5.5, 8.5):.1f}" fill="{cor}"/>')
    for _ in range(40):  # brilho dos cachos
        ang = rnd.uniform(math.pi * 0.95, math.pi * 2.05)
        x = 100 + 52 * rnd.uniform(0.6, 1.0) * math.cos(ang)
        y = 80 + 46 * rnd.uniform(0.6, 1.0) * math.sin(ang)
        if y > 100:
            continue
        partes.append(f'<path d="M{x - 3:.1f} {y:.1f} q3 -4 6 0" stroke="{CABELO_CLARO}" '
                      f'stroke-width="1.3" fill="none" opacity=".7"/>')
    return "".join(partes)


def _olhos(tipo):
    if tipo == "sorrindo":
        return ('<path d="M73 92 Q80 86 87 92" stroke="#1d1411" stroke-width="3" fill="none" stroke-linecap="round"/>'
                '<path d="M113 92 Q120 86 127 92" stroke="#1d1411" stroke-width="3" fill="none" stroke-linecap="round"/>')
    dy = -2 if tipo == "para_cima" else 0
    dx = 2 if tipo == "para_cima" else 0
    return (f'<ellipse cx="80" cy="91" rx="5.5" ry="6" fill="#fff"/><ellipse cx="120" cy="91" rx="5.5" ry="6" fill="#fff"/>'
            f'<circle cx="{80 + dx}" cy="{91 + dy}" r="3.6" fill="#1d1411"/><circle cx="{120 + dx}" cy="{91 + dy}" r="3.6" fill="#1d1411"/>'
            f'<circle cx="{81 + dx}" cy="{90 + dy}" r="1.1" fill="#fff"/><circle cx="{121 + dx}" cy="{90 + dy}" r="1.1" fill="#fff"/>')


def _simbolo(tipo):
    """Pequeno selo no canto superior direito que reforça a expressão."""
    if tipo is None:
        return ""
    base = '<circle cx="164" cy="38" r="21" fill="#fff" stroke="#d9cfe6" stroke-width="2"/>'
    desenhos = {
        "grafico": ('<rect x="153" y="40" width="5" height="9" rx="1" fill="#2a78d6"/>'
                    '<rect x="161" y="34" width="5" height="15" rx="1" fill="#2a78d6"/>'
                    '<rect x="169" y="28" width="5" height="21" rx="1" fill="#2a78d6"/>'),
        "lupa": ('<circle cx="161" cy="35" r="8" stroke="#5b2a55" stroke-width="3" fill="none"/>'
                 '<path d="M167 41 L174 48" stroke="#5b2a55" stroke-width="3.5" stroke-linecap="round"/>'),
        "cuidado": ('<path d="M164 25 L177 48 L151 48 Z" fill="#fab219" stroke="#c98500" stroke-width="1.5" stroke-linejoin="round"/>'
                    '<rect x="162.5" y="32" width="3" height="9" rx="1.5" fill="#3a2a00"/><circle cx="164" cy="44.5" r="1.8" fill="#3a2a00"/>'),
        "pergunta": ('<text x="164" y="47" text-anchor="middle" font-family="Georgia, serif" font-size="26" '
                     'font-weight="700" fill="#5b2a55">?</text>'),
    }
    return base + desenhos[tipo]


def svg(expressao="acolhedora"):
    e = EXPRESSOES.get(expressao, EXPRESSOES["acolhedora"])
    sob_e, sob_d = e["sobrancelhas"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="{ROTULOS.get(expressao, 'Lia')}">
<title>{ROTULOS.get(expressao, 'Lia')}</title>
<circle cx="100" cy="100" r="98" fill="{FUNDO}"/>
<clipPath id="corte"><circle cx="100" cy="100" r="98"/></clipPath>
<g clip-path="url(#corte)">
  <path d="M28 205 Q32 158 72 146 L128 146 Q168 158 172 205 Z" fill="{BLUSA}"/>
  <path d="M84 146 L100 172 L116 146 Z" fill="{GOLA}"/>
  <rect x="88" y="124" width="24" height="26" rx="8" fill="{PELE_SOMBRA}"/>
  {_cabelo()}
  <ellipse cx="62" cy="98" rx="6" ry="9" fill="{PELE_SOMBRA}"/><ellipse cx="138" cy="98" rx="6" ry="9" fill="{PELE_SOMBRA}"/>
  <circle cx="62" cy="109" r="3" fill="#f4f1ec"/><circle cx="138" cy="109" r="3" fill="#f4f1ec"/>
  <ellipse cx="100" cy="98" rx="37" ry="42" fill="{PELE}"/>
  <path d="{sob_e}" stroke="#2b1c16" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  <path d="{sob_d}" stroke="#2b1c16" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  {_olhos(e["olhos"])}
  <rect x="67" y="81" width="27" height="21" rx="8" stroke="{ARMACAO}" stroke-width="2.6" fill="#ffffff" fill-opacity=".08"/>
  <rect x="106" y="81" width="27" height="21" rx="8" stroke="{ARMACAO}" stroke-width="2.6" fill="#ffffff" fill-opacity=".08"/>
  <path d="M94 89 Q100 86 106 89" stroke="{ARMACAO}" stroke-width="2.4" fill="none"/>
  <path d="M100 98 Q97 108 100 110 Q103 111 106 109" stroke="{PELE_SOMBRA}" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  <ellipse cx="80" cy="110" rx="6" ry="3.5" fill="#a25a44" opacity=".35"/><ellipse cx="120" cy="110" rx="6" ry="3.5" fill="#a25a44" opacity=".35"/>
  {e["boca"]}
</g>
{_simbolo(e["simbolo"])}
</svg>'''


def img(expressao="acolhedora", tamanho=96):
    """<img> com o SVG embutido (funciona em st.markdown)."""
    dados = base64.b64encode(svg(expressao).encode("utf-8")).decode("ascii")
    return (f'<img src="data:image/svg+xml;base64,{dados}" width="{tamanho}" height="{tamanho}" '
            f'alt="{ROTULOS.get(expressao, "Lia")}" style="display:block"/>')
