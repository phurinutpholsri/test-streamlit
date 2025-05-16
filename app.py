import streamlit as st
from openai import OpenAI

openai_api_key = st.secrets['OPENAI_API_KEY']
client = OpenAI(api_key=openai_api_key)

with open("genai-mf-prompt-for-first-draft.txt", "r", encoding="utf-8") as file:
    prompt_mf = file.read()

with open("gen-ai-motor-first-draft.txt", "r", encoding="utf-8") as file:
    prompt_motor = file.read()


st.title("🧠 Smart Financial Assistant")

# --- Session Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "สวัสดีครับ คุณสามารถถามเกี่ยวกับกองทุนรวม หรือประกันรถยนต์ได้เลย"
    }]
if "awaiting_clarification" not in st.session_state:
    st.session_state.awaiting_clarification = False
if "original_question" not in st.session_state:
    st.session_state.original_question = None

# --- Define Agents ---
AGENTS = {
    "mutual_fund": prompt_mf,
    "motor_insurance": prompt_motor,
    "controller": (
        "You are a smart assistant controller. Based on the user's input, determine if they are asking about 'mutual_fund' or 'motor_insurance'. "
        "If unclear, ask a clarifying question. If clear, respond with only one of these words: 'mutual_fund' or 'motor_insurance'."
    )
}
VALID_TOPICS = ["mutual_fund", "motor_insurance"]

# --- Show Chat History ---
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- LLM Classifier Function ---
def route_topic_or_ask_clarification(user_input: str):
    system_msg = {"role": "system", "content": AGENTS["controller"]}
    user_msg = {"role": "user", "content": user_input}

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_msg, user_msg]
    )
    reply = response.choices[0].message.content.strip().lower()

    if reply in VALID_TOPICS:
        return reply, None
    else:
        return None, reply

# --- Chat Handling ---
if prompt := st.chat_input("ถามได้เลย เช่น กองทุนรวม หรือ ประกันรถ"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if st.session_state.awaiting_clarification:
        # Follow-up after clarification
        original_q = st.session_state.original_question
        full_question = f"{original_q}\n\n(เพิ่มเติมจากผู้ใช้: {prompt})"

        topic, _ = route_topic_or_ask_clarification(full_question)

        if topic:
            # Include full chat history
            system_msg = {"role": "system", "content": AGENTS[topic]}
            chat_history = [system_msg] + st.session_state.messages

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_history
            )
            reply = response.choices[0].message.content

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(f"🔧 *{topic.replace('_', ' ').title()} Agent*\n\n{reply}")
        else:
            st.session_state.messages.append({"role": "assistant", "content": "ขออภัย ยังไม่สามารถระบุหัวข้อได้ครับ"})
            st.chat_message("assistant").write("🤖 *Controller*\n\nยังไม่สามารถระบุหัวข้อได้ครับ")

        # Reset
        st.session_state.awaiting_clarification = False
        st.session_state.original_question = None

    else:
        # First-time message
        topic, clarifying = route_topic_or_ask_clarification(prompt)

        if topic:
            system_msg = {"role": "system", "content": AGENTS[topic]}
            chat_history = [system_msg] + st.session_state.messages

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_history
            )
            reply = response.choices[0].message.content

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(f"🔧 *{topic.replace('_', ' ').title()} Agent*\n\n{reply}")
        else:
            # Ask for clarification
            st.session_state.awaiting_clarification = True
            st.session_state.original_question = prompt
            st.session_state.messages.append({"role": "assistant", "content": clarifying})
            st.chat_message("assistant").write(f"🤖 *Controller*\n\n{clarifying}")
