import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# 鼠标拖拽组件支持
try:
    from streamlit_drawable_canvas import st_canvas
    HAS_CANVAS = True
except ImportError:
    HAS_CANVAS = False

st.set_page_config(page_title="RestoSuite QR 桌台码生成器", layout="wide")
st.title("📦 RestoSuite QR 桌台码生成器（滑块 + 拖拽）")

LETTER_SIZE = (612, 792)
LABEL_SIZE = (200, 250)
LABELS_PER_PAGE = 9
COLUMNS = 3

@st.cache_data
def load_font(size=20):
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

font = load_font(20)
qr_files = st.file_uploader("📷 上传 QR 图像", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if qr_files:
    st.success(f"✅ 成功上传 {len(qr_files)} 张二维码")
    mode = st.radio("请选择模式：", ["简单模式（滑块调节）", "高级模式（鼠标拖拽）"])
    custom_text = st.text_input("✏️ 自定义文字（店名等）", value="欢迎光临")

    if mode.startswith("简单"):
        desk_x = st.slider("桌号 X 坐标", 0, LABEL_SIZE[0], 40)
        desk_y = st.slider("桌号 Y 坐标", 0, LABEL_SIZE[1], 180)
        custom_x = st.slider("文字 X 坐标", 0, LABEL_SIZE[0], 20)
        custom_y = st.slider("文字 Y 坐标", 0, LABEL_SIZE[1], 210)
    else:
        if not HAS_CANVAS:
            st.error("缺少 streamlit-drawable-canvas 库，无法使用高级模式")
            st.stop()
        qr_img = Image.open(qr_files[0]).convert("RGBA").resize((180, 180))
        st.markdown("🖱️ 拖拽画布中的文字，设置位置")
        canvas = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            background_image=qr_img,
            height=LABEL_SIZE[1], width=LABEL_SIZE[0],
            drawing_mode="transform",
            initial_drawing=[
                {"type":"text","text":os.path.splitext(qr_files[0].name)[0],"left":40,"top":180,"font":"20px Arial"},
                {"type":"text","text":custom_text,"left":20,"top":210,"font":"20px Arial"},
            ],
            key="canvas",
        )
        objs = canvas.json_data["objects"]
        desk_x, desk_y = int(objs[0]["left"]), int(objs[0]["top"])
        custom_x, custom_y = int(objs[1]["left"]), int(objs[1]["top"])
        st.success(f"坐标锁定：桌号 ({desk_x},{desk_y}), 文字 ({custom_x},{custom_y})")

    pages = []
    for i in range(0, len(qr_files), LABELS_PER_PAGE):
        page = Image.new("RGB", LETTER_SIZE, "white")
        for idx, f in enumerate(qr_files[i:i+LABELS_PER_PAGE]):
            qr = Image.open(f).convert("RGBA").resize((180, 180))
            desk = os.path.splitext(f.name)[0]
            label = Image.new("RGB", LABEL_SIZE, "white")
            draw = ImageDraw.Draw(label)
            label.paste(qr, (10, 0))
            draw.text((desk_x, desk_y), desk, font=font, fill="black")
            draw.text((custom_x, custom_y), custom_text, font=font, fill="gray")
            r, c = divmod(idx, COLUMNS)
            page.paste(label, (c*LABEL_SIZE[0], r*LABEL_SIZE[1]))
        pages.append(page)

    st.subheader("🖼️ PDF 预览（第 1 页）")
    st.image(pages[0])
    buf = BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    st.download_button("📥 下载 Letter 大小 PDF", buf.getvalue(), "桌台二维码.pdf", mime="application/pdf")
