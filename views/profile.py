import streamlit as st
import database
import base64

def show():
    st.title("Profile")
    st.caption("Manage your account, workout preferences, and daily training goal.")
    st.write("---")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    
    if st.session_state["logged_in"]:
        current_user = st.session_state["username"]
        user_data = database.get_user_profile(current_user)
        if user_data["full_name"].strip():
            display_name = user_data["full_name"]
        else:
            display_name = current_user
        profile_goal = user_data["fitness_goal"]
        profile_level = user_data["fitness_level"]
        daily_target = user_data["daily_target"]
        if user_data["profile_picture"] == "default" or not user_data["profile_picture"]:
            display_image = "assets/default_avatar.png"
        else:
            display_image = user_data["profile_picture"]

        col_avatar, col_summary = st.columns([0.7, 2.3])
        with col_avatar:
            with st.container(border = True):
                st.image(display_image, width = 120)
                st.markdown(f"**{display_name}**")
                st.caption(f"@{current_user}")
                st.write("")
                if st.button("Log out", type = "secondary"):
                    st.session_state["logged_in"] = False
                    st.session_state["username"] = None
                    st.rerun()
        with col_summary:
            with st.container(border = True):
                st.markdown("### Profile overview")
                st.caption("Your current training setup and saved preferences.")
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                with summary_col1:
                    st.markdown(
                        "<span style='color: #14B8A6; font-weight: 800;'>GOAL</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{profile_goal}**")
                with summary_col2:
                    st.markdown(
                        "<span style='color: #14B8A6; font-weight: 800;'>LEVEL</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{profile_level}**")
                with summary_col3:
                    st.markdown(
                        "<span style='color: #14B8A6; font-weight: 800;'>DAILY TARGET</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{daily_target} reps**")

        st.write("---")

        settings_left, settings_center, settings_right = st.columns([1, 2.5, 1])
        with settings_center:
            with st.expander("Personal Information", expanded = False):
                st.write("Update your basic profile details.")
                new_name = st.text_input("Full Name", value = user_data["full_name"])
                new_age = st.number_input("Age", min_value = 0, max_value = 100, value = user_data["age"])
                gender_options = ["Male", "Female", "Other/Prefer not to say"]
                default_gender_index = gender_options.index(user_data["gender"]) if user_data["gender"] in gender_options else 0
                new_gender = st.selectbox("Gender", options = gender_options, index = default_gender_index)

                st.write("")
                st.markdown("**Profile picture**")
                uploaded_file = st.file_uploader("Upload a profile picture", type = ["png", "jpg", "jpeg"])
                reset_to_default = st.checkbox("Reset to default avatar")
            with st.expander("Workout Preferences", expanded = False):
                st.write("Customize your training goal, experience level, and daily target.")
                goal_options = ["Stay Fit", "Lose Weight", "Build Muscle", "Increase Endurance"]
                default_goal_index = goal_options.index(user_data["fitness_goal"]) if user_data["fitness_goal"] in goal_options else 0
                new_goal = st.selectbox("Primary fitness goal", options = goal_options, index = default_goal_index)
                level_options = ["Beginner", "Intermediate", "Advanced"]
                default_level_index = level_options.index(user_data["fitness_level"]) if user_data["fitness_level"] in level_options else 0
                new_level = st.selectbox("Fitness level", options = level_options, index = default_level_index)
                new_target = st.slider("Daily repetition target", min_value = 10, max_value = 200, value = int(user_data["daily_target"]), step = 5)
            with st.expander("Account Security", expanded = False):
                st.write("Change your password to keep your account secure.")
                with st.form("password_form", clear_on_submit = True):
                    current_password = st.text_input("Current password", type = "password")
                    new_password = st.text_input("New password", type = "password")
                    confirm_password = st.text_input("Confirm new password", type = "password")
                    submit_password = st.form_submit_button("Update password")
                    if submit_password:
                        if not current_password or not new_password or not confirm_password:
                            st.error("Please fill in all password fields.")
                        elif new_password != confirm_password:
                            st.error("The new password and confirmation do not match.")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters long.")
                        else:
                            user_check = database.check_login(current_user, current_password)
                            if user_check:
                                hashed_new = database.hash_password(new_password)
                                conn = database.sqlite3.connect(database.db_file)
                                cursor = conn.cursor()
                                cursor.execute("update users set password = ? where username = ?", (hashed_new, current_user))
                                conn.commit()
                                conn.close()
                                st.markdown(
                                    "<span style='color: #14B8A6; font-weight: 700;'>Password updated successfully.</span>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.error("Incorrect current password.")

            st.write("")

            if st.button("Save Changes", type = "secondary", use_container_width = True):
                try:
                    final_avatar_string = user_data["profile_picture"]
                    if reset_to_default:
                        final_avatar_string = "default"
                    elif uploaded_file is not None:
                        file_bytes = uploaded_file.read()
                        encoded_base64 = base64.b64encode(file_bytes).decode("utf-8")
                        final_avatar_string = f"data:image/png;base64,{encoded_base64}"

                    database.update_user_profile(current_user, new_name, new_age, new_gender, final_avatar_string, new_goal, new_level, new_target)
                    st.session_state["profile_save_notice"] = "Profile changes saved successfully."
                    st.rerun()
                except Exception:
                    st.session_state["profile_save_error"] = "Could not save profile changes. Please try again."
                    st.rerun()
            if "profile_save_notice" in st.session_state:
                st.markdown(
                    f"<span style='color: #14B8A6; font-weight: 700;'>{st.session_state['profile_save_notice']}</span>",
                    unsafe_allow_html=True
                )
                del st.session_state["profile_save_notice"]

            if "profile_save_error" in st.session_state:
                st.markdown(
                    f"<span style='color: #B91C1C; font-weight: 700;'>{st.session_state['profile_save_error']}</span>",
                    unsafe_allow_html=True
                )
                del st.session_state["profile_save_error"]

    else:
        st.markdown("### Access your training profile")
        st.caption("Sign in or create an account to save workout history, daily goals, and personal preferences.")
        st.write("")

        col_left, col_center, col_right = st.columns([1.3, 1.8, 1.3])
        
        with col_center:
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

            with tab_login:
                st.subheader("Welcome back")
                login_user = st.text_input("Username", key = "login_user_input")
                login_pass = st.text_input("Password", type = "password", key = "login_pass_input")
                if st.button("Sign In", use_container_width = True):
                    if login_user and login_pass:
                        user_found = database.check_login(login_user, login_pass)
                        if user_found:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = login_user
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")
                    else:
                        st.warning("Please enter both Username and Password to log in.")

            with tab_signup:
                st.subheader("Create your profile")
                reg_user = st.text_input("Username", key = "reg_user_input")
                reg_pass = st.text_input("Password", type = "password", key = "reg_pass_input")
                reg_pass_confirm = st.text_input("Confirm password", type = "password", key = "reg_pass_confirm_input")
                if st.button("Create Account", use_container_width = True):
                    if reg_user and reg_pass and reg_pass_confirm:
                        if reg_pass != reg_pass_confirm:
                            st.error("Passwords do not match. Please try again.")
                        elif len(reg_pass) < 6:
                            st.error("Password must be at least 6 characters long. Please try again.")
                        else:
                            success = database.register_user(reg_user, reg_pass)
                            if success:
                                st.caption("Account created successfully. You can now switch to the Sign In tab.")
                            else:
                                st.error("Username already exists. Please try again with a different one.")
                    else:
                        st.warning("Please enter both Username and Password to create an account.")