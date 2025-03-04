import json
from flask import Flask, request, jsonify
from flask_cors import CORS  
from google import genai
from google.genai import types

app = Flask(__name__)

CORS(app, origins="*", supports_credentials=True) 

client = genai.Client(api_key="AIzaSyDAz2dWenXfdzVx9mjMCl5NzE6dQNDb6zk")

@app.route('/generate_news', methods=['POST'])
def generate_news():
    if 'file' not in request.files:
        return jsonify({"error": "Arquivo PDF não encontrado."}), 400

    pdf_file = request.files['file']
    if pdf_file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    pdf_data = pdf_file.read()

    # Verificar se foi enviado um prompt, caso contrário usar o prompt padrão
    custom_prompt = request.form.get('custom_prompt')

    if custom_prompt:
        prompt = f"""
        {custom_prompt}

        **IMPORTANTE:** Retorne **somente um JSON** e nada mais, no formato exato abaixo:

        ```json
        {{
            "title": "Título da notícia",
            "content": "Conteúdo completo da notícia gerada"
        }}
        ```

        🚫 **Não escreva nada além do JSON acima!** 🚫  
        🚫 **Não inclua explicações, comentários ou qualquer outro texto.** 🚫  
        🚫 **Não modifique o formato do JSON.** 🚫  
        """
    else:
        prompt = """
        Você é um jornalista especializado em gerar notícias com base em documentos.
        Gere uma notícia detalhada com base no conteúdo do PDF enviado.

        **IMPORTANTE:** Retorne **somente um JSON** e nada mais, no formato exato abaixo:

        ```json
        {
            "title": "Título da notícia",
            "content": "Conteúdo completo da notícia gerada"
        }
        ```

        🚫 **Não escreva nada além do JSON acima!** 🚫  
        🚫 **Não inclua explicações, comentários ou qualquer outro texto.** 🚫  
        🚫 **A notícia tem que conter no mínimo 3200 caracteres ** 🚫  

        A notícia deve ser longa, estruturada corretamente com quebras de linha, como em uma notícia brasileira, e usar toda a informação relevante do PDF.
        Não omita nenhum detalhe e escreva o conteúdo de forma bem detalhada, como é esperado em uma boa reportagem.
        """


    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'), prompt]
        )

        print("DEBUG - Resposta da API Gemini:", response)

        if response and hasattr(response, 'text') and response.text.strip():
            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()

            try:
                news_json = json.loads(json_text)
                return jsonify(news_json)
            except json.JSONDecodeError:
                return jsonify({"error": "Erro ao decodificar JSON", "response": response.text}), 500
        else:
            return jsonify({"error": "Resposta vazia ou inválida da API Gemini", "response": str(response)}), 500
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro na chamada da API Gemini: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
