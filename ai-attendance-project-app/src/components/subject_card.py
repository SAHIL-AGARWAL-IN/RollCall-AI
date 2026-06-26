import streamlit as st
def subject_card(name, code, section, stats=None, footer_callback=None):
    html = f"""
        <div style="background: rgba(255, 255, 255, 0.03); border-left: 8px solid #EC4899; padding: 25px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);">
        <h3 style="margin: 0; color: #F8FAFC; font-size: 1.5rem; font-family: sans-serif; font-weight: 700;">{name}</h3>
        <p style="color: #94A3B8; margin: 10px 0; font-family: sans-serif;">Code : <span style="background: rgba(99, 102, 241, 0.15); color: #A5B4FC; padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.2); font-weight: 600;">{code} </span> | Section : {section}</p>
        
        """
    
    if stats:
        html+= """
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 15px; font-family: sans-serif;">
        """
        for icon, label, value in stats:
            html+= f'<div style="background: rgba(236, 72, 153, 0.1); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.2); padding: 6px 14px; border-radius: 12px; font-size: 0.9rem;">{icon} <b>{value}</b> {label} </div>'
        
        html+= "</div>"
    html+= "</div>"

    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()
