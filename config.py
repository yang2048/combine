# -*- coding: utf-8 -*-
"""
蝴蝶影视 缝合矩阵 - 终极动态解耦配置文件
"""
import json
from pathlib import Path

# ====================================================================
# 📂 【零、路径与动态配置中心 (优先读取 settings.json)】
# ====================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "datas"
SETTINGS_FILE_PATH = DATA_DIR / "settings.json"
SOURCE_DIR = BASE_DIR / "source"
DOCS_DIR = BASE_DIR / "docs"

_dynamic_settings = {}
if SETTINGS_FILE_PATH.exists():
    try:
        _dynamic_settings = json.loads(SETTINGS_FILE_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"⚠️ 读取 settings.json 失败，将降级使用默认配置: {e}")

def get_setting(key, default_val):
    return _dynamic_settings.get(key, default_val)

# ====================================================================
# 🆔 【一、工程版本与全局控制参数定义】
# ====================================================================
VERSION = "3.4.0"
BUILD_DATE = "2026.09.09"

GLOBAL_SPIDER_JAR = get_setting("GLOBAL_SPIDER_JAR", "https://cnb.cool/fish2035/xs/-/git/raw/main/spider.jar")
INSERT_POS = get_setting("INSERT_POS", 0)           
SITE_INSERT_POS = get_setting("SITE_INSERT_POS", 0) 
DEFAULT_LOGO_URL = get_setting("DEFAULT_LOGO_URL", "https://img.naixiai.cn/2026/06/18/IMG_6638.jpeg")


TG_TIMEOUT = 15          
TOKEN_LENGTH = 3         
TG_MAX_DISPLAY = 15      

# 是否启用"每月密码后缀"。False 时输出文件名为固定 BASE_OUTPUT_FULL/CLEAN(与历史行为一致)；
# True 时输出文件名追加当月随机密锁(如 蝴蝶影视全量版2la.json)。
ENABLE_PASSWORD_SUFFIX = get_setting("ENABLE_PASSWORD_SUFFIX", False)      

# ====================================================================
# 🌐 【二、全局核心路径与网络代理配置区】
# ====================================================================

LOCK_FILE_PATH = DATA_DIR / "控制开关.txt"
TRACKER_PATH = DATA_DIR / "最新接口文件名.txt"

GITHUB_PROXY = ""

# lz 福利源相对路径 ./ / ./py/ / ./js/ 的重写目标绝对地址
LZ_RAW_BASE = "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz"

# ====================================================================
# 📦 【二点五、上游源声明式配置中心】
#    ➕ 扩展 source 目录：只需在 source 下新增 json，并在此追加一条声明即可自动并入编译
# ====================================================================
# 每个源支持的声明字段说明：
#   as_base           -> 作为最终输出对象骨架(继承 spider/wallpaper/flags 等顶层字段)，全局仅允许一个
#   collect           -> 需要采集的字段，可选值：sites / lives / parses / rules / headers / doh
#   clean_and_suffix  -> 对 sites/lives 名称清洗上游脏词(UPSTREAM_DIRTY_WORDS)并追加 TG 后缀(MY_TG_SUFFIX)
#   nsfw_sites_only   -> 仅提取含 🔞 的成人站点，并配合 api_prefix_base 重写相对 api 路径
#   api_prefix_base   -> nsfw_sites_only 模式下相对路径的替换目标绝对地址
#   rules/headers/doh -> 源级自定义直通值，与 json 采集结果合并(可覆盖 json 中的 headers)
#   注意：列表顺序即 sites/lives/parses 的合并优先级顺序（影响同分类内的相对点位）。
UPSTREAM_SOURCES = [
    {
        "name": "haitun",
        "file": "haitun.json",
        "collect": ["sites", "lives", "parses"],
        "clean_and_suffix": True,
    },
    {
        "name": "lz",
        "file": "lz.json",
        "collect": ["sites", "parses"],
        "nsfw_sites_only": True,
        "api_prefix_base": LZ_RAW_BASE,
    },
    {
        "name": "cnb",
        "file": "cnb.json",
        "as_base": True,
        "collect": ["sites", "lives", "parses", "rules", "doh"],
    },
    {
        "name": "mafly",
        "file": "mafly.json",
        "collect": ["sites", "lives", "parses"],
        # 如需采集 mafly 自带 headers，将 "headers" 加入 collect；或直接在此自定义：
        # "headers": {"User-Agent": "okhttp/5.3.2"},
        # "doh": [{"name": "AliDNS", "url": "https://dns.alidns.com/dns-query"}],
    },
]

# ====================================================================
# 🚫 【三、双版本过滤依据、广告拦截与恶意杂质直接清洗区】
# ====================================================================
BLOCK_KEYWORDS = tuple(get_setting("BLOCK_KEYWORDS", ["羊壳", "弹幕", "Gather", "Mytv"]))
UPSTREAM_DIRTY_WORDS = tuple(get_setting("UPSTREAM_DIRTY_WORDS", ['🐬', '海豚影视', '海豚', '完全免费，如有收费的都是骗子', '交流群 TG：@hshsjk9']))
NSFW_KEYWORDS = tuple(get_setting("NSFW_KEYWORDS", ["🔞", "福利", "探花", "约炮", "色播", "av", "爆料", "欧美", "蜜桃", "三级片"]))
BLOCK_MALICIOUS_KEYWORDS = tuple(get_setting("BLOCK_MALICIOUS_KEYWORDS", ["日本女优", "日本女友"]))

AD_HOSTS_LIST = ["vip.wwgz.cn", "lziplayer.com", "m3u8.apibdzy.com", "cj.ffzyapi.com", "api.hbzyapi.com"]

# ====================================================================
# 🔍 【四、全局搜索与分类规则控制面板】
# ====================================================================
NO_SEARCH_KEYWORDS = get_setting("NO_SEARCH_KEYWORDS", [])
NO_SEARCH_KEYS = get_setting("NO_SEARCH_KEYS", ["js_douban", "豆瓣", "本地", "配置中心", "版本信息", "push_agent"])
NO_QUICK_SEARCH_KEYS = get_setting("NO_QUICK_SEARCH_KEYS", ["js_douban", "配置中心"])

CATEGORY_RULES = get_setting("CATEGORY_RULES", {
    "短剧": ["短剧", "剧场"],
    "动漫": ["动漫", "新番", "anime", "a1"],
    "网盘/磁力": ["磁力", "索", "盘", "云盘", "4k"],
    "体育/直播": ["体育", "球", "直播"],
    "少儿": ["少儿", "课堂", "教学", "教育"],
    "音乐": ["音乐", "网易云", "听书", "唱会", "fm", "相声", "小品", "戏曲", "dj"]
})

# 成人(福利)站点判定：name 命中 OR key(小写) 命中
NSFW_NAME_KEYWORDS = tuple(get_setting("NSFW_NAME_KEYWORDS", ["🔞", "色播", "瓜", "爆料"]))
NSFW_KEY_KEYWORDS = tuple(get_setting("NSFW_KEY_KEYWORDS", ["av", "chat", "cam", "panda", "video", "md"]))

# 站点最终输出的固定分类顺序（决定大屏端分类点位重排顺序）
ORDERED_CATEGORIES = ["综合", "短剧", "动漫", "体育/直播", "少儿", "音乐", "网盘/磁力", "福利"]

# 命中后自动关闭搜索的分类
NO_SEARCH_CATEGORIES = ["少儿", "音乐"]

# ====================================================================
# 🏷️ 【四点五、站点名称末尾分类打标规则面板】
# ====================================================================
CATEGORY_TAG_MAP = {
    "综合": "[合]",
    "短剧": "[专]",
    "动漫": "[专]",
    "体育/直播": "[专]",
    "少儿": "[专]",
    "音乐": "[专]",
    "网盘/磁力": "[磁]",
    "福利": "[密]",
}

# 打标判定词表（按优先级顺序命中）：adult_name 福利 / official_name 官方 / tool 辅助 / app / netdisk 磁力 / v4k 高清
TAG_RULES = {
    "adult_name": ["🔞", "成人", "伦理", "福利"],
    "official_name": ["优酷", "爱奇艺", "腾讯视频", "芒果", "哔哩", "1905", "豆瓣"],
    "tool_keys": {"js_douban", "配置中心", "push_agent", "Nostr", "Nostr2", "本地", "预告", "版本信息", "工具"},
    "tool_name": ["配置", "推送", "版本", "预告", "搜索"],
    "app_name": ["APP", "app"],
    "netdisk_name": ["网盘", "云盘", "磁力"],
    "v4k_name": ["4K", "4k", "高清"],
}

# ====================================================================
# 👑 【五、专属品牌与视觉定制区】
# ====================================================================
MY_QQ_GROUP = ""
MY_PROMO_CHANNEL = ""
MY_TG_SUFFIX = "｜"
LOGO_PREFIX = "🦋"

WALLPAPER_FULL = "https://img.naixiai.cn/2026/wallpapers/full_vip.jpg"
WALLPAPER_CLEAN = "https://img.naixiai.cn/2026/wallpapers/home_clean.jpg"

HOT_VIDEO_KEY = get_setting("HOT_VIDEO_KEY", "js_douban")
# 如果 settings.json 里设置了，就用 settings 的；否则兜底使用组装名称
HOT_VIDEO_SITE_NAME = get_setting("HOT_VIDEO_SITE_NAME", f"豆瓣(js),该接口完全免费，如有收费都是骗子｜{MY_TG_SUFFIX.strip('｜')}")

MY_NAME_REPLACEMENTS = {}

PATH_REPLACEMENTS = {
    r'\./spider\.jar': 'https://cnb.cool/fish2035/xs/-/git/raw/main/spider.jar',
    r'\./XBPQ/': 'https://cnb.cool/fish2035/xs/-/git/raw/main/XBPQ/',
    r'\./XYQHiker': 'https://cnb.cool/fish2035/xs/-/git/raw/main/XYQHiker',
    r'\./js/': 'https://cnb.cool/fish2035/xs/-/git/raw/main/js/',
    r'\./json/': 'https://cnb.cool/fish2035/xs/-/git/raw/main/json/',
    r'\./py/': 'https://cnb.cool/fish2035/xs/-/git/raw/main/py/',
    r'http://127\.0\.0\.1:9978/file/TVBox/logo\.png': DEFAULT_LOGO_URL
}

# ====================================================================
# 🔒 【六、双版本输出控制与“金蝉脱壳”大轰炸配置区】
# ====================================================================
BASE_OUTPUT_FULL = "蝴蝶影视全量版"
BASE_OUTPUT_CLEAN = "蝴蝶影视纯净版"

TRAP_NOTICE_TEXT = f"⚠️ 警告：关注Tg频道（{MY_PROMO_CHANNEL}）获取最新接口密码\n\n当前专线已过期断流！老链接已彻底作废！"
TRAP_WARNING_TEXT = f"👑 特别提示：关注Tg频道（{MY_PROMO_CHANNEL}）获取最新接口"
TRAP_SITE_NAME_1 = f"🚨 ⚠️ 警告：关注Tg频道（{MY_PROMO_CHANNEL}）获取最新接口密码\n\n当前专线已过期断流！老链接已彻底作废！🚨 当前专线密码已过期断流！"
TRAP_SITE_NAME_2 = f"🚨 ⚠️ 警告：关注Tg频道（{MY_PROMO_CHANNEL}）获取最新接口密码\n\n当前专线已过期断流！老链接已彻底作废！"
TRAP_LIVE_GROUP = "🚨 接口过期断流 ｜ 提示"
TRAP_LIVE_CHANNEL = f"👉 线路已过期 ➡️ 关注Tg频道（{MY_PROMO_CHANNEL}）获取最新接口密码\n\n当前专线已过期断流！老链接已彻底作废！"

# ====================================================================
# 📡 【七、客户端通知弹窗与 DOH/JS 注入高级规则配置区】
# ====================================================================
THANKS_WARNING = f"\n\n👑 🚨 重要提示：谨防诈骗·禁止非法倒卖"
WELCOME_NOTICE_FULL = "👑 欢迎使用【缝合怪】！本接口结合多方大底包无损重排而成，干净流畅."
WELCOME_NOTICE_CLEAN = "🏡 欢迎使用【缝合怪】！本接口已全面过滤敏感、擦边和福利内容，全家老少看电视更安全、更绿色！"

ALI_DOH_CONFIG = {"name": "AliDNS", "url": "https://dns.alidns.com/dns-query", "ips": ["223.5.5.5", "223.6.6.6"]}

# 自定义全局请求 headers（合并进最终输出顶层 headers，优先级最高）
CUSTOM_HEADERS = get_setting("CUSTOM_HEADERS", {})

# 自定义附加 DOH 节点（合并进最终输出 doh 列表）
CUSTOM_DOH = get_setting("CUSTOM_DOH", [])

CUSTOM_AD_BLOCK_JS = [
    "console.log('蝴蝶影视 WebView 去广告模块启动');",
    "window.addEventListener('DOMContentLoaded', function() {",
    "   document.querySelectorAll('video').forEach(v => { v.muted = true; v.play().catch(e=>{}); });",
    "   Function.prototype.__constructor__ = Function.prototype.constructor;",
    "   Function.prototype.constructor = function() { if (arguments && typeof arguments[0] === 'string' && arguments[0].includes('debugger')) { return function(){}; } return Function.prototype.__constructor__.apply(this, arguments); };",
    "});",
    "setInterval(() => { let selectors = ['.adv-class', '.pop-banner', '#notice-modal', '[id*=\"partner\"]', '[class*=\"baidu\"]', 'iframe[src*=\"game\"]', 'iframe[src*=\"bet\"]', '#pop-ad', '.sidebar-ads', 'a[href*=\"999\"]']; selectors.forEach(sel => { document.querySelectorAll(sel).forEach(el => el.remove()); }); }, 400);"
]

TG_PWD_MSG_TEMPLATE = (
    "🔔 *蝴蝶影视全量版 · 全新硬核双通道密码锁发布* 🔔\n\n"
    "📅 *生效时间*：`{current_time}` (北京时间)\n"
    "🔑 *全新专线密锁*：`{current_token}`\n\n"
    "🚀 *重要提示*：\n密码锁已成功交替！旧接口已全线开启【金蝉脱壳】大轰炸，老链接彻底作废，请及时复制下方对应通道的最新链接！\n\n"
    "🔞 *最新【蝴蝶影视全量版】矩阵订阅*：\n"
    "`https://r2.xdev.cc/tvbox/蝴蝶影视全量版{current_token}.json`\n\n"
    "🏡 *最新【蝴蝶影视纯净版】客厅订阅*：\n"
    "`https://r2.xdev.cc/tvbox/蝴蝶影视纯净版{current_token}.json`\n\n"
    f"👑 矩阵连接已在后台全自动换锁，请及时前往电视端更新。若电视端遇到断流请尝试重启软件或前往TG频道（{MY_PROMO_CHANNEL}）获取支持！"
)

TG_UPDATE_MSG_TEMPLATE = (
    "🔔 *蝴蝶影视全量版 缝合矩阵接口变更通知* 🔔\n\n"
    "📅 *更新时间*：{current_time} (北京时间)\n"
    "🚀 *变动说明*：检测到上游数据源更新或手工区调整，双版本配置已全自动编译上链！\n\n"
    "{detail_msg}\n\n"
    "📡 *【 最新多版本订阅矩阵 (点击可自动复制)】*：\n\n"
    "🔞 *最新【蝴蝶影视全量版】矩阵订阅*：\n"
    "`https://r2.xdev.cc/tvbox/蝴蝶影视全量版{current_token}.json`\n\n"
    "🏡 *最新【蝴蝶影视纯净版】客厅订阅*：\n"
    "`https://r2.xdev.cc/tvbox/蝴蝶影视纯净版{current_token}.json`\n\n"
    f"👑 全量版与纯净版已在后台无缝更新。更新配置即可，若遇到断流请尝试重启软件或及时前往TG频道（{MY_PROMO_CHANNEL}）获取当前最新密码锁！"
)

# ====================================================================
# 🖥️ 【八、Cloudflare Pages 可视化运维控制台 SPA HTML 模板】
# ====================================================================
DASHBOARD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" class="h-full bg-slate-900">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蝴蝶影视 - 矩阵运维控制台</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        [x-cloak] {{ display: none !important; }}
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; }}
        ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
    </style>
</head>

<body class="h-full text-slate-200 flex flex-col font-sans overflow-hidden">

    <!-- 顶部 Header Bar -->
    <header class="bg-slate-800 border-b border-slate-700 h-16 flex items-center justify-between px-4 sm:px-6 flex-shrink-0 z-20">
        <div class="flex items-center gap-3">
            <span class="text-2xl">🦋</span>
            <div>
                <h1 class="text-base font-bold text-white leading-tight">蝴蝶影视 缝合矩阵运维控制台</h1>
                <p class="text-xs text-slate-400">Core Engine V{version} | Build: {build_time}</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <div id="authStatusBadge" class="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <i class="fa-solid fa-key text-[10px]"></i>
                <span id="authStatusText">未绑定 GitHub Token</span>
            </div>

            <button onclick="openTokenModal()" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-xs font-semibold rounded-lg text-slate-200 transition flex items-center gap-1.5 border border-slate-600">
                <i class="fa-solid fa-user-gear"></i>
                <span>鉴权设置</span>
            </button>
        </div>
    </header>

    <div class="flex flex-1 h-[calc(100vh-4rem)] overflow-hidden">
        
        <!-- 左侧 SideBar 导航 -->
        <aside class="w-16 sm:w-60 bg-slate-800/60 border-r border-slate-700/80 flex flex-col justify-between flex-shrink-0">
            <nav class="p-2 sm:p-3 space-y-1">
                <button onclick="switchTab('overview')" id="nav-overview" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-emerald-400 bg-slate-700/60">
                    <i class="fa-solid fa-chart-line text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">📊 运行概览</span>
                </button>

                <button onclick="switchTab('control')" id="nav-control" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-slate-400 hover:text-slate-200 hover:bg-slate-700/30">
                    <i class="fa-solid fa-sliders text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">⚙️ 控制中心</span>
                </button>

                <button onclick="switchTab('resources')" id="nav-resources" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-slate-400 hover:text-slate-200 hover:bg-slate-700/30">
                    <i class="fa-solid fa-boxes-stacked text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">📦 资源管理</span>
                </button>

                <button onclick="switchTab('inspect')" id="nav-inspect" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-slate-400 hover:text-slate-200 hover:bg-slate-700/30">
                    <i class="fa-solid fa-microscope text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">🔍 巡检中心</span>
                </button>

                <button onclick="switchTab('logs')" id="nav-logs" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-slate-400 hover:text-slate-200 hover:bg-slate-700/30">
                    <i class="fa-solid fa-terminal text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">📜 日志中心</span>
                </button>

                <button onclick="switchTab('settings')" id="nav-settings" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition text-slate-400 hover:text-slate-200 hover:bg-slate-700/30">
                    <i class="fa-solid fa-gear text-lg w-5 text-center"></i>
                    <span class="hidden sm:inline">🛠 系统设置</span>
                </button>
            </nav>

            <div class="p-3 border-t border-slate-700/50 hidden sm:block">
                <div class="text-[11px] text-slate-500 text-center">
                    Serverless Matrix Architecture<br>Powered by Cloudflare & GitHub
                </div>
            </div>
        </aside>

        <!-- 右侧主内容展示区域 -->
        <main class="flex-1 bg-slate-900 p-4 sm:p-6 overflow-y-auto">
            
            <!-- 1. 📊 运行概览 Tab -->
            <section id="tab-overview" class="tab-content space-y-6">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="bg-slate-800/80 rounded-xl p-4 border border-slate-700/60 shadow-lg">
                        <div class="text-xs font-medium text-slate-400 mb-1">点播频道总数</div>
                        <div class="text-2xl font-bold text-emerald-400">{site_cnt} <span class="text-xs font-normal text-slate-400">个</span></div>
                    </div>
                    <div class="bg-slate-800/80 rounded-xl p-4 border border-slate-700/60 shadow-lg">
                        <div class="text-xs font-medium text-slate-400 mb-1">直播源站总数</div>
                        <div class="text-2xl font-bold text-cyan-400">{live_cnt} <span class="text-xs font-normal text-slate-400">个</span></div>
                    </div>
                    <div class="bg-slate-800/80 rounded-xl p-4 border border-slate-700/60 shadow-lg">
                        <div class="text-xs font-medium text-slate-400 mb-1">解析接口总数</div>
                        <div class="text-2xl font-bold text-indigo-400">{parse_cnt} <span class="text-xs font-normal text-slate-400">个</span></div>
                    </div>
                    <div class="bg-slate-800/80 rounded-xl p-4 border border-slate-700/60 shadow-lg">
                        <div class="text-xs font-medium text-slate-400 mb-1">当前矩阵密锁</div>
                        <div class="text-xl font-bold text-amber-400 cursor-pointer select-none transition"
                             onclick="if(this.dataset.revealed==='true'){{this.innerText='🔒 *** 点击显示'; this.dataset.revealed='false';}}else{{this.innerText='{current_token}'; this.dataset.revealed='true';}}"
                             title="点击显示/隐藏">
                            🔒 *** 点击显示
                        </div>
                    </div>
                </div>

                <div class="bg-slate-800/80 rounded-xl p-5 border border-slate-700/60 shadow-lg">
                    <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-list-check text-emerald-400"></i>
                        已打包部署的订阅清单 ({file_num} 个)
                    </h3>
                    <div class="space-y-3">
{file_cards}
                    </div>
                </div>
            </section>

            <!-- 2. ⚙️ 控制中心 Tab -->
            <section id="tab-control" class="tab-content hidden space-y-6">
                <div class="bg-slate-800/80 rounded-xl p-6 border border-slate-700/60 shadow-lg space-y-6">
                    <div>
                        <h3 class="text-base font-bold text-white flex items-center gap-2">
                            <i class="fa-solid fa-bolt text-amber-400"></i>
                            快捷触发与一键运维
                        </h3>
                        <p class="text-xs text-slate-400 mt-1">通过 GitHub REST API 实时调度 Action 自动化矩阵构建总线或重置矩阵密锁。</p>
                    </div>
                    
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                        <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 space-y-3">
                            <div class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <i class="fa-solid fa-rotate text-emerald-400"></i>
                                常规手动编译
                            </div>
                            <p class="text-[11px] text-slate-400">保持当前密码锁不变，仅同步上游最新接口与手工区规则。</p>
                            <button onclick="triggerDispatch()" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20">
                                <i class="fa-solid fa-play"></i>
                                一键触发常规构建
                            </button>
                        </div>

                        <div class="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 space-y-3">
                            <div class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <i class="fa-solid fa-key text-amber-400"></i>
                                强行更换矩阵密锁 (炸旧换新)
                            </div>
                            <p class="text-[11px] text-slate-400">生成新 3 位随机锁并提交 Git，旧接口即刻触发陷阱轰炸并下发 TG 通知。</p>
                            <button onclick="resetMatrixToken()" class="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-amber-600/20">
                                <i class="fa-solid fa-arrows-rotate"></i>
                                强行生成新锁并重新编译
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            <!-- 3. 📦 资源管理 Tab -->
            <section id="tab-resources" class="tab-content hidden space-y-6">
                <div class="bg-slate-800/80 rounded-xl p-6 border border-slate-700/60 shadow-lg space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-700/80 pb-4">
                        <div>
                            <h3 class="text-base font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-filter text-cyan-400"></i>
                                全量矩阵规则与黑名单控制面板
                            </h3>
                            <p class="text-xs text-slate-400 mt-1">直接在线修改 datas/settings.json，自动提交 Git 仓库并触发重新编译。</p>
                        </div>
                        <button onclick="saveSettingsToGithub()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-blue-600/20">
                            <i class="fa-solid fa-floppy-disk"></i>
                            保存全量变更提交 Git
                        </button>
                    </div>
                    <!-- ⬇️⬇️⬇️ 【新加区域：6 个核心变量输入框】 ⬇️⬇️⬇️ -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 border-b border-slate-700/80 pb-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">GLOBAL_SPIDER_JAR (全局主蜘蛛 Jar 地址)</label>
                            <input type="text" id="input_global_spider_jar" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">DEFAULT_LOGO_URL (默认 Logo 图片地址)</label>
                            <input type="text" id="input_default_logo_url" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">SITE_INSERT_POS (手工点播源插入位置)</label>
                            <input type="number" id="input_site_insert_pos" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">INSERT_POS (手工直播源插入位置)</label>
                            <input type="number" id="input_insert_pos" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">HOT_VIDEO_KEY (首页置顶热门站 Key)</label>
                            <input type="text" id="input_hot_video_key" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-200 mb-1">HOT_VIDEO_SITE_NAME (首页置顶热门站显示名称)</label>
                            <input type="text" id="input_hot_video_site_name" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none">
                        </div>
                    </div>

                    <div class="space-y-5">
                        <div class="space-y-2">
                            <label class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                                BLOCK_KEYWORDS (全局名称/关键字黑名单)
                            </label>
                            <textarea id="json_block_keywords" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-emerald-400 font-mono focus:outline-none focus:border-blue-500" placeholder='["词1", "词2"]'></textarea>
                        </div>

                        <div class="space-y-2">
                            <label class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                                UPSTREAM_DIRTY_WORDS (上游强力广告剔除词)
                            </label>
                            <textarea id="json_upstream_dirty" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-cyan-400 font-mono focus:outline-none focus:border-blue-500" placeholder='["广告词1", "广告词2"]'></textarea>
                        </div>

                        <div class="space-y-2">
                            <label class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                                NSFW_KEYWORDS (纯净版客厅专线剔除词)
                            </label>
                            <textarea id="json_nsfw_keywords" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-amber-400 font-mono focus:outline-none focus:border-blue-500" placeholder='["🔞", "福利"]'></textarea>
                        </div>

                        <div class="space-y-2">
                            <label class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-rose-400"></span>
                                BLOCK_MALICIOUS_KEYWORDS (全线恶意杂质直接丢弃词)
                            </label>
                            <textarea id="json_malicious_keywords" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-rose-400 font-mono focus:outline-none focus:border-blue-500" placeholder='["恶意词1"]'></textarea>
                        </div>

                        <div class="space-y-2">
                            <label class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
                                NO_SEARCH_KEYWORDS (命中的站点自动关闭全局搜索 searchable = 0)
                            </label>
                            <textarea id="json_no_search_keywords" rows="6" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-indigo-400 font-mono focus:outline-none focus:border-blue-500" placeholder='["接口全名或关键词"]'></textarea>
                        </div>
                    </div>
                </div>
            </section>

            <!-- 4. 🔍 巡检中心 Tab -->
            <section id="tab-inspect" class="tab-content hidden space-y-6">
                <div class="bg-slate-800/80 rounded-xl p-6 border border-slate-700/60 shadow-lg space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-700/80 pb-4">
                        <div>
                            <h3 class="text-base font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-microscope text-indigo-400"></i>
                                多线程探针与全量接口实时巡检
                            </h3>
                            <p class="text-xs text-slate-400 mt-1">多并发探测当前最新全量 JSON 订阅中的点播接口与直播源可用性。</p>
                        </div>
                        
                        <div class="flex items-center gap-2">
                            <button onclick="startInspection()" id="btnStartInspect" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-2">
                                <i class="fa-solid fa-play"></i>
                                开始并发巡检
                            </button>
                            <button onclick="purgeDeadSites()" id="btnPurgeDead" class="hidden px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition items-center gap-2">
                                <i class="fa-solid fa-trash-can"></i>
                                一键拉黑剔除失效源
                            </button>
                        </div>
                    </div>

                    <div id="inspectStats" class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                            <div class="text-[11px] text-slate-400">已扫描 / 总数</div>
                            <div class="text-lg font-bold text-slate-200" id="stat_total">0 / 0</div>
                        </div>
                        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                            <div class="text-[11px] text-emerald-400">正常响应 (OK)</div>
                            <div class="text-lg font-bold text-emerald-400" id="stat_ok">0</div>
                        </div>
                        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                            <div class="text-[11px] text-amber-400">高延迟 (>2000ms)</div>
                            <div class="text-lg font-bold text-amber-400" id="stat_slow">0</div>
                        </div>
                        <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                            <div class="text-[11px] text-rose-400">失效 / 404 / 超时</div>
                            <div class="text-lg font-bold text-rose-400" id="stat_dead">0</div>
                        </div>
                    </div>

                    <div id="inspectConsole" class="bg-slate-950 rounded-xl p-4 border border-slate-800 text-xs font-mono space-y-1.5 max-h-[28rem] overflow-y-auto">
                        <div class="text-slate-500">// 点击上方“开始并发巡检”按钮启动网络探针...</div>
                    </div>
                </div>
            </section>

            <!-- 5. 📜 日志中心 Tab -->
            <section id="tab-logs" class="tab-content hidden space-y-6">
                <div class="bg-slate-800/80 rounded-xl p-6 border border-slate-700/60 shadow-lg space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-list-ol text-emerald-400"></i>
                        Git 提交与编译日志流
                    </h3>
                    <p class="text-xs text-slate-400">实时调取 GitHub Repo 最近 Commit 历史记录。</p>
                    <div id="commitLogsContainer" class="space-y-2 text-xs font-mono">
                        <div class="text-slate-500">点击拉取或载入中...</div>
                    </div>
                </div>
            </section>

            <!-- 6. 🛠 系统设置 Tab -->
            <section id="tab-settings" class="tab-content hidden space-y-6">
                <div class="bg-slate-800/80 rounded-xl p-6 border border-slate-700/60 shadow-lg space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-key text-amber-400"></i>
                        GitHub API Token 与凭据管理
                    </h3>
                    <p class="text-xs text-slate-400">配置 Personal Access Token (PAT)，赋予控制台对仓库的读写与 Workflow 执行权限。</p>

                    <div class="space-y-4 pt-2 max-w-xl">
                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">GitHub Personal Access Token (PAT)</label>
                            <input type="password" id="input_github_token" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none" placeholder="ghp_xxxxxxxxxxxx">
                        </div>

                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">GitHub 仓库 (Owner/Repo)</label>
                            <input type="text" id="input_github_repo" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none" placeholder="Godlike/Ly">
                        </div>

                        <div>
                            <label class="block text-xs font-medium text-slate-300 mb-1">默认分支 (Branch)</label>
                            <input type="text" id="input_github_branch" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none" value="main">
                        </div>

                        <button onclick="saveAuthSettings()" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition">
                            保存鉴权凭据到本地
                        </button>
                    </div>
                </div>
            </section>

        </main>
    </div>

    <!-- PAT 鉴权设置 Modal 弹窗 -->
    <div id="authModal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-800 rounded-2xl border border-slate-700 max-w-md w-full p-6 shadow-2xl space-y-4">
            <div class="flex justify-between items-center border-b border-slate-700 pb-3">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                    <i class="fa-solid fa-lock text-amber-400"></i>
                    配置 GitHub PAT 访问凭据
                </h3>
                <button onclick="closeTokenModal()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
            </div>
            
            <p class="text-xs text-slate-400 leading-relaxed">
                为实现控制台保存黑名单、一键编译等无感知运维操作，请填入具有 <code class="text-amber-400">repo</code> 及 <code class="text-amber-400">workflow</code> 权限的 GitHub Token。
            </p>

            <div class="space-y-3">
                <input type="password" id="modal_token" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none" placeholder="ghp_xxx 或 github_pat_xxx">
                <input type="text" id="modal_repo" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 focus:outline-none" placeholder="仓库路径: Godlike/Ly">
            </div>

            <div class="flex justify-end gap-2 pt-2">
                <button onclick="closeTokenModal()" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-xs font-medium rounded-lg text-slate-300">取消</button>
                <button onclick="saveModalAuth()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-xs font-medium rounded-lg text-white">确认并绑定</button>
            </div>
        </div>
    </div>

    <!-- 控制台核心 JS 逻辑流 -->
    <script>
    function switchTab(tabKey) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.nav-btn').forEach(el => {{
            el.classList.remove('text-emerald-400', 'bg-slate-700/60');
            el.classList.add('text-slate-400');
        }});

        const targetTab = document.getElementById('tab-' + tabKey);
        const targetNav = document.getElementById('nav-' + tabKey);
        if (targetTab) targetTab.classList.remove('hidden');
        if (targetNav) {{
            targetNav.classList.add('text-emerald-400', 'bg-slate-700/60');
            targetNav.classList.remove('text-slate-400');
        }}

        if (tabKey === 'resources') loadSettingsFromGithub();
        if (tabKey === 'logs') loadCommitLogs();
    }}

    function getStoredAuth() {{
        return {{
            token: localStorage.getItem('gh_pat') || '',
            repo: localStorage.getItem('gh_repo') || 'yang2048/combine',
            branch: localStorage.getItem('gh_branch') || 'master'
        }};
    }}

    function updateAuthUI() {{
        const auth = getStoredAuth();
        const badge = document.getElementById('authStatusBadge');
        const text = document.getElementById('authStatusText');
        
        if (auth.token && auth.repo) {{
            badge.classList.remove('bg-amber-500/10', 'text-amber-400', 'border-amber-500/20');
            badge.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20');
            text.innerText = 'GitHub Token 已就绪 (' + auth.repo + ')';
        }} else {{
            badge.classList.add('bg-amber-500/10', 'text-amber-400', 'border-amber-500/20');
            badge.classList.remove('bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20');
            text.innerText = '未绑定 Token (功能受限)';
        }}

        document.getElementById('input_github_token').value = auth.token;
        document.getElementById('input_github_repo').value = auth.repo;
        document.getElementById('input_github_branch').value = auth.branch;
    }}

    function openTokenModal() {{
        const auth = getStoredAuth();
        document.getElementById('modal_token').value = auth.token;
        document.getElementById('modal_repo').value = auth.repo;
        document.getElementById('authModal').classList.remove('hidden');
    }}

    function closeTokenModal() {{
        document.getElementById('authModal').classList.add('hidden');
    }}

    function saveModalAuth() {{
        const token = document.getElementById('modal_token').value.trim();
        const repo = document.getElementById('modal_repo').value.trim();
        if (token) localStorage.setItem('gh_pat', token);
        if (repo) localStorage.setItem('gh_repo', repo);
        closeTokenModal();
        updateAuthUI();
        alert('凭据已成功保存！');
    }}

    function saveAuthSettings() {{
        const token = document.getElementById('input_github_token').value.trim();
        const repo = document.getElementById('input_github_repo').value.trim();
        const branch = document.getElementById('input_github_branch').value.trim();
        localStorage.setItem('gh_pat', token);
        localStorage.setItem('gh_repo', repo);
        localStorage.setItem('gh_branch', branch);
        updateAuthUI();
        alert('系统设置已更新！');
    }}

    async function triggerDispatch() {{
        const auth = getStoredAuth();
        if (!auth.token || !auth.repo) {{
            alert('请先配置 GitHub PAT 与仓库路径！');
            return openTokenModal();
        }}

        if (!confirm('确定要发起一键手动编译吗？系统将在 GitHub Actions 后台启动流水线。')) return;

        const url = `https://api.github.com/repos/${{auth.repo}}/actions/workflows/auto-fetch.yml/dispatches`;
        
        try {{
            const res = await fetch(url, {{
                method: 'POST',
                headers: {{
                    'Authorization': `token ${{auth.token}}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ ref: auth.branch }})
            }});

            if (res.status === 204) {{
                alert('🚀 编译指令已成功成功下发！GitHub Actions 已开始运行！');
            }} else {{
                const errData = await res.json().catch(() => ({{}}));
                alert(`⚠️ 触发失败 (${{res.status}}): ${{errData.message || '请检查 YAML 文件名称或 Token 权限'}}`);
            }}
        }} catch (e) {{
            alert('请求发生错误: ' + e.message);
        }}
    }}

    async function resetMatrixToken() {{
        const auth = getStoredAuth();
        if (!auth.token || !auth.repo) {{
            alert('请先配置 GitHub PAT 与仓库路径！');
            return openTokenModal();
        }}

        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let newToken = '';
        for (let i = 0; i < 3; i++) {{
            newToken += chars.charAt(Math.floor(Math.random() * chars.length));
        }}

        const inputToken = prompt('请输入想要设置的新密锁（直接回车将随机生成 3 位字符）:', newToken);
        if (inputToken === null) return;
        
        const finalToken = inputToken.trim() || newToken;
        const currentMonth = new Date().getMonth() + 1;
        const lockFileContent = `${{currentMonth}}-${{finalToken}}`;

        if (!confirm(`确定要将矩阵密锁重置为【 ${{finalToken}} 】吗？\\n\\n这会导致老接口链接彻底失效炸毁，并触发 Telegram 换锁推送！`)) return;

        try {{
            const url = `https://api.github.com/repos/${{auth.repo}}/contents/datas/控制开关.txt?ref=${{auth.branch}}`;
            const getRes = await fetch(url, {{ headers: {{ 'Authorization': `token ${{auth.token}}` }} }});
            
            let sha = '';
            if (getRes.ok) {{
                const getData = await getRes.json();
                sha = getData.sha;
            }}

            const base64Content = btoa(unescape(encodeURIComponent(lockFileContent)));

            const putRes = await fetch(`https://api.github.com/repos/${{auth.repo}}/contents/datas/控制开关.txt`, {{
                method: 'PUT',
                headers: {{
                    'Authorization': `token ${{auth.token}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    message: `🔑 控制台在线强行换锁重置为: ${{finalToken}}`,
                    content: base64Content,
                    sha: sha || undefined,
                    branch: auth.branch
                }})
            }});

            if (putRes.ok) {{
                alert(`✨ 密锁已成功更新为【 ${{finalToken}} 】并提交 Git！系统正在自动拉起 Actions 流水线进行大轰炸与新包编译...`);
            }} else {{
                const errData = await putRes.json();
                alert('换锁失败: ' + (errData.message || '权限不足或文件不存在'));
            }}
        }} catch (e) {{
            alert('请求发生错误: ' + e.message);
        }}
    }}

    let currentSettingsSha = '';

    async function loadSettingsFromGithub() {{
        const auth = getStoredAuth();
        if (!auth.token || !auth.repo) return;

        const url = `https://api.github.com/repos/${{auth.repo}}/contents/datas/settings.json?ref=${{auth.branch}}`;
        try {{
            const res = await fetch(url, {{
                headers: {{ 'Authorization': `token ${{auth.token}}` }}
            }});
            if (res.ok) {{
                const data = await res.json();
                currentSettingsSha = data.sha;
                const jsonText = decodeURIComponent(escape(atob(data.content)));
                const jsonObj = JSON.parse(jsonText);
                // ⬇️ 填充新增的 6 个单行输入框
                document.getElementById('input_global_spider_jar').value = jsonObj.GLOBAL_SPIDER_JAR || '';
                document.getElementById('input_default_logo_url').value = jsonObj.DEFAULT_LOGO_URL || '';
                document.getElementById('input_site_insert_pos').value = jsonObj.SITE_INSERT_POS ?? 0;
                document.getElementById('input_insert_pos').value = jsonObj.INSERT_POS ?? 0;
                document.getElementById('input_hot_video_key').value = jsonObj.HOT_VIDEO_KEY || 'js_douban';
                document.getElementById('input_hot_video_site_name').value = jsonObj.HOT_VIDEO_SITE_NAME || '';

                document.getElementById('json_block_keywords').value = JSON.stringify(jsonObj.BLOCK_KEYWORDS || [], null, 2);
                document.getElementById('json_upstream_dirty').value = JSON.stringify(jsonObj.UPSTREAM_DIRTY_WORDS || [], null, 2);
                document.getElementById('json_nsfw_keywords').value = JSON.stringify(jsonObj.NSFW_KEYWORDS || [], null, 2);
                document.getElementById('json_malicious_keywords').value = JSON.stringify(jsonObj.BLOCK_MALICIOUS_KEYWORDS || [], null, 2);
                document.getElementById('json_no_search_keywords').value = JSON.stringify(jsonObj.NO_SEARCH_KEYWORDS || [], null, 2);
            }}
        }} catch (e) {{
            console.error('读取 settings.json 失败:', e);
        }}
    }}

    async function saveSettingsToGithub() {{
        const auth = getStoredAuth();
        if (!auth.token || !auth.repo) {{
            alert('请先配置 GitHub PAT！');
            return openTokenModal();
        }}

        try {{
            const blockKw = JSON.parse(document.getElementById('json_block_keywords').value);
            const upstreamDirty = JSON.parse(document.getElementById('json_upstream_dirty').value);
            const nsfwKw = JSON.parse(document.getElementById('json_nsfw_keywords').value);
            const maliciousKw = JSON.parse(document.getElementById('json_malicious_keywords').value);
            const noSearchKw = JSON.parse(document.getElementById('json_no_search_keywords').value);

            const url = `https://api.github.com/repos/${{auth.repo}}/contents/datas/settings.json?ref=${{auth.branch}}`;
            const getRes = await fetch(url, {{ headers: {{ 'Authorization': `token ${{auth.token}}` }} }});
            let existingSettings = {{}};
            if (getRes.ok) {{
                const getData = await getRes.json();
                currentSettingsSha = getData.sha;
                existingSettings = JSON.parse(decodeURIComponent(escape(atob(getData.content))));
            }}

            // ⬇️ 写入 6 个核心变量
            existingSettings.GLOBAL_SPIDER_JAR = document.getElementById('input_global_spider_jar').value.trim();
            existingSettings.DEFAULT_LOGO_URL = document.getElementById('input_default_logo_url').value.trim();
            existingSettings.SITE_INSERT_POS = parseInt(document.getElementById('input_site_insert_pos').value) || 0;
            existingSettings.INSERT_POS = parseInt(document.getElementById('input_insert_pos').value) || 0;
            existingSettings.HOT_VIDEO_KEY = document.getElementById('input_hot_video_key').value.trim();
            existingSettings.HOT_VIDEO_SITE_NAME = document.getElementById('input_hot_video_site_name').value.trim();

            existingSettings.BLOCK_KEYWORDS = blockKw;
            existingSettings.UPSTREAM_DIRTY_WORDS = upstreamDirty;
            existingSettings.NSFW_KEYWORDS = nsfwKw;
            existingSettings.BLOCK_MALICIOUS_KEYWORDS = maliciousKw;
            existingSettings.NO_SEARCH_KEYWORDS = noSearchKw;

            const updatedContentStr = JSON.stringify(existingSettings, null, 2);
            const base64Content = btoa(unescape(encodeURIComponent(updatedContentStr)));

            const putRes = await fetch(`https://api.github.com/repos/${{auth.repo}}/contents/datas/settings.json`, {{
                method: 'PUT',
                headers: {{
                    'Authorization': `token ${{auth.token}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    message: "🛠 控制台在线全量更新 datas/settings.json 矩阵规则配置",
                    content: base64Content,
                    sha: currentSettingsSha,
                    branch: auth.branch
                }})
            }});

            if (putRes.ok) {{
                alert('✨ 新规则已成功全量 Commit 保存至 Git 仓库！自动编译流程即将被触发。');
            }} else {{
                const err = await putRes.json();
                alert('保存失败: ' + (err.message || '格式错误或 SHA 冲突'));
            }}
        }} catch (e) {{
            alert('JSON 格式输入有误，请确保所有文本框内符合正确的 JSON 数组语法 (例如 ["词1", "词2"])：' + e.message);
        }}
    }}

    async function loadCommitLogs() {{
        const auth = getStoredAuth();
        const container = document.getElementById('commitLogsContainer');
        if (!auth.repo) {{
            container.innerHTML = '<div class="text-slate-500">未配置仓库信息</div>';
            return;
        }}

        container.innerHTML = '<div class="text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> 正在拉取 Commit 历史...</div>';

        const headers = {{}};
        if (auth.token) headers['Authorization'] = `token ${{auth.token}}`;

        try {{
            const res = await fetch(`https://api.github.com/repos/${{auth.repo}}/commits?per_page=8&sha=${{auth.branch}}`, {{ headers }});
            if (res.ok) {{
                const commits = await res.json();
                let html = '';
                commits.forEach(c => {{
                    const msg = c.commit.message;
                    const date = new Date(c.commit.author.date).toLocaleString('zh-CN');
                    const author = c.commit.author.name;
                    const sha = c.sha.substring(0, 7);

                    html += `
                    <div class="bg-slate-900/90 rounded-lg p-3 border border-slate-800 flex justify-between items-center gap-3">
                        <div class="space-y-1 overflow-hidden">
                            <div class="font-bold text-slate-200 truncate">${{msg}}</div>
                            <div class="text-[10px] text-slate-500">作者: ${{author}} | 时间: ${{date}}</div>
                        </div>
                        <span class="px-2 py-1 bg-slate-800 text-blue-400 rounded text-[10px] font-mono flex-shrink-0">${{sha}}</span>
                    </div>
                    `;
                }});
                container.innerHTML = html;
            }} else {{
                container.innerHTML = '<div class="text-amber-400">拉取日志失败，请检查仓库路径或 Token</div>';
            }}
        }} catch (e) {{
            container.innerHTML = '<div class="text-rose-400">请求异常: ' + e.message + '</div>';
        }}
    }}

    let deadSiteNames = [];

    async function startInspection() {{
        const consoleEl = document.getElementById('inspectConsole');
        const btnInspect = document.getElementById('btnStartInspect');
        const btnPurge = document.getElementById('btnPurgeDead');
        
        btnInspect.disabled = true;
        btnInspect.classList.add('opacity-50');
        btnPurge.classList.add('hidden');
        btnPurge.classList.remove('flex');
        
        consoleEl.innerHTML = '<div class="text-cyan-400">🚀 正在获取当前全量订阅 JSON 并解析接口节点...</div>';
        deadSiteNames = [];

        let sites = [], lives = [];
        try {{
            const res = await fetch('蝴蝶影视全量版{current_token}.json');
            if (res.ok) {{
                const fullData = await res.json();
                sites = fullData.sites || [];
                lives = fullData.lives || [];
            }} else {{
                consoleEl.innerHTML += '<div class="text-amber-400">⚠️ 无法在线拉取全量 JSON，尝试本地代理尝试...</div>';
            }}
        }} catch(e) {{
            consoleEl.innerHTML += `<div class="text-rose-400">❌ 加载订阅文件失败: ${{e.message}}</div>`;
            btnInspect.disabled = false;
            btnInspect.classList.remove('opacity-50');
            return;
        }}

        const targets = [];
        sites.forEach(s => {{
            let targetUrl = '';

            if (s.api && typeof s.api === 'string') {{
                if (s.api.startsWith('http')) {{
                    targetUrl = s.api;
                }} else if (s.api.startsWith('./')) {{
                    targetUrl = s.api.replace('./', 'https://cnb.cool/fish2035/xs/-/git/raw/main/');
                }}
            }}

            if (!targetUrl && s.ext) {{
                if (typeof s.ext === 'string') {{
                    if (s.ext.startsWith('http')) {{
                        targetUrl = s.ext;
                    }} else if (s.ext.startsWith('./')) {{
                        targetUrl = s.ext.replace('./', 'https://cnb.cool/fish2035/xs/-/git/raw/main/');
                    }}
                }}
            }}

            if (targetUrl) {{
                targets.push({{ name: s.name, url: targetUrl, type: '点播 API' }});
            }}
        }});

        lives.forEach(l => {{
            if (l.url && typeof l.url === 'string') {{
                let liveUrl = l.url;
                if (liveUrl.startsWith('./')) {{
                    liveUrl = liveUrl.replace('./', 'https://cnb.cool/fish2035/xs/-/git/raw/main/');
                }}
                if (liveUrl.startsWith('http')) {{
                    targets.push({{ name: l.name, url: liveUrl, type: '直播源' }});
                }}
            }}
        }});

        const totalCnt = targets.length;
        document.getElementById('stat_total').innerText = `0 / ${{totalCnt}}`;
        let okCnt = 0, slowCnt = 0, deadCnt = 0, processed = 0;

        consoleEl.innerHTML += `<div class="text-emerald-400 font-bold">✨ 共解析出 ${{totalCnt}} 个独立远程接口与源站，并发线程池启动巡检...</div><br>`;

        const concurrencyLimit = 8;
        let index = 0;

        async function worker() {{
            while (index < targets.length) {{
                const item = targets[index++];
                const startTime = performance.now();
                let status = 'DEAD', ms = 0, colorClass = 'text-rose-400';

                try {{
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 6000);

                    await fetch(item.url, {{ method: 'HEAD', mode: 'no-cors', signal: controller.signal }});
                    clearTimeout(timeoutId);
                    
                    ms = Math.round(performance.now() - startTime);
                    if (ms > 2000) {{
                        status = 'SLOW';
                        colorClass = 'text-amber-400';
                        slowCnt++;
                    }} else {{
                        status = 'OK';
                        colorClass = 'text-emerald-400';
                        okCnt++;
                    }}
                }} catch (err) {{
                    ms = Math.round(performance.now() - startTime);
                    status = 'DEAD';
                    colorClass = 'text-rose-400';
                    deadCnt++;
                    deadSiteNames.push(item.name.replace("🦋", "").replace("｜Tg：@huliys9", "").trim());
                }}

                processed++;
                document.getElementById('stat_total').innerText = `${{processed}} / ${{totalCnt}}`;
                document.getElementById('stat_ok').innerText = okCnt;
                document.getElementById('stat_slow').innerText = slowCnt;
                document.getElementById('stat_dead').innerText = deadCnt;

                const logItem = document.createElement('div');
                logItem.className = 'flex justify-between items-center py-0.5 border-b border-slate-900/60';
                logItem.innerHTML = `
                    <span class="truncate max-w-[60%] text-slate-300">[${{item.type}}] ${{item.name}}</span>
                    <span class="${{colorClass}} font-bold font-mono">${{status}} (${{ms}}ms)</span>
                `;
                consoleEl.appendChild(logItem);
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }}
        }}

        const workers = Array(concurrencyLimit).fill(0).map(() => worker());
        await Promise.all(workers);

        consoleEl.innerHTML += `<br><div class="text-cyan-400 font-bold">🏁 全量巡检完成！正常: ${{okCnt}} | 高延迟: ${{slowCnt}} | 失效: ${{deadCnt}}</div>`;
        btnInspect.disabled = false;
        btnInspect.classList.remove('opacity-50');

        if (deadCnt > 0) {{
            btnPurge.classList.remove('hidden');
            btnPurge.classList.add('flex');
            btnPurge.innerText = `一键拉黑剔除 ${{deadCnt}} 个失效源`;
        }}
    }}

    async function purgeDeadSites() {{
        if (deadSiteNames.length === 0) return;
        const auth = getStoredAuth();
        if (!auth.token || !auth.repo) {{
            alert('请先配置 GitHub PAT！');
            return openTokenModal();
        }}

        if (!confirm(`确定要将巡检出的 ${{deadSiteNames.length}} 个失效/404源加入 BLOCK_KEYWORDS 黑名单并提交 Git 吗？`)) return;

        try {{
            const cleanDeadKeywords = deadSiteNames.map(name => name.split('｜')[0].trim()).filter(Boolean);

            const url = `https://api.github.com/repos/${{auth.repo}}/contents/datas/settings.json?ref=${{auth.branch}}`;
            const getRes = await fetch(url, {{ headers: {{ 'Authorization': `token ${{auth.token}}` }} }});
            if (!getRes.ok) throw new Error('无法获取远程 settings.json');

            const getData = await getRes.json();
            const currentSha = getData.sha;
            const existingSettings = JSON.parse(decodeURIComponent(escape(atob(getData.content))));

            const currentBlocks = existingSettings.BLOCK_KEYWORDS || [];
            const mergedBlocks = Array.from(new Set([...currentBlocks, ...cleanDeadKeywords]));

            existingSettings.BLOCK_KEYWORDS = mergedBlocks;

            const updatedContentStr = JSON.stringify(existingSettings, null, 2);
            const base64Content = btoa(unescape(encodeURIComponent(updatedContentStr)));

            const putRes = await fetch(`https://api.github.com/repos/${{auth.repo}}/contents/datas/settings.json`, {{
                method: 'PUT',
                headers: {{
                    'Authorization': `token ${{auth.token}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    message: `🔍 巡检自动化：拉黑剔除 ${{cleanDeadKeywords.length}} 个失效源站点`,
                    content: base64Content,
                    sha: currentSha,
                    branch: auth.branch
                }})
            }});

            if (putRes.ok) {{
                alert('✨ 已自动将失效源加入黑名单并提交 Git 仓库！Actions 编译流水线即将被触发。');
                document.getElementById('btnPurgeDead').classList.add('hidden');
            }} else {{
                alert('一键剔除提交失败');
            }}
        }} catch(e) {{
            alert('剔除提交失败: ' + e.message);
        }}
    }}

    document.addEventListener('DOMContentLoaded', () => {{
        updateAuthUI();
    }});
    </script>
</body>
</html>
""".replace("TG_LINK_PLACEHOLDER", MY_PROMO_CHANNEL.lstrip('@')).replace("TG_NAME_PLACEHOLDER", MY_PROMO_CHANNEL)

# ====================================================================
# ✍️ 【九、蝴蝶专属点播手工加线区】
# ====================================================================
MY_CUSTOM_SITES = [
    {
        "key": "采集合集py",
        "name": f"🦋采集合集(py)｜{MY_TG_SUFFIX.strip('｜')}",
        "type": 3,
        "api": "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz/py/采集合集.py",
        "searchable": 1,
        "quickSearch": 1,
        "filterable": 1,
        "changeable": 1,
        "playerType": 2,
        "ext": "0"
    },
    {
        "key": "js_douban",
        "name": "🦋豆瓣(js)",
        "type": 3,
        "api": "https://gh-proxy.com/https://raw.githubusercontent.com/ediart/tvbox/refs/heads/main/lz/douban_min.js",
        "searchable": 0,
        "quickSearch": 0,
        "filterable": 1,
        "changeable": 0
    }
]

# ====================================================================
# 📺 【十、蝴蝶专属直播手工加线区】
# ====================================================================
MY_CUSTOM_LIVES = [	
    {
        "name": "老杨TV",
        "type": 0,
        "url": "https://ghfast.top/https://raw.githubusercontent.com/GodLike631/Ly/refs/heads/Live/datas/custom_lives.m3u",
        "ua": "okhttp/5.3.2"
    },
    {
        "name": "央卫TV",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "http://47.120.41.246:8025/vip/jar/zb.php"
    },
    {
        "name": "咪咕",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://develop202.github.io/migu_video/interface.txt"
    },   
    {
        "name": "裤佬TV｜Tg：@huliys9",
        "type": 0,
        "ua": "okhttp",
        "url": "https://live.445569.xyz/live.m3u"
    },
    {
        "name": "综合直播",
        "type": 0,
        "playerType": 2,
        "url": "https://ghfast.top/https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt",
        "ua": "bingcha/1.1 (mianfeifenxiang) "
    },    
    {
        "name": "Kimentanm",
        "type": 0,
        "url": "https://ghfast.top/https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u",
        "playerType": 2
    },
    {
        "name": "超稳定流畅",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/GodLike631/test/refs/heads/main/datas/%E8%B6%85%E7%A8%B3%E5%AE%9A%E6%B5%81%E7%95%85.txt"
    },
    {
        "name": "Gather「IPTV」(梯子）",
        "type": 3,
        "url": "https://iptv.1989.click/playlist.m3u",
        "epg":"https://material.1989.click/epg.xml.gz",
        "ua": "okhttp/3.8.1",
        "timeout": 10,
        "playerType": 2
    },
    {
        "name": "Live「直播」",
        "type": 3,
        "url": "https://live.yang-1989.eu.org/Live.m3u",
        "ua": "okhttp/3.8.1",
        "timeout": 10,
        "playerType": 2
    },
    {
        "name": "锋云直播",
        "type": 3,
        "url": "https://gh-proxy.org/https://raw.githubusercontent.com/807080747/zv/refs/heads/main/suale.txt",
        "ua": "okhttp/5.3.2",
        "timeout": 10,
        "playerType": 2
    },
    {
        "name": "最新电影",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/GodLike631/Ly_18/refs/heads/main/datas/%E6%9C%80%E6%96%B0%E7%94%B5%E5%BD%B1.m3u"
    }, 
    {
        "name": "海外频道（开梯）🔞",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/yihad168/tv/refs/heads/main/live.m3u"
    },
    {
        "name": "国产直播🔞",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/Ameria22/TV/refs/heads/main/data/01%E5%9B%BD%E4%BA%A7%E7%9B%B4%E6%92%AD_20260417_024507.m3u"
    },
    {
        "name": "国产精品🔞",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/Ameria22/TV/refs/heads/main/data/01%E5%9B%BD%E4%BA%A7%E7%B2%BE%E5%93%81_20260417_024507.m3u"
    },
    {
        "name": "探花🔞",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://raw.githubusercontent.com/Ameria22/TV/refs/heads/main/data/01%E6%8E%A2%E8%8A%B1%E7%BA%A6%E7%82%AE_20260417_024507.m3u"
    },
    {
        "name": "欧美🔞",
        "type": 0,
        "ua": "okhttp/5.3.2",
        "url": "https://ghfast.top/https://raw.githubusercontent.com/Ameria22/TV/refs/heads/main/data/%E6%AC%A7%E7%BE%8E%E9%A2%91%E9%81%93.m3u"
    }
]
