# -*- coding: utf-8 -*-
"""
蝴蝶影视 自动编译核心流主程序
"""
import re
import os
import sys
import json
import time
import random
import string
import copy
import datetime
import logging
from pathlib import Path

# 引入优化请求库
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 引入独立配置文件
import config

# ====================================================================
# 🎛️ 【高可用场景色彩日志控制中心】
# ====================================================================
class CustomFormatter(logging.Formatter):
    green = "\033[92m"
    cyan = "\033[96m"
    yellow = "\033[93m"
    red = "\033[91m"
    magenta = "\033[95m"
    reset = "\033[0m"
    base_fmt = "%(asctime)s [%(levelname)s] %(message)s"
    FORMATS = {
        logging.DEBUG: cyan + base_fmt + reset,
        logging.INFO: green + base_fmt + reset,
        logging.WARNING: yellow + base_fmt + reset,
        logging.ERROR: red + base_fmt + reset,
        logging.CRITICAL: magenta + base_fmt + reset
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.base_fmt)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

_logger = logging.getLogger("ButterflyEngine")
_logger.setLevel(logging.DEBUG)
_logger.handlers.clear()
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(CustomFormatter())
_logger.addHandler(stream_handler)

def log_info(msg): _logger.info(msg)
def log_warning(msg): _logger.warning(msg)
def log_error(msg, exc_info=False): _logger.error(msg, exc_info=exc_info)
def log_critical(msg, exc_info=False): _logger.critical(msg, exc_info=exc_info)
def log_success(msg): _logger.info(f"✨ [SUCCESS] {msg}")
def log_network(msg): _logger.info(f"🌐 [NETWORK] {msg}")
def log_diff(msg):    _logger.info(f"📊 [DIFF_DET] {msg}")

# ====================================================================
# 📡 【统一网络环境初始化与高可用 Session 连接池】
# ====================================================================
HTTP_SESSION = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
HTTP_SESSION.mount("http://", HTTPAdapter(max_retries=retries))
HTTP_SESSION.mount("https://", HTTPAdapter(max_retries=retries))

def send_telegram_request(token, chat_id, text):
    """使用统一 Session 高效下发 Telegram 通知"""
    if not token or not chat_id:
        log_warning("缺失 TG_TOKEN 或 TG_CHAT_ID，跳过发送 TG 通知。")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "parse_mode": "Markdown", "text": text}
    try:
        log_network("正在向 TG 频道下发蝴蝶影视编译快报...")
        res = HTTP_SESSION.post(url, json=payload, timeout=config.TG_TIMEOUT)
        if res.status_code == 200:
            log_success("Telegram 通知在独立连接池中直发成功！")
            return True
        else:
            log_error(f"TG 接口响应异常: 状态码 {res.status_code}，死因: {res.text}")
    except Exception as e:
        log_error(f"Telegram 网络总线请求崩溃: {e}")
    return False

# ====================================================================
# 🛡️ 【智能容灾本地 JSON 安全加载模块】
# ====================================================================
def load_json_safe(file_path: Path) -> dict:
    """底包安全过滤器与自动历史恢复引擎"""
    backup_path = file_path.parent / f"{file_path.stem}_backup{file_path.suffix}"
    current_data = None
    is_current_valid = False

    if file_path.exists():
        try:
            current_data = json.loads(file_path.read_text(encoding='utf-8'))
            if isinstance(current_data, dict) and ("sites" in current_data or "lives" in current_data or "parses" in current_data):
                is_current_valid = True
            else:
                log_warning(f"底包 {file_path.name} 根节点不合规，标记为损坏源。")
        except Exception:
            log_warning(f"底包 {file_path.name} 解析 JSON 崩溃，文件可能为空。")

    if is_current_valid:
        try:
            backup_path.write_text(json.dumps(current_data, ensure_ascii=False, indent=4), encoding='utf-8')
            log_info(f"底包 {file_path.name} 安全复核通过，增量同步到本地备份链中。")
        except Exception as e:
            log_error(f"本地同步备份链写入失败: {e}")
        return current_data
    else:
        log_critical(f"上游数据源 {file_path.name} 彻底断流！启动自动化容灾降级...")
        if backup_path.exists():
            try:
                backup_data = json.loads(backup_path.read_text(encoding='utf-8'))
                log_success(f"容灾降级成功！已从历史干净数据中提取并重构底包: {backup_path.name}")
                file_path.write_text(json.dumps(backup_data, ensure_ascii=False, indent=4), encoding='utf-8')
                return backup_data
            except Exception:
                log_critical(f"致命灾难：本地老本数据 {backup_path.name} 也意外遭到物理损坏！")
        else:
            log_critical(f"致命灾难：本地库中未检索到任何备份副本 {backup_path.name}！")
        return {}

# ====================================================================
# ⏰ 【每月 1 号自动大洗牌与密锁控制模块】
# ====================================================================
def manage_monthly_token():
    """管理密码生存周期控制"""
    today = datetime.datetime.now()
    current_month = str(today.month)
    is_reset_day = (today.day == 1)

    saved_month, saved_code = "", ""
    is_new_token_generated = False

    if config.LOCK_FILE_PATH.exists():
        content = config.LOCK_FILE_PATH.read_text(encoding='utf-8').strip()
        if "-" in content:
            saved_month, saved_code = content.split("-", 1)
        else:
            saved_code = content

    if is_reset_day and saved_month != current_month:
        current_token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=config.TOKEN_LENGTH))
        config.LOCK_FILE_PATH.write_text(f"{current_month}-{current_token}", encoding='utf-8')
        log_success(f"每月1号大清洗！全自动抽签生成的本月蝴蝶新密锁为: {current_token}")
        is_new_token_generated = True
    elif is_reset_day and saved_month == current_month:
        current_token = saved_code
    else:
        if not saved_code or len(saved_code) != config.TOKEN_LENGTH or "-" not in (config.LOCK_FILE_PATH.read_text(encoding='utf-8') if config.LOCK_FILE_PATH.exists() else ""):
            current_token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=config.TOKEN_LENGTH))
            config.LOCK_FILE_PATH.write_text(f"{current_month}-{current_token}", encoding='utf-8')
        else:
            current_token = saved_code

    if current_token in ["全量版", "纯净版"]:
        full_output_filename = f"{config.BASE_OUTPUT_FULL}.json"
        clean_output_filename = f"{config.BASE_OUTPUT_CLEAN}.json"
    else:
        full_output_filename = f"{config.BASE_OUTPUT_FULL}{current_token}.json"
        clean_output_filename = f"{config.BASE_OUTPUT_CLEAN}{current_token}.json"

    return current_token, full_output_filename, clean_output_filename, is_new_token_generated

# ====================================================================
# 🛡️ 【过期接口金蝉脱壳爆破模块】
# ====================================================================
def execute_trap_boom(full_output_filename, clean_output_filename):
    """金蝉脱壳：全自动过期大轰炸覆盖机制"""
    if not config.DATA_DIR.exists():
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    old_configs = list(config.DATA_DIR.glob(f'{config.BASE_OUTPUT_FULL}*.json')) + \
                  list(config.DATA_DIR.glob(f'{config.BASE_OUTPUT_CLEAN}*.json')) + \
                  list(config.DATA_DIR.glob('老杨TV*.json')) + \
                  list(config.DATA_DIR.glob('蝴蝶影视*.json'))

    for old_file in old_configs:
        if old_file.name != full_output_filename and old_file.name != clean_output_filename:
            try:
                trap_json = {
                    "spider": "", 
                    "notice": config.TRAP_NOTICE_TEXT,
                    "warningText": config.TRAP_WARNING_TEXT,
                    "sites": [
                        {"key": "蝴蝶纯文字提示", "name": config.TRAP_SITE_NAME_1, "type": 3, "api": "csp_JuDou", "searchable": 0, "quickSearch": 0, "filterable": 0},
                        {"key": "蝴蝶纯文字提示2", "name": config.TRAP_SITE_NAME_2, "type": 3, "api": "csp_JuDou", "searchable": 0, "quickSearch": 0, "filterable": 0}
                    ],
                    "lives": [
                        {"group": config.TRAP_LIVE_GROUP, "channels": [{"name": config.TRAP_LIVE_CHANNEL, "urls": ["http://127.0.0.1"]}]}
                    ]
                }
                old_file.write_text(json.dumps(trap_json, ensure_ascii=False, indent=4), encoding='utf-8')
            except Exception:
                pass

    for garbage in config.DATA_DIR.glob('config_*.json'):
        try: garbage.unlink()
        except Exception: pass

# ====================================================================
# ⚙️ 【核心业务：对象级链式清洗与归类编译引擎】
# ====================================================================
def object_level_wash_and_compile():
    """100%纯内存对象流操作，杜绝二次重载"""
    json_cnb = load_json_safe(config.CNB_PATH)
    json_haitun = load_json_safe(config.HAITUN_PATH)
    json_lz = load_json_safe(config.LZ_PATH)

    haitun_sites = json_haitun.get("sites", [])
    haitun_lives = json_haitun.get("lives", [])
    lz_sites = json_lz.get("sites", [])

    lz_nsfw_list = []
    for item in lz_sites:
        site_name = item.get("name", "")
        if "🔞" in site_name:
            item["name"] = f"{site_name.replace('🔞', '').strip()}｜🔞"
            api_str = item.get("api", "")
            if isinstance(api_str, str) and api_str.startswith("./"):
                if api_str.startswith("./py/"):
                    item["api"] = api_str.replace("./py/", "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz/py/")
                elif api_str.startswith("./js/"):
                    item["api"] = api_str.replace("./js/", "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz/js/")
                else:
                    item["api"] = api_str.replace("./", "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz/")
            lz_nsfw_list.append(item)

    for item in haitun_sites:
        if "name" in item:
            for dirty in config.UPSTREAM_DIRTY_WORDS:
                item["name"] = item["name"].replace(dirty, "")
            item["name"] = f"{item['name'].strip()}{config.MY_TG_SUFFIX}"

    for item in haitun_lives:
        if "name" in item:
            for dirty in config.UPSTREAM_DIRTY_WORDS:
                item["name"] = item["name"].replace(dirty, "")
            item["name"] = f"{item['name'].strip()}{config.MY_TG_SUFFIX}"

    cnb_sites = json_cnb.get("sites", [])
    cnb_lives = json_cnb.get("lives", [])

    combined_parses = json_haitun.get("parses", []) + json_lz.get("parses", []) + json_cnb.get("parses", [])
    unique_parses = []
    seen_parse_names = set()
    for p in combined_parses:
        p_name = p.get("name", "")
        if p_name and p_name not in seen_parse_names:
            unique_parses.append(p)
            seen_parse_names.add(p_name)

    all_raw_sites = haitun_sites + lz_nsfw_list + cnb_sites
    custom_keys = {site.get("key") for site in config.MY_CUSTOM_SITES if site.get("key")}
    clean_upstream_sites = [site for site in all_raw_sites if site.get("key") not in custom_keys]

    compiled_sites = []
    tg_tail_count = 0

    for site in clean_upstream_sites:
        name = site.get("name", "")
        if any(kw in name for kw in config.BLOCK_KEYWORDS) or any(mkw in name for mkw in config.BLOCK_MALICIOUS_KEYWORDS):
            continue

        for dirty in config.UPSTREAM_DIRTY_WORDS:
            name = name.replace(dirty, "")

        for char in ['丨', '┃', ' ']: name = name.strip(char)
        name = re.sub(r'\s+', ' ', name)
        if config.MY_TG_SUFFIX in name:
            tg_tail_count += 1
            if tg_tail_count > 5: name = name.replace(config.MY_TG_SUFFIX, "").strip()

        if not name.startswith(config.LOGO_PREFIX):
            name = f"{config.LOGO_PREFIX} {name}"

        for src_word, dst_word in config.MY_NAME_REPLACEMENTS.items():
            name = name.replace(src_word, dst_word)

        site["name"] = name

        api_field = site.get("api", "")
        if isinstance(api_field, str):
            for pattern, target in config.PATH_REPLACEMENTS.items():
                api_field = re.sub(pattern, target, api_field)
            site["api"] = api_field

        ext_field = site.get("ext", "")
        if isinstance(ext_field, str):
            for pattern, target in config.PATH_REPLACEMENTS.items():
                ext_field = re.sub(pattern, target, ext_field)
            site["ext"] = ext_field
        elif isinstance(ext_field, dict):
            try:
                ext_str = json.dumps(ext_field, ensure_ascii=False)
                for pattern, target in config.PATH_REPLACEMENTS.items():
                    ext_str = re.sub(pattern, target, ext_str)
                site["ext"] = json.loads(ext_str)
            except Exception:
                pass
            if "PanWebShare" in api_field:
                site["api"] = "csp_PanWebShare"
                site["changeable"] = 1
                if "jar" in site: site.pop("jar")

        if site.get("ext") == {}: site["ext"] = ""
        compiled_sites.append(site)

    bucket_map = {category: [] for category in config.CATEGORY_RULES.keys()}
    bucket_map["综合"] = []
    bucket_map["福利"] = []

    no_search_kw = getattr(config, "NO_SEARCH_KEYWORDS", [])
    no_search_keys = getattr(config, "NO_SEARCH_KEYS", [])
    no_quick_keys = getattr(config, "NO_QUICK_SEARCH_KEYS", [])

    for site in compiled_sites:
        s_key = site.get("key", "")
        s_name = site.get("name", "")

        if any(kw in s_name for kw in no_search_kw) or (s_key in no_search_keys):
            site["searchable"] = 0
            
        if s_key in no_quick_keys:
            site["quickSearch"] = 0

        if s_key == config.HOT_VIDEO_KEY:
            site["name"] = config.HOT_VIDEO_SITE_NAME
            site["category"] = "综合"
            bucket_map["综合"].insert(0, site)
            continue
        elif "豆瓣" in s_name and "首页" in s_name:
            site["name"] = f"{config.LOGO_PREFIX} 豆瓣 • 首页"
            site["category"] = "综合"
            site["searchable"] = 0
            bucket_map["综合"].append(site)
            continue
        elif s_key == "AQY":
            site["name"] = f"{config.LOGO_PREFIX} 爱奇艺 {config.MY_TG_SUFFIX}"

        is_guazi = "瓜子" in s_name or s_key == "GZ"
        is_nsfw = False if is_guazi else ("🔞" in s_name or "色播" in s_name or "av" in s_key.lower() or "瓜" in s_name or "爆料" in s_name or "chat" in s_key.lower() or "cam" in s_key.lower() or "panda" in s_key.lower() or "video" in s_key.lower() or "md" in s_key.lower())
        
        if is_nsfw:
            site["category"] = "福利"
            bucket_map["福利"].append(site)
            continue

        matched_category = None
        for category, keywords in config.CATEGORY_RULES.items():
            if any(kw in s_name or (kw in s_key.lower() if s_key else False) for kw in keywords):
                matched_category = category
                break
        
        if matched_category:
            site["category"] = matched_category
            if matched_category in ["少儿", "音乐"] or "dj" in s_name.lower():
                site["searchable"] = 0
            bucket_map[matched_category].append(site)
        else:
            site["category"] = "综合"
            bucket_map["综合"].append(site)

        if site.get("category") not in ["少儿", "音乐"] and "searchable" not in site:
            site["searchable"] = 1

    ordered_sites = []
    for cate in ["综合", "短剧", "动漫", "体育/直播", "少儿", "音乐", "网盘/磁力", "福利"]:
        if cate in bucket_map:
            ordered_sites.extend(bucket_map[cate])

    target_pos = getattr(config, "SITE_INSERT_POS", 1)
    hot_key = getattr(config, "HOT_VIDEO_KEY", "")
    hot_name = getattr(config, "HOT_VIDEO_SITE_NAME", "")

    hot_sites = []
    normal_sites = []

    for custom_site in config.MY_CUSTOM_SITES:
        site = custom_site.copy()
        s_key = site.get("key", "")
        
        if s_key and s_key == hot_key:
            site["name"] = hot_name or site.get("name")
            site["category"] = "综合"
            hot_sites.append(site)
        else:
            if "searchable" not in site:
                site["searchable"] = 1
            normal_sites.append(site)

    for site in reversed(normal_sites):
        idx = min(target_pos, len(ordered_sites))
        ordered_sites.insert(idx, site)

    for site in reversed(hot_sites):
        ordered_sites.insert(0, site)

    # 🎯 【最终名称打标】：根据分类在 name 后面追加分类标签
    CATEGORY_TAG_MAP = {
        "综合": "[综合]",
        "短剧": "[专类]",
        "动漫": "[专类]",
        "体育/直播": "[专类]",
        "少儿": "[专类]",
        "音乐": "[专类]",
        "网盘/磁力": "[磁力]",
        "福利": "[密]"
    }

    TOOL_KEYS = {"js_douban", "配置中心", "push_agent", "Nostr", "Nostr2", "本地", "预告", "版本信息", "工具"}
    TOOL_NAME_KW = ["配置", "推送", "版本", "预告", "搜索"]
    OFFICIAL_NAME_KW = ["优酷", "爱奇艺", "腾讯视频", "芒果", "哔哩", "1905", "豆瓣"]
    ADULT_KW = ["🔞", "成人", "伦理", "福利"]
    APP_NAME_KW = ["APP", "app"]

    for site in ordered_sites:
        s_name = site.get("name", "")
        s_category = site.get("category", "综合")
        s_key = site.get("key", "")
        s_api = str(site.get("api", ""))

        if s_category == "福利" or any(kw in s_name for kw in ADULT_KW):
            tag = "[密]"
        elif any(kw in s_name for kw in OFFICIAL_NAME_KW) and s_category == "综合":
            tag = "[官]"
        elif s_key in TOOL_KEYS or any(kw in s_name for kw in TOOL_NAME_KW):
            tag = "[工具]"
        elif any(kw in s_name for kw in APP_NAME_KW) or "csp_App" in s_api:
            tag = "[APP采集]"
        elif any(kw in s_name for kw in ["网盘", "云盘", "磁力"]):
            tag = "[磁力]"
        elif any(kw in s_name for kw in ["4K", "4k", "高清"]):
            tag = "[4K]"
        else:
            tag = CATEGORY_TAG_MAP.get(s_category, "[综合]")

        if not s_name.endswith(tag):
            site["name"] = f"{s_name} {tag}"

    custom_live_names = {l.get("name") for l in config.MY_CUSTOM_LIVES if l.get("name")}
    clean_base_lives = [
        l for l in (haitun_lives + cnb_lives)
        if l.get("name") not in custom_live_names and not any(kw in l.get("name", "") for kw in config.BLOCK_MALICIOUS_KEYWORDS)
    ]
    clean_base_lives = [l for l in clean_base_lives if not any(kw.lower() in l.get("name", "").lower() for kw in config.BLOCK_KEYWORDS)]

    live_inserted_count = 0
    for custom_live in config.MY_CUSTOM_LIVES:
        l_name = custom_live.get("name", "")
        if not l_name.startswith(config.LOGO_PREFIX):
            l_name = f"{config.LOGO_PREFIX} {l_name}"
        if config.MY_TG_SUFFIX not in l_name:
            l_name = f"{l_name}{config.MY_TG_SUFFIX}"
        custom_live["name"] = l_name

        if "🔞" in l_name:
            clean_base_lives.append(custom_live)
        else:
            idx = min(config.INSERT_POS + live_inserted_count, len(clean_base_lives))
            clean_base_lives.insert(idx, custom_live)
            live_inserted_count += 1

    final_obj = copy.deepcopy(json_cnb)
    
    if hasattr(config, "DEFAULT_LOGO_URL") and config.DEFAULT_LOGO_URL:
        final_obj["logo"] = config.DEFAULT_LOGO_URL

    final_obj.update({
        "parses": unique_parses,
        "sites": ordered_sites,
        "lives": clean_base_lives
    })

    for s in final_obj.get("sites", []):
        if s.get("key") in ["hajim-腾讯备", "茫茫"]:
            s["spider"] = "./tvbox.jar"

    if "doh" in final_obj and isinstance(final_obj["doh"], list):
        for doh_item in final_obj["doh"]:
            if doh_item.get("url", "").endswith("/dns-quer"): doh_item["url"] = f"{doh_item['url']}y"
        if not any(d.get("name") == config.ALI_DOH_CONFIG["name"] for d in final_obj["doh"]):
            final_obj["doh"].insert(0, config.ALI_DOH_CONFIG)

    if "rules" in final_obj and isinstance(final_obj["rules"], list):
        current_rules = final_obj["rules"]
        ad_hosts = list(config.AD_HOSTS_LIST)
        for r in current_rules:
            if isinstance(r, dict) and "hosts" in r:
                for h in r["hosts"]:
                    if h not in ad_hosts: ad_hosts.append(h)
        js_rule = {"name": "蝴蝶影视·云端高级去广告JS注入", "hosts": ad_hosts, "script": config.CUSTOM_AD_BLOCK_JS}
        final_obj["rules"] = [js_rule] + [r for r in current_rules if r.get("name") != "蝴蝶影视·云端高级去广告JS注入"]

    final_obj["spider"] = config.GLOBAL_SPIDER_JAR

    for site in final_obj.get("sites", []):
        s_key = site.get("key", "")
        if s_key in ["hajim-腾讯备", "茫茫"]:
            site["spider"] = "./tvbox.jar"

    if "lives" in final_obj and isinstance(final_obj["lives"], list):
        clean_lives = []
        for live in final_obj["lives"]:
            if not live or not isinstance(live, dict) or len(live) == 0:
                continue
            clean_lives.append(live)
        final_obj["lives"] = clean_lives

    return final_obj

# ====================================================================
# 🔀 【双版本矩阵构建与差异下发调度中枢】
# ====================================================================
def generate_dashboard_html(current_token, site_cnt, live_cnt, parse_cnt):
    """自动读取 datas 目录并根据 config 里的模板编译 Dashboard html 页面"""
    try:
        current_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        
        file_cards_html = ""
        json_files = sorted(list(config.DATA_DIR.glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for json_file in json_files:
            size_kb = round(json_file.stat().st_size / 1024, 2)
            fname = json_file.name
            
            is_active = current_token in fname
            badge = '<span class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">最新版本</span>' if is_active else '<span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">历史/陷阱</span>'
            
            safe_key = fname.replace('.', '_').replace('-', '_')

            file_cards_html += f"""
            <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="font-semibold text-slate-800">{fname}</span>
                        {badge}
                        <span class="text-xs text-gray-400">{size_kb} KB</span>
                    </div>
                    <p class="text-xs text-gray-400 mt-1">https://hd.lytvs.top/{fname}</p>
                </div>
                
                <div class="flex items-center gap-3">
                    <div class="text-right px-2">
                        <div class="text-[10px] text-gray-400">点击/获取量</div>
                        <div class="text-xs font-bold text-emerald-600" id="cnt_{safe_key}">-- 次</div>
                    </div>
                    <div class="flex gap-2">
                        <a href="/{fname}" target="_blank" onclick="hitCount('{safe_key}')" class="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-xs font-medium hover:bg-blue-100">
                            预览 JSON
                        </a>
                        <button onclick="navigator.clipboard.writeText('https://hd.lytvs.top/{fname}'); hitCount('{safe_key}'); alert('已复制该接口链接！')" class="px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-medium hover:bg-slate-700">
                            复制链接
                        </button>
                    </div>
                </div>
            </div>
            """

        html_out = config.DASHBOARD_HTML_TEMPLATE.format(
            build_time=current_time,
            site_cnt=site_cnt,
            live_cnt=live_cnt,
            parse_cnt=parse_cnt,
            current_token=current_token,
            file_num=len(json_files),
            file_cards=file_cards_html,
            version=config.VERSION,
            qq_group=config.MY_QQ_GROUP
        )

        secret_filename = "admin_888.html"
        
        admin_path = config.DATA_DIR / secret_filename
        admin_path.write_text(html_out, encoding="utf-8")
        
        public_index_path = config.DATA_DIR / "index.html"
        public_index_path.write_text("<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1></body></html>", encoding="utf-8")

        log_success(f"可视化 Dashboard 页面已成功加密注入！专属后台路径: datas/{secret_filename}")
        
    except Exception as e:
        log_error(f"生成 Dashboard 页面崩溃: {e}")


def build_and_dispatch_matrix(ordered_obj, current_token, full_out_name, clean_out_name, is_new_token_gen):
    """构建多通道分流，精准比对 Diff 并下发变更明细快报"""
    full_version_obj = copy.deepcopy(ordered_obj)
    full_version_obj["notice"] = config.WELCOME_NOTICE_FULL + config.THANKS_WARNING
    full_version_obj["wallpaper"] = config.WALLPAPER_FULL
    
    full_final_out = {"notice": full_version_obj.pop("notice")}
    full_final_out.update(full_version_obj)

    clean_version_obj = copy.deepcopy(ordered_obj)
    clean_version_obj["notice"] = config.WELCOME_NOTICE_CLEAN + config.THANKS_WARNING
    clean_version_obj["wallpaper"] = config.WALLPAPER_CLEAN
    
    clean_version_obj["sites"] = [
        s for s in clean_version_obj.get("sites", [])
        if not any(kw in s.get("name", "") or kw in s.get("category", "") or kw in s.get("key", "").lower() for kw in config.NSFW_KEYWORDS)
    ]
    clean_version_obj["lives"] = [
        l for l in clean_version_obj.get("lives", [])
        if not any(kw in l.get("name", "") for kw in config.NSFW_KEYWORDS)
    ]
    
    clean_final_out = {"notice": clean_version_obj.pop("notice")}
    clean_final_out.update(clean_version_obj)

    full_output_path = config.DATA_DIR / full_out_name
    clean_output_path = config.DATA_DIR / clean_out_name

    tg_token = os.getenv("TG_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    repo_info = os.getenv("GITHUB_REPOSITORY", "Godlike/Ly")
    branch_info = os.getenv("GITHUB_REF_NAME", "main")
    
    full_raw_url = f"https://raw.githubusercontent.com/{repo_info}/refs/heads/{branch_info}/datas/{full_out_name}"
    clean_raw_url = f"https://raw.githubusercontent.com/{repo_info}/refs/heads/{branch_info}/datas/{clean_out_name}"
    
    full_sub_url = f"{config.GITHUB_PROXY}{full_raw_url}" if config.GITHUB_PROXY else full_raw_url
    clean_sub_url = f"{config.GITHUB_PROXY}{clean_raw_url}" if config.GITHUB_PROXY else clean_raw_url
    
    current_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    is_password_changed = False
    old_file_name = ""
    
    if config.TRACKER_PATH.exists():
        old_file_name = config.TRACKER_PATH.read_text(encoding='utf-8').strip()
    if old_file_name != full_out_name and old_file_name != "":
        is_password_changed = True

    if is_password_changed or is_new_token_gen:
        pwd_msg = config.TG_PWD_MSG_TEMPLATE.format(
            current_time=current_time, current_token=current_token,
            full_sub_url=full_sub_url, clean_sub_url=clean_sub_url
        )
        send_telegram_request(tg_token, tg_chat_id, pwd_msg)
    else:
        try:
            old_sites, old_lives = set(), set()
            old_file_path = config.DATA_DIR / old_file_name
            if old_file_path.exists():
                old_data = json.loads(old_file_path.read_text(encoding='utf-8'))
                old_sites = {s.get("name", "").strip() for s in old_data.get("sites", []) if s.get("name")}
                old_lives = {l.get("name", "").strip() for l in old_data.get("lives", []) if l.get("name")}

            new_sites = {s.get("name", "").strip() for s in full_final_out.get("sites", []) if s.get("name")}
            new_lives = {l.get("name", "").strip() for l in full_final_out.get("lives", []) if l.get("name")}

            added_sites, del_sites = sorted(list(new_sites - old_sites)), sorted(list(old_sites - new_sites))
            added_lives, del_lives = sorted(list(new_lives - old_lives)), sorted(list(old_lives - new_lives))

            if added_sites or del_sites or added_lives or del_lives:
                msg_lines = ["📝 *【 变动明细预览 】*", "📊 *━━━━━━━━━━━━━━*"]
                if added_sites or del_sites:
                    msg_lines.append("📺 *【点播线路变动】*")
                    if added_sites:
                        msg_lines.append("➕ *新增点播*：")
                        msg_lines.extend([f"  🟢 {name}" for name in added_sites[:config.TG_MAX_DISPLAY]])
                        if len(added_sites) > config.TG_MAX_DISPLAY: msg_lines.append(f"  ...等共 {len(added_sites)} 个源")
                    if del_sites:
                        if added_sites: msg_lines.append("")
                        msg_lines.append("➖ *剔除点播*：")
                        msg_lines.extend([f"  🔴 {name}" for name in del_sites[:config.TG_MAX_DISPLAY]])
                        if len(del_sites) > config.TG_MAX_DISPLAY: msg_lines.append(f"  ...等共 {len(del_sites)} 个源")
                    msg_lines.append("📊 *━━━━━━━━━━━━━━*")
                if added_lives or del_lives:
                    if len(msg_lines) > 2: msg_lines.append("")
                    msg_lines.append("📡 *【直播源站变动】*")
                    if added_lives:
                        msg_lines.append("➕ *新增直播*：")
                        msg_lines.extend([f"  🟢 {name}" for name in added_lives[:config.TG_MAX_DISPLAY]])
                        if len(added_lives) > config.TG_MAX_DISPLAY: msg_lines.append(f"  ...等共 {len(added_lives)} 个源")
                    if del_lives:
                        if added_lives: msg_lines.append("")
                        msg_lines.append("➖ *剔除直播*：")
                        msg_lines.extend([f"  🔴 {name}" for name in del_lives[:config.TG_MAX_DISPLAY]])
                        if len(del_lives) > config.TG_MAX_DISPLAY: msg_lines.append(f"  ...等共 {len(del_lives)} 个源")
                    msg_lines.append("📊 *━━━━━━━━━━━━━━*")

                full_msg = config.TG_UPDATE_MSG_TEMPLATE.format(
                    current_time=current_time, 
                    current_token=current_token,
                    detail_msg="\n".join(msg_lines),
                    full_sub_url=full_sub_url, 
                    clean_sub_url=clean_sub_url
                )
                send_telegram_request(tg_token, tg_chat_id, full_msg)
            else:
                log_diff("蝴蝶名录内容等价，智能拦截重复变更广播。")
        except Exception as e:
            log_error(f"比对 Diff 变动逻辑发生致命故障: {e}")

    full_output_path.write_text(json.dumps(full_final_out, ensure_ascii=False, indent=4), encoding='utf-8')
    clean_output_path.write_text(json.dumps(clean_final_out, ensure_ascii=False, indent=4), encoding='utf-8')
    config.TRACKER_PATH.write_text(full_out_name, encoding='utf-8')
    
    site_cnt = len(full_final_out.get("sites", []))
    live_cnt = len(full_final_out.get("lives", []))
    parse_cnt = len(full_final_out.get("parses", []))
    generate_dashboard_html(current_token, site_cnt, live_cnt, parse_cnt)

    return site_cnt, live_cnt, parse_cnt, full_output_path.stat().st_size

# ====================================================================
# 🚀 【程序统一总调度入口】
# ====================================================================
def main():
    start_time = time.time()
    try:
        log_info(f"====================================================")
        log_info(f"蝴蝶影视 自动编译核心架构工程架设流 V{config.VERSION}")
        log_info(f"编译流构建序列日期: {config.BUILD_DATE}")
        log_info(f"====================================================")
        
        current_token, full_out_name, clean_out_name, is_new_token_gen = manage_monthly_token()
        execute_trap_boom(full_out_name, clean_out_name)
        ordered_obj = object_level_wash_and_compile()
        
        site_cnt, live_cnt, parse_cnt, file_size = build_and_dispatch_matrix(
            ordered_obj, current_token, full_out_name, clean_out_name, is_new_token_gen
        )
        
        today = datetime.datetime.now()
        if not config.LOCK_FILE_PATH.exists() or "-" not in config.LOCK_FILE_PATH.read_text(encoding='utf-8'):
            config.LOCK_FILE_PATH.write_text(f"{today.month}-{current_token}", encoding='utf-8')
            
        elapsed_time = time.time() - start_time
        log_success(f"蝴蝶影视 编译总流水线平稳运行结束！【编译快报总览】:")
        print(f"\033[94m"
              f"  ⏱️  Compile Time : {elapsed_time:.2f} sec\n"
              f"  📺 Total Sites   : {site_cnt} channels\n"
              f"  📡 Total Lives   : {live_cnt} channels\n"
              f"  🥇 Total Parses  : {parse_cnt} objects\n"
              f"  💾 Output Weight : {file_size / 1024 / 1024:.2f} MB"
              f"\033[0m")
              
    except Exception as e:
        log_critical(f"核心编译主总线遭到未知突发崩溃: {e}", exc_info=True)

if __name__ == "__main__":
    main()
