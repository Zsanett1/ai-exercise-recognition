import streamlit as st


def show():
    st.title("About the Project")
    st.caption("Why this AI home workout assistant was created")
    st.write("---")

    st.markdown("### Why this project was created")
    st.write(
        "Regular physical activity is important, but going to a gym is not always realistic for everyone. "
        "Some people feel uncomfortable training in public spaces, while others struggle with limited time, "
        "travel distance, or lack of access to personal guidance."
    )

    st.write(
        "This project was created as a graduation thesis to explore how artificial intelligence can support "
        "home workouts in a more accessible and structured way. The goal is to help users train independently "
        "while still receiving basic guidance, repetition tracking, and progress-related feedback."
    )

    st.write("---")

    problem_img_col, problem_content_col = st.columns([1, 1.5])
    with problem_img_col:
        st.image("assets/home_tracking.png", use_container_width=True)
    with problem_content_col:
        st.markdown("### The problem")
        barrier_col, challenge_col = st.columns(2)
        with barrier_col:
            st.markdown("**Common barriers to gym training**")
            st.markdown(
                """
        - Lack of time for regular gym visits
        - Distance from suitable training facilities
        - Discomfort or anxiety in public workout environments
                """
            )
        with challenge_col:
            st.markdown("**Challenges of training at home**")
            st.markdown(
                """
        - Limited feedback on exercise execution
        - Uncertainty about correct movement form
        - Difficulty staying consistent without structure
        - Lack of simple progress tracking
                """
            )

    st.write("---")

    st.markdown("### The idea behind the solution")
    st.write(
        "The application aims to bring basic AI-supported workout guidance into the home environment. "
        "By using pose-based movement analysis, the system can recognize supported exercises, count repetitions, "
        "and help users follow their training in a more measurable way."
    )

    st.write(
        "Instead of replacing a professional trainer, the goal is to provide an accessible digital assistant "
        "that makes independent home exercises easier to start, easier to follow, and easier to track over time."
    )

    st.write("---")

    st.markdown("### Who can benefit from it")
    audience_col1, audience_col2, audience_col3 = st.columns(3)
    with audience_col1:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>BEGINNERS</span>", unsafe_allow_html = True)
            st.markdown("**People starting out**")
            st.write("Users who want a simple and structured way to begin exercising at home.")
    with audience_col2:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>BUSY USERS</span>", unsafe_allow_html = True)
            st.markdown("**People with limited time**")
            st.write("Users who need a flexible workout option without travelling to a gym.")
    with audience_col3:
        with st.container(border = True):
            st.markdown("<span style='color: #14B8A6; font-weight: 800;'>HOME TRAINING</span>", unsafe_allow_html = True)
            st.markdown("**People preferring privacy**")
            st.write("Users who feel more comfortable exercising in their own environment.")

    st.write("---")

    st.markdown("### Project mission")
    st.write(
        "The mission of this project is to make home workouts more accessible, measurable, and "
        "confidence-friendly through AI-supported movement recognition and progress tracking."
    )