import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# 尝试导入鼠标拖拽组件
try:
    from streamlit_drawable_canvas import st_canvas
    HAS_CANVAS = True
except ImportError:
    HAS_CANVAS = False

st.set_page_config(page_title="RestoSuite QR 生成器", layout="wide")
st.title("📦 RestoSuite 桌台码标签生成器（Logo + 边框 + 可调文字）")

# 配置
LETTER_SIZE = (612, 792)
LABEL_SIZE = (220, 300)  # 稍微加高点以容纳 Logo 和文字
LABELS_PER_PAGE = 9
COLUMNS = 3

# 加载字体
@st.cache_data
def load_font(size=20):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf"
    ]:
        try:
            return ImageFont.truetype(p, size)
        except:
            continue
    return ImageFont.load_default()

font = load_font(20)

# 加载 Logo
logo_img = None
if os.path.exists("logo.png"):
    logo_img = Image.open("logo.png").convert("RGBA")

# 上传二维码
qr_files = st.file_uploader("📷 批量上传 QR 图（文件名即桌号）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if qr_files:
    st.success(f"✅ 上传 {len(qr_files)} 张二维码")
    
    custom_text = st.text_input("✏️ 输入店铺名称", "欢迎光临")

    mode = st.radio("选择调节方式：", ["滑块调节（简便快速）", "鼠标拖拽（直观灵活）"])

    if mode.startswith("滑块"):
        st.info("滑块调节：")
        desk_x = st.slider("桌号文字 X 坐标", 0, LABEL_SIZE[0], 70)
        desk_y = st.slider("桌号文字 Y 坐标", 0, LABEL_SIZE[1], 200)
        custom_x = st.slider("店铺文字 X 坐标", 0, LABEL_SIZE[0], 50)
        custom_y = st.slider("店铺文字 Y 坐标", 0, LABEL_SIZE[1], 240)
    else:
        if not HAS_CANVAS:
            st.error("缺少 streamlit-drawable-canvas，无法使用鼠标拖拽功能")
            st.stop()

        qr_img = Image.open(qr_files[0]).convert("RGBA").resize((180, 180))
        canvas = st_canvas(
            fill_color="rgba(0,0,0,0)",
            background_image=qr_img,
            height=LABEL_SIZE[1], width=LABEL_SIZE[0],
            drawing_mode="transform",
            initial_drawing=[
                {"type":"text", "text":os.path.splitext(qr_files[0].name)[0], "left":70, "top":200, "font":"20px Arial"},
                {"type":"text", "text":custom_text, "left":50, "top":240, "font":"20px Arial"},
            ],
            key="canvas",
        )
        objs = canvas.json_data["objects"]
        desk_x, desk_y = int(objs[0]["left"]), int(objs[0]["top"])
        custom_x, custom_y = int(objs[1]["left"]), int(objs[1]["top"])

    # 生成标签
    def create_label(qr_img, desk_name):
        label = Image.new("RGB", LABEL_SIZE, "white")
        draw = ImageDraw.Draw(label)
        # 蓝色圆角边框
        draw.rounded_rectangle((5,5,LABEL_SIZE[0]-5,LABEL_SIZE[1]-5), radius=20, outline="#237EFB", width=6)
        label.paste(qr_img, (20,20))
        draw.text((desk_x, desk_y), desk_name, font=font, fill="black")
        draw.text((custom_x, custom_y), custom_text, font=font, fill="gray")
        if logo_img:
            w = 120
            r = w / logo_img.width
            logo_resized = logo_img.resize((w, int(logo_img.height * r)))
            x = (LABEL_SIZE[0] - w) // 2
            y = LABEL_SIZE[1] - logo_resized.height - 10
            label.paste(logo_resized, (x,y), logo_resized)
        return label

    # 批量生成 PDF
    pages = []
    for i in range(0, len(qr_files), LABELS_PER_PAGE):
        page = Image.new("RGB", LETTER_SIZE, "white")
        for idx, f in enumerate(qr_files[i:i+LABELS_PER_PAGE]):
            qr = Image.open(f).convert("RGBA").resize((180, 180))
            desk_name = os.path.splitext(f.name)[0]
            lbl = create_label(qr, desk_name)
            r, c = divmod(idx, COLUMNS)
            page.paste(lbl, (c*LABEL_SIZE[0], r*LABEL_SIZE[1]))
        pages.append(page)

    st.subheader("🖼️ PDF 预览（第 1 页）")
    st.image(pages[0])

    buf = BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    st.download_button("📥 下载标签 PDF（Letter 尺寸）", buf.getvalue(), "桌台二维码标签.pdf", mime="application/pdf")
