import streamlit as st
import database
from datetime import datetime

@st.dialog("Exercise Analysis", width="large")
def show_workout_details_popup(workout_data):
    st.write(f"**{workout_data['exercise_name']}**")
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
            st.write(workout_data["feedback"])
        else:
            st.caption("No detailed feedback was saved for this session.")
            
    with col_popup_pic:
        st.markdown("### **Captured Form**")
        if workout_data['screenshot'] and workout_data['screenshot'] != "default":
            st.image(workout_data['screenshot'], caption="Saved session snapshot", use_container_width=True)
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

    st.title("Workout History")
    st.caption("Review your completed sessions and daily performance.")
    st.write("---")

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
        st.markdown("### Daily summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Exercises", value=len(daily_workouts))
        with col2:
            st.metric(label="Total Repetitions", value=f"{total_reps_day} reps")
        with col3:
            st.metric(label="Daily AI Accuracy", value=f"{accuracy}%")

        st.write("---")

        session_left, session_center, session_right = st.columns([0.5, 3, 0.5])
        with session_center:  
            st.markdown("### Session details")
            st.caption("Select a session to view its detailed analysis.")
            for index, workout in enumerate(daily_workouts):
                col_name, col_stats, col_btn = st.columns([1.5, 1.5, 1])
                with col_name:
                    st.markdown(f"**{workout['exercise_name']}**")
                with col_stats:
                    st.write(f"Score: **{workout['correct_reps']}/{workout['total_reps']} reps**")
                with col_btn:
                    if st.button("View Details", key=f"btn_{index}", use_container_width=True):
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