import streamlit as st


def header_home():

    logo_url = "https://roll-call-ai.vercel.app/static/img/logo.png"
    
    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px">
            <img src='{logo_url}' style='height:100px;' />
            <h1 style='text-align:center; color:#E0E3FF; font-family:sans-serif;'>ROLLCALL<br/>AI</h1>
        </div>   
                
                """, unsafe_allow_html=True)


def header_dashboard():

    logo_url = "https://roll-call-ai.vercel.app/static/img/logo.png"
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; gap:12px">
            <img src='{logo_url}' style='height:85px;' />
            <h2 style='text-align:left; color:#6366F1;'>RollCall AI</h2>
        </div>   
                
                """, unsafe_allow_html=True)
