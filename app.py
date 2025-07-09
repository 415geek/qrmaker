
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

st.set_page_config(page_title="RestoSuite QR Generator", layout="wide")
st.title("📦 RestoSuite 桌台码生成器（滑块 + 拖拽 + Logo + 边框）")

# 常量定义
LETTER_SIZE = (612, 792)
LABEL_SIZE = (200, 300)
LABELS_PER_PAGE = 9
COLUMNS = 3

# 加载字体（缓存）
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
    logo_raw = Image.open("logo.png").convert("RGBA")
    logo_img = logo_raw

# 上传二维码图片
qr_files = st.file_uploader("📷 批量上传 QR 图（文件名作为桌号）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if qr_files:
    st.success(f"✅ 成功上传 {len(qr_files)} 张二维码")

    # 模式选择
    mode = st.radio("选择文字定位模式：", ["滑块调节（兼容快速）", "鼠标拖拽（更直观）"])

    custom_text = st.text_input("✏️ 自定义文字（店名等）", value="欢迎光临")

    # 初始化文字坐标变量
    desk_x = desk_y = custom_x = custom_y = None

    if mode.startswith("滑块"):
        desk_x = st.slider("桌号 X 坐标", 0, LABEL_SIZE[0], 40)
        desk_y = st.slider("桌号 Y 坐标", 0, LABEL_SIZE[1] - 60, 180)
        custom_x = st.slider("文字 X 坐标", 0, LABEL_SIZE[0], 20)
        custom_y = st.slider("文字 Y 坐标", 0, LABEL_SIZE[1] - 60, 230)

    else:
        if not HAS_CANVAS:
            st.error("缺少 streamlit-drawable-canvas 库，请安装后启用高级模式")
            st.stop()
        qr_img = Image.open(qr_files[0]).convert("RGBA").resize((180, 180))
        st.markdown("🖱️ 在画布中拖动文字来设置位置")
        canvas = st_canvas(
            fill_color="rgba(0,0,0,0)",
            background_image=qr_img,
            height=LABEL_SIZE[1], width=LABEL_SIZE[0],
            drawing_mode="transform",
            initial_drawing=[
                {"type":"text","text":os.path.splitext(qr_files[0].name)[0],"left":40,"top":180,"font":"20px Arial"},
                {"type":"text","text":custom_text,"left":20,"top":230,"font":"20px Arial"},
            ],
            key="cv",
        )
        objs = canvas.json_data["objects"]
        desk_x, desk_y = int(objs[0]["left"]), int(objs[0]["top"])
        custom_x, custom_y = int(objs[1]["left"]), int(objs[1]["top"])
        st.success(f"✔️ 锁定文字位置：桌号 ({desk_x},{desk_y}), 自定义文字 ({custom_x},{custom_y})")

    # 标签绘制函数（含边框 Logo）
    def create_label(qr_img, desk_name):
        label = Image.new("RGB", LABEL_SIZE, "white")
        draw = ImageDraw.Draw(label)
        # 边框
        draw.rounded_rectangle((5,5, LABEL_SIZE[0]-5, LABEL_SIZE[1]-5), radius=20, outline="#237EFB", width=6)
        label.paste(qr_img, (10,10))
        draw.text((desk_x, desk_y), desk_name, font=font, fill="black")
        draw.text((custom_x, custom_y), custom_text, font=font, fill="gray")
        if logo_img:
            w = 120
            r = w / logo_img.width
            logo_r = logo_img.resize((w, int(logo_img.height * r)))
            x = (LABEL_SIZE[0] - w)//2
            y = LABEL_SIZE[1] - logo_r.height - 10
            label.paste(logo_r, (x,y), logo_r)
        return label

    # 生成 PDF 各页
    pages = []
    for i in range(0, len(qr_files), LABELS_PER_PAGE):
        page = Image.new("RGB", LETTER_SIZE, "white")
        for idx, f in enumerate(qr_files[i:i+LABELS_PER_PAGE]):
            qr = Image.open(f).convert("RGBA").resize((180,180))
            desk = os.path.splitext(f.name)[0]
            lbl = create_label(qr, desk)
            r, c = divmod(idx, COLUMNS)
            page.paste(lbl, (c*LABEL_SIZE[0], r*LABEL_SIZE[1]))
        pages.append(page)

    st.subheader("🖼️ PDF 预览（第1页）")
    st.image(pages[0])

    buf = BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    st.download_button("📥 下载 Letter 大小 PDF", buf.getvalue(), "桌台二维码标签.pdf", mime="application/pdf")
