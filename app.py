import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
from pathlib import Path

st.set_page_config(
    page_title="Icon Grid Printer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    :root {
        --primary-color: #007bff;
        --primary-hover: #0056b3;
        --success-color: #28a745;
        --success-hover: #218838;
        --border-radius: 8px;
        --padding: 1rem;
    }

    .main { padding: 2rem; }

    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        padding: 0.6rem 2rem;
        font-size: 16px;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: var(--primary-hover);
        transform: translateY(-2px);
    }

    .info-box, .success-box {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .info-box {
        background-color: rgba(0, 123, 255, 0.1);
        border-left: 4px solid var(--primary-color);
    }
    .success-box {
        background-color: rgba(40, 167, 69, 0.1);
        border-left: 4px solid var(--success-color);
    }

    .stDownloadButton>button {
        background-color: var(--success-color);
        color: white;
        width: 100%;
        padding: 0.75rem;
        font-size: 16px;
        border-radius: var(--border-radius);
        border: none;
    }
    .stDownloadButton>button:hover { background-color: var(--success-hover); }

    .upload-section {
        border: 2px dashed #888;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }

    /* Toggle button style override */
    div[data-testid="stToggle"] label {
        font-size: 16px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def create_icon_grid(file_entries, columns=4, rows=None, dpi=300, show_labels=True):
    """
    Create a printable grid of icons with cutting guides.
    file_entries: list of (uploaded_file, count) tuples
    """
    # Expand entries by their duplicate count
    expanded = []
    for uploaded_file, count in file_entries:
        for _ in range(count):
            expanded.append(uploaded_file)

    if not expanded:
        return None

    if rows is None:
        rows = (len(expanded) + columns - 1) // columns

    page_width = int(8.5 * dpi)
    page_height = int(11 * dpi)

    usable_width = 8.2
    usable_height = 10.7

    max_width_per_icon = usable_width / columns
    max_height_per_icon = usable_height / rows

    icon_size = min(max_width_per_icon, max_height_per_icon)
    icon_width_px = int(icon_size * dpi)
    icon_height_px = int(icon_size * dpi)

    total_grid_width = columns * icon_width_px
    total_grid_height = rows * icon_height_px
    margin_x = (page_width - total_grid_width) // 2
    margin_y = (page_height - total_grid_height) // 2

    canvas = Image.new('RGB', (page_width, page_height), 'white')
    draw = ImageDraw.Draw(canvas)

    font_size = int(0.14 * icon_height_px)
    font = ImageFont.load_default()

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue

    for idx, uploaded_file in enumerate(expanded):
        row_idx = idx // columns
        col_idx = idx % columns

        # Reset file pointer (needed since same file object may be reused for duplicates)
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        white_bg.paste(img, (0, 0), img)
        img = white_bg.convert('RGB')

        if show_labels:
            label_space = int(0.40 * icon_height_px)
            img_display_height = int(0.50 * icon_height_px)
        else:
            label_space = 0
            img_display_height = int(0.88 * icon_height_px)

        img_display_width = int(0.85 * icon_width_px)

        img.thumbnail((img_display_width, img_display_height), Image.Resampling.LANCZOS)

        filename = Path(uploaded_file.name).stem
        display_name = filename.replace('_', ' ')

        x = margin_x + (col_idx * icon_width_px)
        y = margin_y + (row_idx * icon_height_px)

        border_width = max(2, int(0.008 * dpi))
        draw.rectangle(
            [x, y, x + icon_width_px, y + icon_height_px],
            outline='black',
            width=border_width
        )

        img_x = x + (icon_width_px - img.width) // 2
        img_y = y + (icon_height_px - label_space - img.height) // 2
        canvas.paste(img, (img_x, img_y))

        if show_labels:
            available_width = int(icon_width_px * 0.90)
            available_height = int(label_space * 0.85)

            def wrap_and_measure(text, test_font, max_width):
                words = text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=test_font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                return lines

            min_font_size = int(0.08 * icon_height_px)
            max_font_size = int(0.16 * icon_height_px)
            best_font = font
            best_lines = []

            for test_size in range(max_font_size, min_font_size - 1, -1):
                test_font = None
                for font_path in font_paths:
                    try:
                        test_font = ImageFont.truetype(font_path, test_size)
                        break
                    except:
                        continue
                if test_font is None:
                    test_font = font

                test_lines = wrap_and_measure(display_name, test_font, available_width)
                line_height = int(test_size * 1.2)
                total_height = len(test_lines) * line_height

                if total_height <= available_height and len(test_lines) <= 4:
                    all_fit = all(
                        draw.textbbox((0, 0), line, font=test_font)[2] - draw.textbbox((0, 0), line, font=test_font)[0] <= available_width
                        for line in test_lines
                    )
                    if all_fit:
                        best_font = test_font
                        best_lines = test_lines
                        break

            if not best_lines:
                best_lines = wrap_and_measure(display_name, font, available_width)
                if len(best_lines) > 4:
                    best_lines = best_lines[:4]
                    best_lines[-1] = best_lines[-1][:12] + '...'

            line_height = int(best_font.size * 1.2)
            total_text_height = len(best_lines) * line_height
            text_start_y = y + icon_height_px - label_space + (label_space - total_text_height) // 2

            for i, line in enumerate(best_lines):
                bbox = draw.textbbox((0, 0), line, font=best_font)
                text_width = bbox[2] - bbox[0]
                text_x = x + (icon_width_px - text_width) // 2
                text_y = text_start_y + (i * line_height)
                draw.text((text_x, text_y), line, fill='black', font=best_font)

    output = io.BytesIO()
    canvas.save(output, format='PNG', dpi=(dpi, dpi))
    output.seek(0)

    return output, canvas


# ── Main App ──────────────────────────────────────────────────────────────────

st.title("Icon Grid Printer")
st.markdown("### Create printable grids of icons for classroom activities")

st.markdown("""
<div class="info-box">
    <strong>How it works:</strong><br><br>
    1. Upload your icon images (PNG, JPG, GIF, etc.)<br>
    2. Set how many copies of each icon you want<br>
    3. Toggle labels on or off, then configure the grid layout<br>
    4. Generate and download your printable 8.5×11" grid
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload Icon Images",
    type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
    accept_multiple_files=True,
    help="Upload multiple icon images to create a grid"
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} image(s) uploaded")

    # ── Per-image controls ─────────────────────────────────────────────────
    st.markdown("### Icon Settings")

    # Initialize session state for counts
    if "icon_counts" not in st.session_state:
        st.session_state.icon_counts = {}

    file_entries = []  # (uploaded_file, count)

    # Header row
    h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
    with h_col1:
        st.markdown("**Image**")
    with h_col2:
        st.markdown("**Preview**")
    with h_col3:
        st.markdown("**Copies**")

    st.divider()

    for uploaded_file in uploaded_files:
        key = f"count_{uploaded_file.name}"
        if key not in st.session_state.icon_counts:
            st.session_state.icon_counts[key] = 1

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{Path(uploaded_file.name).stem.replace('_', ' ')}**")
            st.caption(uploaded_file.name)

        with col2:
            uploaded_file.seek(0)
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, width=60)

        with col3:
            count = st.number_input(
                "Copies",
                min_value=1,
                max_value=20,
                value=st.session_state.icon_counts[key],
                step=1,
                key=key,
                label_visibility="collapsed"
            )
            st.session_state.icon_counts[key] = count

        uploaded_file.seek(0)
        file_entries.append((uploaded_file, count))

    # ── Grid & Label options ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Grid Configuration")

    # Label toggle — single prominent toggle
    show_labels = st.toggle("Show Labels", value=True, help="Display the image filename as a label below each icon")

    total_icons = sum(count for _, count in file_entries)
    st.caption(f"Total icons to place: **{total_icons}**")

    col1, col2 = st.columns(2)
    with col1:
        columns = st.number_input(
            "Columns",
            min_value=1, max_value=6, value=4, step=1,
            help="Number of icons per row"
        )
    with col2:
        auto_rows = (total_icons + columns - 1) // columns
        rows = st.number_input(
            "Rows",
            min_value=1, max_value=10, value=auto_rows, step=1,
            help="Number of rows (auto-calculated based on total icons)"
        )

    total_cells = columns * rows
    st.info(f"Grid: {columns} columns × {rows} rows = {total_cells} cells  |  Icons to place: {total_icons}")

    if total_icons > total_cells:
        st.warning(f"⚠️ {total_icons} icons but only {total_cells} cells — some icons will be excluded.")

    st.markdown("---")

    if st.button("Generate Grid", type="primary"):
        with st.spinner("Creating icon grid…"):
            try:
                output, preview = create_icon_grid(
                    file_entries,
                    columns=columns,
                    rows=rows,
                    show_labels=show_labels
                )

                st.markdown(f"""
                <div class="success-box">
                    <strong>Grid Created Successfully</strong><br><br>
                    Grid size: <strong>{columns} × {rows}</strong> &nbsp;|&nbsp;
                    Labels: <strong>{"On" if show_labels else "Off"}</strong><br>
                    Format: 8.5" × 11" at 300 DPI — ready to print
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### Preview")
                st.image(preview, caption="Icon Grid Preview", use_container_width=True)

                st.download_button(
                    label="⬇️ Download Printable Grid (PNG)",
                    data=output,
                    file_name="icon_grid.png",
                    mime="image/png",
                    type="primary"
                )

            except Exception as e:
                st.error(f"Error creating grid: {str(e)}")

else:
    st.markdown("""
    <div class="upload-section">
        <h3>Upload icon images to get started</h3>
        <p>Select multiple images to create a printable grid with cutting guides.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

with st.expander("Tips for Best Results"):
    st.markdown("""
    - **File names** become labels — use descriptive names (`apple.png` → "apple")
    - **Underscores** are converted to spaces (`red_apple.png` → "red apple")
    - **Copies** — set each icon's copy count to fill answer keys, matching sets, etc.
    - **Labels toggle** — turn off for clean picture-only grids
    - **Print settings**: Use 100% scale (no fit-to-page) for accurate sizing
    - **Common uses**:
        - 4 columns × 1 row = Answer key for 4-question worksheet
        - 3 columns × 3 rows = Matching activity grid
    - **Supported formats**: PNG (best), JPG, JPEG, GIF, BMP
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px;">
    <p>Created by Derik Vo | N2Y Adaptation Tools</p>
</div>
""", unsafe_allow_html=True)