#!/usr/bin/env python3
"""生成用户指南 PDF — 使用 ReportLab Platypus 排版"""
import os
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

VERSION = "v1.0.1"
OUTPUT = Path(__file__).parent / "packaged" / "用户指南.pdf"

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

PRIMARY = colors.HexColor("#1a2ffb")
DARK = colors.HexColor("#1a1b1f")
MUTED = colors.HexColor("#6b7280")
LINE = colors.HexColor("#e5e7eb")
TIP_BG = colors.HexColor("#eef1ff")
TIP_BORDER = colors.HexColor("#c7d2fe")
TIP_TEXT = colors.HexColor("#3730a3")
ROW_ALT = colors.HexColor("#f7f8fc")

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyh.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]
BOLD_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyhbd.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]


def find_font(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def register_fonts():
    regular = find_font(FONT_CANDIDATES)
    if not regular:
        raise RuntimeError("未找到中文字体，无法生成 PDF")
    pdfmetrics.registerFont(TTFont("CJK", regular))
    font_bold = "CJK"
    bold = find_font(BOLD_CANDIDATES)
    if bold:
        pdfmetrics.registerFont(TTFont("CJK-Bold", bold))
        font_bold = "CJK-Bold"
    registerFontFamily(
        "CJK", normal="CJK", bold=font_bold, italic="CJK", boldItalic=font_bold
    )
    return "CJK", font_bold


def make_styles(font, bold):
    s = {}
    s["h1"] = ParagraphStyle(
        "h1", fontName=bold, fontSize=17, leading=26,
        textColor=PRIMARY, spaceBefore=6, spaceAfter=10, wordWrap="CJK",
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName=bold, fontSize=12.5, leading=20,
        textColor=DARK, spaceBefore=10, spaceAfter=4, wordWrap="CJK",
    )
    s["body"] = ParagraphStyle(
        "body", fontName=font, fontSize=10.5, leading=17,
        textColor=DARK, spaceAfter=5, wordWrap="CJK",
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=s["body"], leftIndent=14, bulletIndent=3, spaceAfter=3,
    )
    s["tip"] = ParagraphStyle(
        "tip", parent=s["body"], textColor=TIP_TEXT, spaceAfter=0,
    )
    s["table_cell"] = ParagraphStyle(
        "table_cell", fontName=font, fontSize=9.5, leading=14.5,
        textColor=DARK, wordWrap="CJK",
    )
    s["table_head"] = ParagraphStyle(
        "table_head", parent=s["table_cell"], fontName=bold, textColor=colors.white,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName=bold, fontSize=34, leading=44,
        alignment=TA_CENTER, textColor=PRIMARY,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName=font, fontSize=17, leading=26,
        alignment=TA_CENTER, textColor=DARK,
    )
    s["cover_info"] = ParagraphStyle(
        "cover_info", fontName=font, fontSize=10.5, leading=18,
        alignment=TA_CENTER, textColor=MUTED,
    )
    s["toc_title"] = ParagraphStyle(
        "toc_title", fontName=bold, fontSize=17, leading=26,
        textColor=PRIMARY, spaceBefore=6, spaceAfter=10, wordWrap="CJK",
    )
    s["toc0"] = ParagraphStyle(
        "toc0", fontName=bold, fontSize=11.5, leading=20, textColor=DARK,
    )
    s["toc1"] = ParagraphStyle(
        "toc1", fontName=font, fontSize=10, leading=17, textColor=MUTED, leftIndent=16,
    )
    return s


def tip_box(text, styles):
    box = Table([[Paragraph(text, styles["tip"])]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TIP_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, TIP_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [Spacer(1, 3), box, Spacer(1, 6)]


def make_table(rows, styles, col_widths):
    data = [[Paragraph(c, styles["table_head"]) for c in rows[0]]]
    data += [[Paragraph(c, styles["table_cell"]) for c in row] for row in rows[1:]]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


class GuideDocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        self.font = kwargs.pop("font")
        self.font_bold = kwargs.pop("font_bold")
        super().__init__(*args, **kwargs)
        cover_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id="cover")
        body_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN - 6 * mm, id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=self.draw_cover),
            PageTemplate(id="body", frames=[body_frame], onPage=self.draw_body),
        ])

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(PRIMARY)
        canvas.rect(0, PAGE_H - 6 * mm, PAGE_W, 6 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#c1ff00"))
        canvas.rect(0, PAGE_H - 6 * mm, PAGE_W * 0.28, 6 * mm, fill=1, stroke=0)
        canvas.restoreState()

    def draw_body(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, PAGE_H - MARGIN + 7 * mm, "Pixiv Downloader · 用户指南")
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 7 * mm, VERSION)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, PAGE_H - MARGIN + 5 * mm, PAGE_W - MARGIN, PAGE_H - MARGIN + 5 * mm)
        canvas.line(MARGIN, MARGIN - 6 * mm, PAGE_W - MARGIN, MARGIN - 6 * mm)
        canvas.drawCentredString(PAGE_W / 2, MARGIN - 11 * mm, f"第 {canvas.getPageNumber()} 页")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            if name in ("h1", "h2"):
                level = 0 if name == "h1" else 1
                self.notify("TOCEntry", (level, flowable.getPlainText(), self.page))


def build_story(styles):
    story = []

    # ===== 封面 =====
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph("Pixiv Downloader", styles["cover_title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("用户指南", styles["cover_sub"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"版本 {VERSION} &nbsp;·&nbsp; {date.today():%Y-%m-%d}", styles["cover_info"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("自动分类下载 &nbsp;·&nbsp; WebUI 管理 &nbsp;·&nbsp; 断点续传", styles["cover_info"]))
    story.append(Spacer(1, 65 * mm))
    story.append(Paragraph("本项目 100% 由 AI 生成", styles["cover_info"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph("MIT License &nbsp;·&nbsp; github.com/Najabom/Pixiv_Downloader", styles["cover_info"]))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ===== 目录 =====
    story.append(Paragraph("目录", styles["toc_title"]))
    toc = TableOfContents()
    toc.levelStyles = [styles["toc0"], styles["toc1"]]
    story.append(toc)
    story.append(PageBreak())

    # ===== 1. 快速开始 =====
    story.append(Paragraph("1. 快速开始", styles["h1"]))

    story.append(Paragraph("1.1 下载与解压", styles["h2"]))
    story.append(Paragraph(
        "从 GitHub Releases 页面下载 PixivDownloader-"
        f"{VERSION}.7z 或 .zip 压缩包（内容相同，任选其一），解压到任意可写目录，"
        "例如 D:\\Tools\\PixivDownloader。不建议放在 C:\\Program Files 等需要管理员权限的系统目录。",
        styles["body"]))

    story.append(Paragraph("1.2 Windows SmartScreen 提示", styles["h2"]))
    story.append(Paragraph(
        "本程序未购买商业代码签名证书，首次运行从网络下载的 exe 时，Windows 可能弹出"
        "“Windows 已保护你的电脑”。这是未签名程序的常规提示，并非检测到病毒。处理方法：",
        styles["body"]))
    story.append(Paragraph("点击“更多信息” → “仍要运行”", styles["bullet"], bulletText="•"))
    story.append(Paragraph(
        "或右键 PixivDownloader.exe → 属性 → 勾选底部的“解除锁定” → 确定",
        styles["bullet"], bulletText="•"))
    story.extend(tip_box(
        "可在 Release 页面比对 SHA256 校验值，确认下载的文件完整且未被篡改。",
        styles))

    story.append(Paragraph("1.3 启动程序", styles["h2"]))
    story.append(Paragraph("双击 PixivDownloader.exe", styles["bullet"], bulletText="1."))
    story.append(Paragraph(
        "出现黑色 CMD 窗口（主程序，显示后台日志）。首次运行会自动创建 config\\ 文件夹",
        styles["bullet"], bulletText="2."))
    story.append(Paragraph(
        "浏览器自动打开 http://127.0.0.1:8000，进入仪表盘，即可开始使用",
        styles["bullet"], bulletText="3."))
    story.extend(tip_box(
        "CMD 窗口即程序本体：关闭窗口即退出程序，WebUI 将无法访问。",
        styles))

    story.append(Paragraph("1.4 目录结构", styles["h2"]))
    story.append(make_table([
        ["文件 / 文件夹", "说明"],
        ["PixivDownloader.exe", "主程序，双击运行"],
        ["_internal\\", "运行时依赖，请勿删除或移动"],
        ["用户指南.pdf", "本文档"],
        ["config\\", "配置文件，首次运行自动生成"],
        ["downloads\\", "默认下载目录（可在设置中修改）"],
    ], styles, [45 * mm, CONTENT_W - 45 * mm]))

    story.append(PageBreak())

    # ===== 2. 首次配置 =====
    story.append(Paragraph("2. 首次配置", styles["h1"]))

    story.append(Paragraph("2.1 登录 Pixiv", styles["h2"]))
    story.append(Paragraph(
        "打开 WebUI 的「设置」页，以下两种方式任选其一，保存后点击“测试登录”验证：",
        styles["body"]))
    story.append(Paragraph(
        "<b>方式 A · Cookie</b>：粘贴 Pixiv 网站 Cookie（获取方法见第 4 章）",
        styles["bullet"], bulletText="•"))
    story.append(Paragraph(
        "<b>方式 B · refresh_token</b>：App API 方式，长期有效，不易过期",
        styles["bullet"], bulletText="•"))
    story.extend(tip_box(
        "登录失效时（Cookie 过期等），下载会提示未授权，重新获取凭证并更新即可。",
        styles))

    story.append(Paragraph("2.2 添加作品", styles["h2"]))
    story.append(Paragraph(
        "进入「作品管理」页 → 添加作品（填写作品名）→ 进入作品详情页：", styles["body"]))
    story.append(Paragraph(
        "添加角色：填写角色名与 Pixiv 搜索标签（决定搜索和分类结果）",
        styles["bullet"], bulletText="•"))
    story.append(Paragraph(
        "配置 CP：为 CP 组合添加对应标签；排除标签用于过滤不想要的内容",
        styles["bullet"], bulletText="•"))
    story.extend(tip_box(
        "以上内容也可直接编辑 config\\works.yaml（保存后刷新页面生效）。",
        styles))

    story.append(Paragraph("2.3 常用设置", styles["h2"]))
    story.append(make_table([
        ["设置项", "说明"],
        ["下载目录", "默认 downloads\\，可改为任意路径"],
        ["请求间隔", "API 请求间隔（秒），建议不小于 2，过低易被频率限制"],
        ["最大搜索页数", "每个搜索标签的页数上限"],
        ["NSFW 检测", "发行包未内置检测依赖，详见常见问题"],
    ], styles, [35 * mm, CONTENT_W - 35 * mm]))

    story.append(PageBreak())

    # ===== 3. 功能说明 =====
    story.append(Paragraph("3. 功能说明", styles["h1"]))
    story.append(make_table([
        ["页面", "功能"],
        ["仪表盘", "作品数 / 角色数 / CP 数 / 下载量 / 存储占用"],
        ["作品管理", "卡片网格展示全部作品，详情页管理角色、CP 与过滤标签"],
        ["图库浏览", "按 作品 → 分类 → 图片 三级浏览，点击可查看大图"],
        ["下载", "一键开始 / 停止，实时日志，自动分类，支持断点续传"],
        ["设置", "Pixiv 登录、下载参数、NSFW 检测、全局过滤、全局背景"],
    ], styles, [30 * mm, CONTENT_W - 30 * mm]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "下载流程：按角色 / CP 标签搜索 Pixiv → 逐张下载并按分类存放到作品目录 → "
        "记录下载历史，下次自动跳过已下载内容。中断后再次开始即可续传。",
        styles["body"]))
    story.extend(tip_box(
        "无法自动分类的图片会放入对应作品的“未分类”目录，原因见其中的 _原因记录.txt；"
        "疑似 CP 的标签组合会记录在作品目录下的 _潜在CP.txt。",
        styles))

    # ===== 4. Cookie 获取详解 =====
    story.append(Paragraph("4. Cookie 获取详解", styles["h1"]))
    steps = [
        "浏览器打开 https://www.pixiv.net/ 并登录",
        "按 F12 打开开发者工具，切换到 Network（网络）标签，然后刷新页面",
        "在筛选框中输入 ajax，任选一条请求点击",
        "在 Request Headers（请求标头）中找到以 Cookie: 开头的一整行，完整复制",
        "回到 WebUI「设置」页，粘贴到 Cookie 输入框，保存并点击“测试登录”",
    ]
    for i, text in enumerate(steps, 1):
        story.append(Paragraph(text, styles["bullet"], bulletText=f"{i}."))
    story.extend(tip_box(
        "Cookie 有效期从几天到几周不等，过期后按上述步骤重新获取即可。",
        styles))

    story.append(PageBreak())

    # ===== 5. 常见问题 =====
    story.append(Paragraph("5. 常见问题", styles["h1"]))
    story.append(make_table([
        ["问题", "解决方法"],
        ["出现 SmartScreen 警告", "点击“更多信息 → 仍要运行”；或右键 exe → 属性 → 解除锁定（见 1.2）"],
        ["浏览器没有自动打开", "手动访问 http://127.0.0.1:8000"],
        ["提示端口被占用", "可能已有一个实例在运行，请在任务管理器中结束旧的 PixivDownloader.exe 后重试"],
        ["登录失败 / 提示未授权", "Cookie 或 refresh_token 已失效，重新获取并更新"],
        ["下载慢或频繁失败", "Pixiv 有访问频率限制，请在设置中增大请求间隔"],
        ["图片分类不正确", "检查角色的搜索标签是否准确；未分类图片见“未分类”目录中的 _原因记录.txt"],
        ["找不到配置文件", "config\\ 与 exe 位于同一目录，首次运行后自动生成"],
        ["NSFW 检测不可用", "发行包未内置检测依赖；如需使用，请以源码方式运行并安装 opennsfw2 与 tensorflow"],
        ["如何更新版本", "下载新版压缩包，解压后覆盖 exe 与 _internal\\（保留 config\\ 与 downloads\\ 即可）"],
        ["其他问题", "请到 GitHub Issues 反馈"],
    ], styles, [40 * mm, CONTENT_W - 40 * mm]))

    story.append(PageBreak())

    # ===== 6. 免责声明 =====
    story.append(Paragraph("6. 免责声明与版权", styles["h1"]))
    story.append(Paragraph(
        "本工具仅供个人学习与技术交流使用，请遵守 Pixiv 服务条款"
        "（https://www.pixiv.net/terms/）及所在地区的法律法规。", styles["bullet"], bulletText="•"))
    story.append(Paragraph(
        "请尊重画师版权：下载的作品请勿二次分发、传播或用于商业用途。",
        styles["bullet"], bulletText="•"))
    story.append(Paragraph(
        "使用本工具产生的一切后果由使用者自行承担。",
        styles["bullet"], bulletText="•"))

    story.append(Paragraph("关于本项目", styles["h2"]))
    story.append(Paragraph("全部代码与文档 100% 由 AI 生成，经人工测试与使用。",
        styles["bullet"], bulletText="•"))
    story.append(Paragraph("开源许可证：MIT License",
        styles["bullet"], bulletText="•"))
    story.append(Paragraph("项目地址：https://github.com/Najabom/Pixiv_Downloader",
        styles["bullet"], bulletText="•"))

    return story


def build():
    font, font_bold = register_fonts()
    styles = make_styles(font, font_bold)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = GuideDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="Pixiv Downloader 用户指南",
        author="Najabom (AI-generated)",
        font=font,
        font_bold=font_bold,
    )
    doc.multiBuild(build_story(styles))
    print(f"PDF 已生成: {OUTPUT}")


if __name__ == "__main__":
    build()
