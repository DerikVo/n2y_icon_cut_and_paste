import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from pathlib import Path

st.set_page_config(
    page_title="Icon Grid Printer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-size: 16px;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
    }
    
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .stDownloadButton>button {
        background-color: #28a745;
        color: white;
        width: 100%;
        padding: 0.75rem;
        font-size: 16px;
        border-radius: 8px;
    }
    
    .stDownloadButton>button:hover {
        background-color: #218838;
    }
    
    .upload-section {
        border: 2px dashed #ddd;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_icon_grid(uploaded_files, columns=4, rows=None, dpi=300):
    """
    Create a printable grid of icons with cutting guides
    """
    if not uploaded_files:
        return None
    
    # Calculate rows if not specified
    if rows is None:
        rows = (len(uploaded_files) + columns - 1) // columns
    
    # Page dimensions (8.5 x 11 inches)
    page_width = int(8.5 * dpi)
    page_height = int(11 * dpi)
    
    # Calculate icon size to fit the page - make SQUARE icons
    usable_width = 8.2
    usable_height = 10.7
    
    max_width_per_icon = usable_width / columns
    max_height_per_icon = usable_height / rows
    
    icon_size = min(max_width_per_icon, max_height_per_icon)
    icon_width_px = int(icon_size * dpi)
    icon_height_px = int(icon_size * dpi)
    
    # Calculate margins to center the grid
    total_grid_width = columns * icon_width_px
    total_grid_height = rows * icon_height_px
    margin_x = (page_width - total_grid_width) // 2
    margin_y = (page_height - total_grid_height) // 2
    
    # Create white canvas
    canvas = Image.new('RGB', (page_width, page_height), 'white')
    draw = ImageDraw.Draw(canvas)
    
    # Font setup
    font_size = int(0.14 * icon_height_px)
    font = ImageFont.load_default()
    
    # Try to load a better font
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
    
    # Process each image
    for idx, uploaded_file in enumerate(uploaded_files):
        row_idx = idx // columns
        col_idx = idx % columns
        
        # Load image
        img = Image.open(uploaded_file)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create white background
        white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        white_bg.paste(img, (0, 0), img)
        img = white_bg.convert('RGB')
        
        # Space for label
        label_space = int(0.40 * icon_height_px)
        img_display_height = int(0.50 * icon_height_px)
        img_display_width = int(0.85 * icon_width_px)
        
        # Resize image maintaining aspect ratio
        img.thumbnail((img_display_width, img_display_height), Image.Resampling.LANCZOS)
        
        # Get filename without extension
        filename = Path(uploaded_file.name).stem
        display_name = filename.replace('_', ' ')
        
        # Available space for text
        available_width = int(icon_width_px * 0.90)
        available_height = int(label_space * 0.85)
        
        # Wrap text function
        def wrap_and_measure(text, test_font, max_width):
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=test_font)
                line_width = bbox[2] - bbox[0]
                
                if line_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
        
        # Try different font sizes
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
                all_fit = True
                for line in test_lines:
                    bbox = draw.textbbox((0, 0), line, font=test_font)
                    if bbox[2] - bbox[0] > available_width:
                        all_fit = False
                        break
                
                if all_fit:
                    best_font = test_font
                    best_lines = test_lines
                    break
        
        if not best_lines:
            best_lines = wrap_and_measure(display_name, font, available_width)
            if len(best_lines) > 4:
                best_lines = best_lines[:4]
                best_lines[-1] = best_lines[-1][:12] + '...'
        
        lines = best_lines
        
        # Calculate position
        x = margin_x + (col_idx * icon_width_px)
        y = margin_y + (row_idx * icon_height_px)
        
        # Draw cutting guide border
        border_width = max(2, int(0.008 * dpi))
        draw.rectangle(
            [x, y, x + icon_width_px, y + icon_height_px],
            outline='black',
            width=border_width
        )
        
        # Center the image
        img_x = x + (icon_width_px - img.width) // 2
        img_y = y + (icon_height_px - label_space - img.height) // 2
        canvas.paste(img, (img_x, img_y))
        
        # Draw text
        line_height = int(best_font.size * 1.2)
        total_text_height = len(lines) * line_height
        text_start_y = y + icon_height_px - label_space + (label_space - total_text_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=best_font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (icon_width_px - text_width) // 2
            text_y = text_start_y + (i * line_height)
            draw.text((text_x, text_y), line, fill='black', font=best_font)
    
    # Save to bytes
    output = io.BytesIO()
    canvas.save(output, format='PNG', dpi=(dpi, dpi))
    output.seek(0)
    
    return output, canvas

# Main App
st.title("Icon Grid Printer")
st.markdown("### Create printable grids of icons for classroom activities")

# Info box
st.markdown("""
<div class="info-box">
    <strong>How it works:</strong><br><br>
    1. Upload your icon images (PNG, JPG, GIF, etc.)<br>
    2. Configure grid layout (columns and rows)<br>
    3. Generate a printable 8.5x11" grid with cutting guides<br>
    4. Download and print at 100% scale
</div>
""", unsafe_allow_html=True)

# File upload - multiple files
uploaded_files = st.file_uploader(
    "Upload Icon Images",
    type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
    accept_multiple_files=True,
    help="Upload multiple icon images to create a grid"
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} images uploaded")
    
    # Show preview of uploaded images
    with st.expander("Preview Uploaded Images"):
        cols = st.columns(4)
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                img = Image.open(file)
                st.image(img, caption=file.name, use_container_width=True)
                file.seek(0)  # Reset file pointer
    
    # Grid configuration
    st.markdown("### Grid Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        columns = st.number_input(
            "Columns",
            min_value=1,
            max_value=6,
            value=4,
            step=1,
            help="Number of icons per row"
        )
    
    with col2:
        auto_rows = (len(uploaded_files) + columns - 1) // columns
        rows = st.number_input(
            "Rows",
            min_value=1,
            max_value=10,
            value=auto_rows,
            step=1,
            help="Number of rows (auto-calculated by default)"
        )
    
    total_cells = columns * rows
    st.info(f"Grid will have {columns} columns × {rows} rows = {total_cells} cells")
    
    if len(uploaded_files) > total_cells:
        st.warning(f"You have {len(uploaded_files)} images but only {total_cells} cells. Some images will be excluded.")
    
    st.markdown("---")
    
    if st.button("Generate Grid", type="primary"):
        with st.spinner("Creating icon grid... This may take a moment."):
            try:
                output, preview = create_icon_grid(uploaded_files, columns=columns, rows=rows)
                
                st.markdown("""
                <div class="success-box">
                    <strong>Grid Created Successfully</strong><br><br>
                    Grid size: <strong>{} × {}</strong><br>
                    Format: 8.5" × 11" at 300 DPI<br>
                    Ready to print
                </div>
                """.format(columns, rows), unsafe_allow_html=True)
                
                # Show preview
                st.markdown("### Preview")
                st.image(preview, caption="Icon Grid Preview", use_container_width=True)
                
                # Download button
                st.download_button(
                    label="Download Printable Grid (PNG)",
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

# Tips section
with st.expander("Tips for Best Results"):
    st.markdown("""
    - **File names** become labels - use descriptive names (e.g., "apple.png" shows as "apple")
    - **Underscores** are converted to spaces ("red_apple.png" → "red apple")
    - **Square images** work best for consistent appearance
    - **Print settings**: Use 100% scale (no fit-to-page) for accurate sizing
    - **Common uses**:
        - 4 columns × 1 row = Answer key for 4-question worksheet
        - 4 columns × 2 rows = Answer keys for 2 students
        - 3 columns × 3 rows = Matching activity grid
    - **Supported formats**: PNG (best), JPG, JPEG, GIF, BMP
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px;">
    <p>Created by Derik Vo | N2Y Adaptation Tools</p>
</div>
""", unsafe_allow_html=True)