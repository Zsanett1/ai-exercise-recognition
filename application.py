import streamlit as st
from streamlit_option_menu import option_menu

import database

database.init_db()

st.set_page_config(page_title="AI Home Personal Trainer", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarCollapseButton"] {display: none;}
    </style>
    """,
    unsafe_allow_html = True,
)

selected_page = option_menu(
    menu_title=None,
    options=["Home", "Exercises", "Profile", "History", "About"],
    icons=["house", "activity", "person", "calendar-check", "info-circle"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "4px",
            "background-color": "#E2E8F0",
            "border-radius": "8px",
        },
        "icon": {
            "color": "#14B8A6", 
            "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "color": "#0F172A",
            "--hover-color": "#CBD5E1",
        },
        "nav-link-selected": {
            "background-color": "#0F172A",
            "color": "#F8FAFC",
            "font-weight": "bold",
        },
    },
)

if selected_page == "Home":
    import views.home as home

    home.show()
elif selected_page == "Exercises":
    import views.exercises as exercises

    exercises.show()
elif selected_page == "Profile":
    import views.profile as profile

    profile.show()
elif selected_page == "History":
    import views.history as history

    history.show()
elif selected_page == "About":
    import views.about as about

    about.show()

st.write("")
st.write("---")
col_foot1, col_foot2 = st.columns(2)

with col_foot1:
    st.caption("(c) 2026 AI Home Personal Trainer.")
with col_foot2:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.8rem;'>"
        "Developed for Graduation Thesis by Raduly Zsanett"
        "</div>",
        unsafe_allow_html=True,
    )
