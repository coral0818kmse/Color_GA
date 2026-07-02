import json
import random
import numpy as np
import colorsys
import streamlit as st
import requests
from math import log2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import sys
import os
import uuid
import base64
import html

# --- Streamlitページ設定 ---
st.set_page_config(page_title="感性駆動型三色配色GA (Dify連携)", layout="wide")

# --- カスタムCSS ---
st.markdown("""
<style>
.stApp {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
.generation-palette-container {
    display: flex;
    flex-wrap: wrap; 
    gap: 20px; 
    justify-content: flex-start; 
    border-radius: 5px;
    padding: 10px;
}
.palette-item {
    width: calc(50% - 10px); 
    box-sizing: border-box;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #eee; 
}
.color-swatch-group {
    display: flex;
    margin-top: 5px;
}
.color-swatch {
    width: 80px; 
    height: 40px; 
    box-sizing: border-box;
}
.stCheckbox {
    margin-top: -10px;
}
.finish-btn-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
}
</style>""", unsafe_allow_html=True)


# --- Dify API呼び出し関数 ---
def call_dify_api(base_color_id, input_text):
    API_ENDPOINT = "https://api.dify.ai/v1/workflows/run" 
    API_KEY = st.secrets["DIFY_API_KEY"] 
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"base_color_id": base_color_id, "input_text": input_text},
        "query": f"AI分析 for ID: {base_color_id}", 
        "user": "ga-research-user",
        "response_mode": "blocking" 
    }
    
    json_string = "初期化エラー: API呼び出し前"
    response_data = None 

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status() 
        response_data = response.json() 
        
        target_data_list = None 
        
        if 'data' in response_data and isinstance(response_data['data'], dict):
            workflow_data = response_data['data']
            if 'outputs' in workflow_data and isinstance(workflow_data['outputs'], dict):
                outputs = workflow_data['outputs']
                
                if 'structured_output' in outputs and \
                   isinstance(outputs['structured_output'], dict) and \
                   'data' in outputs['structured_output'] and \
                   isinstance(outputs['structured_output']['data'], list):
                    target_data_list = outputs['structured_output']['data']
                elif outputs:
                    first_output_key = next(iter(outputs))
                    first_value = outputs[first_output_key]
                    if isinstance(first_value, str):
                        json_string = str(first_value).replace("```json", "").replace("```", "").strip()
                        target_data_list = json.loads(json_string)
                    else:
                        raise ValueError("AI 'outputs' フィールドが予期しない形式です。")
                else:
                    raise ValueError(f"AI応答の 'outputs' が空です。")
            else:
                 raise ValueError(f"AI応答に 'outputs' がありません。")
        else:
             raise ValueError(f"AI応答に処理可能な 'data' がありません。")

        if not isinstance(target_data_list, list) or not target_data_list:
            raise ValueError("AIはターゲットのリストを返しませんでした。")
        
        validated_list = []
        for target in target_data_list:
            if not all(k in target for k in ['target_tone_1', 'target_tone_2', 'target_hue_1', 'target_hue_2']):
                st.warning(f"AIの解釈の一部に必要なキーがありません: {target}")
                continue
            target['name'] = target.get('name', 'Unnamed Interpretation')
            target['target_hue_1'] = int(target['target_hue_1'])
            target['target_hue_2'] = int(target['target_hue_2'])
            validated_list.append(target)
            
        if not validated_list:
            raise ValueError("AIの応答リストに、有効なターゲットが含まれていません。")

        st.sidebar.subheader("🤖 Dify AI 分析結果 (5つの解釈)")
        st.sidebar.json(validated_list)
        return validated_list

    except requests.exceptions.HTTPError as e:
        st.error(f"Dify API HTTPエラー: ステータスコード {response.status_code}")
        st.code(f"エラー詳細: {response.text}", language='json')
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        st.error(f"AI応答の解析エラー: {e}")
        return None


# --- HSV → HEX 変換 ---
def hsv_to_rgb_hex(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360, s, v) 
    return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))


# --- SVGロゴ生成関数 (重複バグ防止のためuuidを付与) ---
# --- SVGロゴ生成関数 ---
# --- SVGロゴ生成関数 ---
# --- SVGロゴ生成関数 ---
def generate_logo_svg(current_hexes):
    # 端が切れるのを防ぐため、viewBoxを広げて transform で全体に余白を持たせています
    return f"""
    <svg id="_レイヤー_1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1010 930" style="width:100%; max-width:200px; height:auto; margin:10px 0; overflow:visible;">
        <g transform="translate(20, 25)">
            <path d="M205.88,321.49l-56.47,7.43c-.49-3.7-1.15-9-1.99-15.91-.84-6.9-2.2-17.48-4.08-31.75-3.98.52-7.36.95-10.14,1.28-2.78.33-5.99.74-9.62,1.21-3.09.41-6.03.81-8.84,1.22-2.81.41-5.92.83-9.35,1.28,1.1,8.37,2.27,16.95,3.5,25.75,1.23,8.8,2.22,16.08,2.98,21.84l-56.47,7.43c-.79-6.03-1.77-13.72-2.93-23.05-1.16-9.33-3.35-26.28-6.59-50.83-1.07-8.16-2.4-17.98-3.98-29.46-1.58-11.48-3.12-22.94-4.63-34.39l56.47-7.43c1.21,9.19,2.21,17.03,2.99,23.52.78,6.49,1.64,13.27,2.57,20.33,3.43-.45,6.55-.84,9.37-1.18,2.82-.34,5.8-.71,8.96-1.13,3.7-.49,6.91-.93,9.61-1.32,2.7-.39,6.04-.85,10.02-1.37-.82-6.24-1.75-13.04-2.79-20.4-1.04-7.36-2.1-15.16-3.18-23.39l56.47-7.43c1.74,13.24,3.4,26.1,4.98,38.59,1.57,12.49,2.88,22.64,3.9,30.46,1.82,13.85,3.63,27.32,5.43,40.41,1.79,13.09,3.07,22.51,3.83,28.27Z" style="fill:{current_hexes[0]};"/>
            <path d="M373.64,229.4c1.42,10.77.69,21.05-2.17,30.84-2.86,9.79-8.12,18.96-15.79,27.51-6.02,6.72-13.6,12.24-22.73,16.54-9.13,4.31-19.11,7.17-29.95,8.6-10.77,1.42-21.04,1.29-30.82-.39-9.78-1.68-18.63-5.03-26.54-10.06-9.31-6.03-16.73-13.44-22.29-22.23-5.55-8.79-9.05-18.67-10.5-29.65-1.4-10.63-.76-20.62,1.91-29.97,2.68-9.35,7.42-18.07,14.24-26.15,6.28-7.38,13.97-13.38,23.06-18,9.09-4.61,19.53-7.7,31.33-9.25,11.18-1.47,21.71-1.32,31.61.44,9.89,1.77,19.04,5.41,27.44,10.93,9.17,6.05,16.3,13.36,21.41,21.93,5.1,8.57,8.36,18.21,9.77,28.9ZM315.78,237.38c-.57-4.33-1.85-8.65-3.85-12.96-2-4.31-4.79-7.6-8.36-9.86-1.76-1.16-3.83-2.06-6.21-2.69-2.38-.63-5.05-.75-8-.36-2.81.37-5.25,1.16-7.33,2.38-2.07,1.22-4.04,2.96-5.9,5.23-2.33,2.96-3.94,6.64-4.83,11.02-.89,4.38-1.06,8.63-.52,12.75.58,4.4,1.83,8.58,3.75,12.56,1.92,3.98,4.57,7.18,7.96,9.59,2.01,1.48,4.24,2.54,6.69,3.16,2.45.62,5.15.74,8.1.35,2.61-.34,5-1.13,7.17-2.36,2.17-1.23,4.08-2.79,5.71-4.69,2.59-3.06,4.31-6.87,5.14-11.42.83-4.55.99-8.78.47-12.7Z" style="fill:{current_hexes[0]};"/>
            <path d="M520.46,192.07c1.38,10.49.04,19.65-4.02,27.48-4.06,7.82-10.27,14.73-18.62,20.71-5.93,4.2-13.47,7.76-22.61,10.67-9.14,2.91-17.24,4.87-24.29,5.87l4.3,31.87-56.47,7.43c-1.19-9.05-2.44-18.76-3.73-29.12-1.3-10.36-3.22-25.28-5.79-44.76-1.07-8.16-2.4-17.98-3.98-29.46-1.58-11.48-3.12-22.94-4.63-34.39,3.77-.5,8.44-1.16,14.02-2,5.58-.84,11.21-1.63,16.9-2.38,18.45-2.43,32.23-3.73,41.34-3.92,9.11-.19,17.76.61,25.95,2.39,11.84,2.49,21.39,7.09,28.66,13.81,7.27,6.72,11.59,15.32,12.97,25.81ZM463.51,204.59c-.38-2.88-1.34-5.53-2.88-7.94-1.54-2.41-3.61-4.25-6.22-5.51-2.31-1.09-4.55-1.67-6.72-1.73-2.17-.06-4.32.05-6.44.33-.21.03-.93.12-2.16.28.16,1.23.49,3.74.99,7.51.5,3.77.93,7.06,1.3,9.88.42,3.22,1.29,9.77,2.59,19.65.21-.03.58-.08,1.13-.15.55-.07.93-.12,1.13-.15,1.65-.22,3.66-.78,6.06-1.69,2.39-.91,4.18-1.89,5.37-2.96,2.44-2.14,4.18-4.42,5.22-6.86,1.04-2.44,1.25-5.99.64-10.65Z" style="fill:{current_hexes[0]};"/>
            <path d="M597.85,129.77c2.1,19.12,3.07,36.19,2.92,51.2-.15,15.02-.63,27.12-1.45,36.29l-41.86,5.51c-3.32-9.33-6.91-20.93-10.75-34.79-3.85-13.86-7.37-30.56-10.57-50.09l61.72-8.12ZM612.38,267.97l-54.62,7.19-5.46-41.45,54.62-7.19,5.46,41.45Z" style="fill:{current_hexes[0]};"/>
            <path d="M425,439.67c-1.08,8.23-4.38,14.86-9.89,19.89-5.51,5.03-12.63,8.92-21.37,11.68-7.5,2.36-17.1,3.52-28.82,3.48-11.71-.04-22.54-.72-32.49-2.03-9.12-1.2-16.5-2.28-22.13-3.23-5.63-.95-9.84-1.68-12.63-2.19l-.41-45.36c.74.17,4.51.8,11.31,1.91,6.79,1.1,11.26,1.8,13.38,2.08,2.74.36,5.9.78,9.46,1.25,3.56.47,7.04.82,10.43,1.06,4.64.26,7.64-.02,9.01-.85,1.36-.83,2.13-1.86,2.29-3.1.2-1.51-.43-2.85-1.88-4.01-1.45-1.17-4.23-2.86-8.33-5.07-2.21-1.2-5.51-3.08-9.88-5.64-4.37-2.56-7.79-4.84-10.24-6.84-5.8-4.67-9.77-9.75-11.91-15.22-2.14-5.48-2.8-11.3-1.99-17.48.51-3.91,1.73-7.6,3.66-11.08,1.92-3.48,4.32-6.35,7.21-8.63,7.73-6.24,18.48-10.53,32.25-12.86,13.77-2.34,30.26-2.24,49.46.29,8.43,1.11,14.8,2.02,19.1,2.72,4.3.71,7.33,1.25,9.1,1.62l.31,45.35c-3.14-.55-6.12-1.08-8.95-1.6-2.83-.51-6.37-1.05-10.62-1.61-3.84-.5-7.19-.89-10.05-1.17-2.86-.27-6.02-.53-9.47-.78-3.32-.23-5.81-.09-7.49.43-1.67.51-2.6,1.46-2.78,2.83-.21,1.58.53,3,2.21,4.27,1.68,1.27,4.31,2.9,7.88,4.91,3.44,1.92,6.9,3.86,10.38,5.81,3.47,1.96,6.82,4.2,10.05,6.71,5.55,4.43,9.46,9.3,11.73,14.62,2.26,5.32,2.96,11.27,2.1,17.86Z" style="fill:{current_hexes[1]};"/>
            <path d="M567.98,408.37c-5.21-.69-11.86-1.58-19.95-2.68-8.09-1.1-14.67-1.98-19.74-2.65-.84,6.38-1.66,12.32-2.45,17.83-.79,5.51-1.68,11.97-2.65,19.38-1.5,11.38-2.8,21.54-3.91,30.46-1.11,8.92-2.12,16.88-3.04,23.88l-56.47-7.43c.85-6.45,1.81-13.52,2.9-21.23,1.08-7.71,2.53-18.45,4.35-32.23.81-6.17,1.61-12.35,2.39-18.52.78-6.18,1.58-12.7,2.42-19.56-6.86-.9-14.54-1.9-23.05-2.98-8.51-1.08-14.06-1.8-16.67-2.14l6.09-46.29c3.02.4,11.95,1.59,26.79,3.58,14.84,1.99,28.71,3.83,41.6,5.53,10.35,1.36,22.92,3,37.71,4.91,14.78,1.91,24.71,3.2,29.78,3.87l-6.09,46.29Z" style="fill:{current_hexes[1]};"/>
            <path d="M682.97,516.53c-4.94-.65-14.72-1.96-29.36-3.92-14.64-1.96-26.48-3.54-35.53-4.73-10.63-1.4-21.67-2.84-33.13-4.31-11.46-1.47-18.66-2.4-21.61-2.79.42-3.15,1.37-10.11,2.85-20.87,1.48-10.76,3.84-28.41,7.08-52.96,1.07-8.16,2.33-17.99,3.78-29.48,1.44-11.49,2.92-22.97,4.43-34.42,4.32.57,11.64,1.55,21.95,2.94,10.31,1.39,20.51,2.75,30.59,4.08,10.15,1.34,23.01,3.01,38.58,5.03,15.57,2.02,24.66,3.19,27.26,3.54l-5.28,40.11c-1.78-.24-6.51-.87-14.19-1.92-7.68-1.04-12.89-1.75-15.63-2.11-3.91-.51-9.71-1.26-17.39-2.24-7.69-.98-13.62-1.74-17.8-2.29-.23,1.72-.54,4.1-.94,7.15-.4,3.05-.71,5.37-.91,6.94,4.25.56,9.99,1.33,17.22,2.32,7.23.99,12.76,1.73,16.61,2.24,4.66.61,9.67,1.26,15.02,1.93,5.35.67,10.09,1.28,14.2,1.82l-3.78,28.7c-2.47-.32-7.34-.98-14.6-1.97-7.26-.99-12.23-1.66-14.91-2.01-3.84-.51-9.31-1.21-16.41-2.11-7.1-.9-12.81-1.63-17.13-2.2-.21,1.58-.53,4-.95,7.25s-.76,5.74-.98,7.46c4.25.56,10.54,1.41,18.87,2.54,8.33,1.13,14.48,1.96,18.46,2.48,4.66.61,9.82,1.28,15.49,1.99,5.66.71,10.14,1.28,13.43,1.72l-5.28,40.12Z" style="fill:{current_hexes[1]};"/>
            <path d="M846.9,450.11c-1.38,10.49-5.05,18.99-11,25.5-5.95,6.51-13.73,11.57-23.35,15.19-6.82,2.52-15.02,4-24.6,4.45-9.58.45-17.91.24-24.98-.62l-4.1,31.9-56.47-7.43c1.19-9.05,2.5-18.75,3.94-29.1,1.43-10.34,3.43-25.25,5.99-44.73,1.07-8.16,2.33-17.99,3.78-29.48,1.44-11.49,2.92-22.97,4.43-34.42,3.77.5,8.46,1.06,14.06,1.69,5.6.63,11.25,1.32,16.94,2.07,18.45,2.43,32.09,4.73,40.95,6.91,8.85,2.18,17,5.19,24.45,9.03,10.79,5.47,18.83,12.39,24.11,20.75,5.28,8.37,7.23,17.8,5.85,28.29ZM788.65,447.46c.38-2.88.14-5.68-.72-8.41-.86-2.73-2.39-5.04-4.58-6.93-1.95-1.65-3.96-2.79-6.04-3.41-2.08-.62-4.18-1.07-6.31-1.35-.21-.03-.93-.12-2.16-.28-.16,1.23-.49,3.74-.99,7.51-.5,3.77-.93,7.06-1.3,9.87-.42,3.22-1.29,9.77-2.59,19.65.21.03.58.08,1.13.15.55.07.93.12,1.13.15,1.65.22,3.74.2,6.29-.06,2.54-.26,4.53-.75,5.95-1.47,2.91-1.43,5.18-3.19,6.82-5.28,1.63-2.09,2.76-5.46,3.37-10.13Z" style="fill:{current_hexes[1]};"/>
            <path d="M916.05,547.22l-54.62-7.19,5.46-41.45,54.62,7.19-5.46,41.45ZM937.79,409.96c-2.92,19.01-6.4,35.75-10.43,50.22-4.03,14.47-7.63,26.03-10.79,34.68l-41.86-5.51c-.79-9.87-1.26-22-1.38-36.39-.13-14.39.79-31.43,2.75-51.12l61.72,8.12Z" style="fill:{current_hexes[1]};"/>
            <path d="M140.28,573.32c0,7.33-.02,15.91-.07,25.72-.04,9.82-.07,17.56-.07,23.24,0,5.24.02,11.48.07,18.72.04,7.24.07,16.32.07,27.23,0,14.92-2.51,27.62-7.52,38.09-5.02,10.47-12.1,18.98-21.26,25.52-9.07,6.46-19.82,11.41-32.24,14.86-12.43,3.44-26.01,5.78-40.75,7l-14.78-55.83c4.27-.44,9.03-1.24,14.26-2.42,5.23-1.18,9.98-3.04,14.26-5.57,4.97-3.14,8.94-7.27,11.9-12.38,2.96-5.11,4.45-12.07,4.45-20.89,0-3.93.02-8.88.07-14.87.04-5.98.07-13.29.07-21.94,0-7.86-.04-15.69-.13-23.51-.09-7.81-.13-15.48-.13-22.99h71.81Z" style="fill:{current_hexes[2]};"/>
            <path d="M353.49,573.32c0,15.79-.04,27.38-.13,34.75-.09,7.37-.13,14.81-.13,22.32,0,9.95.02,18.63.07,26.05.04,7.42.07,13.7.07,18.85,0,14.4-2.68,26.57-8.05,36.52-5.37,9.95-12.2,17.76-20.49,23.43-10.21,6.98-20.25,11.8-30.11,14.47-9.86,2.66-21.42,3.99-34.69,3.99-16.49,0-29.74-1.79-39.73-5.37-9.99-3.58-18.87-8.25-26.64-14.01-8.73-6.46-15.45-14.55-20.16-24.28-4.71-9.73-7.07-21.75-7.07-36.06,0-5.15.02-11.43.07-18.85.04-7.42.07-16.1.07-26.05s-.02-17.21-.07-23.1c-.04-5.89-.07-16.78-.07-32.66h71.81c0,14.32-.02,25.95-.07,34.9-.04,8.95-.07,15.91-.07,20.89,0,7.33.02,14.27.07,20.82.04,6.55.07,13.36.07,20.43,0,8.56,2,15.01,6,19.38,4,4.37,9.26,6.55,15.78,6.55s11.87-2.23,15.78-6.68c3.91-4.45,5.87-10.87,5.87-19.25,0-7.07.02-14.32.07-21.74.04-7.42.07-13.92.07-19.51s-.02-12.2-.07-20.62c-.04-8.42-.07-20.14-.07-35.16h71.81Z" style="fill:{current_hexes[2]};"/>
            <path d="M620.34,738.92l-68.67,12.95-15.44-80.05h-1.31c-1.05,3.23-3.14,9.99-6.28,20.27-3.14,10.29-6.93,23.24-11.38,38.85h-51.8c-5.06-18.05-9.03-31.44-11.9-40.16-2.88-8.72-4.97-15.04-6.28-18.97h-1.31c-1.4,6.72-3.51,17.77-6.34,33.16-2.83,15.39-5.65,31.02-8.44,46.89l-67.1-12.95c9.77-45.08,17.29-81.49,22.56-109.22,5.27-27.73,8.7-45.39,10.27-52.98l69.85-6.15c1.57,5.23,4.6,15.52,9.09,30.87,4.49,15.35,9.61,32.53,15.37,51.54h1.31c5.23-15.52,10.83-32.39,16.81-50.62,5.97-18.22,9.48-28.82,10.53-31.79l73.12,6.15c.78,4.45,3.36,20.49,7.72,48.14,4.36,27.65,10.9,65.67,19.62,114.06Z" style="fill:{current_hexes[2]};"/>
            <path d="M803.86,638.46c0,13.34-3.18,24.57-9.55,33.68-6.37,9.11-15.26,16.72-26.68,22.83-8.11,4.27-18.12,7.48-30.02,9.61-11.9,2.14-22.35,3.25-31.33,3.34l.13,40.55h-71.81c0-11.51.04-23.85.13-37.02.09-13.17.13-32.13.13-56.9,0-10.38-.04-22.87-.13-37.48-.09-14.61-.13-29.19-.13-43.75,4.79,0,10.75-.07,17.86-.2,7.11-.13,14.28-.2,21.52-.2,23.46,0,40.9.63,52.32,1.9,11.42,1.27,22.11,3.69,32.05,7.26,14.39,5.06,25.57,12.38,33.55,21.97,7.98,9.59,11.97,21.06,11.97,34.4ZM730.61,644.74c0-3.66-.76-7.13-2.29-10.4-1.53-3.27-3.82-5.91-6.87-7.91-2.7-1.74-5.41-2.83-8.11-3.27-2.7-.44-5.41-.65-8.11-.65h-2.75v47.09h2.88c2.09,0,4.71-.37,7.85-1.11,3.14-.74,5.54-1.68,7.19-2.81,3.4-2.27,5.95-4.84,7.65-7.72,1.7-2.88,2.55-7.28,2.55-13.21Z" style="fill:{current_hexes[2]};"/>
            <path d="M910.86,573.32c-.52,24.24-2.12,45.74-4.77,64.49-2.66,18.75-5.25,33.79-7.78,45.13h-53.24c-2.62-12.21-5.19-27.29-7.72-45.26-2.53-17.96-4.19-39.42-4.97-64.36h78.48ZM906.28,748.47h-69.46v-52.71h69.46v52.71Z" style="fill:{current_hexes[2]};"/>
        </g>
    </svg>"""


# --- 色相調和スコア ---
def advanced_hue_harmony_score(hues):
    unique_hues = sorted(list(set(hues)))
    n_hues = len(unique_hues)

    if n_hues == 1: return 0.95 

    if n_hues == 2:
        h1, h2 = unique_hues
        diff = min(abs(h1 - h2), 24 - abs(h1 - h2))
        if diff == 12: return 1.0 
        elif diff <= 4: return 0.95 
        elif diff >= 8 and diff <= 10: return 0.85 
        else: return 0.2

    if n_hues == 3:
        d1 = min(abs(unique_hues[1] - unique_hues[0]), 24 - abs(unique_hues[1] - unique_hues[0]))
        d2 = min(abs(unique_hues[2] - unique_hues[1]), 24 - abs(unique_hues[2] - unique_hues[1]))
        d3 = 24 - d1 - d2
        a, b, c = sorted([d1, d2, d3])
        
        if abs(a-8) <= 1 and abs(b-8) <= 1 and abs(c-8) <= 1: return 1.0
        if c >= 11 and c <= 13 and (a+b) == 24-c and a <= 7 and b <= 7: return 0.90
        if a <= 4 and b <= 4: return 0.8
        return 0.3 
        
    return 0.0


# --- Sat-Bri 空間 内角ベーススコア ---
def sb_angle_score(sb_list):
    pts = np.array(sb_list)
    if np.allclose(pts[0], pts[1]) and np.allclose(pts[1], pts[2]): return 1.0
    if (np.allclose(pts[0], pts[1]) or np.allclose(pts[1], pts[2]) or np.allclose(pts[0], pts[2])): return 0.8

    def calculate_angle(p1, p_center, p2):
        vec1 = p1 - p_center
        vec2 = p2 - p_center
        magnitudes_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        if magnitudes_product < 1e-9: return 0.0
        cosval = np.dot(vec1, vec2) / magnitudes_product
        return np.degrees(np.arccos(np.clip(cosval, -1, 1)))

    angles = [calculate_angle(pts[1], pts[0], pts[2]), calculate_angle(pts[0], pts[1], pts[2]), calculate_angle(pts[0], pts[2], pts[1])]
    max_ang = max(angles)

    if max_ang >= 162: return 1.0
    diffs = [abs(angles[i] - angles[j]) for i in range(3) for j in range(i+1,3)]
    
    if any(diff < 5 for diff in diffs): return 0.75
    if all(ang < 90 for ang in angles): return 0.6
    
    score = (max_ang - 90) / 90
    return min(max(score, 0.0), 1.0)


# --- PCCS色データ前処理 ---
def preprocess_colors(color_list):
    color_by_id = {c['ID']: c for c in color_list}
    tone_hue_map = {}
    tone_sb_coords_raw = {}
    for c in color_list:
        key = (c['Tone'], c['Hue'])
        tone_hue_map.setdefault(key, []).append(c)
        tone_sb_coords_raw.setdefault(c['Tone'], []).append((c['Sat'], c['Bri']))
    tone_sb_coords = {tone: (np.mean([s for s, b in lst]), np.mean([b for s, b in lst])) for tone, lst in tone_sb_coords_raw.items()}
    return color_by_id, tone_hue_map, tone_sb_coords


def get_individual_fingerprint(individual):
    ids = sorted([individual['base_color_data']['ID'], individual['gene1_color_data']['ID'], individual['gene2_color_data']['ID']])
    return tuple(ids)


# --- 印象一致スコア ---
def revised_impression_match_score(individual, single_target_data, base_color_data, tone_sb_coords, human_tone_weight, human_hue_weight):
    t1_coord = tone_sb_coords.get(single_target_data['target_tone_1'], (0, 0))
    t2_coord = tone_sb_coords.get(single_target_data['target_tone_2'], (0, 0))
    g1_coord = tone_sb_coords.get(individual['gene1_color_data']['Tone'], (0, 0))
    g2_coord = tone_sb_coords.get(individual['gene2_color_data']['Tone'], (0, 0))

    dist_case1 = (np.linalg.norm(np.array(g1_coord) - np.array(t1_coord)) + np.linalg.norm(np.array(g2_coord) - np.array(t2_coord))) / 2
    dist_case2 = (np.linalg.norm(np.array(g1_coord) - np.array(t2_coord)) + np.linalg.norm(np.array(g2_coord) - np.array(t1_coord))) / 2

    tone_match_score = max(0, 1.0 - (min(dist_case1, dist_case2) / 1.7))

    def calculate_flexible_hue_diff(gene_hue, target_hue):
        diff1 = min(abs(gene_hue - target_hue), 24 - abs(gene_hue - target_hue))
        comp_hue = (target_hue + 12) % 24
        diff2 = min(abs(gene_hue - comp_hue), 24 - abs(gene_hue - comp_hue))
        return min(diff1, diff2)

    g_hues = [individual['gene1_color_data']['Hue'], individual['gene2_color_data']['Hue']]
    t_hues = [single_target_data['target_hue_1'], single_target_data['target_hue_2']]
    
    diff_case1 = (calculate_flexible_hue_diff(g_hues[0], t_hues[0]) + calculate_flexible_hue_diff(g_hues[1], t_hues[1])) / 2
    diff_case2 = (calculate_flexible_hue_diff(g_hues[0], t_hues[1]) + calculate_flexible_hue_diff(g_hues[1], t_hues[0])) / 2
    
    hue_match_score = max(0, 1.0 - (min(diff_case1, diff_case2) / 6))

    weighted_impression_score = (tone_match_score * human_tone_weight + hue_match_score * human_hue_weight) / (human_tone_weight + human_hue_weight + 1e-6)
    return weighted_impression_score, tone_match_score, hue_match_score


# --- 最終フィットネススコア ---
def calculate_full_fitness(individual, target_data_list, base_color_data, tone_sb_coords, human_weights):
    hues = [base_color_data['Hue'], individual['gene1_color_data']['Hue'], individual['gene2_color_data']['Hue']]
    harmony_score = (advanced_hue_harmony_score(hues) + sb_angle_score([(base_color_data['Sat'], base_color_data['Bri']), (individual['gene1_color_data']['Sat'], individual['gene1_color_data']['Bri']), (individual['gene2_color_data']['Sat'], individual['gene2_color_data']['Bri'])])) / 2
    
    impression_scores_possible = [revised_impression_match_score(individual, tgt, base_color_data, tone_sb_coords, human_weights["W_T"], human_weights["W_HUE"])[0] for tgt in target_data_list]

    final_score = (human_weights["W_H"] * harmony_score + human_weights["W_I"] * max(impression_scores_possible))
    return final_score * 10


# --- GAコア関数 ---
def generate_initial_population(base_color_data, color_by_id, tone_hue_map, tone_sb_coords, all_colors_list, n=10, target_data_list=None, human_weights=None):
    population = []
    existing_fingerprints = set()
    all_pccs_ids = [c['ID'] for c in all_colors_list if c['Tone'] not in ('W', 'Bk', 'Gy')]

    def is_sb_related(t1, t2):
        if t1 == t2: return True 
        return np.linalg.norm(np.array(tone_sb_coords.get(t1, (0,0))) - np.array(tone_sb_coords.get(t2, (0,0)))) <= 1.42

    attempts = 0
    while len(population) < n and attempts < n * 1000:
        attempts += 1
        try: g1_id, g2_id = random.sample(list(set(all_pccs_ids) - {base_color_data['ID']}), 2)
        except ValueError: continue

        g1, g2 = color_by_id.get(g1_id), color_by_id.get(g2_id)
        if not g1 or not g2 or len({base_color_data['ID'], g1['ID'], g2['ID']}) < 3: continue

        hues = [base_color_data['Hue'], g1['Hue'], g2['Hue']]
        h_score = advanced_hue_harmony_score(hues)
        sb_score = sb_angle_score([(base_color_data['Sat'], base_color_data['Bri']), (g1['Sat'], g1['Bri']), (g2['Sat'], g2['Bri'])])

        tones = [base_color_data['Tone'], g1['Tone'], g2['Tone']]
        if len(set(tones)) == 2 and not is_sb_related(list(set(tones))[0], list(set(tones))[1]): continue

        ind = {'base_color_data': base_color_data, 'gene1_color_data': g1, 'gene2_color_data': g2, 'hues': hues, 'score': (h_score, sb_score), 'user_score': 5}
        
        if target_data_list and human_weights:
            ind['final_score'] = calculate_full_fitness(ind, target_data_list, base_color_data, tone_sb_coords, human_weights)
            if ind['final_score'] < 3.0: continue
            
        fp = get_individual_fingerprint(ind)
        if fp not in existing_fingerprints:
            population.append(ind)
            existing_fingerprints.add(fp)
            
    if target_data_list: population.sort(key=lambda x: -x['final_score'])
    return population[:n]


def generate_next_generation(population, color_by_id, tone_hue_map, tone_sb_coords, all_colors_list, target_data_list, human_weights):
    base_color_data = population[0]['base_color_data']
    next_gen = []
    existing_fingerprints = set()
    
    for p in population:
        p['final_score'] = p.get('user_score', 5) if p.get('user_score', 5) != 5 else calculate_full_fitness(p, target_data_list, base_color_data, tone_sb_coords, human_weights)
    
    for elite in sorted([p for p in population if p['final_score'] >= 9.0], key=lambda x: -x['final_score']):
        fp = get_individual_fingerprint(elite)
        if fp not in existing_fingerprints:
            next_gen.append(json.loads(json.dumps(elite)))
            existing_fingerprints.add(fp)

    parent_pool = [p for p in population if p['final_score'] >= 6.0] or sorted(population, key=lambda x: -x['final_score'])[:max(2, len(population))]

    attempts = 0
    while len(next_gen) < len(population) and attempts < len(population) * 500:
        attempts += 1
        p1, p2 = random.sample(parent_pool, 2)
        new_g1, new_g2 = dict(p1['gene1_color_data']), dict(p2['gene2_color_data'])

        if random.random() < 0.20:
            mut_tgt = random.choice(target_data_list)
            gene_ref = random.choice([new_g1, new_g2])
            mut_cand = dict(gene_ref)
            
            tgt_tone = mut_tgt['target_tone_1'] if gene_ref is new_g1 else mut_tgt['target_tone_2']
            tgt_hue = mut_tgt['target_hue_1'] if gene_ref is new_g1 else mut_tgt['target_hue_2']

            valid_colors = [c for c in all_colors_list if c['Tone'] == mut_cand['Tone'] and c['Tone'] not in ('W','Bk','Gy')]
            if valid_colors: mut_cand = random.choice(valid_colors)

            if gene_ref is new_g1: new_g1 = mut_cand
            else: new_g2 = mut_cand

        if len({base_color_data['ID'], new_g1['ID'], new_g2['ID']}) < 3: continue
        
        ind = {'base_color_data': base_color_data, 'gene1_color_data': new_g1, 'gene2_color_data': new_g2, 'score': (0,0), 'user_score': 5}
        ind['final_score'] = calculate_full_fitness(ind, target_data_list, base_color_data, tone_sb_coords, human_weights)
        
        fp = get_individual_fingerprint(ind)
        if fp not in existing_fingerprints:
            next_gen.append(ind)
            existing_fingerprints.add(fp)
    
    sorted_pop = sorted(population, key=lambda x: -x['final_score'])
    for p in sorted_pop:
        if len(next_gen) >= len(population): break
        c_p = json.loads(json.dumps(p))
        c_p['user_score'] = 5
        fp = get_individual_fingerprint(c_p)
        if fp not in existing_fingerprints:
            next_gen.append(c_p)
            existing_fingerprints.add(fp)

    return next_gen[:len(population)]


# --- 配色表示 (配置入れ替え対応) ---
def display_population_with_input(population):
    st.markdown('<div class="generation-palette-container">', unsafe_allow_html=True)
    sorted_population = sorted(population, key=lambda p: -p['final_score'])

    st.session_state.population = sorted_population

    for i, p in enumerate(st.session_state.population):
        if i % 2 == 0: cols = st.columns(2)
        with cols[i % 2]:
            b, g1, g2 = p['base_color_data'], p['gene1_color_data'], p['gene2_color_data']
            items = sorted([(c['Hue'], c['ID'], hsv_to_rgb_hex(c['h'], c['s'], c['v'])) for c in (b, g1, g2)], key=lambda x: x[0])
            
            original_hexes = [item[2] for item in items]
            original_ids = [item[1] for item in items]
            
            # --- 3色の配置パターン(全6通り)の定義 ---
            patterns = [
                (0, 1, 2), (0, 2, 1), 
                (1, 0, 2), (1, 2, 0), 
                (2, 0, 1), (2, 1, 0)
            ]
            
            pattern_labels = [
                f"パターン{idx+1}: {original_ids[p1]}, {original_ids[p2]}, {original_ids[p3]}" 
                for idx, (p1, p2, p3) in enumerate(patterns)
            ]
            
            order_key = f"order_{st.session_state.gen}_{i}"
            selected_label = st.selectbox("配色の順番を変更", pattern_labels, key=order_key)
            selected_idx = pattern_labels.index(selected_label)
            selected_pattern = patterns[selected_idx]
            
            current_hexes = [
                original_hexes[selected_pattern[0]], 
                original_hexes[selected_pattern[1]], 
                original_hexes[selected_pattern[2]]
            ]
            
            # --- 終了ボタンをタイトルの横に配置 ---
            header_col1, header_col2 = st.columns([0.6, 0.4])
            with header_col1:
                st.markdown(f"##### No.{i+1} (スコア: {p.get('final_score', 5.0):.1f})")
            with header_col2:
                if st.button(f"✨ 制作を終了", key=f"finish_{st.session_state.gen}_{i}", use_container_width=True):
                    if not st.session_state.participant_name:
                        st.warning("上にスクロールして、実験参加者名を入力してから終了してください！")
                    else:
                        # 終了直前に現在の画面上のスコアを確実に取得
                        for j, pop_item in enumerate(st.session_state.population):
                            state_key = f"score_gen{st.session_state.gen}_idx{j}"
                            if state_key in st.session_state:
                                pop_item['user_score'] = st.session_state[state_key]

                        if st.session_state.history:
                            st.session_state.history[-1]["population"] = json.loads(json.dumps(st.session_state.population))

                        # 現在アクティブな並び替えパターン（HEXとID）をレポート用に保存
                        st.session_state.final_hexes_ordered = current_hexes
                        st.session_state.final_ids_ordered = [original_ids[selected_pattern[0]], original_ids[selected_pattern[1]], original_ids[selected_pattern[2]]]

                        st.session_state.final_selection = p
                        st.session_state.is_finished = True
                        st.rerun()
            
            dynamic_svg = generate_logo_svg(current_hexes)

            st.markdown(f"""
            <div class="palette-item" style="border: 1px solid #eee; padding: 10px;">
                <div style="display: flex; gap: 15px;">
                    <div style="flex-direction: column; gap: 4px;">
                        <div class="color-swatch" style="background:{current_hexes[0]};"></div>
                        <div class="color-swatch" style="background:{current_hexes[1]};"></div>
                        <div class="color-swatch" style="background:{current_hexes[2]};"></div>
                    </div>
                    <div>{dynamic_svg}</div>
                </div>
                <p style="font-size: 0.7em;">Original IDs: {', '.join(original_ids)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # --- 世代ごとに一意のKeyを発行して確実に保存 ---
            state_key = f"score_gen{st.session_state.gen}_idx{i}"
            
            # 1. セッションステートにまだ値がない場合のみ初期値をセット
            if state_key not in st.session_state:
                st.session_state[state_key] = p.get('user_score', 5)

            # 2. 値の保持は key に完全にお任せする
            st.number_input(
                f"評価 (0〜10)", 0, 10, 
                key=state_key
            )
            
            # 3. 入力された最新の値を population に反映
            p['user_score'] = st.session_state[state_key]
    st.markdown('</div>', unsafe_allow_html=True)


# ================================================
# --- メインロジック ---
# ================================================

try:
    with open("color_GA.json", encoding="utf-8") as f:
        colors = json.load(f)
except FileNotFoundError:
    st.error("エラー: `color_GA.json` が見つかりません。")
    st.stop()

color_by_id, tone_hue_map, tone_sb_coords = preprocess_colors(colors)

# --- セッションステートの初期化 ---
if 'selected_gene' not in st.session_state: st.session_state.selected_gene = None
if 'participant_name' not in st.session_state: st.session_state.participant_name = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'is_finished' not in st.session_state: st.session_state.is_finished = False
if 'final_selection' not in st.session_state: st.session_state.final_selection = None
if 'mail_sent' not in st.session_state: st.session_state.mail_sent = False
if 'target_data_list' not in st.session_state: st.session_state.target_data_list = None
if 'gen' not in st.session_state: st.session_state.gen = 0
if 'population' not in st.session_state: st.session_state.population = []
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'final_hexes_ordered' not in st.session_state: st.session_state.final_hexes_ordered = []
if 'final_ids_ordered' not in st.session_state: st.session_state.final_ids_ordered = []

# ================================================
# --- 画面表示の切り替え（通常モード vs 終了モード） ---
# ================================================
if st.session_state.is_finished:
    # --- 終了後のレポート・メール送信画面 ---
    st.success("🎉 ロゴ制作が完了しました！ご参加ありがとうございました。")
    
    script_name = os.path.basename(sys.argv[0])
    
    # 決定された順序通りのロゴSVGを取得
    final_logo_svg = generate_logo_svg(st.session_state.final_hexes_ordered)
    
    # メーラーでSVGを表示させるため、Base64エンコードしてimgタグに変換 (※Streamlit画面上ではこれで表示されます)
    b64_svg = base64.b64encode(final_logo_svg.encode('utf-8')).decode('utf-8')
    img_tag_svg = f'<img src="data:image/svg+xml;base64,{b64_svg}" alt="Logo" style="width:100%; max-width:200px; height:auto; margin:10px 0;">'

    # ▼▼▼ 追加：SVGの生コードをテキストとして出力するためのエスケープ処理 ▼▼▼
    raw_svg_code = html.escape(final_logo_svg.strip())

    # --- HTMLレポートのスタイルをダークテーマに変更 ---
    report_html = f"""
    <html>
    <body style="font-family: sans-serif; background-color: #1e1e1e; color: #ffffff; padding: 20px;">
        <h2 style="color: #ffffff;">📊 配色GA実験レポート</h2>
        <ul>
            <li><strong>参加者:</strong> {st.session_state.participant_name}</li>
            <li><strong>入力プロンプト:</strong> {st.session_state.input_text}</li>
            <li><strong>実行ファイル名:</strong> {script_name}</li>
        </ul>
        
        <h3 style="color: #ffffff;">🎨 最終決定した配色と完成ロゴ</h3>
        <div style="display: flex; gap: 25px; align-items: flex-start; background-color: #2b2b2b; padding: 20px; border-radius: 8px; border: 1px solid #444; max-width: 600px; flex-wrap: wrap;">
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:50px; height:45px; background-color:{st.session_state.final_hexes_ordered[0]}; border:1px solid #555; border-radius: 3px;"></div>
                    <span>{st.session_state.final_ids_ordered[0]} ({st.session_state.final_hexes_ordered[0]})</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:50px; height:45px; background-color:{st.session_state.final_hexes_ordered[1]}; border:1px solid #555; border-radius: 3px;"></div>
                    <span>{st.session_state.final_ids_ordered[1]} ({st.session_state.final_hexes_ordered[1]})</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:50px; height:45px; background-color:{st.session_state.final_hexes_ordered[2]}; border:1px solid #555; border-radius: 3px;"></div>
                    <span>{st.session_state.final_ids_ordered[2]} ({st.session_state.final_hexes_ordered[2]})</span>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 200px;">
                {img_tag_svg}
            </div>
        </div>

        <h3 style="color: #ffffff;">📝 完成ロゴのSVGコード（コピペ用）</h3>
        <div style="background-color: #2b2b2b; padding: 10px; border-radius: 5px; border: 1px solid #444;">
            <p style="font-size: 12px; color: #bbb; margin-top: 0;">※ 以下のコードをコピーして <code>.svg</code> 拡張子で保存するか、HTMLに貼り付けてください。</p>
            <pre style="color: #a6e22e; white-space: pre-wrap; font-size: 11px; overflow-x: auto; margin: 0;">{raw_svg_code}</pre>
        </div>

        <h3 style="color: #ffffff;">🤖 LLMの解釈（ターゲットデータ）</h3>
        <pre style="background-color: #2b2b2b; color: #ffffff; padding: 10px; border-radius: 5px; border: 1px solid #444; white-space: pre-wrap;">{json.dumps(st.session_state.target_data_list, indent=2, ensure_ascii=False)}</pre>
        
        <h3 style="color: #ffffff;">📈 世代ごとの履歴</h3>
    """
    
    
    for gen_data in st.session_state.history:
        report_html += f"<h4 style='color: #ffffff;'>世代 {gen_data['gen']}</h4><div style='display:flex; flex-wrap:wrap; gap:10px;'>"
        for idx, ind in enumerate(gen_data['population']):
            b, g1, g2 = ind['base_color_data'], ind['gene1_color_data'], ind['gene2_color_data']
            
            # --- ここが原因でした: 画面表示時と同じようにHue(色相)でソートする ---
            items = sorted([(c['Hue'], c['ID'], hsv_to_rgb_hex(c['h'], c['s'], c['v'])) for c in (b, g1, g2)], key=lambda x: x[0])
            
            h1, h2, h3 = items[0][2], items[1][2], items[2][2]
            id1, id2, id3 = items[0][1], items[1][1], items[2][1]
            
            user_score_display = ind.get('user_score', '-')
            
            report_html += f"""
            <div style='border:1px solid #555; background-color: #2b2b2b; padding:10px; font-size:12px; margin-bottom: 5px; color: #ffffff; border-radius: 5px;'>
                <div style='margin-bottom: 5px;'><strong>No.{idx+1}</strong> (Sys:{ind.get('final_score',0):.1f} | User:{user_score_display})</div>
                <div style='display:flex; align-items:center; gap:5px; margin-bottom:3px;'>
                    <div style='width:20px; height:20px; background-color:{h1}; border:1px solid #444;'></div> <span>{id1} ({h1})</span>
                </div>
                <div style='display:flex; align-items:center; gap:5px; margin-bottom:3px;'>
                    <div style='width:20px; height:20px; background-color:{h2}; border:1px solid #444;'></div> <span>{id2} ({h2})</span>
                </div>
                <div style='display:flex; align-items:center; gap:5px;'>
                    <div style='width:20px; height:20px; background-color:{h3}; border:1px solid #444;'></div> <span>{id3} ({h3})</span>
                </div>
            </div>
            """
        report_html += "</div><hr style='border-color: #555;'>"
    report_html += "</body></html>"

    # レポートを画面に表示
    st.components.v1.html(report_html, height=800, scrolling=True)

    if not st.session_state.mail_sent:
        try:
            from_email = st.secrets["GMAIL_ADDRESS"]
            to_email = st.secrets["GMAIL_ADDRESS"] 
            password = st.secrets["GMAIL_APP_PASSWORD"]

            msg = MIMEMultipart()
            msg['Subject'] = f"【実験データ】配色GA - {st.session_state.participant_name}様"
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Date'] = formatdate(localtime=True)
            msg.attach(MIMEText(report_html, 'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(from_email, password)
                server.send_message(msg)
            
            st.session_state.mail_sent = True
            
        except Exception as e:
            st.error(f"データの自動送信に失敗しました（設定を確認してください）: {e}")
            st.info("※ 実験データは画面上に表示されていますので、スクリーンショット等で保存してください。")

    st.markdown("### ご協力ありがとうございました！")
    if st.button("🔄 新しい実験を始める"):
        st.session_state.clear()
        st.rerun()

else:
    # --- 通常の操作画面 ---
    st.session_state.participant_name = st.text_input("👤 実験参加者名（必須）", st.session_state.participant_name)
    
    st.header("1. ベース色を選択 👆")

    def on_base_change(checkbox_key, color_data):
        if st.session_state.get(checkbox_key):
            st.session_state.selected_gene = color_data
            for k in st.session_state.keys():
                if k.startswith("chk_base_") and k != checkbox_key:
                    st.session_state[k] = False
        else:
            if st.session_state.selected_gene and st.session_state.selected_gene['ID'] == color_data['ID']:
                st.session_state.selected_gene = None

    num_cols = 12
    for i in range(0, len(colors), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(colors):
                c = colors[i + j]
                hex_col = hsv_to_rgb_hex(c['h'], c['s'], c['v'])
                is_selected = (st.session_state.selected_gene is not None and c['ID'] == st.session_state.selected_gene['ID'])
                chk_key = f"chk_base_{c['ID']}"
                
                with cols[j]:
                    border = "3px solid #3b82f6" if is_selected else "1px solid #ccc"
                    shadow = "0 0 8px rgba(59,130,246,0.6)" if is_selected else "none"
                    st.markdown(f'''
                        <div style="background-color:{hex_col}; width:30px; height:30px; border-radius:50%; border:{border}; box-shadow:{shadow}; margin-bottom: 5px;"></div>
                    ''', unsafe_allow_html=True)
                    st.checkbox(c['ID'], key=chk_key, value=is_selected, on_change=on_base_change, args=(chk_key, c))

    if st.session_state.selected_gene:
        c = st.session_state.selected_gene
        hex_col = hsv_to_rgb_hex(c['h'], c['s'], c['v'])
        st.markdown(
            f'''
            <div style="display: flex; align-items: center; gap: 15px; margin-top: 20px; padding: 10px; background-color: #f0f2f6; border-radius: 8px;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background-color: {hex_col}; border: 2px solid #aaa;"></div>
                <span style="font-size: 1.2em; font-weight: bold; color: #333;">現在選択中の色: {c['ID']}</span>
            </div>
            ''', unsafe_allow_html=True
        )
    else:
        st.warning("上のリストからベース色を選んでチェックを入れてください。")


    st.header("2. 印象語・文章を入力 ✍️")
    st.session_state.input_text = st.text_area("残りの2色に反映したいイメージを入力（例: 暖かく、活動的な印象）", value=st.session_state.input_text, height=100)

    with st.expander("📝 実験用: 意図するトーン印象の記録（任意）", expanded=True):
        cols = st.columns(3)
        pccs_tones = ["v", "b", "s", "dp", "lt", "sf", "d", "dk", "p", "ltg", "g", "dkg"]
        st.session_state.experiment_user_intent = [t for i, t in enumerate(pccs_tones) if cols[i % 3].checkbox(t, key=f"chk_{t}")]

    st.sidebar.header("⚖️ 評価ウェイト調整")
    W_H_I = st.sidebar.slider("総合バランス (調和 ⟷ 印象)", 0.0, 1.0, 0.5, 0.05)
    W_T_HUE = st.sidebar.slider("印象バランス (トーン ⟷ 色相)", 0.0, 1.0, 0.5, 0.05)
    human_weights = {"W_H": W_H_I, "W_I": 1.0 - W_H_I, "W_T": W_T_HUE, "W_HUE": 1.0 - W_T_HUE}


    if st.session_state.target_data_list and st.session_state.gen > 0:
        st.subheader("AI分析結果（5つの解釈）")
        st.json(st.session_state.target_data_list)

    btn_text = "▶️ AI分析＆配色生成" if st.session_state.gen==0 else "🔄 次の世代へ"

    if st.button(label=btn_text):
        if not st.session_state.participant_name:
            st.error("実験参加者名を入力してください。")
            st.stop()
        if not st.session_state.selected_gene:
            st.error("ベース色を選択してください。")
            st.stop()
        if not st.session_state.input_text:
            st.error("印象語を入力してください。")
            st.stop()

        if st.session_state.gen == 0:
            with st.spinner("AI分析中..."):
                target_list = call_dify_api(st.session_state.selected_gene['ID'], st.session_state.input_text)
            if target_list is None: st.stop()
            
            st.session_state.target_data_list = target_list
            st.session_state.population = generate_initial_population(st.session_state.selected_gene, color_by_id, tone_hue_map, tone_sb_coords, colors, 10, target_list, human_weights)
            st.session_state.gen = 1
            
            st.session_state.history.append({
                "gen": 1,
                "population": json.loads(json.dumps(st.session_state.population))
            })
            
        else:
            # 次世代の処理に入る前に、現在のUI上の点数を確実にキャプチャする
            for i, p in enumerate(st.session_state.population):
                state_key = f"score_gen{st.session_state.gen}_idx{i}"
                if state_key in st.session_state:
                    p['user_score'] = st.session_state[state_key]
            
            if st.session_state.history:
                st.session_state.history[-1]["population"] = json.loads(json.dumps(st.session_state.population))

            if st.session_state.target_data_list:
                st.session_state.population = generate_next_generation(st.session_state.population, color_by_id, tone_hue_map, tone_sb_coords, colors, st.session_state.target_data_list, human_weights)
                st.session_state.gen += 1
                
                st.session_state.history.append({
                    "gen": st.session_state.gen,
                    "population": json.loads(json.dumps(st.session_state.population))
                })

        st.rerun()

    st.subheader(f"3. 世代 {st.session_state.gen} の配色候補 🌈")
    if st.session_state.population:
        display_population_with_input(st.session_state.population)
    else:
        st.info("印象語を入力してボタンを押してください。")