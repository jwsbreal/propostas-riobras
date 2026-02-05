from flask import Flask, render_template, request, send_file
import pdfkit
import os
from datetime import datetime
from pathlib import Path
from dados_produtos import PRODUTOS


app = Flask(__name__)

config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)


def gerar_codigo_proposta():
    with open("contador_propostas.txt", "r") as f:
        numero = int(f.read())

    numero += 1

    with open("contador_propostas.txt", "w") as f:
        f.write(str(numero))

    ano = datetime.now().year
    return f"{ano}-{numero:04d}"


def pasta_mes_atual():
    agora = datetime.now()
    pasta = f"{agora.year}_{agora.month:02d}"
    caminho = os.path.join("propostas_geradas", pasta)
    os.makedirs(caminho, exist_ok=True)
    return caminho


@app.route("/", methods=["GET", "POST"])
def forms():
    if request.method == "POST":
        codigo = gerar_codigo_proposta()
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        pasta_destino = pasta_mes_atual()

        desconto = float(request.form.get("desconto") or 0)
        frete = float(request.form.get("frete") or 0)

        # Dados do formulário
        linha = request.form["linha"]
        rodagem = request.form["rodagem"]
        material = request.form["material"]
        largura_garfo = request.form["largura_garfo"]

        produto = PRODUTOS.get(linha)

        if not produto:
            return "Produto não encontrado", 400

        try:
            rodagem_info = produto["rodagem"][rodagem]
            material_info = rodagem_info["materiais"][material]
        except KeyError:

            return "Configuração de produto inválida", 400

        rodagem_info = produto["rodagem"][rodagem]
        material_info = rodagem_info["materiais"][material]

        preco_avista = material_info["avista"]
        preco_faturado = material_info["faturado"]

        total_avista = round(preco_avista - desconto + frete, 2)
        total_faturado = round(preco_faturado - desconto + frete, 2)

        caminho_logo = Path("static/logo.png").resolve().as_uri()

        dados = {
            "empresa": request.form["empresa"],
            "cnpj": request.form.get("cnpj"),
            "contato": request.form.get("contato"),
            "telefone": request.form.get("telefone"),

            "linha": linha,
            "rodagem": rodagem,
            "material": material,
            "largura_garfo": largura_garfo,

            "vendedor": request.form["vendedor"],
            "codigo": codigo,
            "data": data_hoje,
            "caminho_logo": caminho_logo,

            "produto": produto,

            "preco_avista": preco_avista,
            "preco_faturado": preco_faturado,
            "tipo_roda": rodagem_info["roda"],
            "capacidade": produto["capacidade"],
            "descricao": produto["descricao"],

            "desconto": desconto,
            "frete": frete,
            "total_avista": total_avista,
            "total_faturado": total_faturado,


        }

        html_renderizado = render_template("proposta.html", **dados)

        linha_limpa = linha.replace(" ", "_")
        empresa_limpa = dados["empresa"].replace(" ", "_")

        nome_arquivo = f"PROP-{linha_limpa}_-_{codigo}_-_{empresa_limpa}.pdf"
        caminho_pdf = os.path.join(pasta_destino, nome_arquivo)

        pdfkit.from_string(
            html_renderizado,
            caminho_pdf,
            configuration=config,
            options={"enable-local-file-access": ""},
        )

        return send_file(caminho_pdf, as_attachment=True)

    # GET
    return render_template("forms.html", produtos=PRODUTOS)


if __name__ == "__main__":
    app.run(debug=True)
