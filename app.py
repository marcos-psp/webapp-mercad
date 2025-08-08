from flask import Flask, render_template, request, redirect, url_for
import easyocr
import pandas as pd
import os
import re
from datetime import datetime

app = Flask(__name__)
reader = easyocr.Reader(['pt'])
HISTORICO_ARQUIVO = "historico_compras.csv"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "Nenhum arquivo enviado", 400
    file = request.files["file"]

    if file.filename == "":
        return "Nenhum arquivo selecionado", 400

    os.makedirs("uploads", exist_ok=True)
    caminho = os.path.join("uploads", file.filename)
    file.save(caminho)

    texto = "\n".join(reader.readtext(caminho, detail=0, paragraph=True))
    compras = processar_texto_recebido(texto)
    salvar_historico_csv(compras)

    return redirect(url_for("historico"))

@app.route("/historico")
def historico():
    if os.path.exists(HISTORICO_ARQUIVO):
        df = pd.read_csv(HISTORICO_ARQUIVO)
        return df.to_html(index=False)
    return "Nenhum histórico encontrado."

def processar_texto_recebido(texto):
    linhas = texto.split("\n")
    compras = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        match = re.search(r"(.+?)\s+(\d+,\d{2})$", linha)
        if match:
            produto = match.group(1).strip()
            valor = match.group(2).replace(",", ".")
            compras.append({
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Produto": produto,
                "Valor": float(valor)
            })
    return compras

def salvar_historico_csv(compras):
    try:
        df_existente = pd.read_csv(HISTORICO_ARQUIVO)
        df_novo = pd.DataFrame(compras)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    except FileNotFoundError:
        df_final = pd.DataFrame(compras)
    df_final.to_csv(HISTORICO_ARQUIVO, index=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
