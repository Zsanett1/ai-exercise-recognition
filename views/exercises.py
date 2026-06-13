import streamlit as st
import database

def show_exercise_card(exercise):
    card_col1, card_col2, card_col3 = st.columns([1.1, 2.4, 1.1])
    with card_col1:
        if exercise["image_path"]:
            st.image(exercise["image_path"], width = 220)
        else:
            st.caption("No image available.")
    with card_col2:
        st.markdown(f"### {exercise['name']}")
        st.caption(exercise["category"])
        st.markdown(f"**Focus:** {exercise['focus']}")
        if exercise["is_trackable"]:
            st.caption("Trackable")
        else:
            st.caption("Preview only")
    with card_col3:
        st.write("")
        st.write("")
        if st.button("View details", key = f"details_{exercise['id']}", use_container_width = True):
            st.session_state["details_exercise"] = exercise
            st.rerun()
    st.write("---")

@st.dialog("Exercise Details", width = "large")
def show_exercise_details(exercise, is_logged_in):
    st.markdown(f"### {exercise['name']}")
    st.caption(exercise["category"])
    st.write("---")
    col_info, col_img = st.columns([1.3, 1])
    with col_info:
        st.markdown("### How to perform")
        for step in exercise["steps"]:
            st.markdown(f"- {step}")
        st.write("")
        st.markdown(f"**Required equipment:** {exercise['equipment']}")
        st.markdown(f"**Anatomical focus:** {exercise['focus']}")
        st.write("")
        st.caption("AI TRACKING")
        if exercise["is_trackable"]:
            st.write("This exercise can be connected to the real-time AI tracking flow.")
        else:
            st.write("This exercise is currently available as a guided exercise preview.")
    with col_img:
        if exercise["image_path"]:
            st.image(exercise["image_path"], use_container_width = True)
        else:
            st.caption("No image available.")
    st.write("---")
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if is_logged_in:
            if st.button("Select this exercise", use_container_width = True):
                st.session_state["selected_exercise"] = exercise
                st.session_state["details_exercise"] = None
                st.rerun()
        else:
            st.caption("Sign in on the Profile page to start tracking this exercise.")
    with action_col2:
        if st.button("Close details", use_container_width = True):
            st.session_state["details_exercise"] = None
            st.rerun()

def show_session_setup(is_logged_in):
    selected_exercise = st.session_state["selected_exercise"]
    if selected_exercise is None:
        return
    st.write("")
    with st.container(border = True):
        top_col1, top_col2, top_col3 = st.columns([1.6, 1.4, 1.4])
        with top_col1:
            st.caption("SELECTED EXERCISE")
            st.markdown(f"**{selected_exercise['name']}**")
        with top_col2:
            st.caption("TRACKING MODE")
            if selected_exercise["is_trackable"]:
                st.markdown("**AI tracking available**")
            else:
                st.markdown("**Guided preview only**")
        with top_col3:
            st.caption("ACCESS")
            if not is_logged_in:
                st.markdown("**Login required**")
            elif selected_exercise["is_trackable"]:
                st.markdown("**Ready to start**")
            else:
                st.markdown("**Preview only**")
        if not is_logged_in:
            st.caption("Sign in on the Profile page to start AI tracking and save your progress.")
            return
        if not selected_exercise["is_trackable"]:
            st.caption("This exercise is not connected to real-time AI tracking yet.")
            return
        st.write("")
        target_col, button_col = st.columns([1, 1])
        with target_col:
            target_reps = st.number_input("Target repetitions for this session", min_value = 1, max_value = 200, value = 10, step = 1,)
        with button_col:
            st.write("")
            st.write("")
            if st.button("Start AI Session", use_container_width = True):
                st.session_state["target_reps"] = target_reps
                st.caption("The camera-based AI session will start here..")

def show():
    st.title("Exercises & Real-Time Tracking")
    st.caption("Browse supported exercises and prepare an AI-assisted training session.")
    st.write("---")
    
    intro_col1, intro_col2, intro_col3 = st.columns(3)
    with intro_col1:
        st.caption("LIBRARY")
        st.markdown("**Choose movement**")
        st.write("Browse exercises by muscle group and review the correct execution.")
    with intro_col2:
        st.caption("TRACKING")
        st.markdown("**Prepare session**")
        st.write("Select an exercise before starting real-time AI analysis.")
    with intro_col3:
        st.caption("PROGRESS")
        st.markdown("**Save results**")
        st.write("Logged-in users will be able to connect completed sessions to history.")
    st.write("---")
    
    if "selected_exercise" not in st.session_state:
        st.session_state["selected_exercise"] = None
    if "details_exercise" not in st.session_state:
        st.session_state["details_exercise"] = None
    if "selected_category" not in st.session_state:
        st.session_state["selected_category"] = None
    is_logged_in = st.session_state.get("logged_in", False)

    categories = database.get_exercise_categories()
    category_names = [category["name"] for category in categories]
    category_description = {
        category["name"]: category["description"]
        for category in categories
    }
    if not categories:
        st.markdown("### No exercises available")
        st.caption("The exercise library is empty. Add exercises to the database to display them here.")
        return
    selected_category = st.radio(
        "Muscle group category", category_names, horizontal = True, index = 0,
    )
    if st.session_state["selected_category"] != selected_category:
        st.session_state["selected_category"] = selected_category
        st.session_state["selected_exercise"] = None
        st.session_state["details_exercise"] = None
    st.markdown(f"### {selected_category}")
    category_description = category_description.get(selected_category, "Browse the exercises in this category and review their main training focus.")
    st.caption(category_description)
    show_session_setup(is_logged_in)
    exercises = database.get_exercises_by_category(selected_category)
    if not exercises:
        st.markdown("### No exercises in this category")
        st.caption("Choose another category or add exercises to this category in the database.")
        return
    for exercise in exercises:
        show_exercise_card(exercise)
    if st.session_state["details_exercise"] is not None:
        show_exercise_details(st.session_state["details_exercise"], is_logged_in)
