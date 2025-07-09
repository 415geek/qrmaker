import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# 🪄 可选：尝试导入高级拖拽库
try:
    from streamlit_drawable_canvas import st_canvas
    HAS_CANVAS = True
except ImportError:
    HAS_CANVAS = False

st.set_page_config(page_title="RestoSuite QR 桌台码生成器", layout="wide")
st.title("📦 RestoSuite QR 桌台码生成器（滑块版 + 鼠标拖拽版）")

LETTER_SIZE = (612, 792)
LABEL_SIZE = (200, 250)
LABELS_PER_PAGE = 9
COLUMNS, ROWS = 3, 3

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

    custom_text = st.text_input("✏️ 输入自定义文字（如店名）", value="欢迎光临")

    if mode == "简单模式（滑块调节）":
        st.info("使用滑块调节文字位置（推荐：快速简便）")
        desk_x = st.slider("桌号 X 坐标", 0, LABEL_SIZE[0], 40)
        desk_y = st.slider("桌号 Y 坐标", 0, LABEL_SIZE[1], 180)
        custom_x = st.slider("自定义文字 X 坐标", 0, LABEL_SIZE[0], 20)
        custom_y = st.slider("自定义文字 Y 坐标", 0, LABEL_SIZE[1], 210)

    elif mode == "高级模式（鼠标拖拽）":
        if not HAS_CANVAS:
            st.error("当前环境缺少 streamlit-drawable-canvas，请运行：pip install streamlit-drawable-canvas")
            st.stop()

        qr_img = Image.open(qr_files[0]).convert("RGBA").resize((180, 180))
        st.markdown("🖱️ 在下方画布中拖拽文字位置：")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            background_image=qr_img,
            update_streamlit=True,
            height=LABEL_SIZE[1],
            width=LABEL_SIZE[0],
            drawing_mode="transform",
            initial_drawing=[
                {"type": "text", "text": os.path.splitext(qr_files[0].name)[0], "left": 40, "top": 180, "font": "20px Arial"},
                {"type": "text", "text": custom_text, "left": 20, "top": 210, "font": "20px Arial"},
            ],
            key="canvas",
        )
        objs = canvas_result.json_data["objects"]
        desk_x, desk_y = int(objs[0]["left"]), int(objs[0]["top"])
        custom_x, custom_y = int(objs[1]["left"]), int(objs[1]["top"])
        st.success(f"✔️ 已锁定坐标：桌号 ({desk_x},{desk_y}), 店名 ({custom_x},{custom_y})")

    # PDF 生成
    pages = []
    for i in range(0, len(qr_files), LABELS_PER_PAGE):
        page = Image.new("RGB", LETTER_SIZE, "white")
        for idx, file in enumerate(qr_files[i:i + LABELS_PER_PAGE]):
            qr = Image.open(file).convert("RGBA").resize((180, 180))
            desk_name = os.path.splitext(file.name)[0]
            label = Image.new("RGB", LABEL_SIZE, "white")
            draw = ImageDraw.Draw(label)
            label.paste(qr, (10, 0))
            draw.text((desk_x, desk_y), desk_name, font=font, fill="black")
            draw.text((custom_x, custom_y), custom_text, font=font, fill="gray")
            row, col = divmod(idx, COLUMNS)
            x = col * LABEL_SIZE[0]
            y = row * LABEL_SIZE[1]
            page.paste(label, (x, y))
        pages.append(page)

    st.subheader("🖼️ 标签 PDF 预览 (第1页)")
    st.image(pages[0])

    pdf_bytes = BytesIO()
    pages[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pages[1:])
    st.download_button("📥 下载标签 PDF（Letter 尺寸）", data=pdf_bytes.getvalue(), file_name="桌台二维码标签.pdf", mime="application/pdf")
