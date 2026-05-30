"""
Módulo de configuración de estilos CSS.
"""

import streamlit as st


def aplicar_estilos():
    """
    Aplica los estilos CSS personalizados al dashboard.
    """
    st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
        .metric-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 16px 20px;
            border-left: 4px solid #1D9E75;
        }
        .metric-card.danger { border-left-color: #D85A30; }
        .metric-card.warn   { border-left-color: #BA7517; }
        .insight-box {
            background: #FAECE7;
            border: 1px solid #F0997B;
            border-radius: 10px;
            padding: 14px 18px;
            margin: 12px 0;
        }
        .insight-ok {
            background: #E1F5EE;
            border: 1px solid #5DCAA5;
            border-radius: 10px;
            padding: 14px 18px;
            margin: 12px 0;
        }
        .phase-header {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 4px;
        }
    </style>
    """, unsafe_allow_html=True)
