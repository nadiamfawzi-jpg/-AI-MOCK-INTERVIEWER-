import os
import tempfile

import pandas as pd
import streamlit as st
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from interview_utils import get_overall_feedback, score_answer
from video_utils import LiveVideoProcessor, analyze_uploaded_video


st.set_page_config(page_title="AI Interview Coach", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#f7f9ff 0%,#eef8ff 50%,#fff8f0 100%)}
.block-container{padding-top:1.6rem;max-width:1250px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#102a43,#183b56)}
[data-testid="stSidebar"] *{color:white}
.hero{padding:32px 38px;border-radius:24px;background:linear-gradient(120deg,#102a43,#2563eb 58%,#06b6d4);color:white;box-shadow:0 18px 45px #102a432e;margin-bottom:22px}
.hero h1{font-size:2.8rem;font-weight:900;margin:0 0 8px;color:white}.hero p{font-size:1.08rem;margin:0;color:#e6f4ff;max-width:780px}
.badge{display:inline-block;background:#ffffff29;padding:7px 12px;border:1px solid #ffffff40;border-radius:100px;font-weight:700;font-size:.82rem;margin-bottom:13px}
.card{background:#ffffffe8;border:1px solid #dbeafe;border-radius:17px;padding:18px;min-height:135px;box-shadow:0 8px 25px #1e40af12}
.icon{font-size:1.75rem}.card-title{font-size:1.02rem;font-weight:850;color:#102a43;margin:8px 0 4px}.card-text{font-size:.9rem;color:#526777;line-height:1.45}
.question{padding:22px;border-radius:18px;background:linear-gradient(120deg,#eff6ff,#fff);border-left:7px solid #2563eb;font-size:1.18rem;font-weight:750;color:#102a43;margin:8px 0 18px}
.safe{background:#fff7ed;color:#7c2d12;padding:14px 16px;border-radius:12px;border:1px solid #fed7aa;margin-bottom:16px}
h1,h2,h3{color:#102a43;font-weight:850!important}.stButton>button{border:0;border-radius:12px;font-weight:800;min-height:44px;background:linear-gradient(90deg,#2563eb,#0891b2);color:white;box-shadow:0 7px 18px #2563eb38}
div[data-testid="stMetric"]{background:#ffffffe8;border:1px solid #dbeafe;padding:15px;border-radius:15px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero"><div class="badge">✨ SMART PRACTICE • SUPPORTIVE FEEDBACK</div>
<h1>🎯 AI Interview Coach</h1><p>Practise field-specific interview questions, improve your answer content,
and review visible delivery cues from a live or recorded interview video.</p></div>
""", unsafe_allow_html=True)

cards = [
    ("🎓", "Choose your field", "Select questions commonly asked in your career area."),
    ("💬", "Answer naturally", "Write the answer as you would say it in an interview."),
    ("🧠", "Receive NLP feedback", "Compare your answer with key ideas and a sample answer."),
    ("🎥", "Review delivery", "Analyse face visibility, expressions, and hand gestures.")
]
for column, card in zip(st.columns(4), cards):
    with column:
        st.markdown(f'<div class="card"><div class="icon">{card[0]}</div><div class="card-title">{card[1]}</div><div class="card-text">{card[2]}</div></div>', unsafe_allow_html=True)

app_folder = os.path.dirname(os.path.abspath(__file__))
questions_df = pd.read_csv(os.path.join(app_folder, "questions.csv"))

with st.sidebar:
    st.title("⚙️ Interview Setup")
    st.caption("Personalise your practice session")
    field = st.selectbox("🎓 Choose your field", questions_df["Field"].unique())
    field_questions = questions_df[questions_df["Field"] == field].reset_index(drop=True)
    question_number = st.selectbox("❓ Choose a question", range(len(field_questions)), format_func=lambda number: "Question " + str(number + 1))
    confidence = st.slider("🌡️ How confident do you feel?", 1, 5, 3)
    st.caption("1 = very nervous • 5 = very confident")
    st.divider()
    st.markdown("**🔍 Technologies**")
    st.caption("NLP • TF-IDF • Cosine Similarity • YOLO • OpenCV • MediaPipe")
    st.divider()
    st.caption("💡 Practice tool only — not a hiring decision system.")

selected = field_questions.iloc[question_number]
tab1, tab2, tab3 = st.tabs(["💬 Mock Interview", "🎥 Video Coach", "📊 My Summary"])


@st.cache_data(ttl=3600)
def get_rtc_configuration():
    try:
        from twilio.rest import Client

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        token = Client(account_sid, auth_token).tokens.create()
        return RTCConfiguration({"iceServers": token.ice_servers}), True
    except Exception:
        return RTCConfiguration({
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }), False

with tab1:
    st.subheader("💼 " + field + " Mock Interview")
    st.markdown('<div class="question">❓ ' + selected["Question"] + '</div>', unsafe_allow_html=True)
    answer = st.text_area("🗣️ Your interview answer", height=190, placeholder="Type your answer here as if you are speaking to the interviewer...")
    c1, c2 = st.columns([1, 3])
    with c1:
        check_answer = st.button("✨ Check My Answer", type="primary", use_container_width=True)
    with c2:
        st.caption("Tip: include the situation, your action, and a clear result or lesson.")

    if check_answer:
        if answer.strip() == "":
            st.warning("⚠️ Please write your answer first.")
        else:
            st.session_state["answer_result"] = score_answer(answer, selected["Ideal_Answer"], selected["Keywords"])
            st.session_state["answer_text"] = answer

    if "answer_result" in st.session_state:
        result = st.session_state["answer_result"]
        st.markdown("### 📈 Instant Feedback")
        columns = st.columns(3)
        columns[0].metric("🎯 Answer relevance", str(result["score"]) + "%")
        columns[1].metric("🔑 Key ideas used", str(result["matched"]) + "/" + str(result["total"]))
        columns[2].metric("📝 Answer length", str(result["word_count"]) + " words")
        if result["score"] >= 70:
            st.success("🌟 Strong answer — you covered most important ideas.")
        elif result["score"] >= 45:
            st.warning("👍 Good start — add one or two important ideas.")
        else:
            st.error("🛠️ Add more detail and connect it clearly to the question.")
        left, right = st.columns(2)
        with left:
            st.markdown("#### ✅ What you did well")
            st.write(result["strength"])
        with right:
            st.markdown("#### 🚀 What to improve")
            st.write(result["improvement"])
            st.write("**Missing ideas:** " + result["missing_text"])
        with st.expander("💡 View a sample strong answer"):
            st.write(selected["Ideal_Answer"])

with tab2:
    st.subheader("🎥 Facial Expression & Hand Gesture Coach")
    st.markdown('<div class="safe"><b>🛡️ Important:</b> The app estimates visible cues only. It cannot know your real feelings, diagnose anxiety, or decide if you are suitable for a job.</div>', unsafe_allow_html=True)
    video_mode = st.radio("📹 Choose a video method", ["🔴 Live webcam", "📤 Upload recorded video"], horizontal=True)
    if video_mode == "🔴 Live webcam":
        st.info("💡 Allow camera access and keep your upper body, face, and hands inside the frame.")
        rtc_configuration, turn_ready = get_rtc_configuration()
        if not turn_ready:
            st.warning(
                "🌐 Live video on Streamlit Cloud may require TURN credentials. "
                "If the connection remains on 'Sharing Camera', use the uploaded-video option "
                "or add Twilio credentials in Streamlit Secrets."
            )
        webrtc_streamer(
            key="interview-video", mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_configuration,
            video_processor_factory=LiveVideoProcessor,
            media_stream_constraints={
                "video": {"width": {"ideal": 640}, "height": {"ideal": 480}},
                "audio": False
            },
            async_processing=True
        )
        st.caption("🎯 Try a natural smile, open palm, peace sign, thumbs up, or closed fist.")
    else:
        uploaded_video = st.file_uploader("📁 Upload an interview video", type=["mp4", "mov", "avi"])
        if uploaded_video is not None:
            st.video(uploaded_video)
            if st.button("🔍 Analyse My Video", type="primary"):
                with st.spinner("🤖 YOLO and landmark models are analysing the video..."):
                    suffix = "." + uploaded_video.name.split(".")[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as input_file:
                        input_file.write(uploaded_video.getbuffer())
                        input_path = input_file.name
                    output_path = os.path.join(tempfile.gettempdir(), "analysed_interview.mp4")
                    video_result = analyze_uploaded_video(input_path, output_path)
                    st.session_state["video_result"] = video_result
                st.success("✅ Video analysis completed.")
                st.video(output_path)
                columns = st.columns(4)
                columns[0].metric("🙂 Face visible", str(video_result["face_percentage"]) + "%")
                columns[1].metric("🧍 Person visible", str(video_result["person_percentage"]) + "%")
                columns[2].metric("😊 Main expression", video_result["main_expression"])
                columns[3].metric("👋 Main gesture", video_result["main_gesture"])
                if video_result["cue_level"] == "Calm visible delivery":
                    st.success("🌟 Visible delivery was mostly steady. Continue practising naturally.")
                elif video_result["cue_level"] == "Some nervous cues":
                    st.warning("🌿 Some possible nervous cues appeared. Slow down and breathe before answering.")
                else:
                    st.info("💡 Improve lighting and keep your face and upper body inside the frame.")

with tab3:
    st.subheader("📊 Your Practice Summary")
    if "answer_result" not in st.session_state:
        st.info("💬 Complete the mock interview first to unlock your summary.")
    else:
        summary = get_overall_feedback(st.session_state["answer_result"], st.session_state.get("video_result"), confidence)
        columns = st.columns(2)
        columns[0].metric("🏆 Overall practice score", str(summary["overall"]) + "%")
        columns[1].metric("🚦 Readiness level", summary["level"])
        st.progress(summary["overall"] / 100)
        st.markdown("#### 💪 Main strength")
        st.write(summary["strength"])
        st.markdown("#### 🎯 Next practice goal")
        st.write(summary["next_step"])
        st.caption("The score supports practice only and must not be used for recruitment decisions.")
