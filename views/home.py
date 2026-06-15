import streamlit as st
import database

GOAL_GUIDANCE = {
    "Stay Fit": {
        "title": "Maintain a balanced routine",
        "text": "Focus on regular movement, a mix of strength and core exercises, and consistent daily activity."
    },
    "Lose Weight": {
        "title": "Support a calorie deficit",
        "text": "Combine regular workouts with a sustainable calorie deficit, more daily steps, and consistent training habits."
    },
    "Build Muscle": {
        "title": "Prioritize strength and recovery",
        "text": "Aim for progressive strength training, enough protein, and 3-4 focused workout sessions per week."
    },
    "Increase Endurance": {
        "title": "Build consistency over time",
        "text": "Use higher-repetition sessions, shorter rest periods, and regular activity to improve stamina gradually."
    },
}

def show():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

    is_logged_in = st.session_state["logged_in"]

    current_user = st.session_state["username"] if is_logged_in else None
    user_data = database.get_user_profile(current_user) if is_logged_in else None

    if user_data and user_data["full_name"].strip():
        display_name = user_data["full_name"]
    else:
        display_name = current_user
    hero_left, hero_right = st.columns([1.4, 1], vertical_alignment = "center")
    with hero_left:
        st.markdown(
            """
            <h1 style='color: #14B8A6; font-size: 2.3rem; font-weight: 800; margin-bottom: 10px; padding-top: 10px;'>
                Train Smarter at Home<br>with AI Guidance
            </h1>
            """, 
            unsafe_allow_html=True
        )
        st.markdown(
            "Improve your workouts with **real-time exercise recognition**, **repetition tracking**, "
            "and **personalized progress insights**. Choose an exercise, start your session, "
            "and let the system help you train with better structure and confidence."
        )
    with hero_right:
        st.markdown(
            """
            <style>
                .hero-img-container img {
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    border: 1px solid #E2E8F0;
                }
            </style>
            <div class="hero-img-container">
            """, 
            unsafe_allow_html=True
        )
        st.image("assets/pose_detection.png", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html = True)

    st.markdown("### Built for accessible home training")
    st.write(
        "The goal of this project is to make independent workouts easier to follow, "
        "more measurable, and more confidence-friendly through AI-supported movement analysis."
    )

    st.write("---")

    if is_logged_in:
        total_workouts, total_reps = database.get_user_stats(current_user)
        last_active = database.get_last_active_session(current_user)
        daily_reps_done = database.get_daily_reps(current_user)
        daily_target = user_data["daily_target"]
        st.markdown(f"### Welcome back, {display_name}")
        st.write("Your workout space is ready. Continue tracking your daily goal or start a new exercise session.")
        st.write("")
        fitness_goal = user_data["fitness_goal"]
        goal_guidance = GOAL_GUIDANCE.get(fitness_goal, GOAL_GUIDANCE["Stay Fit"])
        overview_col, focus_col = st.columns([2, 1])
        with overview_col:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>TRAINING OVERVIEW</span>", unsafe_allow_html=True)
                st.write("")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric(label="Completed Workouts", value=f"{total_workouts}")
                with metric_col2:
                    st.metric(label="Total Reps", value=f"{total_reps}")
                with metric_col3:
                    st.metric(label="Last Session", value=last_active)
                st.write("")
                st.caption("Your saved sessions and repetitions are updated from completed AI tracking workouts.")
        with focus_col:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>TRAINING FOCUS</span>", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"**{fitness_goal}**")
                st.caption(goal_guidance["title"])
                st.write(goal_guidance["text"])

        st.write("")
        st.markdown("### Today's goal")
        progress_percentage = min(daily_reps_done / daily_target, 1.0)
        st.markdown(f"**{daily_reps_done} / {daily_target} reps completed today**")
        st.progress(progress_percentage)
        if daily_reps_done == 0:
            st.caption("Start your first exercise session today to begin filling your daily goal.")
        elif daily_reps_done < daily_target:
            remaining_reps = daily_target - daily_reps_done
            st.caption(f"{remaining_reps} reps remaining to reach your daily goal.")
        else:
            st.caption("Daily target completed. Great work.")

    else:
        st.markdown("### New here?")
        st.write("Explore the exercise library first, then create an account when you want "
                "saved progress, daily targets, and a more personalized training experience.")
        st.write("")
        st.markdown("### Get started in three simple steps")
        st.caption("A quick path from exploring the app to saving your first workout.")
        st.write("")
        step_col1, step_col2, step_col3 = st.columns(3)
        with step_col1:
            with st.container(border=True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>STEP 1</span>", unsafe_allow_html = True)
                st.markdown("#### Choose an exercise")
                st.write("Explore the workout library and choose the movement you want to start with.")      
        with step_col2:
            with st.container(border=True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>STEP 2</span>", unsafe_allow_html = True)
                st.markdown("#### Start tracking")
                st.write("Use the camera-based AI system to follow your repetitions and movement execution.")              
        with step_col3:
            with st.container(border=True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>STEP 3</span>", unsafe_allow_html = True)
                st.markdown("#### Save progress")
                st.write("Create a profile to store your workout history, daily targets and results.")

    st.write("---")

    st.markdown("### What you can do next")
    st.caption("Use the main sections of the app depending on where you are in your training.")
    st.write("")
    next_col1, next_col2, next_col3 = st.columns(3)
    
    with next_col1:
        with st.container(border=True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>EXERCISES</span>", unsafe_allow_html = True)
            st.markdown("#### Explore exercises")
            st.write("Browse supported movements, review instructions, and learn which muscles each exercise targets.")
    with next_col2:
        with st.container(border=True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>TRACKING</span>", unsafe_allow_html = True)
            st.markdown("#### Track a session")
            st.write("Start an AI-assisted workout session and follow your repetitions during training.")
    with next_col3:
        with st.container(border=True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>HISTORY</span>", unsafe_allow_html = True)
            st.markdown("#### Review progress")
            st.write("Use your workout history to understand consistency, total repetitions, and performance over time.")
