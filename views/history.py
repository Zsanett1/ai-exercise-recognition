import streamlit as st
import pandas as pd
import altair as alt
import database
from datetime import datetime
import json

def format_duration(duration_seconds):
    if not duration_seconds:
        return "Not recorded"
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def estimate_calories(duration_seconds, weight_kg, met_value):
    if not duration_seconds or not weight_kg or not met_value:
        return None
    duration_hours = duration_seconds / 3600
    return round(float(met_value) * float(weight_kg) * duration_hours)

@st.dialog("Exercise Analysis", width="large")
def show_workout_details_popup(workout_data):
    st.write(f"**{workout_data['exercise_name']}**")
    if workout_data["saved_at"]:
        saved_time = datetime.strptime(workout_data["saved_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y at %H:%M")
        st.caption(f"Saved on {saved_time}")
    else:
        st.caption("Session performance and saved feedback.")
    st.write("---")
    
    col_popup_text, col_popup_pic = st.columns([1.2, 1])
    
    with col_popup_text:
        st.markdown("### **Performance Summary**")
        st.write(f"**Total Repetitions:** {workout_data['total_reps']} reps")
        st.write(f"**Correct Repetitions:** {workout_data['correct_reps']} reps")
        
        w_accuracy = int((workout_data['correct_reps'] / workout_data['total_reps']) * 100) if workout_data['total_reps'] > 0 else 100
        st.write(f"**Form Accuracy:** {w_accuracy}%")
        
        st.write("---")
        st.markdown("### AI Coach Feedback")
        if workout_data["feedback"]:
            for feedback_line in workout_data["feedback"].splitlines():
                st.write(feedback_line)
        else:
            st.caption("No detailed feedback was saved for this session.")
            
    with col_popup_pic:
        st.markdown("### **Captured Form**")
        screenshots = []
        if workout_data['screenshot'] and workout_data['screenshot'] != "default":
            try:
                screenshots = json.loads(workout_data["screenshot"])
            except json.JSONDecodeError:
                screenshots = [{
                    "rep": "", "feedback": "Saved session snapshot", "image_path": workout_data["screenshot"],
                }]
        if screenshots:
            for screenshot in screenshots:
                caption = screenshot.get("feedback", "Saved form snapshot.")
                rep = screenshot.get("rep")
                if rep:
                    caption = f"Rep {rep}: {caption}"
                st.image(screenshot["image_path"], caption = caption, use_container_width = True,)
        else:
            st.caption("No form snapshot was saved for this session.")

    st.write("---")
    close_left, close_center, close_right = st.columns([1, 1, 1])
    with close_center:
        if st.button("Close Analysis", use_container_width=True):
            st.rerun()

def show():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.title("Workout History")
        st.caption("Review your completed sessions and daily performance.")
        st.write("---")
        st.markdown("### Sign in required")
        st.caption("Your workout history is connected to your personal profile.")
        st.write("")
        auth_col1, auth_col2, auth_col3 = st.columns(3)
        with auth_col1:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>PROFILE</span>", unsafe_allow_html = True)
                st.markdown("**Sign in first**")
                st.write("Open the Profile page and sign in to access your saved workout sessions.")
        with auth_col2:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>HISTORY</span>", unsafe_allow_html = True)
                st.markdown("**Saved sessions**")
                st.write("Completed workouts will appear here once they are connected to your account.")
        with auth_col3:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>PROGRESS</span>", unsafe_allow_html = True)
                st.markdown("**Track consistency**")
                st.write("Your training days, repetitions, and session feedback will be available after login.")
        return

    current_user = st.session_state["username"]
    user_profile = database.get_user_profile(current_user)
    user_weight = user_profile["weight_kg"] if user_profile else 0

    st.title("Workout History")
    st.caption("Review your completed sessions and daily performance.")
    st.write("---")

    progress_data = database.get_workout_progress(current_user)
    if progress_data:
        progress_df = pd.DataFrame(progress_data)
        progress_df["date"] = pd.to_datetime(progress_df["date"])
        progress_df = progress_df.set_index("date").asfreq("D", fill_value = 0).reset_index()
        progress_df["day"] = progress_df["date"].dt.strftime("%b %d")
        chart_df = progress_df.melt(
            id_vars = ["date", "day"], value_vars = ["total_reps", "correct_reps"], var_name = "type", value_name = "reps"
        )
        max_reps = int(chart_df["reps"].max()) if not chart_df.empty else 10
        y_max = max(10, ((max_reps // 10) + 1) * 10)
        st.markdown(
            "<span style='color: #14B8A6; font-weight: 800;'>TRAINING PROGRESS</span>"
            " <span style='color: #64748B;'>- your saved workout repetitions by day</span>",
            unsafe_allow_html=True
        )
        chart = (
            alt.Chart(chart_df).mark_line(point = True).encode(
                x = alt.X("day:N", title = "Day", sort = list(progress_df["day"])),
                y = alt.Y("reps:Q", title = "Repetitions", scale = alt.Scale(domain = [0, y_max]), axis = alt.Axis(values = list(range(0, y_max + 1, 10)))),
                color = alt.Color("type:N", title = "", scale = alt.Scale(domain = ["total_reps", "correct_reps"], range = ["#60A5FA", "#14B8A6"]))
            ).properties(height = 280)
        )
        st.altair_chart(chart, use_container_width = True)
    else:
        st.markdown(
            "<span style='color: #14B8A6; font-weight: 800;'>TRAINING PROGRESS</span>"
            " <span style='color: #64748B;'>- your saved workout repetitions by day</span>",
            unsafe_allow_html=True
        )
        with st.container(border = True):
            st.markdown("### No progress data yet")
            st.caption("Complete your first tracked workout session to start building your progress chart.")
            st.write("")
            empty_col1, empty_col2, empty_col3 = st.columns(3)
            with empty_col1:
                st.markdown("**1. Choose an exercise**")
                st.caption("Open the Exercises page and select a trackable movement.")
            with empty_col2:
                st.markdown("**2. Start AI tracking**")
                st.caption("Use the camera-based tracking flow to record repetitions.")
            with empty_col3:
                st.markdown("**3. Save your result**")
                st.caption("Saved sessions will appear here with progress and feedback.")
        return
    st.write("---")
    st.markdown(
        "<span style='color: #14B8A6; font-weight: 800;'>DATE FILTER</span>"
        " <span style='color: #64748B; font-weight: 500;'>- select a day to review its saved workouts</span>",
        unsafe_allow_html=True
    )
    date_col, _ = st.columns([1, 3])
    with date_col:
        selected_date = st.date_input("Training date", value=datetime.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    st.markdown(f"### Sessions on {selected_date.strftime('%B %d, %Y')}")
    daily_workouts = database.get_workouts_by_date(current_user, date_str)

    if len(daily_workouts) > 0:
        total_reps_day = sum(w["total_reps"] for w in daily_workouts)
        correct_reps_day = sum(w["correct_reps"] for w in daily_workouts)
        accuracy = int((correct_reps_day / total_reps_day) * 100) if total_reps_day > 0 else 100
        total_calories_day = 0
        for workout in daily_workouts:
            estimated_calories = estimate_calories(
                workout["duration_seconds"],
                user_weight,
                workout["met_value"]
            )
            if estimated_calories:
                total_calories_day += estimated_calories
        summary_col, session_col = st.columns([1, 2])
        with summary_col:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>DAILY SUMMARY</span>", unsafe_allow_html=True)
                st.caption("Estimated Calories")
                st.markdown(f"### {total_calories_day} kcal")
                st.caption("Total Exercises")
                st.markdown(f"### {len(daily_workouts)}")
                st.caption("Total Repetitions")
                st.markdown(f"### {total_reps_day} reps")
                st.caption("Daily AI Accuracy")
                st.markdown(f"### {accuracy}%")
        with session_col:
            with st.container(border = True):
                st.markdown("<span style='color: #14B8A6; font-weight: 800;'>SESSION DETAILS</span>", unsafe_allow_html=True)
                st.caption("Select a session to view its detailed analysis.")
                for index, workout in enumerate(daily_workouts):
                    col_name, col_stats, col_btn = st.columns([1.5, 1.2, 1])
                    with col_name:
                        st.markdown(f"**{workout['exercise_name']}**")
                        if workout["saved_at"]:
                            saved_time = datetime.strptime(workout["saved_at"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                            st.caption(f"Saved at {saved_time}")
                    with col_stats:
                        estimated_calories = estimate_calories(workout["duration_seconds"], user_weight, workout["met_value"])
                        st.write(f"Score: **{workout['correct_reps']}/{workout['total_reps']} reps**")
                        st.caption(f"Duration: {format_duration(workout['duration_seconds'])}")
                        if estimated_calories:
                            st.caption(f"Calories burned: {estimated_calories} kcal")
                        elif not user_weight:
                            st.caption("Add your weight in Profile to see the burned calories.")
                        else:
                            st.caption("Calories are not available.")
                    with col_btn:
                        if st.button("View Details", key = f"btn_{index}", use_container_width = True):
                            show_workout_details_popup(workout)
                    st.write("---")
    else:
        st.markdown("### No sessions recorded")
        st.caption("There are no workouts saved for the selected date.")
        st.write("")
        empty_col1, empty_col2, empty_col3 = st.columns(3)
        with empty_col1:
            with st.container(border=True):
                st.markdown(
                    "<span style='color: #14B8A6; font-weight: 800;'>NEXT STEP</span>",
                    unsafe_allow_html=True
                )
                st.markdown("**Start a workout**")
                st.write("Open the Exercises page and complete a session to create your first history entry.")
        with empty_col2:
            with st.container(border=True):
                st.markdown(
                    "<span style='color: #14B8A6; font-weight: 800;'>TIP</span>",
                    unsafe_allow_html=True
                )
                st.markdown("**Check another date**")
                st.write("Use the date selector above to review previous training days.")
        with empty_col3:
            with st.container(border=True):
                st.markdown(
                    "<span style='color: #14B8A6; font-weight: 800;'>PROGRESS</span>",
                    unsafe_allow_html=True
                )
                st.markdown("**Build consistency**")
                st.write("Your completed sessions will appear here once workouts are saved.")