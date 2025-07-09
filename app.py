import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# 页面设置
st.set_page_config(page_title="RestoSuite 桌台码生成器", layout="centered")
st.title("📦 RestoSuite QR 桌台码生成器")
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <span style="font-size: 0.9rem; color: gray;">
            📷 上传 QR 图像，系统生成标准标签样式并导出 PDF
        </span>
        <a href="https://www.linkedin.com/in/lingyu-maxwell-lai" target="_blank"
           style="background-color: white; border: 1px solid #ddd; border-radius: 6px; padding: 2px 6px; display: flex; align-items: center; text-decoration: none;">
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png"
                 width="16" height="16" style="margin-right: 4px;" />
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# 加载字体
@st.cache_data
def load_font(size=48):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()
font_large = load_font(72)
font_small = load_font(40)

# 自动裁剪透明留白的 logo
def trim_logo(img):
    bbox = img.getbbox()
    return img.crop(bbox)

# 尝试加载 logo
try:
    logo_raw = Image.open("logo.png").convert("RGBA")
    logo_img = trim_logo(logo_raw).resize((480, 120))
except:
    logo_img = None
    st.warning("⚠️ 未找到 logo.png，标签中将省略 Logo。")

# 上传 QR 图像
qr_files = st.file_uploader("📷 上传 QR 图像（如 A1.png、B2.jpg）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# 样式定义
label_w, label_h = 800, 1000
qr_size = (460, 460)
qr_offset = (170, 140)
labels_per_page = 9
cols, rows = 3, 3

# 店铺文字输入
custom_text = st.text_input("✏️ 输入店铺名称", "欢迎光临")

# 文字位置调节（滑块）
st.markdown("🎯 调整文字位置：")
desk_x = st.slider("桌号文字 X 坐标", 0, label_w, 280)
desk_y = st.slider("桌号文字 Y 坐标", 0, label_h, 650)
custom_x = st.slider("店铺文字 X 坐标", 0, label_w, 250)
custom_y = st.slider("店铺文字 Y 坐标", 0, label_h, 850)

# 生成单个标签
def create_label(qr_img, desk_name):
    canvas = Image.new("RGB", (label_w, label_h), "white")
    draw = ImageDraw.Draw(canvas)

    # 蓝色圆角边框
    draw.rounded_rectangle((10, 10, label_w - 10, label_h - 10), radius=40, outline="#237EFB", width=13)

    # QR
    qr_resized = qr_img.resize(qr_size)
    canvas.paste(qr_resized, qr_offset, qr_resized)

    # 桌号文字
    draw.text((desk_x, desk_y), desk_name, font=font_large, fill="black")

    # 店铺文字
    draw.text((custom_x, custom_y), custom_text, font=font_small, fill="gray")

    # Logo
    if logo_img:
        canvas.paste(logo_img, ((label_w - logo_img.width) // 2, 740), logo_img)

    return canvas

if qr_files:
    st.success(f"✅ 已上传 {len(qr_files)} 张二维码，将生成标签并分页导出")

    page_w = label_w * cols
    page_h = label_h * rows
    pages = []

    for i in range(0, len(qr_files), labels_per_page):
        canvas = Image.new("RGB", (page_w, page_h), "white")

        for idx, file in enumerate(qr_files[i:i + labels_per_page]):
            qr = Image.open(file).convert("RGBA")
            desk_name = os.path.splitext(file.name)[0]
            label = create_label(qr, desk_name)

            row, col = divmod(idx, cols)
            x = col * label_w
            y = row * label_h
            canvas.paste(label, (x, y))

        pages.append(canvas)

    # 预览
    st.subheader("🖼️ 标签预览（第1页）：")
    st.image(pages[0])

    # 导出 PDF
    pdf_bytes = BytesIO()
    pages[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pages[1:])
    st.download_button("📥 下载标签 PDF", data=pdf_bytes.getvalue(), file_name="RestoSuite_Tags.pdf", mime="application/pdf")
