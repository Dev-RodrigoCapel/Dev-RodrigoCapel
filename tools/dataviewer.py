"""Gera os cartões da Dataviewer para o README (rodado pelo workflow, que tem acesso à internet).

Baixa o logo e os logos de clientes de dataviewer.com.br e monta SVGs com as imagens embutidas
(o GitHub não carrega imagens externas de dentro de um SVG). Saída em dist/:
  dataviewer-dark.svg / dataviewer-light.svg   cartão da consultoria
  clientes-dark.svg   / clientes-light.svg     faixa "Empresas com projetos conosco"
Uso: python tools/dataviewer.py [pasta_de_saida]
"""
import base64, io, sys, urllib.request
from PIL import Image

BASE = "https://dataviewer.com.br/images/"
LOGO = "dataviewer.png"
CLIENTES = ["Asfrete.png", "logogrupocangaia.png", "Apolar.png", "logoclarity.png", "Imagem2.png", "logo2.png"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
FONT = "'Segoe UI',Helvetica,Arial,sans-serif"


def baixar(nome):
    if nome.startswith("/") or nome.startswith("."):  # arquivo local (testes)
        dados = open(nome, "rb").read()
    else:
        req = urllib.request.Request(BASE + nome, headers={"User-Agent": "Mozilla/5.0"})
        dados = urllib.request.urlopen(req, timeout=30).read()
    im = Image.open(io.BytesIO(dados)).convert("RGBA")
    bbox = im.getbbox()  # corta bordas transparentes
    if bbox:
        im = im.crop(bbox)
    im.thumbnail((480, 240))
    # logo claro (ex.: branco sobre transparente) vai num fundo escuro; os demais em fundo branco
    dados = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
    px = [p for p in dados if p[3] > 128] or [(0, 0, 0, 255)]
    lum = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px) / len(px)
    fundo = "#101826" if lum > 200 else "#ffffff"
    buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
    return im.size, "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), fundo


def caber(size, w, h):
    iw, ih = size; k = min(w / iw, h / ih)
    return iw * k, ih * k


def cartao(logo, dark):
    bg, ink, mute, line = ("#0d1117", "#f0f3f6", "#9aa4b2", "#2a3547") if dark else ("#ffffff", "#16181d", "#57606a", "#d0d7de")
    acc = "#4f8cff" if dark else "#2350b8"
    (lw, lh) = caber(logo[0], 250, 160)
    servicos = [("Power BI", "implantação, modelagem semântica, DAX avançado e governança"),
                ("Integração de dados", "ETL/ELT, APIs, pipelines e automações entre ERPs, CRMs e bancos"),
                ("Treinamentos", "capacitações in-company de Power BI e cultura data-driven")]
    linhas = ""
    for i, (t, d) in enumerate(servicos):
        y = 92 + i * 46
        linhas += (f'<circle cx="372" cy="{y - 5}" r="4" fill="{acc}"/>'
                   f'<text x="386" y="{y}" font-family="{FONT}" font-size="17" font-weight="700" fill="{ink}">{t}</text>'
                   f'<text x="386" y="{y + 20}" font-family="{FONT}" font-size="14" fill="{mute}">{d}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="240" viewBox="0 0 1200 240">
<rect x="1" y="1" width="1198" height="238" rx="16" fill="{bg}" stroke="{line}"/>
<rect x="24" y="24" width="300" height="192" rx="12" fill="{logo[2]}" stroke="{line}"/>
<image x="{174 - lw / 2}" y="{120 - lh / 2}" width="{lw}" height="{lh}" href="{logo[1]}" xlink:href="{logo[1]}"/>
<text x="356" y="50" font-family="{FONT}" font-size="22" font-weight="700" fill="{acc}">Consultoria em dados &amp; Power BI</text>
<text x="1170" y="50" text-anchor="end" font-family="{FONT}" font-size="15" fill="{mute}">o próximo nível da análise de dados</text>
{linhas}
</svg>'''


def faixa(logos, dark):
    bg, line, mute = ("#0d1117", "#2a3547", "#9aa4b2") if dark else ("#ffffff", "#d0d7de", "#57606a")
    n = len(logos); gap = 16; cw = (1200 - 48 - gap * (n - 1)) / n; ch = 96
    itens = ""
    for i, lg in enumerate(logos):
        x = 24 + i * (cw + gap)
        w, h = caber(lg[0], cw - 28, ch - 28)
        itens += (f'<rect x="{x:.1f}" y="52" width="{cw:.1f}" height="{ch}" rx="12" fill="{lg[2]}" stroke="{line}"/>'
                  f'<image x="{x + cw / 2 - w / 2:.1f}" y="{52 + ch / 2 - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" href="{lg[1]}" xlink:href="{lg[1]}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="172" viewBox="0 0 1200 172">
<rect x="1" y="1" width="1198" height="170" rx="16" fill="{bg}" stroke="{line}"/>
<text x="24" y="34" font-family="{FONT}" font-size="15" font-weight="600" fill="{mute}">Empresas com projetos conosco</text>
{itens}
</svg>'''


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    logo = baixar(LOGO)
    clientes = []
    for c in CLIENTES:
        try:
            clientes.append(baixar(c))
        except Exception as e:
            print(f"aviso: não baixou {c}: {e}")
    for dark, suf in ((True, "dark"), (False, "light")):
        open(f"{OUT}/dataviewer-{suf}.svg", "w").write(cartao(logo, dark))
        open(f"{OUT}/clientes-{suf}.svg", "w").write(faixa(clientes, dark))
    print(f"Dataviewer: logo + {len(clientes)} clientes")


if __name__ == "__main__":
    if len(sys.argv) > 2:  # modo teste: python tools/dataviewer.py dist logo.png c1.png c2.png...
        LOGO, CLIENTES = sys.argv[2], sys.argv[3:]
    main()
