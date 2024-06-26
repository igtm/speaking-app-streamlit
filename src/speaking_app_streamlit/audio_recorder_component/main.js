import "./style.css";
import { Streamlit } from "streamlit-component-lib";

let mimeType = "audio/webm";
if (!MediaRecorder.isTypeSupported("audio/webm")) {
  if (MediaRecorder.isTypeSupported("video/mp4")) {
    mimeType = "video/mp4";
  } else {
    alert("both audio/webm and video/mp4 are not supported");
  }
}

const buttonStart = document.querySelector("#buttonStart");
const buttonStop = document.querySelector("#buttonStop");
const buttonCancel = document.querySelector("#buttonCancel");
// const player = document.querySelector("#player");

buttonStart.addEventListener("click", async () => {
  Streamlit.setComponentValue("");
  const stream = await navigator.mediaDevices
    .getUserMedia({
      video: false,
      audio: true,
    })
    .catch((error) => {
      alert(error);
    });
  const mediaRecorder = new MediaRecorder(stream, {
    mimeType: mimeType,
  });
  mediaRecorder.start();

  // hide start button
  buttonStart.setAttribute("disabled", "");
  // show stop button
  buttonStop.removeAttribute("disabled");
  buttonCancel.removeAttribute("disabled");
  buttonStop.addEventListener("click", () => {
    mediaRecorder.addEventListener("dataavailable", (event) => {
      // player.src = URL.createObjectURL(event.data);
      event.data
        .arrayBuffer()
        .then((buffer) => {
          Streamlit.setComponentValue({
            arr: new Uint8Array(buffer),
          });
        })
        .finally(() => {
          // hide blinking red dot on the tab
          // https://stackoverflow.com/a/74656111
          stream.getTracks().forEach((track) => {
            track.stop();
            track.enabled = false;
          });
        });
    });
    mediaRecorder.stop();
    buttonStart.removeAttribute("disabled");
    buttonStop.setAttribute("disabled", "");
    buttonCancel.setAttribute("disabled", "");
  });
  buttonCancel.addEventListener("click", () => {
    mediaRecorder.stop();
    stream.getTracks().forEach((track) => {
      track.stop();
      track.enabled = false;
    });
    buttonStart.removeAttribute("disabled");
    buttonStop.setAttribute("disabled", "");
    buttonCancel.setAttribute("disabled", "");
  });
});

function onRender(event) {
  const data = event.detail;
  if (data.theme) {
  }
  buttonStart.disabled = data.disabled;
  let name = data.args["name"];
  console.log(name);
  Streamlit.setFrameHeight();
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
Streamlit.setFrameHeight();
