import streamlit as st
from tempfile import NamedTemporaryFile
from openai import OpenAI
import os
import base64
import streamlit.components.v1 as components
from io import BytesIO
import numpy as np


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


system_prompt = """
You are an AI English Conversation Teacher. Your response will be read aloud. 
so use only casual lines speech. Do not include any markdown formats or any other symbols.
If you can correct my sentence in terms of grammer, correct it at first like "you should say, <CORRECTED SENTENCE>" and then keep going the conversation.
When I say "Start", start conversation.
"""

_RELEASE = not st.secrets["LOCAL"]


def audio_recorder_component():
    if not _RELEASE:
        _component_func = components.declare_component(
            "audio_recorder_component",
            url="http://localhost:5173",  # vite dev server port
        )
    else:
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(parent_dir, "audio_recorder_component/dist")
        _component_func = components.declare_component(
            "audio_recorder_component", path=build_dir
        )

    def _my_component(name, key=None):
        component_value = _component_func(name=name, key=key)
        return component_value

    # https://dev.to/aisone/streamlit-custom-components-vite-vanilla-js-40hl
    # https://github.com/stefanrmmr/streamlit-audio-recorder/blob/777d18114130137d492c0378a86631fff1ff1be5/st_audiorec/__init__.py#L26
    wav_bytes = None
    raw_audio_data = _my_component(name="NameViteVanilla")
    if isinstance(raw_audio_data, dict):  # retrieve audio data
        with st.spinner("retrieving audio-recording..."):
            ind, raw_audio_data = zip(*raw_audio_data["arr"].items())
            ind = np.array(ind, dtype=int)  # convert to np array
            raw_audio_data = np.array(raw_audio_data)  # convert to np array
            sorted_ints = raw_audio_data[ind]
            stream = BytesIO(b"".join([int(v).to_bytes(1, "big") for v in sorted_ints]))
            # wav_bytes contains audio data in byte format, ready to be processed further
            wav_bytes = stream.read()
    return wav_bytes


def transcribe_audio_to_text(audio_bytes):
    with NamedTemporaryFile(delete=True, suffix=".wav") as temp_file:
        temp_file.write(audio_bytes)
        temp_file.flush()
        with open(temp_file.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="en",
            )
    return transcript


def text_to_speech(input):
    response = client.audio.speech.create(model="tts-1", voice="nova", input=input)
    file = NamedTemporaryFile(delete=False, suffix=".mp3")
    response.stream_to_file(file.name)
    return file


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true" style="opacity:0;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )


def chat_ui():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def send_chat(input):
    st.session_state.messages.append({"role": "user", "content": input})
    with st.chat_message("user"):
        st.markdown(input)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}]
            + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
    speech_file = text_to_speech(response)
    if speech_file:
        autoplay_audio(speech_file.name)
        os.unlink(speech_file.name)


# Example usage with Streamlit:
def main():
    st.title("English Conversation with GPT-4o")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "is_started" not in st.session_state:
        st.session_state.is_started = False

    if not st.session_state.is_started:
        # Start conversation
        with st.empty():
            if st.button("Let's Start!"):
                st.session_state.is_started = True
                send_chat("Start")

    wav_audio_data = None
    if st.session_state.is_started:
        # Record audio
        wav_audio_data = audio_recorder_component()

    chat_ui()

    if (
        wav_audio_data is not None
        and len(wav_audio_data) > 100
        and len(wav_audio_data) < 10000000
    ):
        # Convert audio to text using OpenAI Whisper API
        transcript = transcribe_audio_to_text(wav_audio_data)

        # chat
        send_chat(transcript)


if __name__ == "__main__":
    main()
