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
def generate_logo_svg(current_hexes):
    uid = str(uuid.uuid4())[:8]
    return f"""
    <svg id="_レイヤー_1_{uid}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 875.13 877.13" style="width:100%; max-width:200px; height:auto; margin:10px 0;">
        <defs>
            <clipPath id="clippath_{uid}">
                <rect x="0" y="0" width="284.99" height="493.61" style="fill:none;"/>
            </clipPath>
            <pattern id="_헥사곤_패턴_{uid}" x="0" y="0" width="284.99" height="493.61" patternTransform="translate(1525.5352 1551.4831) scale(1.2738)" patternUnits="userSpaceOnUse" viewBox="0 0 284.99 493.61">
                <rect width="284.99" height="493.61" style="fill:none;"/>
                <g style="clip-path:url(#clippath_{uid});">
                    <rect x="0" y="0" width="284.99" height="493.61" style="fill:{current_hexes[0]};"/>
                    <polygon points="42.03 68.11 107.49 105.9 124.99 95.8 124.99 75.59 59.53 37.8 81.35 0 40.94 0 0 70.9 20.21 105.9 42.03 68.11" style="fill:{current_hexes[1]};"/>
                    <polygon points="59.53 174.01 124.99 136.21 124.99 116.01 107.49 105.9 42.03 143.7 20.21 105.9 0 140.9 40.94 211.81 81.35 211.81 59.53 174.01" style="fill:{current_hexes[1]};"/>
                    <polygon points="225.46 37.8 159.99 75.59 159.99 95.8 177.49 105.9 242.96 68.11 264.78 105.9 284.99 70.9 244.05 0 203.64 0 225.46 37.8" style="fill:{current_hexes[1]};"/>
                    <polygon points="159.99 211.81 159.99 136.21 142.49 126.11 124.99 136.21 124.99 211.81 81.35 211.81 101.56 246.81 183.43 246.81 203.64 211.81 159.99 211.81" style="fill:{current_hexes[1]};"/>
                    <polygon points="124.99 0 124.99 75.59 142.49 85.7 159.99 75.59 159.99 0 203.64 0 183.43 -35 101.56 -35 81.35 0 124.99 0" style="fill:{current_hexes[1]};"/>
                    <polygon points="264.78 105.9 242.96 143.7 177.49 105.9 159.99 116.01 159.99 136.21 225.46 174.01 203.64 211.81 244.05 211.81 284.99 140.9 264.78 105.9" style="fill:{current_hexes[1]};"/>
                    <polygon points="183.43 246.81 223.84 246.81 244.05 211.81 203.64 211.81 183.43 246.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="284.99 140.9 305.19 105.9 284.99 70.9 264.78 105.9 284.99 140.9" style="fill:{current_hexes[2]};"/>
                    <polygon points="244.05 0 223.84 -35 183.43 -35 203.64 0 244.05 0" style="fill:{current_hexes[2]};"/>
                    <polygon points="101.56 -35 61.14 -35 40.94 0 81.35 0 101.56 -35" style="fill:{current_hexes[2]};"/>
                    <polygon points="0 70.9 -20.21 105.9 0 140.9 20.21 105.9 0 70.9" style="fill:{current_hexes[2]};"/>
                    <polygon points="40.94 211.81 61.14 246.81 101.56 246.81 81.35 211.81 40.94 211.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="159.99 75.59 142.49 85.7 124.99 75.59 124.99 95.8 107.49 105.9 124.99 116.01 124.99 136.21 142.49 126.11 159.99 136.21 159.99 116.01 177.49 105.9 159.99 95.8 159.99 75.59" style="fill:{current_hexes[2]};"/>
                    <polygon points="42.03 561.72 107.49 599.52 124.99 589.41 124.99 569.21 59.53 531.41 81.35 493.61 40.94 493.61 0 564.52 20.21 599.52 42.03 561.72" style="fill:{current_hexes[1]};"/>
                    <polygon points="59.53 667.62 124.99 629.83 124.99 609.62 107.49 599.52 42.03 637.31 20.21 599.52 0 634.52 40.94 705.42 81.35 705.42 59.53 667.62" style="fill:{current_hexes[1]};"/>
                    <polygon points="225.46 531.41 159.99 569.2 159.99 589.41 177.49 599.52 242.96 561.72 264.78 599.52 284.99 564.52 244.05 493.61 203.64 493.61 225.46 531.41" style="fill:{current_hexes[1]};"/>
                    <polygon points="159.99 705.42 159.99 629.83 142.49 619.72 124.99 629.83 124.99 705.42 81.35 705.42 101.56 740.42 183.43 740.42 203.64 705.42 159.99 705.42" style="fill:{current_hexes[1]};"/>
                    <polygon points="124.99 493.61 124.99 569.21 142.49 579.31 159.99 569.2 159.99 493.61 203.64 493.61 183.43 458.61 101.56 458.61 81.35 493.61 124.99 493.61" style="fill:{current_hexes[1]};"/>
                    <polygon points="264.78 599.52 242.96 637.31 177.49 599.52 159.99 609.62 159.99 629.83 225.46 667.62 203.64 705.42 244.05 705.42 284.99 634.52 264.78 599.52" style="fill:{current_hexes[1]};"/>
                    <polygon points="183.43 740.42 223.84 740.42 244.05 705.42 203.64 705.42 183.43 740.42" style="fill:{current_hexes[2]};"/>
                    <polygon points="284.99 634.52 305.19 599.52 284.99 564.52 264.78 599.52 284.99 634.52" style="fill:{current_hexes[2]};"/>
                    <polygon points="244.05 493.61 223.84 458.61 183.43 458.61 203.64 493.61 244.05 493.61" style="fill:{current_hexes[2]};"/>
                    <polygon points="101.56 458.61 61.14 458.61 40.94 493.61 81.35 493.61 101.56 458.61" style="fill:{current_hexes[2]};"/>
                    <polygon points="0 564.52 -20.21 599.52 0 634.52 20.21 599.52 0 564.52" style="fill:{current_hexes[2]};"/>
                    <polygon points="40.94 705.42 61.14 740.42 101.56 740.42 81.35 705.42 40.94 705.42" style="fill:{current_hexes[2]};"/>
                    <polygon points="159.99 569.2 142.49 579.31 124.99 569.21 124.99 589.41 107.49 599.52 124.99 609.62 124.99 629.83 142.49 619.72 159.99 629.83 159.99 609.62 177.49 599.52 159.99 589.41 159.99 569.2" style="fill:{current_hexes[2]};"/>
                    <polygon points="-100.46 314.91 -35 352.71 -17.5 342.61 -17.5 322.4 -82.96 284.6 -61.14 246.81 -101.56 246.81 -142.49 317.71 -122.29 352.71 -100.46 314.91" style="fill:{current_hexes[1]};"/>
                    <polygon points="-82.96 420.82 -17.5 383.02 -17.5 362.81 -35 352.71 -100.46 390.51 -122.29 352.71 -142.49 387.71 -101.56 458.61 -61.14 458.61 -82.96 420.82" style="fill:{current_hexes[1]};"/>
                    <polygon points="82.97 284.6 17.5 322.4 17.5 342.61 35 352.71 100.46 314.91 122.29 352.71 142.49 317.71 101.56 246.81 61.14 246.81 82.97 284.6" style="fill:{current_hexes[1]};"/>
                    <polygon points="17.5 458.61 17.5 383.02 0 372.92 -17.5 383.02 -17.5 458.61 -61.14 458.61 -40.94 493.61 40.94 493.61 61.14 458.61 17.5 458.61" style="fill:{current_hexes[1]};"/>
                    <polygon points="-17.5 246.81 -17.5 322.4 0 332.5 17.5 322.4 17.5 246.81 61.14 246.81 40.94 211.81 -40.94 211.81 -61.14 246.81 -17.5 246.81" style="fill:{current_hexes[1]};"/>
                    <polygon points="122.29 352.71 100.46 390.51 35 352.71 17.5 362.81 17.5 383.02 82.96 420.82 61.14 458.61 101.56 458.61 142.49 387.71 122.29 352.71" style="fill:{current_hexes[1]};"/>
                    <polygon points="40.94 493.61 81.35 493.61 101.56 458.61 61.14 458.61 40.94 493.61" style="fill:{current_hexes[2]};"/>
                    <polygon points="142.49 387.71 162.7 352.71 142.49 317.71 122.29 352.71 142.49 387.71" style="fill:{current_hexes[2]};"/>
                    <polygon points="101.56 246.81 81.35 211.81 40.94 211.81 61.14 246.81 101.56 246.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="-40.94 211.81 -81.35 211.81 -101.56 246.81 -61.14 246.81 -40.94 211.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="-142.49 317.71 -162.7 352.71 -142.49 387.71 -122.29 352.71 -142.49 317.71" style="fill:{current_hexes[2]};"/>
                    <polygon points="-101.56 458.61 -81.35 493.61 -40.94 493.61 -61.14 458.61 -101.56 458.61" style="fill:{current_hexes[2]};"/>
                    <polygon points="17.5 322.4 0 332.5 -17.5 322.4 -17.5 342.61 -35 352.71 -17.5 362.81 -17.5 383.02 0 372.92 17.5 383.02 17.5 362.81 35 352.71 17.5 342.61 17.5 322.4" style="fill:{current_hexes[2]};"/>
                    <polygon points="184.52 314.91 249.99 352.71 267.49 342.61 267.49 322.4 202.02 284.6 223.84 246.81 183.43 246.81 142.49 317.71 162.7 352.71 184.52 314.91" style="fill:{current_hexes[1]};"/>
                    <polygon points="202.02 420.82 267.49 383.02 267.49 362.81 249.99 352.71 184.52 390.51 162.7 352.71 142.49 387.71 183.43 458.61 223.84 458.61 202.02 420.82" style="fill:{current_hexes[1]};"/>
                    <polygon points="367.95 284.6 302.49 322.4 302.49 342.61 319.99 352.71 385.45 314.91 407.27 352.71 427.48 317.71 386.54 246.81 346.13 246.81 367.95 284.6" style="fill:{current_hexes[1]};"/>
                    <polygon points="302.49 458.61 302.49 383.02 284.99 372.92 267.49 383.02 267.49 458.61 223.84 458.61 244.05 493.61 325.92 493.61 346.13 458.61 302.49 458.61" style="fill:{current_hexes[1]};"/>
                    <polygon points="267.49 246.81 267.49 322.4 284.99 332.5 302.49 322.4 302.49 246.81 346.13 246.81 325.92 211.81 244.05 211.81 223.84 246.81 267.49 246.81" style="fill:{current_hexes[1]};"/>
                    <polygon points="407.27 352.71 385.45 390.51 319.99 352.71 302.49 362.81 302.49 383.02 367.95 420.82 346.13 458.61 386.54 458.61 427.48 387.71 407.27 352.71" style="fill:{current_hexes[1]};"/>
                    <polygon points="325.92 493.61 366.34 493.61 386.54 458.61 346.13 458.61 325.92 493.61" style="fill:#242424;"/>
                    <polygon points="427.48 387.71 447.69 352.71 427.48 317.71 407.27 352.71 427.48 387.71" style="fill:{current_hexes[2]};"/>
                    <polygon points="386.54 246.81 366.34 211.81 325.92 211.81 346.13 246.81 386.54 246.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="244.05 211.81 203.64 211.81 183.43 246.81 223.84 246.81 244.05 211.81" style="fill:{current_hexes[2]};"/>
                    <polygon points="142.49 317.71 122.29 352.71 142.49 387.71 162.7 352.71 142.49 317.71" style="fill:{current_hexes[2]};"/>
                    <polygon points="183.43 458.61 203.64 493.61 244.05 493.61 223.84 458.61 183.43 458.61" style="fill:{current_hexes[2]};"/>
                    <polygon points="302.49 322.4 284.99 332.5 267.49 322.4 267.49 342.61 249.99 352.71 267.49 362.81 267.49 383.02 284.99 372.92 302.49 383.02 302.49 362.81 319.99 352.71 302.49 342.61 302.49 322.4" style="fill:{current_hexes[2]};"/>
                </g>
            </pattern>
        </defs>
        <rect y="1" width="875.13" height="875.13" style="fill:url(#_헥사곤_패턴_{uid});"/>
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

    # --- 修正ポイント：親プールの安全網を確実に機能させる ---
    parent_pool = [p for p in population if p['final_score'] >= 6.0]
    
    # 6点以上の個体が2個未満（0個または1個）しかない場合のフォールバック
    if len(parent_pool) < 2:
        # スコア順に並べ替えた集団全体を親プールとして代用する
        parent_pool = sorted(population, key=lambda x: -x['final_score'])
        
        # 万が一、初期集団自体が2個未満だった場合のエラー防止
        if len(parent_pool) < 2:
            raise ValueError("エラー: 母集団(population)の数が2未満です。初期生成を見直してください。")
    # ----------------------------------------------------

    attempts = 0
    while len(next_gen) < len(population) and attempts < len(population) * 500:
        attempts += 1
        # ここで確実に2個以上の要素を持つ parent_pool からサンプリングされるようになります
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
