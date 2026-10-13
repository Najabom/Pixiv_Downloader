# PixivDownloader

**Pixiv 图片下载管理器** — 按作品 / 角色 / CP 自动分类下载 Pixiv 插画。
**A Pixiv image download manager** — search, download and auto-classify Pixiv illustrations by work / character / CP.

> ⚠️ **AI 开发声明 / AI Disclosure**
> 本项目 100% 由 AI 生成（代码、文档、构建脚本均为 AI 辅助开发），经人工测试与使用。
> This project is 100% AI-generated (code, docs and build scripts are all AI-assisted development), tested and used by a human.

> ⚠️ **免责声明 / Disclaimer**
> 本项目仅供个人学习与技术交流，请遵守 [Pixiv 服务条款](https://www.pixiv.net/terms/) 及当地法律法规，尊重画师版权，请勿二次分发下载的作品。使用本工具产生的任何后果由使用者自行承担。
> For personal learning and technical exchange only. Please comply with the [Pixiv Terms of Service](https://www.pixiv.net/terms/) and local laws, respect artists' copyright, and do not redistribute downloaded works. Use at your own risk.

[中文文档](#中文文档) | [English Docs](#english-docs)

---

## 中文文档

### 功能特性

- **自动分类下载**：按作品 / 角色 / CP 标签搜索下载，自动归类到对应子目录
- **WebUI 管理界面**：Vue 3 现代化界面（仪表盘 / 作品 / 画廊 / 日志 / 设置）
- **断点续传**：下载历史 + 标签检查点，中断后可继续
- **CP 配对识别**：通过标签组合识别 CP 作品，单人 / 多人 / 组图自动分类
- **NSFW 检测**（可选）：基于 opennsfw2，超阈值图片自动移入 `_待审核/`
- **Cookie / OAuth 双鉴权**：支持网站 Cookie 或 App API refresh_token
- **一键打包**：PyInstaller 构建独立 exe，无需 Python 环境

### 技术栈

| 层 | 技术 |
|---|------|
| 运行时 | Python 3.14 |
| 后端 | FastAPI + Uvicorn |
| 前端 | Vue 3 + Vite + TypeScript + Tailwind CSS |
| 状态管理 | Pinia |
| 打包 | PyInstaller |
| Pixiv API | pixivpy3 |

### 目录结构

```
PixivDownloader/
├── main.py                 CLI 入口
├── run.py                  WebUI 入口（主启动器）
├── build.bat               一键构建脚本
├── build_exe.spec          PyInstaller 配置
├── requirements.txt        Python 依赖
│
├── src/                    核心模块
│   ├── models.py           数据类定义
│   ├── config_loader.py    YAML 配置加载/保存
│   ├── pixiv_client.py     Pixiv API 交互（App API / Web Session）
│   ├── downloader.py       下载引擎（搜索 → 分类 → 下载 → 元数据）
│   ├── organizer.py        图片分类、文件名生成、NSFW 检测
│   ├── metadata.py         下载历史持久化
│   └── cli.py              交互式命令行菜单
│
├── webui/                  Web 界面
│   ├── start.py            开发模式启动器
│   ├── backend/            FastAPI 后端（api / schemas / services）
│   └── frontend/           Vue 3 前端（views / components / stores）
│
├── templates/              配置模板（首次运行自动复制到 config/）
│   ├── settings.yaml
│   └── works.yaml
│
├── tools/
│   └── cleanup_duplicates.py   重复文件清理工具
│
├── cleanup.py              清空下载 + 数据
├── generate_guide.py       生成用户指南 PDF
├── rebuild_history.py      从本地下载目录重建下载历史
├── remap_folders.py        重映射旧目录名到新配置
├── reorganize.py           用当前配置重新归类已有下载
└── sync_checkpoint.py      从下载历史重建标签检查点
```

### 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Linux / macOS
pip install -r requirements.txt

# 2. 启动（首次运行会自动从 templates/ 复制配置到 config/）
python run.py                    # WebUI 模式（推荐），自动打开 http://localhost:8000
python main.py                   # CLI 模式
```

前端开发模式（前后端分离热重载）：

```bash
python webui\start.py            # 仅启动后端 API
cd webui\frontend
npm install
npm run dev                      # Vite HMR
npm run build                    # 生产构建
```

### 配置说明

首次运行后，编辑 `config/settings.yaml`：

| 字段 | 说明 |
|------|------|
| `download_dir` | 下载根目录，默认 `downloads` |
| `max_search_pages` | 每个标签最大搜索页数 |
| `request_delay` | API 请求间隔（秒），建议 ≥2 |
| `nsfw` | NSFW 检测配置（需 `pip install opennsfw2`） |
| `global_exclude_tags` | 全局排除标签 |
| `pixiv.refresh_token` | App API OAuth token |
| `pixiv.cookie_string` | 网站 Cookie 鉴权 |

**Cookie 获取方法**（二选一）：

- 方式 A：浏览器 F12 → Network → 任选一条 ajax 请求 → Request Headers → 复制整行 `Cookie:` 填入 `cookie_string`
- 方式 B：使用 pixivpy3 的 OAuth 流程获取 `refresh_token`（需要能访问 accounts.pixiv.net）

`config/works.yaml` 配置要下载的作品：每个作品可设置 `active`（是否启用）、`directory`（本地目录名）、`tags`（搜索标签）、`cp_tags`（CP 标签）、`exclude_tags`（专属排除标签）。

> 🔒 `config/` 已被 `.gitignore` 排除，**切勿**将包含 Cookie / token 的配置文件提交到公开仓库。

### 下载逻辑

```
对每个 active 作品：
  1. 遍历 tags[] → Pixiv 搜索 → 获取作品列表
  2. 对每个作品：检查下载历史（skip 已下载）
  3. 下载图片 → classify_image() 识别角色/CP/多人/组图
  4. 按分类移动到对应子目录
  5. 记录到 download_history.json
  6. 更新 tag_checkpoint.json（断点续传）
```

### 构建可执行文件

```bash
.\build.bat    # 自动构建前端 + 生成 PDF + PyInstaller 打包
```

构建产物位于 `packaged/`（不提交到 git，通过 GitHub Releases 分发）。

### 注意事项

- Pixiv API 有速率限制，`request_delay` 不要设置过低
- NSFW 检测首次运行会下载约 150MB 模型
- 构建 exe 时需在项目根目录执行

---

## English Docs

### Features

- **Auto-classified downloads**: search by work / character / CP tags and organize files into matching subdirectories
- **Modern WebUI**: Vue 3 interface (Dashboard / Works / Gallery / Logs / Settings)
- **Resumable**: download history + tag checkpoints allow resuming after interruption
- **CP pairing detection**: recognizes CP works by tag combinations; auto-classifies solo / multi-character / image sets
- **Optional NSFW detection** via opennsfw2; flagged images are moved to `_待审核/` (pending review)
- **Dual authentication**: site cookie or App API `refresh_token`
- **One-click packaging**: standalone Windows exe via PyInstaller

### Tech Stack

Python 3.14 · FastAPI + Uvicorn · Vue 3 + Vite + TypeScript + Tailwind CSS · Pinia · PyInstaller · pixivpy3

### Quick Start

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt

python run.py                    # WebUI mode (recommended) → http://localhost:8000
python main.py                   # CLI mode
```

On first run, `config/` is auto-created from `templates/` — edit `config/settings.yaml` and fill in your Pixiv credentials:

- **Option A**: copy the `Cookie:` header of any ajax request from your browser DevTools into `pixiv.cookie_string`
- **Option B**: use a pixivpy3 OAuth `refresh_token` (requires access to accounts.pixiv.net)

> 🔒 `config/` is git-ignored. **Never** commit files containing cookies or tokens.

### Build

```bash
.\build.bat    # build frontend + PDF + PyInstaller package
```

Output goes to `packaged/` (not committed; distributed via GitHub Releases).

---

## License

[MIT](LICENSE)
