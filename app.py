import os
from flask import Flask, render_template, request, jsonify
import requests
from pypinyin import pinyin, Style
import jieba

app = Flask(__name__)

YAHOO_API_KEY = os.getenv("YAHOO_API_KEY")  # 從環境變數讀取API KEY
YAHOO_API_URL = "https://jlp.yahooapis.jp/JIMService/V2/conversion"

def yahoo_japanese_convert(text, options=None, mode="kanakanji"):
    payload = {
        "id": "test-1",
        "jsonrpc": "2.0",
        "method": "jlp.jimservice.conversion",
        "params": {
            "q": text,
            "format": "hiragana",
            "mode": mode,
            "option": options or ["hiragana", "katakana", "alphanumeric", "half_katakana", "half_alphanumeric"],
            "dictionary": ["base", "name", "place", "zip", "symbol"],
            "results": 5
        }
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": YAHOO_API_KEY,
        "X-Yahoo-App-Id": YAHOO_API_KEY
    }
    response = requests.post(YAHOO_API_URL, headers=headers, json=payload)
    return response.json()

def chinese_pinyin(text):
    seg_list = list(jieba.cut(text))
    py = [' '.join([s[0] for s in pinyin(seg, style=Style.NORMAL)]) for seg in seg_list]
    return list(zip(seg_list, py))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    req = request.json
    in_text = req.get("text")
    lang = req.get("lang")
    mode = req.get("mode")
    out = {}

    if lang == "jp":
        y_resp = yahoo_japanese_convert(in_text)
        if mode == "jp_furigana":
            furigana = []
            for seg in y_resp['result']['segment']:
                src = seg.get('candidate', [seg['hiragana']])[0]
                kana = seg['hiragana']
                furigana.append((src, kana))
            out['furigana'] = furigana
        elif mode == "jp_romaji":
            roma = []
            for seg in y_resp['result']['segment']:
                roman = seg['half_alphanumeric']
                roma.append(roman)
            out['roma'] = ' '.join(roma)
    elif lang == "zh":
        if mode == "zh_pinyin":
            out['pinyin'] = chinese_pinyin(in_text)
        elif mode == "zh_bopomofo":
            # 簡易示範，實際需補充中文注音轉換函式
            out['bopo'] = chinese_pinyin(in_text)  # 先用拼音代替
    else:
        out['err'] = "語言未支援"
    return jsonify(out)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
