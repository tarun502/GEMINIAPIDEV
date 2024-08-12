from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Firebase only if it hasn't been initialized yet
if not firebase_admin._apps:
    cred = credentials.Certificate('gemini-fb602-firebase-adminsdk-xk8kw-311f2e689d.json')
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Define function to get response from Google Gemini API
def get_gemini_response(input, image=None, prompt=None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash' if image else 'gemini-1.5-flash')
        if image:
            response = model.generate_content([input, image[0], prompt])
        else:
            response = model.generate_content([input, prompt])
        return response.text
    except Exception as e:
        st.error(f"Error getting response from Google Gemini API: {e}")
        return "An error occurred while generating the response."

# Define function to handle image upload
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit app configuration
st.set_page_config(page_title="Gemini Math Tutor App")

st.header("Gemini Math Tutor App")
input_prompt = st.text_input("Input Prompt: ", key="input")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
image = ""
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

submit = st.button("Get Explanation and Questions")

# Define prompts
text_prompt_template = """
You are an expert in Maths. Greet the Student as MathSolver if the Student greets.

Start by introducing yourself.

If the Student specifically asks you to solve a problem, reply only with the solution. No additional explanation or 
questions are required unless the Student asks for them.

Explain the Student's query in a clear and engaging manner like a friendly teacher , using the image if provided to enhance understanding.

Provide a comprehensive learning experience with the following structure:

"explanation": "Provide a clear and detailed explanation of the Student's query related to quadratic equations.",

"practice_problems_with_realtime": "Generate three practice problems based on the Student's query with real-time context to make the problems more relatable.",

"fun_facts": "Share two fun facts or trivia related to the Student's query related to quadratic equations.",

"interactive_question": "Ask an interactive question that encourages the student to explore the topic further."

If the Student asks for practice problems, help them solve the problems and provide additional support.

Always refer to yourself as MathSolver. Be concise and clear in your explanations.
"""

image_prompt_template = """
You are an expert in Maths. Greet the Student as MathSolver if the Student greets.

Start by introducing yourself and discussing the importance and applications of "Quadratic Equations" in daily life.

If the Student uploads an image, first analyze the image to understand the context and content. Then, incorporate this visual information into your response.

If the Student specifically asks you to solve a problem using an image, reply only with the solution. No additional explanation or questions are required unless the Student asks for them.

Explain the Student's query in a clear and engaging manner, using the image if provided to enhance understanding.
"""

# If submit button is clicked
if submit:
    try:
        if uploaded_file is not None:
            explainer_prompt = image_prompt_template.format(query=input_prompt)
            image_data = input_image_setup(uploaded_file)
            response = get_gemini_response(input_prompt, image_data, explainer_prompt)
        else:
            explainer_prompt = text_prompt_template.format(query=input_prompt)
            response = get_gemini_response(input_prompt, prompt=explainer_prompt)
        
        st.subheader("The Response is")
        st.write(response)
        
        # Save response to Firebase Firestore
        db.collection('responses').add({
            'input_prompt': input_prompt,
            'response': response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        st.write("Response saved to Firebase!")
    except Exception as e:
        st.error(f"An error occurred: {e}")

