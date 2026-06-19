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
    if not is_logged_in:
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
        daily_target = max(user_data["daily_target"] or 50, 1)
        weekly_reps = database.get_weekly_reps(current_user)
        current_streak = database.get_current_streak(current_user)
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
        progress_percent = int(progress_percentage * 100)
        remaining_reps = max(daily_target - daily_reps_done, 0)
        max_weekly_reps = max([day["reps"] for day in weekly_reps], default = 1)
        week_cards_html = ""
        for day_data in weekly_reps:
            is_active = day_data["reps"] > 0
            is_today = day_data["is_today"]
            card_background = "rgba(255, 255, 255, 0.92)" if is_today else "rgba(255, 255, 255, 0.72)"
            border_color = "#0F766E" if is_active else "rgba(255, 255, 255, 0.55)"
            label = "Today" if is_today else day_data["date"][5:].replace("-", "/")
            week_cards_html += f'<div style="background: {card_background}; border: 1px solid {border_color}; border-radius: 8px; padding: 12px 8px; text-align: center; min-height: 86px;"><div style="font-weight: 800; color: #0F172A;">{day_data["day"]}</div><div style="font-size: 1.25rem; font-weight: 900; color: #0F766E; margin-top: 8px;">{day_data["reps"]}</div><div style="font-size: 0.75rem; color: #64748B;">reps</div><div style="font-size: 0.7rem; color: #64748B; margin-top: 6px;">{label}</div></div>'
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, #14B8A6 0%, #0F766E 55%, #0F172A 100%); border-radius: 10px; padding: 28px; color: white; box-shadow: 0 12px 30px rgba(15, 118, 110, 0.18);">
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; align-items: center;">
                <div>
                    <div style="font-size: 0.85rem; font-weight: 900; letter-spacing: 0.03em; opacity: 0.9;">YOUR PROGRESS</div>
                    <div style="font-size: 3.4rem; font-weight: 900; line-height: 1; margin-top: 18px;">{progress_percent}%</div>
                    <div style="margin-top: 10px; opacity: 0.9;">{daily_reps_done} / {daily_target} reps completed today</div>
                    <div style="height: 10px; background: rgba(255,255,255,0.32); border-radius: 999px; margin-top: 24px; overflow: hidden;">
                        <div style="height: 100%; width: {progress_percent}%; background: #0F172A; border-radius: 999px;"></div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.28); border-radius: 10px; padding: 20px;">
                    <div style="font-size: 0.85rem; font-weight: 900; opacity: 0.9;">STREAK</div>
                    <div style="font-size: 3rem; font-weight: 900; margin-top: 18px;">{current_streak}</div>
                    <div style="opacity: 0.85;">training days in a row</div>
                </div>
            </div>
            <div style="margin-top: 28px; font-size: 0.85rem; font-weight: 900; letter-spacing: 0.03em;">WEEK DAYS</div>
            <div style="display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 12px; margin-top: 12px;">
                {week_cards_html}
            </div>
            <div style="margin-top: 18px; opacity: 0.9;">{remaining_reps} reps remaining to reach today's target.</div>
        </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")

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
