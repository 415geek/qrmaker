import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

st.set_page_config(page_title="RestoSuite QR 桌台码生成器 (拖拽版)", layout="wide")
st.title("📦 RestoSuite QR 桌台码生成器 (鼠标拖拽版)")

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
    st.success(f"✅ 上传了 {len(qr_files)} 张二维码")
    desk_name = os.path.splitext(qr_files[0].name)[0]
    qr_img = Image.open(qr_files[0]).convert("RGBA").resize((180, 180))

    custom_text = st.text_input("✏️ 输入自定义文字", value="欢迎光临")

    # 预览画布（拖拽）
    st.markdown("🖱️ 拖拽桌号和店铺文字到合适位置")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # Transparent background
        background_image=qr_img,
        update_streamlit=True,
        height=LABEL_SIZE[1],
        width=LABEL_SIZE[0],
        drawing_mode="transform",
        initial_drawing=[
            {"type": "text", "text": desk_name, "left": 40, "top": 180, "font": "20px Arial"},
            {"type": "text", "text": custom_text, "left": 20, "top": 210, "font": "20px Arial"},
        ],
        key="canvas",
    )

    # 获取拖拽后坐标
    if canvas_result.json_data:
        objs = canvas_result.json_data["objects"]
        desk_obj = objs[0]
        custom_obj = objs[1]
        desk_coords = (int(desk_obj["left"]), int(desk_obj["top"]))
        custom_coords = (int(custom_obj["left"]), int(custom_obj["top"]))

        st.info(f"桌号坐标: {desk_coords}, 自定义文字坐标: {custom_coords}")

        # PDF 批量生成
        pages = []
        for i in range(0, len(qr_files), LABELS_PER_PAGE):
            page = Image.new("RGB", LETTER_SIZE, "white")
            for idx, file in enumerate(qr_files[i:i + LABELS_PER_PAGE]):
                qr = Image.open(file).convert("RGBA").resize((180, 180))
                desk_name = os.path.splitext(file.name)[0]

                # 单个标签
                label = Image.new("RGB", LABEL_SIZE, "white")
                draw = ImageDraw.Draw(label)
                label.paste(qr, (10, 0))
                draw.text(desk_coords, desk_name, font=font, fill="black")
                draw.text(custom_coords, custom_text, font=font, fill="gray")

                # 拼接到整页
                row, col = divmod(idx, COLUMNS)
                x = col * LABEL_SIZE[0]
                y = row * LABEL_SIZE[1]
                page.paste(label, (x, y))
            pages.append(page)

        st.subheader("🖼️ 标签 PDF 预览 (第 1 页)")
        st.image(pages[0])

        # 导出 PDF
        pdf_bytes = BytesIO()
        pages[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pages[1:])
        st.download_button("📥 下载标签 PDF（Letter 尺寸）", data=pdf_bytes.getvalue(), file_name="桌台二维码标签.pdf", mime="application/pdf")
