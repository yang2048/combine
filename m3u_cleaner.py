# -*- coding: utf-8 -*-
"""
M3U 直播源存量巡检、清洗与高级重构脚本 (GitHub Actions 专属)
集成：双重缓存 + 同频道前3优选 + 多维加权评分 + 线程安全 + FFmpeg深层探测 + 标准化归一
"""

import os
import re
import json
import time
import threading
import requests
import subprocess
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 路径自动定位：指向 datas 文件夹下的文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "datas")
TARGET_M3U = os.path.join(DATA_DIR, "custom_lives.m3u")
INPUT_TXT = os.path.join(BASE_DIR, "channels.txt")
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")

# 配置项
ENABLE_CHECK = True            # 是否开启连通性校验
MAX_WORKERS = 15               # 并发检测线程数 (推荐 10-15)
TIMEOUT = 3                    # HTTP 超时时间 (秒)
ENABLE_FFMPEG = True           # 是否开启 FFmpeg 深层视频流探测 (需系统已安装 ffmpeg)
ENABLE_CACHE = True            # 是否开启检测结果缓存
CACHE_EXPIRATION = 86400        # 缓存有效期 (秒，默认 24 小时)
MIN_BITRATE = 600000           # 最小有效码率阈值 (bps，低于 600 kbps 自动剔除)
MAX_ROUTES_PER_CHANNEL = 3     # 单频道保留的最优线路上限数 (保留前 N 条)

# EPG 地址列表 (支持多 EPG 备用)
EPG_URLS = [
    "https://material.yang-1989.xyz/epg.xml.gz",
    "http://epg.51zmt.top:8000/e.xml.gz"
]

# 广告/劫持/失效重定向黑名单
AD_KEYWORDS = [
    "guanggao", "notice", "redirect", "error.m3u8", "ad.m3u8", 
    "welcome", "invalid", "vip_ad", "gg.m3u8", "test.m3u8", "解析失败"
]

# 线程锁：保护缓存与并发打印
CACHE_LOCK = threading.Lock()

# ----------------- 全局 Session 与 连接池配置 -----------------
def create_global_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=1,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(pool_connections=MAX_WORKERS * 2, pool_maxsize=MAX_WORKERS * 2, max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

GLOBAL_SESSION = create_global_session()

# ----------------- 缓存管理 (线程安全) -----------------
def load_cache() -> dict:
    if ENABLE_CACHE and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data: dict):
    if ENABLE_CACHE:
        os.makedirs(DATA_DIR, exist_ok=True)
        with CACHE_LOCK:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

def get_from_cache(norm_url: str, cache_data: dict):
    if not ENABLE_CACHE:
        return None
    with CACHE_LOCK:
        if norm_url in cache_data:
            item = cache_data[norm_url]
            if time.time() - item.get("timestamp", 0) < CACHE_EXPIRATION:
                return item
    return None

def update_cache(norm_url: str, is_valid: bool, reason: str, err_code: str, meta: dict, cache_data: dict):
    if not ENABLE_CACHE:
        return
    with CACHE_LOCK:
        cache_data[norm_url] = {
            "valid": is_valid,
            "reason": reason,
            "err_code": err_code,
            "timestamp": time.time(),
            "meta": meta
        }

# ----------------- 数据标准化与智能评分 -----------------
def normalize_url(url: str) -> str:
    """去重专用的 URL 标准化：剥离动态 Token / Sign / TS 等 Query 参数"""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        qs = parse_qs(parsed.query)
        filtered_qs = {k: v for k, v in qs.items() if k.lower() not in ['token', 'sign', 'ts', 'auth', 'key', '_t']}
        new_query = urlencode(filtered_qs, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    except Exception:
        return url

def normalize_channel_name(name: str) -> str:
    """频道名称标准化归一"""
    n = name.strip()
    cctv_match = re.search(r'(?:CCTV|中央|央视)[-_\s]*(\d+|13新闻|14少儿|15音乐|5\+体育赛事|17农业农村|7国防军事)', n, re.IGNORECASE)
    if cctv_match:
        num = cctv_match.group(1).upper()
        return f"CCTV-{num}"
    if re.search(r'中央一|央视一', n): return "CCTV-1"
    if re.search(r'中央二|央视二', n): return "CCTV-2"
    if re.search(r'中央三|央视三', n): return "CCTV-3"
    return n

def calculate_smart_score(height: int, bitrate: int, delay: float, codec: str) -> float:
    """更智能的多维综合权重评分计算 (Height + Bitrate + Delay + Codec Bonus)"""
    res_score = (height / 2160.0) * 400.0 if height else 100.0
    effective_bitrate = min(bitrate, 10000000) if bitrate else 1000000
    bitrate_score = (effective_bitrate / 10000000.0) * 300.0
    delay_score = max(0.0, (TIMEOUT - delay) / TIMEOUT) * 300.0
    codec_bonus = 150.0 if codec and ("hevc" in codec.lower() or "265" in codec.lower()) else 0.0

    return round(res_score + bitrate_score + delay_score + codec_bonus, 2)

def auto_classify(name: str, url: str) -> str:
    """自动高精度推导频道分类"""
    n_upper = name.strip().upper()
    u_lower = url.strip().lower()

    if re.search(r"(4K|8K|超高清)", n_upper) or "4k" in u_lower: return "4K/8K超清"
    if "🔞" in name or any(k in name for k in ["福利", "成人", "探花", "尤物"]): return "🔞福利专区"
    if "咪咕" in name or "咪视" in name or "migu" in u_lower or "/mg/" in u_lower: return "咪咕体育/直播"
    
    if re.search(r"^(CCTV|CGTN|CETV|CETN|中央新影|CEC|中央)", n_upper) or "cctv" in u_lower:
        if any(k in name for k in ["第一剧场", "风云剧场", "怀旧剧场", "电视指南", "世界地理", "兵器科技", "央视台球"]):
            return "央视数字付费"
        return "央视频道"

    if "卫视" in name and not any(k in name for k in ["香港", "凤凰", "大湾区", "星空", "人间", "唯心", "华藏", "三沙"]):
        return "卫视频道"

    hk_tw = ["翡翠台", "明珠台", "TVB", "凤凰", "NOW", "HOY", "ViuTV", "RTHK", "澳视", "澳门", "中视", "华视", "台视", "民视", "公视", "TVBS", "寰宇", "中天", "三立", "纬来", "东森", "星空卫视", "香港卫视", "大湾区卫视", "人间卫视", "三沙卫视", "美亚", "龙华", "靖天", "靖洋", "采昌"]
    if any(k in name for k in hk_tw): return "港台频道"

    glo = ["NHK", "CNN", "BBC", "EBS", "Arirang", "KCTV", "tvN", "CBC", "Fox", "Bloomberg", "France 24", "Al Jazeera", "RT", "韩国", "日本", "美国", "全球", "国际"]
    if any(k in name for k in glo): return "海外/国际频道"

    if name.startswith("NewTV") or "BESTV" in n_upper or "百视通" in name or "71edge.com" in u_lower:
        return "NewTV/百视通专区"

    if any(k in name for k in ["少儿", "卡通", "动漫", "动画", "柯南", "数码宝贝", "神奇宝贝", "蜡笔小新", "猫和老鼠", "七龙珠", "瑞克与莫蒂", "成龙历险记"]):
        return "动漫/少儿直播"

    if any(k in name for k in ["邵氏", "电影", "影院", "CHC", "峨眉", "美亚", "好莱坞", "专场", "片系列", "高分片", "热门片", "硬汉", "灾难", "科幻", "怪兽", "盗墓", "枪战"]):
        return "电影/影剧直播"

    if any(k in name for k in ["剧专区", "剧场", "武林外传", "四大名著", "亮剑", "潜伏", "庆余年", "家有儿女", "三国演义", "水浒传", "西游记", "狄仁杰", "父母爱情", "汉武大帝", "雍正王朝", "康熙王朝", "闯关东", "重温经典"]):
        return "电视/电视剧轮播"

    if any(k in name for k in ["综艺", "短剧", "小品", "喜剧", "好声音", "变形计", "客栈", "大侦探", "12道锋味", "陈翔六点半", "本山", "宋小宝", "贾玲", "沈腾", "脱口秀", "极限挑战", "奔跑吧"]):
        return "综艺/短剧直播"

    if any(k in name for k in ["手游", "端游", "单机", "游戏", "王者荣耀", "和平精英", "英雄联盟", "吃鸡", "穿越火线", "CF", "DNF", "炉石", "DOTA", "我的世界", "拳皇", "斗地主", "三角洲"]):
        return "游戏/单机直播"

    if any(k in name for k in ["音乐", "点歌", "电台", "DJ", "周杰伦", "双笙", "翻唱", "歌台", "轻音乐", "下饭音乐"]):
        return "音乐/DJ点歌台"

    if any(k in name for k in ["体育", "篮球", "足球", "斯诺克", "红牛", "皇马", "高尔夫", "网球", "台球", "竞速", "NBA", "UFC", "ESPN"]):
        return "体育/竞技直播"

    if any(k in name for k in ["女团", "热舞", "车模", "瑜伽", "颜老师", "舞台天才", "颜值", "钓鱼欧尼"]):
        return "娱乐/网红女团"

    if any(k in name for k in ["戏曲", "梨园", "曲艺", "财经", "点掌", "老年"]):
        return "老年/戏曲/财经"

    if any(k in name for k in ["ipanda", "熊猫", "监控", "上海G1503", "大道"]):
        return "监控/实景直播"

    provinces = ["北京", "上海", "天津", "重庆", "浙江", "江苏", "广东", "湖南", "湖北", "河南", "河北", "山东", "山西", "陕西", "安徽", "福建", "江西", "四川", "贵州", "云南", "黑龙江", "吉林", "辽宁", "广西", "海南", "甘肃", "宁夏", "青海", "新疆", "内蒙古", "西藏", "广州", "深圳", "杭州", "南京", "苏州", "无锡", "合肥", "福州", "厦门", "郑州", "洛阳", "武汉", "长沙", "成都", "西安"]
    if "台" in name or any(p in name for p in provinces) or any(k in name for k in ["新闻", "综合", "交通", "都市", "生活", "公共", "影视"]):
        return "地方直播/特色"

    return "其他精选"

def get_tv_headers(url: str) -> dict:
    """构建电视盒子专用 Headers"""
    parsed = urlparse(url)
    origin_host = f"{parsed.scheme}://{parsed.netloc}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SmartTV Build/RQ3A.210905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.105 Mobile Safari/537.36 ExoPlayer/2.18.1',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8',
        'Connection': 'keep-alive',
        'Referer': origin_host + '/',
        'Origin': origin_host
    }

    if "migu" in url.lower():
        headers['User-Agent'] = 'MiguVideo/3.9.0 (Android; SmartTV)'
        headers['Referer'] = 'https://www.miguvideo.com/'

    return headers

def check_ffprobe_valid(url: str, headers: dict) -> tuple:
    """使用 ffprobe 检测视频流编码、帧率、分辨率及码率"""
    user_agent = headers.get('User-Agent', '')
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-user_agent', user_agent,
        '-show_streams', '-show_format',
        '-timeout', str(TIMEOUT * 1000000), url
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT + 2)
        data = json.loads(res.stdout)
        
        streams = data.get('streams', [])
        format_info = data.get('format', {})
        
        bitrate = int(format_info.get('bit_rate', 0)) if format_info.get('bit_rate') else 0

        for stream in streams:
            if stream.get('codec_type') == 'video':
                fps_eval = stream.get('r_frame_rate', '0/1')
                fps = 0
                if '/' in fps_eval:
                    num, den = map(float, fps_eval.split('/'))
                    fps = num / den if den > 0 else 0

                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                codec_name = stream.get('codec_name', '').lower()

                if not bitrate and stream.get('bit_rate'):
                    bitrate = int(stream.get('bit_rate'))

                if fps >= 10:
                    return True, width, height, codec_name, bitrate
    except Exception:
        pass
    return False, 0, 0, "", 0

def extract_first_ts_url(m3u8_url: str, m3u8_text: str, headers: dict) -> str:
    """智能解析 M3U8 文本，提取第一个真正的 TS 切片 URL"""
    lines = [line.strip() for line in m3u8_text.splitlines() if line.strip() and not line.startswith("#")]
    if not lines:
        return None

    first_line = lines[0]
    full_url = urljoin(m3u8_url, first_line)

    if ".m3u8" in first_line.lower() or "m3u8" in full_url.lower():
        try:
            sub_res = GLOBAL_SESSION.get(full_url, headers=headers, timeout=TIMEOUT, stream=True)
            if sub_res.status_code < 400:
                sub_text = sub_res.raw.read(4096).decode('utf-8', errors='ignore')
                sub_lines = [l.strip() for l in sub_text.splitlines() if l.strip() and not l.startswith("#")]
                if sub_lines:
                    return urljoin(full_url, sub_lines[0])
        except Exception:
            pass

    return full_url

def check_channel_valid(item: dict, cache_data: dict) -> tuple:
    """全套高阶融合校验 (支持成功/失败双重缓存 + 线程锁保护)"""
    url = item["url"]
    norm_url = item["norm_url"]
    headers = get_tv_headers(url)

    # 1. 优先读取缓存
    cached_node = get_from_cache(norm_url, cache_data)
    if cached_node:
        is_valid = cached_node["valid"]
        reason = cached_node.get("reason", "Cache")
        err_code = cached_node.get("err_code", "CACHE")
        if is_valid:
            item.update(cached_node.get("meta", {}))
            return item, True, f"{reason} [缓存]", err_code
        else:
            return item, False, f"{reason} [缓存]", err_code

    # 特殊协议处理
    if url.startswith("rtp://") or url.startswith("udp://"):
        item['delay'] = 0.1
        item['score'] = 500.0
        update_cache(norm_url, True, "PASS", "SUCCESS", item, cache_data)
        return item, True, "PASS", "SUCCESS"

    # 2. 规则判断：URL 黑名单
    hit_kw = next((kw for kw in AD_KEYWORDS if kw in url.lower()), None)
    if hit_kw:
        reason = f"URL命中广告黑名单[{hit_kw}]"
        update_cache(norm_url, False, reason, "AD", {}, cache_data)
        return item, False, reason, "AD"

    start_time = time.time()
    try:
        res = GLOBAL_SESSION.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=True)
        if res.status_code >= 400:
            reason = f"HTTP响应错误({res.status_code})"
            update_cache(norm_url, False, reason, "HTTP_ERROR", {}, cache_data)
            return item, False, reason, "HTTP_ERROR"

        content_bytes = res.raw.read(4096)
        content_head = content_bytes.decode('utf-8', errors='ignore').lower()

        # 3. 规则判断：内容广告关键词
        hit_txt_kw = next((kw for kw in AD_KEYWORDS if kw in content_head), None)
        if hit_txt_kw:
            reason = f"内容包含广告关键词[{hit_txt_kw}]"
            update_cache(norm_url, False, reason, "AD", {}, cache_data)
            return item, False, reason, "AD"

        # 4. 规则判断：疑似短视频广告
        durations = re.findall(r'#extinf:([\d\.]+)', content_head)
        if durations:
            total_time = sum(float(d) for d in durations)
            if total_time < 6 and len(durations) <= 2:
                reason = f"疑似短时广告片(时长{total_time:.1f}s)"
                update_cache(norm_url, False, reason, "AD", {}, cache_data)
                return item, False, reason, "AD"

        # 5. 智能 TS 校验
        first_ts_url = extract_first_ts_url(url, content_head, headers)
        if first_ts_url and not first_ts_url.endswith(".m3u8"):
            try:
                ts_res = GLOBAL_SESSION.get(first_ts_url, headers=headers, timeout=TIMEOUT, stream=True)
                if ts_res.status_code < 400:
                    chunk = next(ts_res.iter_content(chunk_size=65536), None)
                    if not chunk or len(chunk) < 512:
                        reason = "TS切片数据包空/过小"
                        update_cache(norm_url, False, reason, "EMPTY_TS", {}, cache_data)
                        return item, False, reason, "EMPTY_TS"
                else:
                    if not ENABLE_FFMPEG:
                        reason = f"TS切片获取失败({ts_res.status_code})"
                        update_cache(norm_url, False, reason, "HTTP_ERROR", {}, cache_data)
                        return item, False, reason, "HTTP_ERROR"
            except Exception:
                if not ENABLE_FFMPEG:
                    reason = "TS切片连接超时/死链"
                    update_cache(norm_url, False, reason, "TIMEOUT", {}, cache_data)
                    return item, False, reason, "TIMEOUT"

        elapsed_delay = round(time.time() - start_time, 2)
        item['delay'] = elapsed_delay

        # 6. FFmpeg 深入探测 (分辨率/码率/编码)
        if ENABLE_FFMPEG:
            is_valid, w, h, codec, bitrate = check_ffprobe_valid(url, headers)
            if not is_valid:
                reason = "FFmpeg未识别到有效视频流/无画面"
                update_cache(norm_url, False, reason, "FFMPEG_FAIL", {}, cache_data)
                return item, False, reason, "FFMPEG_FAIL"
            
            if bitrate > 0 and bitrate < MIN_BITRATE:
                reason = f"视频码率极低({bitrate//1000}kbps)"
                update_cache(norm_url, False, reason, "LOW_BITRATE", {}, cache_data)
                return item, False, reason, "LOW_BITRATE"

            item['width'] = w
            item['height'] = h
            item['codec'] = codec
            item['bitrate'] = bitrate

        # 多维加权评分计算
        item['score'] = calculate_smart_score(
            item.get('height', 720),
            item.get('bitrate', 0),
            elapsed_delay,
            item.get('codec', '')
        )

        meta_info = {
            "delay": item.get("delay"),
            "width": item.get("width", 0),
            "height": item.get("height", 0),
            "codec": item.get("codec", ""),
            "bitrate": item.get("bitrate", 0),
            "score": item.get("score", 0)
        }
        update_cache(norm_url, True, "PASS", "SUCCESS", meta_info, cache_data)

        return item, True, f"PASS ({elapsed_delay}s | 得分:{item['score']})", "SUCCESS"

    except requests.exceptions.Timeout:
        reason = f"HTTP连接超时({TIMEOUT}s)"
        update_cache(norm_url, False, reason, "TIMEOUT", {}, cache_data)
        return item, False, reason, "TIMEOUT"
    except Exception:
        reason = "网络请求失败"
        update_cache(norm_url, False, reason, "NET_ERROR", {}, cache_data)
        return item, False, reason, "NET_ERROR"

def parse_m3u_channels(m3u_path: str) -> list:
    """从存量 M3U 文件中解析频道信息"""
    channels = []
    if not os.path.exists(m3u_path):
        return channels

    current_extinf = None
    with open(m3u_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue

            if line.startswith("#EXTINF"):
                current_extinf = line
                continue

            if line.startswith(("http://", "https://", "rtmp://", "rtp://")):
                if current_extinf:
                    name_match = re.search(r',([^,]+)$', current_extinf)
                    raw_name = name_match.group(1).strip() if name_match else "未命名频道"
                    # 清理之前添加的标签标记 [1080P/HEVC]
                    raw_name = re.sub(r'\s*\[.*?\]', '', raw_name).strip()
                    name = normalize_channel_name(raw_name)
                    
                    group_match = re.search(r'group-title="([^"]+)"', current_extinf)
                    group = group_match.group(1) if group_match else auto_classify(name, line)

                    channels.append({"name": name, "url": line, "group": group, "norm_url": normalize_url(line)})
                    current_extinf = None
    return channels

def parse_channels():
    """合并解析 `datas/custom_lives.m3u` 与根目录 `channels.txt`，并全局去重"""
    channels = []
    seen_urls = set()

    # 1. 读取存量 TARGET_M3U
    old_channels = parse_m3u_channels(TARGET_M3U)
    for ch in old_channels:
        if ch["norm_url"] not in seen_urls:
            seen_urls.add(ch["norm_url"])
            channels.append(ch)

    old_count = len(channels)
    if old_count > 0:
        print(f"📦 已载入存量文件 '{TARGET_M3U}' 线路 {old_count} 条")

    # 2. 读取补给文本 INPUT_TXT
    if os.path.exists(INPUT_TXT):
        current_txt_genre = None
        temp_extinf_name = None
        temp_extinf_group = None

        with open(INPUT_TXT, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue

                if line.startswith("#EXTINF"):
                    group_match = re.search(r'group-title="([^"]+)"', line)
                    if group_match:
                        temp_extinf_group = group_match.group(1)
                    if "," in line:
                        temp_extinf_name = line.split(",")[-1].strip()
                    continue

                if "#genre#" in line:
                    raw_genre = line.split(",")[0].strip()
                    clean_genre = re.sub(r'[\u2600-\u27BF\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF]', '', raw_genre).strip()
                    if clean_genre:
                        current_txt_genre = clean_genre
                    continue

                if line.startswith("#"): continue

                name, url = None, None
                if temp_extinf_name:
                    name, url = temp_extinf_name, line
                    group = temp_extinf_group if temp_extinf_group else auto_classify(name, url)
                    temp_extinf_name, temp_extinf_group = None, None
                else:
                    parts = re.split(r'[,，\t\s]+', line, maxsplit=1)
                    if len(parts) >= 2:
                        name, url = parts[0].strip(), parts[1].strip()
                        group = current_txt_genre if current_txt_genre else auto_classify(name, url)

                if name and url:
                    if "$" in name: name = name.split("$")[0].strip()
                    if "$" in url: url = url.split("$")[0].strip()

                    name = normalize_channel_name(name)
                    norm_u = normalize_url(url)

                    if url.startswith(("http://", "https://", "rtmp://", "rtp://")):
                        if norm_u not in seen_urls:
                            seen_urls.add(norm_u)
                            channels.append({"name": name, "url": url, "group": group, "norm_url": norm_u})

    return channels

def print_statistics(total: int, valid: int, filtered_valid: int, stats_counter: dict, delays: list):
    """打印详细统计报告"""
    avg_delay = round(sum(delays) / len(delays), 2) if delays else 0
    print("\n" + "=" * 30 + " 📊 线路检测与统计报告 " + "=" * 30)
    print(f" 🔹 线路总数: {total} 条")
    print(f" ✅ 有效线路: {valid} 条 (保留率: {round(valid/total*100, 1) if total else 0}%)")
    print(f" 🏆 优选导出: {filtered_valid} 条 (同频道最多保留前 {MAX_ROUTES_PER_CHANNEL} 条)")
    print(f" ------------------------------------")
    print(f" 🎯 广告/劫持拦截: {stats_counter.get('AD', 0)} 条")
    print(f" ⏱️  网络请求超时: {stats_counter.get('TIMEOUT', 0)} 条")
    print(f" 🚫 HTTP 状态错误: {stats_counter.get('HTTP_ERROR', 0)} 条")
    print(f" 🎬 FFmpeg 探测失败: {stats_counter.get('FFMPEG_FAIL', 0)} 条")
    print(f" 📉 极低码率过滤:   {stats_counter.get('LOW_BITRATE', 0)} 条")
    print(f" ⚡ 平均响应延迟:   {avg_delay}s")
    print("=" * 80 + "\n")

def main():
    channels = parse_channels()
    total_raw = len(channels)
    print(f"📊 解析与合并完成！标准化去重后共保留 {total_raw} 条唯一频道线路...\n")

    if total_raw == 0:
        print("❌ 未发现有效频道，退出。")
        return

    valid_channels = []
    cache_data = load_cache()

    stats_counter = {"AD": 0, "TIMEOUT": 0, "HTTP_ERROR": 0, "FFMPEG_FAIL": 0, "LOW_BITRATE": 0, "NET_ERROR": 0, "EMPTY_TS": 0}
    delays = []

    if ENABLE_CHECK:
        print(f"⚡ 已开启并发检测 (线程数: {MAX_WORKERS}, 成功/失败双重缓存 + 线程安全保护)...")
        print("=" * 80)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(check_channel_valid, ch, cache_data) for ch in channels]
            completed = 0
            for future in as_completed(futures):
                item, is_valid, reason, err_code = future.result()
                completed += 1
                if is_valid:
                    valid_channels.append(item)
                    if 'delay' in item and item['delay'] > 0:
                        delays.append(item['delay'])
                    print(f"[{completed}/{total_raw}] ✅ 保留: {item['name']} | {reason} ({len(valid_channels)}/{total_raw})")
                else:
                    stats_counter[err_code] = stats_counter.get(err_code, 0) + 1
                    print(f"[{completed}/{total_raw}] ❌ 剔除: {item['name']} | 原因: {reason}")
        print("=" * 80)
        print("✅ 连通性检测完毕！\n")
    else:
        print("⏩ 已跳过连通性检测，直接导出所有频道。")
        valid_channels = channels

    save_cache(cache_data)

    # ----------------- 线路智能评分排序 & 同频道限制前 3 条 -----------------
    valid_channels.sort(key=lambda x: x.get('score', 0), reverse=True)

    channel_counts = {}
    top_channels = []

    for ch in valid_channels:
        c_name = ch['name']
        count = channel_counts.get(c_name, 0)
        if count < MAX_ROUTES_PER_CHANNEL:
            top_channels.append(ch)
            channel_counts[c_name] = count + 1

    # 按照 分类 + 名称 重新整理排版输出
    top_channels.sort(key=lambda x: (x.get('group', ''), x.get('name', '')))

    # 保证存储文件夹存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 构建 M3U 文件
    epg_header = f'#EXTM3U x-tvg-url="{",".join(EPG_URLS)}"'
    m3u_lines = [epg_header]

    for ch in top_channels:
        tag_info = []
        if ch.get('height'): tag_info.append(f"{ch['height']}P")
        if ch.get('codec') and ("hevc" in ch['codec'].lower() or "265" in ch['codec'].lower()): tag_info.append("HEVC")
        
        tag_str = f" [{'/'.join(tag_info)}]" if tag_info else ""
        m3u_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}{tag_str}')
        m3u_lines.append(ch["url"])

    with open(TARGET_M3U, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    # 打印最终统计数据
    print_statistics(total_raw, len(valid_channels), len(top_channels), stats_counter, delays)
    print(f"🎉 处理完成！已导出优选线路至 '{TARGET_M3U}'")

if __name__ == "__main__":
    main()
