#!/usr/bin/env python3
"""生成用户指南 PDF — 使用 reportlab + 内置 CJK 支持"""
import os
from pathlib import Path
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

OUTPUT = Path(__file__).parent / "packaged" / "用户指南.pdf"
W, H = A4
MARGIN = 25 * mm
LINE_H = 6 * mm
PAGE_W = W - 2 * MARGIN


def find_cjk_font():
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


class Writer:
    def __init__(self, pdf, font_name, font_bold, font_size=11):
        self.pdf = pdf
        self.font = font_name
        self.bold = font_bold
        self.fs = font_size
        self.y = H - MARGIN

    def new_page(self):
        self.pdf.showPage()
        self.y = H - MARGIN

    def check_space(self, need=LINE_H):
        if self.y < MARGIN + need:
            self.new_page()

    def write(self, text, bold=False, color=None, size=None, center=False, box=False):
        s = size or self.fs
        fn = self.bold if bold else self.font
        self.pdf.setFont(fn, s)

        if box:
            self.check_space(8 * mm)
            self.pdf.setFillColorRGB(0.96, 0.96, 0.98)
            self.pdf.rect(MARGIN, self.y - s * 0.4, PAGE_W, s * 1.5, fill=1, stroke=0)
            self.pdf.setFillColorRGB(0, 0, 0)

        if color:
            self.pdf.setFillColorRGB(*color)
        else:
            self.pdf.setFillColorRGB(0, 0, 0)

        if center:
            self.pdf.drawCentredString(W / 2, self.y, text)
        else:
            self.pdf.drawString(MARGIN, self.y, text)
        self.y -= LINE_H if not box else 9 * mm

    def multi(self, text, indent=0):
        words = list(text)
        line = ""
        max_w = PAGE_W - indent
        for ch in words:
            if ch == "\n":
                self._flush_line(line, indent)
                line = ""
                continue
            test = line + ch
            if self.pdf.stringWidth(test, self.font, self.fs) > max_w and line:
                self._flush_line(line, indent)
                line = ch
            else:
                line = test
        if line:
            self._flush_line(line, indent)

    def _flush_line(self, line, indent):
        self.check_space()
        if line.strip():
            self.pdf.drawString(MARGIN + indent, self.y, line)
        self.y -= LINE_H

    def gap(self, mm_val=4):
        self.y -= mm_val * mm


def build():
    font_path = find_cjk_font()
    if not font_path:
        print("ERROR: 未找到中文字体")
        return

    pdf = canvas.Canvas(str(OUTPUT), pagesize=A4)
    pdfmetrics.registerFont(ttfonts.TTFont("cjk", font_path))
    w = Writer(pdf, "cjk", "cjk", 11)

    # ===== 封面 =====
    w.gap(40)
    w.write("Pixiv Downloader", bold=True, size=26, center=True)
    w.gap(10)
    w.write("用户指南", bold=True, size=18, center=True)
    w.gap(15)
    w.multi("本工具用于批量下载 Pixiv 插画, 支持按作品 / 角色 / CP 自动分类存放.\n双击运行后通过浏览器操作, 无需命令行知识.")
    w.new_page()

    # ===== 1. 快速开始 =====
    w.write("1. 快速开始", bold=True, size=16, color=(0.1, 0.12, 0.98))
    w.gap(4)
    w.multi("(1) 双击 PixivDownloader.exe, 等待 CMD 窗口出现\n"
            "(2) 首次运行会自动创建 config/settings.yaml 和 config/works.yaml\n"
            "(3) 浏览器自动打开 http://127.0.0.1:8000 进入仪表盘\n"
            "(4) CMD 窗口不可关闭, 否则服务停止.")
    w.gap(6)
    w.write("启动流程: 双击 exe -> CMD 窗口 -> 后端启动 -> 浏览器打开 -> 开始使用", box=True)
    w.new_page()

    # ===== 2. 首次配置 =====
    w.write("2. 首次配置", bold=True, size=16, color=(0.1, 0.12, 0.98))
    w.gap(3)
    w.write("2.1 配置 Pixiv 登录", bold=True)
    w.multi("打开设置页, 粘贴浏览器 Cookie. 获取方法: F12 -> Network -> 任一条 ajax 请求 -> Request Headers -> Cookie: 整行复制.")
    w.gap(3)
    w.write("2.2 配置作品", bold=True)
    w.multi("打开作品管理页, 点击添加输入作品名. 进入详情页, 添加角色并填写搜索标签. 可配置 CP 组合和排除标签.")
    w.new_page()

    # ===== 3. 功能说明 =====
    w.write("3. 功能说明", bold=True, size=16, color=(0.1, 0.12, 0.98))
    w.gap(3)

    for title, desc in [
        ("仪表盘", "顶部 5 个磁贴展示作品数/角色数/CP数/下载量/存储占用"),
        ("作品管理", "卡片网格展示作品, 点击进入详情管理角色/CP/过滤标签"),
        ("图库浏览", "三级浏览: 选择作品 -> 选择分类 -> 查看图片, 点击可看大图"),
        ("下载", "一键开始/停止, 实时日志流, 自动分类存放"),
        ("设置", "Cookie管理/下载参数/NSFW检测/全局过滤/全局背景"),
    ]:
        w.write(f"  {title}", bold=True)
        w.multi(f"    {desc}")
        w.gap(2)

    w.new_page()

    # ===== 4. Cookie 获取 =====
    w.write("4. Cookie 获取", bold=True, size=16, color=(0.1, 0.12, 0.98))
    w.gap(3)
    w.multi("(1) 浏览器打开 https://www.pixiv.net/ 并登录\n"
            "(2) F12 -> Network, 刷新页面\n"
            "(3) 筛选 ajax, 点击任一条请求\n"
            "(4) Request Headers 中找到 Cookie: 开头的整行, 全部复制\n"
            "(5) 粘贴到设置页 Cookie String 输入框, 保存, 测试登录\n"
            "Cookie 有效期几天到几周, 过期需重新获取.")
    w.new_page()

    # ===== 5. 常见问题 =====
    w.write("5. 常见问题", bold=True, size=16, color=(0.1, 0.12, 0.98))
    w.gap(3)

    qa = [
        ("登录失败", "Cookie 过期, 重新获取并更新"),
        ("下载速度慢", "Pixiv 有频率限制, 调大请求间隔 >= 2 秒"),
        ("图片未正确分类", "检查搜索标签是否匹配, 未分类图片查看 _原因记录.txt"),
        ("config 在哪", "与 exe 同目录的 config/ 文件夹"),
        ("端口被占用", "Ctrl+C 停止, 修改 run.py 中端口号"),
        ("浏览器未自动打开", "手动访问 http://127.0.0.1:8000"),
    ]
    for q, a in qa:
        w.write(f"  Q: {q}", bold=True)
        w.multi(f"     {a}")
        w.gap(2)

    pdf.save()
    print(f"PDF 已生成: {OUTPUT}")


if __name__ == "__main__":
    build()
