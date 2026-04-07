from flask import Flask, jsonify, request
import random
import firebase_admin
from firebase_admin import credentials, firestore
from auth import token_obrigatorio, gerar_token
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)
# verson do open api
app.config['SWAGGER'] = {
    'openapi': '3.0.0'
}
# chamar o open api para o código
swagger = Swagger(app, template_file='openapi.yaml')

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
CORS(app, origins="*")
ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

if os.getenv("VERCEL"):
    # ONLINE NA VERCEL
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:
    # LOCAL HOST (NO PROPIO PC)
    cred = credentials.Certificate("firebase.json") # carregar as credenciais do firebase

firebase_admin.initialize_app(cred)

# conectar-se ao firestore
db = firestore.client()

# rota principal de boas-vindas 
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "api": "charadas",
        "version": "1.0",
        "author": "Mayara"
    }), 200

# ROTA LOGIN
@app.route("/login", methods = ["POST"])
def login():
    dados = request.get_json()

    if not dados:
        return jsonify({"Error": "Envie os dados para login"}), 400
    
    usuario = dados.get('usuario')
    senha = dados.get('senha')

    if not usuario or not senha:
        return jsonify({"Error": "Usuário e senha são obrigatórios!"})
    
    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({"message": "Login realizao com sucesso!", "token":token}),200
    
    return jsonify({"Error": "Usuário ou senha inválidos"}),401

# -------------------------------------------------
# rotas PÚBLICAS
# -------------------------------------------------
# Rota 1 - Método GET - Todas as charadas
@app.route("/charadas", methods=['GET'])
def get_charadas():
    charadas = [] # lita vazia
    lista = db.collection('charadas').stream() # o stream pega as informações - lista todos os dados

    # o for transforma objeto do firestore em dicionário py
    for item in lista:
        charadas.append(item.to_dict())

    return jsonify(charadas), 200

# Rota 2 - Método GET - Charadas aleatórias
@app.route("/charadas/aleatoria", methods=['GET'])
def get_charadas_random():
    charadas = [] # lita vazia
    lista = db.collection('charadas').stream() # o stream pega as informações - lista todos os dados

    # o for transforma objeto do firestore em dicionário py
    for item in lista:
        charadas.append(item.to_dict())

    return jsonify(random.choice(charadas)), 200

# rota 3 - método GET - retorna uma charada pelo id
@app.route("/charadas/<int:id>", methods=['GET'])
def get_charada_by_id(id):
    lista = db.collection('charadas').where('id', '==', id).stream()

    for item in lista:
        return jsonify(item.to_dict()), 200
    
    return jsonify({"Error: charada não encontrada!"}), 404

# ------------------------------------------
# Rotas Privadas - autentificação bearer
# -----------------------------------------
# Rota 4 - Método POST - Cadastro de novas charadas
@app.route("/charadas", methods=['POST'])
@token_obrigatorio
def post_charadas():
    
    dados = request.get_json()
    
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"error":"Dados inválidos ou incompletos"}), 400
    
    try:
        # busca pelo contador
        contador_ref = db.collection("contador").document("controle_id")
        contador_doc = contador_ref.get()
        ultimo_id = contador_doc.to_dict().get("ultimo_id")

        # somar ao ultimo id
        novo_id = ultimo_id + 1
        
        # vai atualizar o id do contador
        contador_ref.update({"ultimo_id": novo_id})


        # cadastro da nova charada
        db.collection("charadas").add({
            "id": novo_id,
            "pergunta": dados["pergunta"],
            "resposta": dados["resposta"]
        })

        return jsonify({"message": "Charada criada com sucesso!"}), 201
    except:
        return jsonify({"error": "Falha no envio da charada."})

# rota 5 - método PUT - alterar totalmente
@app.route("/charadas/<int:id>", methods=['PUT'])
@token_obrigatorio
def charadas_put(id):
    
    dados = request.get_json()

    # No PUT é necessário enviar a PERGUNTA e a RESPOSTA
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"error":"Dados inválidos ou incompletos"}), 400
    
    try:
        docs = db.collection("charadas").where("id","==", id).limit(1).get()
        if not docs:
            return jsonify({"error":"Charada não encontrada!"}), 404
        
        # pega o primeiro (e o unico) documento da lista
        for doc in docs:
            doc_ref = db.collection("charadas").document(doc.id)
            doc_ref.update({
                "pergunta": dados["pergunta"],
                "resposta": dados["resposta"]
            })

        return jsonify({"message": "Charada alterada com sucesso!"}), 200
    except:   
        return jsonify({"error": "Falha no envio a charada"}), 400

# rota 6 - método PATCH - alterar pontualmente
@app.route("/charadas/<int:id>", methods=['PATCH'])
@token_obrigatorio
def charadas_patch(id):
    
    dados = request.get_json()

    # Não é necessário mudar todos os campos
    if not dados or ("pergunta" not in dados and "resposta" not in dados):
        return jsonify({"error":"Dados inválidos"}), 400
    
    try:
        docs = db.collection("charadas").where("id","==", id).limit(1).get()
        if not docs:
            return jsonify({"error":"Charada não encontrada!"}), 404
        
        doc_ref = db.collection("charadas").document(docs[0].id)
        update_charada = {}
        if "pergunta" in dados:
            update_charada["pergunta"] =  dados["pergunta"]

        if "resposta" in dados:
            update_charada["resposta"] = dados["resposta"]

        # atualiza o firestore
        doc_ref.update(update_charada)

        return jsonify({"message": "Charada alterada com sucesso!"}), 200
    
    except:   
        return jsonify({"error": "Falha no envio a charada"}), 400

# rota 7 - metodo DELETE - para apagar uma charada
@app.route("/charadas/<int:id>", methods=['DELETE'])
@token_obrigatorio
def charadas_delete(id):
    
    docs = db.collection("charadas").where("id","==",id).limit(1).get()

    if not docs:
        return jsonify({"erro": "charada não encontrada!"}), 404
    
    doc_ref = db.collection("charadas").document(docs[0].id)
    doc_ref.delete()
    return jsonify({"message": "Charada excluida com sucesso!"}), 200

# ------------------------------
# ROTAS DE TRATAMENTOS DE ERROS
# -----------------------------
@app.errorhandler(404)
def error404(error):
    return jsonify({"error":"URL não encontrada!"}), 404

@app.errorhandler(500)
def error500(error):
    return jsonify({"error":"Servidor interno com falhas. Tente novamnete mais tarde!"}), 500

if __name__ == "__main__":
    app.run(debug=True)