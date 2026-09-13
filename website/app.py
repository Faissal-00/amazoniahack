import sys
import tempfile
import base64
from pathlib import Path

import streamlit as st

# Add root directory to path to allow importing from scripts/
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir / "scripts"))

from ocr_engine import OCREngine
from extract_fields import extract_fields
from schema import Document
from run_extraction import model_to_dict

st.set_page_config(page_title="Mosaic OCR", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for an Azure-like dense, no-scroll main layout
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .field-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 4px;
        padding: 8px 12px;
        margin-bottom: 6px;
    }
    .field-title {
        font-size: 0.75rem;
        color: #aaa;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .field-value {
        font-size: 0.95rem;
        font-weight: 500;
        word-wrap: break-word;
        line-height: 1.3;
    }
</style>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Document (JPG/PNG)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    if 'last_processed' not in st.session_state or st.session_state['last_processed'] != uploaded_file.name:
        with st.spinner("Extracting..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                file_bytes = uploaded_file.getvalue()
                tmp.write(file_bytes)
                tmp_path = Path(tmp.name)
            
            try:
                engine = OCREngine()
                ocr_results = engine.extract(tmp_path)
                
                if not ocr_results:
                    st.error("OCR returned no text.")
                else:
                    extracted = extract_fields(ocr_results)
                    document = Document(**extracted)
                    data = model_to_dict(document)
                    
                    combined_result = {}
                    
                    for key, val in data.items():
                        if key not in ["confidence", "fields", "signatures", "references"]:
                            combined_result[key] = val if val is not None else "Not available"
                            
                    st.session_state['structured_data'] = combined_result
                    st.session_state['img_base64'] = base64.b64encode(file_bytes).decode("utf-8")
                    st.session_state['img_type'] = uploaded_file.type
                    st.session_state['last_processed'] = uploaded_file.name
            except Exception as e:
                st.error(f"Error during extraction: {str(e)}")
            finally:
                tmp_path.unlink(missing_ok=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        # Render image via HTML so it fits viewport height (no cropping, no scrolling)
        if 'img_base64' in st.session_state:
            img_html = f"""
            <div style="display: flex; justify-content: center; align-items: center; height: 80vh; background-color: #0e1117; border-radius: 8px;">
                <img src="data:{st.session_state['img_type']};base64,{st.session_state['img_base64']}" 
                     style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </div>
            """
            st.markdown(img_html, unsafe_allow_html=True)
            
    with col2:
        if 'structured_data' in st.session_state:
            st.markdown("### Extracted Values")
            
            # Split the extracted values into two columns to eliminate scrolling
            sub_col1, sub_col2 = st.columns(2)
            
            items = list(st.session_state['structured_data'].items())
            midpoint = (len(items) + 1) // 2
            
            for i, (key, val) in enumerate(items):
                # Convert lists/dicts to strings for clean display
                if isinstance(val, (list, dict)):
                    val = str(val) if val else "None"
                    
                card_html = f"""
                <div class="field-card">
                    <div class="field-title">{key}</div>
                    <div class="field-value">{val}</div>
                </div>
                """
                
                # Distribute evenly between the two sub-columns
                if i < midpoint:
                    sub_col1.markdown(card_html, unsafe_allow_html=True)
                else:
                    sub_col2.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("Please upload a document to begin.")
