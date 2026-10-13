# Pixiv Downloader WebUI

基于 Vue 3 + FastAPI 的 Pixiv 下载器 Web 界面，与主程序 `src/` 完全分离。

## 技术栈

- **后端**：FastAPI + uvicorn，复用 `src/` 核心模块
- **前端**：Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia
- **通信**：REST API + SSE 实时日志推送
- **主题**：明亮 / 暗色一键切换

## 目录结构

```
webui/
├── backend/          # FastAPI 服务
│   ├── main.py       # 入口
│   ├── api/          # API 路由
│   ├── services/     # 业务服务
│   └── schemas/      # Pydantic 模型
└── frontend/         # Vue 3 前端
    ├── src/
    │   ├── views/    # 页面
    │   ├── components/
    │   ├── stores/   # Pinia 状态
    │   ├── api/      # 请求封装
    │   └── types/    # TypeScript 类型
    └── dist/         # 构建产物（由 npm run build 生成）
```

## 启动方式

### 方式一：生产模式（推荐日常使用）

先构建前端：

```bash
cd webui/frontend
npm install
npm run build
```

再启动后端（从项目根目录运行，确保模块路径正确）：

```bash
cd ../..
python -m uvicorn webui.backend.main:app --host 127.0.0.1 --port 8000
```

打开浏览器访问：http://127.0.0.1:8000

### 方式二：开发模式

同时启动后端和前端开发服务器：

```bash
# 终端 1（从项目根目录运行）
cd ../..
python -m uvicorn webui.backend.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2
cd webui/frontend
npm run dev
```

前端开发服务器地址：http://127.0.0.1:5173

API 代理已配置到 http://127.0.0.1:8000

## 功能模块

- **仪表盘**：作品数、角色数、CP 数、下载总量、存储占用
- **作品管理**：新增 / 删除 / 启用 / 停用 / 编辑角色与 CP
- **图库浏览**：按作品筛选、分页浏览、悬停信息
- **下载日志**：一键开始 / 停止下载、SSE 实时日志流
- **设置**：Cookie、下载参数、NSFW 检测、全局过滤标签

## 注意事项

- WebUI 与 CLI 共享 `config/settings.yaml` 和 `config/works.yaml`，任一端修改都会同步
- 首次使用前请在「设置」页配置 Pixiv Cookie 或 refresh_token
- 下载任务在后台线程运行，关闭页面不会中断，但关闭后端进程会中断
