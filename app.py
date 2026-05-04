import os
import cv2
import yt_dlp
import json
import google.generativeai as genai
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Libera o acesso para o seu front-end (Google Script)

# Configuração da sua Mente CCO
CHAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "COLE_SUA_CHAVE_AQUI")
genai.configure(api_key=CHAVE_GEMINI)

URL_LIVE_SBCH = "https://www.youtube.com/watch?v=qlDB6AbQyAw"


def capturar_frame_youtube():
    # 1. Acha o link real do vídeo por trás do YouTube
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(URL_LIVE_SBCH, download=False)
            video_url = info['url']

        # 2. Abre a transmissão, tira 1 foto e fecha
        cap = cv2.VideoCapture(video_url)
        ret, frame = cap.read()
        cap.release()

        if ret:
            cv2.imwrite("snapshot_sbch.jpg", frame)
            return True
        return False

    except Exception as e:
        print("Erro na captura:", e)
        return False


@app.route('/api/visao-cco', methods=['GET'])
def analisar_visao():
    if not capturar_frame_youtube():
        return jsonify({"erro": "Falha ao interceptar a câmera de SBCH"}), 500

    try:
        # Chama a IA de Visão Computacional
        model = genai.GenerativeModel('gemini-1.5-flash')
        arquivo_imagem = genai.upload_file("snapshot_sbch.jpg")

        # O Comando de DOV para a máquina
        prompt = """
Atue como um meteorologista aeronáutico sênior analisando a câmera da pista de Chapecó (SBCH).
Responda EXATAMENTE neste formato JSON e nada mais:
{
  "visibilidade_metros": 5000,
  "nevoeiro": true,
  "analise_tática": "Uma frase direta sobre a condição visual da pista."
}
Se a pista estiver super nítida, coloque visibilidade 10000.
"""

        resposta = model.generate_content([prompt, arquivo_imagem])
        genai.delete_file(arquivo_imagem.name)

        # Limpa o retorno para garantir que o Vue.js vai conseguir ler o JSON
        texto_limpo = resposta.text.replace('```json', '').replace('```', '').strip()
        dados_ia = json.loads(texto_limpo)

        return jsonify(dados_ia)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == '__main__':
    # Roda o servidor na porta 5000
    app.run(host='0.0.0.0', port=5000)
