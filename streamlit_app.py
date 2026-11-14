
import streamlit as st
import requests
import time
import uuid
import hmac
import hashlib
import base64
from datetime import datetime, timezone

st.set_page_config(
    page_title="SwitchBot Dashboard",
    page_icon="🌡️",
    layout="wide"
)

BASE = "https://api.switch-bot.com/v1.1"

def auth_headers():
    token = st.secrets["SWITCHBOT_TOKEN"]
    secret = st.secrets["SWITCHBOT_SECRET"]

    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    payload = (token + timestamp + nonce).encode()

    signature = base64.b64encode(
        hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
    ).decode()

    return {
        "Authorization": token,
        "sign": signature,
        "t": timestamp,
        "nonce": nonce,
        "Content-Type": "application/json"
    }

def api_get(path):
    response = requests.get(
        BASE + path,
        headers=auth_headers(),
        timeout=15
    )
    response.raise_for_status()

    result = response.json()
    if str(result.get("statusCode")) != "100":
        raise RuntimeError(
            result.get("message", "SwitchBot API error")
        )

    return result.get("body") or {}

@st.fragment(run_every="300s")
def dashboard():
    try:
        devices = api_get("/devices").get("deviceList", [])
    except Exception:
        st.error("Could not connect to SwitchBot. Check your credentials and API access.")
        return

    st.subheader("Current temperatures")
    readings = []

    for device in devices:
        device_id = device.get("deviceId")
        name = device.get("deviceName") or "Unnamed sensor"

        if not device_id:
            continue

        try:
            status = api_get(
                f"/devices/{device_id}/status"
            )
        except Exception:
            continue

        temp = status.get("temperature")
        humidity = status.get("humidity")

        if temp is None:
            continue

        readings.append({
            "name": name,
            "temperature": float(temp),
            "humidity": humidity
        })

    if not readings:
        st.warning(
            "No temperature readings found. "
            "Check that your thermometers support "
            "SwitchBot Cloud API access."
        )
        return

    for start in range(0, len(readings), 2):
        columns = st.columns(2)

        for col, reading in zip(
            columns, readings[start:start + 2]
        ):
            with col:
                st.metric(
                    reading["name"],
                    f'{reading["temperature"]:.1f} °C'
                )

                if reading["humidity"] is not None:
                    st.caption(
                        f'Humidity: {reading["humidity"]}%'
                    )

    st.caption(
        "Last checked: "
        + datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    )

st.title("🌡️ My SwitchBot Dashboard")
st.caption("Automatic refresh every 5 minutes")

if st.button("Refresh now"):
    st.rerun()

dashboard()
