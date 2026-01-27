# -*- coding:utf-8 -*-
# @Software       :PyCharm
# @Project        :v2ray-sync
# @Path           :/
# @FileName       :main.py
# @Time           :2025/10/19 03:36
# @Author         :Viper373
# @GitHub         :https://github.com/Viper373
# @Home           :https://viper3.top
# @Blog           :https://blog.viper3.top
"""
V2RayN 配置自动同步到 GitHub Gist - GitHub Actions 版本
从 WebDAV 下载 ZIP 文件并解压后读取数据库
"""
import sqlite3
import json
import base64
import requests
import os
import tempfile
import zipfile
import io
from urllib.parse import quote
from datetime import datetime

# ==================== 配置区 ====================
# 从环境变量读取配置
# 修正：从 GIST_TOKEN 环境变量读取
GITHUB_TOKEN = os.getenv('GIST_TOKEN', '')
# WebDAV 配置
WEBDAV_URL = os.getenv('WEBDAV_URL', '')
WEBDAV_USERNAME = os.getenv('WEBDAV_USERNAME', '')
WEBDAV_PASSWORD = os.getenv('WEBDAV_PASSWORD', '')


# ==================== WebDAV 下载和解压 ====================
def download_and_extract_webdav():
    """从 WebDAV 下载 ZIP 文件并解压"""
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"📁 创建临时目录: {temp_dir}")
        # 下载 ZIP 文件
        auth = (WEBDAV_USERNAME, WEBDAV_PASSWORD) if WEBDAV_USERNAME else None
        response = requests.get(WEBDAV_URL, auth=auth, timeout=30)
        if response.status_code != 200:
            print(f"❌ 下载失败: HTTP {response.status_code}")
            return None, None
        # 检查文件大小
        file_size = len(response.content)
        if file_size == 0:
            print("❌ 下载的文件为空")
            return None, None
        print(f"✅ 下载成功，文件大小: {file_size} 字节")
        # 解压 ZIP 文件
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(temp_dir)
            print(f"✅ 解压成功到: {temp_dir}")
        # 查找解压后的文件夹和数据库文件
        for root, dirs, files in os.walk(temp_dir):
            # 查找 v2rayN_ 开头的文件夹
            v2rayn_dirs = [d for d in dirs if d.startswith('v2rayN_')]
            for v2rayn_dir in v2rayn_dirs:
                db_path = os.path.join(root, v2rayn_dir, 'guiConfigs', 'guiNDB.db')
                if os.path.exists(db_path):
                    print(f"🔍 找到数据库: {db_path}")
                    return db_path, temp_dir
            # 如果找不到标准结构，尝试直接查找数据库文件
            for file in files:
                if file == 'guiNDB.db':
                    db_path = os.path.join(root, file)
                    print(f"🔍 找到数据库: {db_path}")
                    return db_path, temp_dir
        print("❌ 在 ZIP 文件中未找到数据库文件")
        return None, temp_dir
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None, None
    except zipfile.BadZipFile:
        print("❌ 文件不是有效的 ZIP 格式")
        return None, None
    except Exception as e:
        print(f"❌ 下载解压失败: {e}")
        return None, None


def cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    if temp_dir and os.path.exists(temp_dir):
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️ 清理临时目录失败: {e}")


# ==================== 数据库读取 ====================
def read_v2rayn_database(db_path):
    """读取 V2RayN 数据库"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 读取订阅分组
        cursor.execute("SELECT Id, Remarks FROM SubItem")
        subscriptions = {row[0]: row[1] for row in cursor.fetchall()}
        # 读取所有节点
        cursor.execute("""
                       SELECT ConfigType,
                              Remarks,
                              Address,
                              Port,
                              Id,
                              AlterId,
                              Security,
                              Network,
                              HeaderType,
                              RequestHost,
                              Path,
                              StreamSecurity,
                              AllowInsecure,
                              Subid,
                              Sni,
                              Alpn,
                              Fingerprint,
                              PublicKey,
                              ShortId,
                              SpiderX,
                              Flow
                       FROM ProfileItem
                       ORDER BY Subid, Remarks
                       """)
        nodes_by_group = {}
        stats = {'total': 0, 'success': 0, 'failed': 0}
        for row in cursor.fetchall():
            node = {
                'config_type': row[0],
                'remarks': row[1],
                'address': row[2],
                'port': row[3],
                'id': row[4],
                'alter_id': row[5],
                'security': row[6],
                'network': row[7],
                'header_type': row[8],
                'request_host': row[9],
                'path': row[10],
                'stream_security': row[11],
                'allow_insecure': row[12],
                'subid': row[13],
                'sni': row[14],
                'alpn': row[15],
                'fingerprint': row[16],
                'public_key': row[17],
                'short_id': row[18],
                'spider_x': row[19],
                'flow': row[20]
            }
            stats['total'] += 1
            group_name = subscriptions.get(node['subid'], '默认分组')
            if group_name not in nodes_by_group:
                nodes_by_group[group_name] = []
            nodes_by_group[group_name].append(node)
        conn.close()
        return nodes_by_group, stats
    except Exception as e:
        print(f"❌ 读取数据库失败: {e}")
        return None, None


# ==================== 分享链接生成 ====================
def generate_vmess_link(node):
    """生成 VMess 分享链接 (ConfigType=1)"""
    config = {
        "v": "2",
        "ps": node['remarks'] or "",
        "add": node['address'] or "",
        "port": str(node['port'] or ""),
        "id": node['id'] or "",
        "aid": str(node['alter_id'] or "0"),
        "scy": node['security'] or "auto",
        "net": node['network'] or "tcp",
        "type": node['header_type'] or "none",
        "host": node['request_host'] or "",
        "path": node['path'] or "",
        "tls": node['stream_security'] or "",
        "sni": node['sni'] or "",
        "alpn": node['alpn'] or "",
        "fp": node['fingerprint'] or ""
    }
    json_str = json.dumps(config, ensure_ascii=False)
    b64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    return f"vmess://{b64}"


def generate_vless_link(node):
    """生成 VLESS 分享链接 (ConfigType=3)"""
    params = []
    # encryption (Security 字段)
    if node['security']:
        params.append(f"encryption={node['security']}")
    else:
        params.append("encryption=none")
    # flow
    if node['flow']:
        params.append(f"flow={node['flow']}")
    # security (StreamSecurity)
    if node['stream_security']:
        params.append(f"security={node['stream_security']}")
    # network type
    if node['network']:
        params.append(f"type={node['network']}")
    # headerType
    if node['header_type'] and node['header_type'] != 'none':
        params.append(f"headerType={node['header_type']}")
    # host
    if node['request_host']:
        params.append(f"host={node['request_host']}")
    # path
    if node['path']:
        params.append(f"path={quote(node['path'])}")
    # sni
    if node['sni']:
        params.append(f"sni={node['sni']}")
    # alpn
    if node['alpn']:
        params.append(f"alpn={node['alpn']}")
    # fingerprint
    if node['fingerprint']:
        params.append(f"fp={node['fingerprint']}")
    # Reality 参数
    if node['public_key']:
        params.append(f"pbk={quote(node['public_key'])}")
    if node['short_id']:
        params.append(f"sid={node['short_id']}")
    if node['spider_x']:
        params.append(f"spx={quote(node['spider_x'])}")
    param_str = "&".join(params)
    remarks = quote(node['remarks'] or "")
    return f"vless://{node['id']}@{node['address']}:{node['port']}?{param_str}#{remarks}"


def generate_hysteria2_link(node):
    """生成 Hysteria2 分享链接 (ConfigType=7)"""
    params = []
    if node['sni']:
        params.append(f"sni={node['sni']}")
    if node['alpn']:
        params.append(f"alpn={node['alpn']}")
    if node['fingerprint']:
        params.append(f"pinSHA256={node['fingerprint']}")
    if node['allow_insecure'] and str(node['allow_insecure']).lower() == 'true':
        params.append("insecure=1")
    param_str = "&".join(params) if params else ""
    remarks = quote(node['remarks'] or "")
    password = node['id'] or ""  # ConfigType=7 的密码是 Id 字段
    if param_str:
        return f"hysteria2://{password}@{node['address']}:{node['port']}?{param_str}#{remarks}"
    return f"hysteria2://{password}@{node['address']}:{node['port']}#{remarks}"


def generate_tuic_link(node):
    """生成 TUIC 分享链接 (ConfigType=5,6,8)"""
    params = []
    if node['sni']:
        params.append(f"sni={node['sni']}")
    if node['alpn']:
        params.append(f"alpn={node['alpn']}")
    if node['allow_insecure'] and str(node['allow_insecure']).lower() == 'true':
        params.append("allow_insecure=1")
    # congestion_control (HeaderType 字段)
    if node['header_type'] and node['header_type'] != 'none':
        params.append(f"congestion_control={node['header_type']}")
    param_str = "&".join(params) if params else ""
    remarks = quote(node['remarks'] or "")
    uuid = node['id'] or ""
    password = node['security'] or ""
    # URL 编码密码中的特殊字符
    password_encoded = quote(password, safe='')
    if param_str:
        return f"tuic://{uuid}%3A{password_encoded}@{node['address']}:{node['port']}?{param_str}#{remarks}"
    return f"tuic://{uuid}%3A{password_encoded}@{node['address']}:{node['port']}#{remarks}"


def generate_shadowsocks_link(node):
    """生成 Shadowsocks 分享链接 (ConfigType=2)"""
    method = node['security'] or "aes-256-gcm"
    password = node['id'] or ""
    remarks = quote(node['remarks'] or "")
    user_info = f"{method}:{password}"
    b64 = base64.b64encode(user_info.encode('utf-8')).decode('utf-8')
    return f"ss://{b64}@{node['address']}:{node['port']}#{remarks}"


def generate_trojan_link(node):
    """生成 Trojan 分享链接 (ConfigType=4)"""
    params = []
    if node['network']: params.append(f"type={node['network']}")
    if node['stream_security']: params.append(f"security={node['stream_security']}")
    if node['request_host']: params.append(f"host={node['request_host']}")
    if node['path']: params.append(f"path={quote(node['path'])}")
    if node['sni']: params.append(f"sni={node['sni']}")
    if node['alpn']: params.append(f"alpn={node['alpn']}")
    if node['fingerprint']: params.append(f"fp={node['fingerprint']}")
    param_str = "&".join(params)
    remarks = quote(node['remarks'] or "")
    return f"trojan://{node['id']}@{node['address']}:{node['port']}?{param_str}#{remarks}"


def generate_share_link(node):
    """根据 ConfigType 生成对应的分享链接"""
    config_type = node['config_type']
    try:
        if config_type == 1:  # VMess
            return generate_vmess_link(node)
        elif config_type == 2:  # Shadowsocks
            return generate_shadowsocks_link(node)
        elif config_type == 3:  # VLESS
            return generate_vless_link(node)
        elif config_type == 4:  # Trojan
            return generate_trojan_link(node)
        elif config_type in [5, 6, 8]:  # TUIC
            return generate_tuic_link(node)
        elif config_type == 7:  # Hysteria2
            return generate_hysteria2_link(node)
        else:
            print(f"⚠️ 未知类型 ConfigType={config_type}: {node['remarks']}")
            return None
    except Exception as e:
        print(f"❌ 生成链接失败 ({node['remarks']}): {e}")
        return None


# ==================== Gist 上传 ====================
def upload_to_gist(nodes_by_group, stats, gist_id=None):
    """上传到 GitHub Gist"""
    all_links = []
    links_by_group = {}
    for group_name, nodes in nodes_by_group.items():
        group_links = []
        for node in nodes:
            link = generate_share_link(node)
            if link:
                all_links.append(link)
                group_links.append(link)
                stats['success'] += 1
            else:
                stats['failed'] += 1
        links_by_group[group_name] = group_links
    # Base64 编码订阅
    raw_subscription_text = "\n".join(all_links)  # 1. 将明文链接合并
    standard_subscription_b64 = base64.b64encode(raw_subscription_text.encode('utf-8')).decode('utf-8')
    # 可读格式
    readable_content = []
    for group_name, links in links_by_group.items():
        readable_content.append(f"\n# ===== {group_name} ({len(links)} 个节点) =====")
        for link in links:
            readable_content.append(link)
    # 上传
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gist_data = {
        "description": f"V2Ray 订阅 - 更新: {timestamp}",
        "public": False,
        "files": {
            "subscription.txt": {"content": standard_subscription_b64},
            "nodes_readable.txt": {"content": "\n".join(readable_content)}
        }
    }
    try:
        if gist_id:
            # 修正：移除了 URL 末尾多余的逗号
            url = f"https://api.github.com/gists/{gist_id}"
            response = requests.patch(url, headers=headers, json=gist_data)
        else:
            url = "https://api.github.com/gists"
            response = requests.post(url, headers=headers, json=gist_data)
        if response.status_code in [200, 201]:
            result = response.json()
            sub_url = result['files']['subscription.txt']['raw_url']
            new_gist_id = result['id']
            print(f"\n✅ 同步成功!")
            print(f"📋 Gist ID: {new_gist_id}")
            print(f"📡 订阅链接: {sub_url}")
            print(f"⏰ 更新时间: {timestamp}")
            print(f"📊 成功: {stats['success']}/{stats['total']} 个节点")
            if stats['failed'] > 0:
                print(f"⚠️ 失败: {stats['failed']} 个节点")
            # 保存新的 Gist ID 到文件，以便下次运行使用
            with open("gist_id.txt", "w") as f:
                f.write(new_gist_id)
            return new_gist_id, sub_url
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"   {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None, None


# ==================== 主程序 ====================
def main():
    """主程序"""
    print("=" * 60)
    print("🚀 V2Ray → GitHub Gist 自动同步工具 (GitHub Actions 版本)")
    print("=" * 60)
    # 检查 WebDAV 配置
    if not WEBDAV_URL or WEBDAV_URL == "":
        print("❌ 请配置 WebDAV 连接信息!")
        return
    # 检查 GitHub Token
    if not GITHUB_TOKEN:
        print("❌ 未找到 GITHUB_TOKEN (请检查仓库密钥 GIST_TOKEN)")
        return
    # 从 WebDAV 下载并解压
    db_path, temp_dir = download_and_extract_webdav()
    if not db_path:
        print("❌ 无法获取数据库文件")
        cleanup_temp_dir(temp_dir)
        return
    nodes_by_group, stats = read_v2rayn_database(db_path)
    if not nodes_by_group:
        print("❌ 未找到任何节点")
        cleanup_temp_dir(temp_dir)
        return
    print(f"📊 共 {len(nodes_by_group)} 个分组，{stats['total']} 个节点")
    # 读取已有的 Gist ID，用于更新
    # 读取已有的 Gist ID，用于更新
    current_gist_id = os.getenv("GIST_ID")  # 优先使用固定环境变量
    if current_gist_id:
        print(f"📝 使用固定 Gist ID 更新: {current_gist_id}")
    else:
        # 如果没设置 GIST_ID，再尝试读取文件
        if os.path.exists("gist_id.txt"):
            with open("gist_id.txt", "r") as f:
                current_gist_id = f.read().strip()
        if current_gist_id:
            print(f"📝 尝试更新现有 Gist: {current_gist_id}")
        else:
            print("📝 未找到 Gist ID，将创建新 Gist")

    new_gist_id, sub_url = upload_to_gist(nodes_by_group, stats, current_gist_id)
    # 清理临时文件
    cleanup_temp_dir(temp_dir)
    if new_gist_id:
        print(f"🆕 本次操作的 Gist ID: {new_gist_id}")
    else:
        print("❌ 同步失败")
    print("\n👋 同步完成")


if __name__ == "__main__":
    main()
