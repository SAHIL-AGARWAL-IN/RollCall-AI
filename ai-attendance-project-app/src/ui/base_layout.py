import streamlit as st

def style_background_home():
    st.markdown("""
        <style>
                .stApp {
                    background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.15), transparent 60%),
                                radial-gradient(circle at bottom right, rgba(236, 72, 153, 0.12), transparent 60%),
                                #060913 !important;
                }

                .stApp div[data-testid="stColumn"] {
                    background: rgba(255, 255, 255, 0.02) !important;
                    border: 1px solid rgba(255, 255, 255, 0.08) !important;
                    backdrop-filter: blur(20px) !important;
                    -webkit-backdrop-filter: blur(20px) !important;
                    padding: 2.5rem !important;
                    border-radius: 2rem !important;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
                }
                
                /* Cascade height and flex layout to all inner column wrappers */
                .stApp div[data-testid="stColumn"],
                .stApp div[data-testid="stColumn"] > div,
                .stApp div[data-testid="stColumn"] > div > div,
                .stApp div[data-testid="stColumn"] [data-testid="stVerticalBlockBorderWrapper"],
                .stApp div[data-testid="stColumn"] [data-testid="stVerticalBlock"] {
                    display: flex !important;
                    flex-direction: column !important;
                    flex-grow: 1 !important;
                    height: 100% !important;
                }
                
                /* Distribute children inside the elements container */
                .stApp div[data-testid="stColumn"] [data-testid="stVerticalBlock"] {
                    justify-content: space-between !important;
                    align-items: center !important;
                }
        </style>  
                """, unsafe_allow_html=True)

def style_background_dashboard():
    st.markdown("""
        <style>
                .stApp {
                    background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.08), transparent 60%),
                                radial-gradient(circle at bottom right, rgba(236, 72, 153, 0.06), transparent 60%),
                                #060913 !important;
                }
        </style>  
                """, unsafe_allow_html=True)

def style_base_layout():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

             #MainMenu, footer, header {
                 visibility: hidden;
             }
                 
             .block-container {
                 padding-top: 1.5rem !important;    
             }

             h1 {
                 font-family: 'Outfit', sans-serif !important;
                 font-size: 3.0rem !important;
                 font-weight: 800 !important;
                 line-height: 1.1 !important;
                 margin-bottom: 0rem !important;
                 background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%) !important;
                 -webkit-background-clip: text !important;
                 -webkit-text-fill-color: transparent !important;
                 letter-spacing: -1px !important;
             }

             h2 {
                 font-family: 'Outfit', sans-serif !important;
                 font-size: 2.0rem !important;
                 font-weight: 800 !important;
                 line-height: 1.0 !important;
                 margin-bottom: 0rem !important;
                 background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%) !important;
                 -webkit-background-clip: text !important;
                 -webkit-text-fill-color: transparent !important;
                 letter-spacing: -1px !important;
                 white-space: nowrap !important;
             }

             h3, h4, p, span, li, label, div {
                 font-family: 'Outfit', sans-serif;    
             }

             /* Glassmorphic Streamlit Buttons */
             button {
                 border-radius: 1.5rem !important;
                 background: rgba(99, 102, 241, 0.1) !important;
                 color: #a5b4fc !important;
                 padding: 10px 24px !important;
                 border: 1px solid rgba(99, 102, 241, 0.3) !important;
                 backdrop-filter: blur(8px) !important;
                 -webkit-backdrop-filter: blur(8px) !important;
                 box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
                 transition: all 0.25s ease-in-out !important;
                 font-weight: 600 !important;
             }

             button[kind="secondary"] {
                 border-radius: 1.5rem !important;
                 background: rgba(236, 72, 153, 0.1) !important;
                 color: #f472b6 !important;
                 padding: 10px 24px !important;
                 border: 1px solid rgba(236, 72, 153, 0.3) !important;
                 backdrop-filter: blur(8px) !important;
                 -webkit-backdrop-filter: blur(8px) !important;
                 box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
                 transition: all 0.25s ease-in-out !important;
                 font-weight: 600 !important;
             }

             button[kind="tertiary"] {
                 border-radius: 1.5rem !important;
                 background: rgba(255, 255, 255, 0.03) !important;
                 color: #cbd5e1 !important;
                 padding: 10px 24px !important;
                 border: 1px solid rgba(255, 255, 255, 0.1) !important;
                 backdrop-filter: blur(8px) !important;
                 -webkit-backdrop-filter: blur(8px) !important;
                 transition: all 0.25s ease-in-out !important;
                 font-weight: 600 !important;
             }

             button:hover {
                 transform: translateY(-2px) !important;
                 background: rgba(99, 102, 241, 0.2) !important;
                 border-color: rgba(99, 102, 241, 0.6) !important;
                 box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
             }
             
             button[kind="secondary"]:hover {
                 transform: translateY(-2px) !important;
                 background: rgba(236, 72, 153, 0.2) !important;
                 border-color: rgba(236, 72, 153, 0.6) !important;
                 box-shadow: 0 6px 20px rgba(236, 72, 153, 0.25) !important;
             }

             button[kind="tertiary"]:hover {
                 transform: translateY(-2px) !important;
                 background: rgba(255, 255, 255, 0.08) !important;
             }
        </style>  
                 """, unsafe_allow_html=True)