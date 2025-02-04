import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests

# Load API Keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Validate API Keys
if not GEMINI_API_KEY:
    st.error("❌ Gemini AI API key not found! Please add GEMINI_API_KEY to your .env file.")
    st.stop()

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit UI Setup
st.set_page_config(page_title="AI What If Simulator", layout="wide")

# Custom CSS for Better UI
st.markdown("""
    <style>
        /* Dark theme */
        .stApp {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Title styling */
        .title {
            font-size: 50px;
            font-weight: bold;
            color: #f5a623;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Input and button styling */
        .stTextInput, .stButton>button {
            font-size: 20px;
        }
        
        /* Image container styling */
        .image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 1rem 0;
        }
        
        /* Explanation text styling */
        .explanation-text {
            background-color: #1E1E2E;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<p class='title'>🤖 AI-Powered 'What If?' Simulator 🌍</p>", unsafe_allow_html=True)
st.write("### Imagine the impossible & let AI bring it to life! 🚀")

# User input
user_input = st.text_input("Enter a 'What If?' scenario (e.g., What if the Earth stopped rotating?):")

# Function to Convert Text to Speech using ElevenLabs
def text_to_speech(text):
    try:
        # Check if API key is available
        if not ELEVENLABS_API_KEY:
            st.error("❌ ElevenLabs API key not found! Please add ELEVENLABS_API_KEY to your .env file.")
            return None
        # Limit text to 100 words and add closing message
        words = text.split()
        if len(words) > 100:
            limited_text = ' '.join(words[:100])
            narration_text = f"{limited_text}... You can read further by yourself."
        else:
            narration_text = text

        # Using Rachel voice (more reliable than the default voice)
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            }
        }
        
        st.info("🎙️ Generating voice narration...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            audio_file = "narration.mp3"
            with open(audio_file, "wb") as f:
                f.write(response.content)
            return audio_file
        elif response.status_code == 401:
            st.error(f"❌ ElevenLabs API Error: {response.text}")
            return None
        else:
            st.error(f"❌ ElevenLabs API Error: Status {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"❌ Error in voice generation: {str(e)}")
        return None

# Function to generate image using Pollinations.ai
def generate_image(prompt):
    try:
        # Clean and format the prompt
        formatted_prompt = prompt.replace(" ", "%20")
        
        # Use Pollinations.ai API
        image_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}"
        
        st.info("🎨 Generating image...")
        response = requests.get(image_url, timeout=20)
        
        if response.status_code == 200:
            image_path = "generated_image.png"
            with open(image_path, "wb") as f:
                f.write(response.content)
            return image_path
        else:
            # Try with a simplified prompt if first attempt fails
            simple_prompt = "%20".join(prompt.split()[:5])  # Take first 5 words
            backup_url = f"https://image.pollinations.ai/prompt/{simple_prompt}"
            backup_response = requests.get(backup_url, timeout=20)
            
            if backup_response.status_code == 200:
                image_path = "generated_image.png"
                with open(image_path, "wb") as f:
                    f.write(backup_response.content)
                return image_path
            else:
                st.error("❌ Unable to generate image. Please try again.")
                return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Image generation timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Error generating image: {str(e)}")
        return None

# Button to Generate AI Response
if st.button("Generate AI Response"):
    if user_input:
        with st.spinner("🤖 Generating AI Explanation..."):
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"""Explain this scenario in a clear and engaging way. Keep your response under 200 words:
            {user_input}"""
            response = model.generate_content(prompt)
            explanation = response.text

        st.markdown('<div class="explanation-text">', unsafe_allow_html=True)
        st.write("### 🧠 AI Explanation:")
        st.write(explanation)
        st.markdown('</div>', unsafe_allow_html=True)

        # Generate Image Prompt using Gemini
        with st.spinner("🎨 Creating Image Prompt..."):
            prompt_request = f"""Create a detailed image generation prompt based on this scenario: {user_input}
            
            Requirements:
            1. STRICTLY keep it under 100 words
            2. Focus on creating a single, clear scene that will work well as a 400x400 pixel image
            3. Make it vivid and descriptive, focusing on visual elements
            4. Use plain text only, no special characters or formatting
            5. Describe the most visually striking moment or aspect of the scenario
            
            Format your response as a single paragraph of plain text."""
            
            prompt_response = model.generate_content(prompt_request)
            image_prompt = prompt_response.text
            
            # Ensure the prompt is under 100 words
            words = image_prompt.split()
            if len(words) > 100:
                image_prompt = ' '.join(words[:100]) + '...'
            
            st.markdown('<div class="explanation-text">', unsafe_allow_html=True)
            st.write("### 🎯 Generated Image Prompt:")
            st.write(image_prompt)
            st.write(f"*Word count: {len(words)}*")
            st.markdown('</div>', unsafe_allow_html=True)

        # AI Image Generation using Pollinations.ai
        with st.spinner("🎨 Creating AI-Generated Image..."):
            image_path = generate_image(image_prompt)
            if image_path:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(image_path, caption="AI-Generated Visualization", width=400)
                st.markdown('</div>', unsafe_allow_html=True)

        # Generate AI Voice Narration
        with st.spinner("🎙️ Generating AI Voice..."):
            audio_file = text_to_speech(explanation)
            if audio_file:
                st.audio(audio_file, format="audio/mp3")

    else:
        st.warning("⚠️ Please enter a 'What If?' scenario before generating!")
