import streamlit as st
from streamlit_webrtc import webrtc_streamer
from datetime import date, datetime
import database
from src.tracking.pose_overlay import draw_pose_landmarks, get_tracking_summary, reset_tracking_session
import json

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
        st.markdown(
            f"<span style='color: #14B8A6; font-weight: 800;'>{exercise.get('level', 'Beginner').upper()}</span>",
            unsafe_allow_html=True
        )
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
                st.session_state["tracking_active"] = True
                st.session_state["tracking_finished"] = False
                st.session_state["camera_was_playing"] = False
                st.session_state["tracking_saved"] = False
                st.session_state["tracking_started_at"] = datetime.now()
                reset_tracking_session(target_label = selected_exercise["model_label"])
                st.rerun()

def sort_exercises_by_user_level(exercises, user_level):
    level_order = {
        "Beginner": ["Beginner", "Intermediate", "Advanced"],
        "Intermediate": ["Intermediate", "Beginner", "Advanced"],
        "Advanced": ["Advanced", "Intermediate", "Beginner"]
    }
    preferred_order = level_order.get(user_level, level_order["Beginner"])
    return sorted(exercises, key = lambda exercise: (
        preferred_order.index(exercise.get("level", "Beginner"))
        if exercise.get("level", "Beginner") in preferred_order else 99, exercise["name"],
    ))

def format_rep_feedback(rep_feedback_history):
    if not rep_feedback_history:
        return ""
    grouped_feedback = []
    for item in rep_feedback_history:
        feedback = item["feedback"]
        rep_number = item["rep"]
        if not grouped_feedback or grouped_feedback[-1]["feedback"] != feedback:
            grouped_feedback.append({
                "start": rep_number,
                "end": rep_number,
                "feedback": feedback, 
            })
        else:
            grouped_feedback[-1]["end"] = rep_number
    lines = []
    for group in grouped_feedback:
        if group["start"] == group["end"]:
            lines.append(f"Rep {group['start']}: {group['feedback']}")
        else:
            lines.append(f"Reps {group['start']}-{group['end']}: {group['feedback']}")
    return "\n".join(lines)

@st.dialog("AI Tracking Session", width = "large")
def show_tracking_camera():
    selected_exercise = st.session_state.get("selected_exercise")
    target_reps = st.session_state.get("target_reps", 10)
    session_col1, session_col2 = st.columns(2)
    with session_col1:
        st.caption("EXERCISE")
        if selected_exercise:
            st.markdown(f"**{selected_exercise['name']}**")
        else:
            st.markdown("**Not selected**")
    with session_col2:
        st.caption("STATUS")
        if st.session_state.get("tracking_finished", False):
            st.markdown("**Completed**")
        else:
            st.markdown("**Tracking**")
    if not st.session_state.get("tracking_finished", False):
        st.write("")
        camera_context = webrtc_streamer(key = "exercise-camera-test", media_stream_constraints = {"video": True, "audio": False,}, 
                        video_frame_callback = draw_pose_landmarks, async_processing = True,)
        if camera_context.state.playing:
            st.session_state["camera_was_playing"] = True
        elif st.session_state.get("camera_was_playing", False):
            st.session_state["tracking_active"] = False
            st.session_state["tracking_finished"] = True
            st.session_state["camera_was_playing"] = False
            st.rerun()
    else:
        summary = get_tracking_summary()
        st.write("")
        with st.container(border = True):
            st.markdown(
                "<span style='color: #14B8A6; font-weight: 800;'>RESULT</span>",
                unsafe_allow_html=True
            )
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.caption("TOTAL REPS")
                st.markdown(f"**{summary['total_reps']}**")
            with summary_col2:
                st.caption("CORRECT REPS")
                st.markdown(f"**{summary['correct_reps']}**")
            with summary_col3:
                st.caption("TARGET")
                st.markdown(f"**{target_reps} reps**")
            if summary["total_reps"] > 0:
                st.write("")
                st.caption("Detailed rep feedback will be available in History after saving this session.")

        st.write("")

        close_col1, close_col2 = st.columns(2)
        with close_col1:
            if st.button("Close", use_container_width = True):
                st.session_state["tracking_finished"] = False
                st.session_state["tracking_active"] = False
                st.session_state["camera_was_playing"] = False
                st.session_state["tracking_saved"] = False
                st.session_state["tracking_started_at"] = None
                st.rerun()
        with close_col2:
            if st.button("Save to History", use_container_width = True):
                current_user = st.session_state.get("username")
                selected_exercise = st.session_state.get("selected_exercise")
                summary = get_tracking_summary()
                started_at = st.session_state.get("tracking_started_at")
                duration_seconds = 0
                if started_at:
                    duration_seconds = int((datetime.now() - started_at).total_seconds())
                if summary["total_reps"] <= 0:
                    st.caption("No repetitions were recorded, so the session will not be saved.")
                elif st.session_state.get("tracking_saved", False):
                    st.caption("This session has already been saved.")
                else:
                    met_value = selected_exercise.get("met_value", 3.0)
                    database.insert_workout(
                        username = current_user,
                        exercise_name = selected_exercise["name"],
                        total_reps = summary["total_reps"],
                        correct_reps = summary["correct_reps"],
                        feedback = format_rep_feedback(summary["rep_feedback_history"]),
                        screenshot = json.dumps(summary["error_screenshots"]) if summary["error_screenshots"] else "default",
                        date_str = date.today().strftime("%Y-%m-%d"),
                        saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        duration_seconds = duration_seconds,
                        met_value = met_value
                    )
                    st.session_state["tracking_saved"] = True
                    st.session_state["tracking_started_at"] = None
                    st.caption("Session saved to history.")

def show():
    st.title("Exercises & Real-Time Tracking")
    st.caption("Browse supported exercises and prepare an AI-assisted training session.")
    st.write("---")
    
    intro_col1, intro_col2, intro_col3 = st.columns(3)
    with intro_col1:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>LIBRARY</span>", unsafe_allow_html = True)
            st.markdown("**Choose movement**")
            st.write("Browse exercises by muscle group and review the correct execution.")
    with intro_col2:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>TRACKING</span>", unsafe_allow_html = True)
            st.markdown("**Prepare session**")
            st.write("Select an exercise before starting real-time AI analysis.")
    with intro_col3:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>PROGRESS</span>", unsafe_allow_html = True)
            st.markdown("**Save results**")
            st.write("Logged-in users will be able to connect completed sessions to history.")
    st.write("---")
    
    if "selected_exercise" not in st.session_state:
        st.session_state["selected_exercise"] = None
    if "details_exercise" not in st.session_state:
        st.session_state["details_exercise"] = None
    if "selected_category" not in st.session_state:
        st.session_state["selected_category"] = None
    if "tracking_active" not in st.session_state:
        st.session_state["tracking_active"] = False
    if "tracking_finished" not in st.session_state:
        st.session_state["tracking_finished"] = False
    if "camera_was_playing" not in st.session_state:
        st.session_state["camera_was_playing"] = False
    if "tracking_saved" not in st.session_state:
        st.session_state["tracking_saved"] = False

    is_logged_in = st.session_state.get("logged_in", False)
    user_level = "Beginner"
    if is_logged_in:
        user_profile = database.get_user_profile(st.session_state["username"])
        user_level = user_profile["fitness_level"]

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
    if st.session_state.get("tracking_active", False) or st.session_state.get("tracking_finished", False):
        show_tracking_camera()
    exercises = database.get_exercises_by_category(selected_category)
    exercises = sort_exercises_by_user_level(exercises, user_level)
    if not exercises:
        st.markdown("### No exercises in this category")
        st.caption("Choose another category or add exercises to this category in the database.")
        return
    for exercise in exercises:
        show_exercise_card(exercise)
    if st.session_state["details_exercise"] is not None:
        show_exercise_details(st.session_state["details_exercise"], is_logged_in)
