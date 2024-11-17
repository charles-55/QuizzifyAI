import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

class QuizProcessor:
    def __init__(self):
        self.document = None
        self.topic = "General Knowledge"
        self.amount = 5
        self.difficulty = "Easy"
        self.template = ""
        self.answer_page = []
    
    def ingest_documents(self):
        uploaded_file = None
        with st.form("quiz_generator"):
            self.topic = st.text_input("Quiz Topic")
            self.amount = st.slider("Number of Questions", 1, 20)
            uploaded_file = st.file_uploader("Upload a PDF file", type="pdf", accept_multiple_files=False)
            st.form_submit_button("Generate")
        
        if uploaded_file is not None:
            temp_file_path = uploaded_file.name
            self.document = genai.upload_file(temp_file_path)

        if (self.document) is not None:
            st.write(f":white_check_mark: File processed: {(self.document.display_name)}")
            self.regenerate_template()
            # print(self.template)

            col1, col2, _, _ = st.columns(4)
            with col1:
                summarize = st.button("Summarize", type="secondary")
            with col2:
                quizzify = st.button("Quizzify", type="primary")

            if summarize:
                self.summarize()
            if quizzify:
                self.quizzify()
        else:
            st.write(":x: No file uploaded")

    def regenerate_template(self):
        self.template = f"""
            You are an expert at the topic: {self.topic}

            Follow the instructions below and create a quiz:
            1. Generate {self.amount} question(s) based on the topic provided  and context as key "question"
            2. Provide 4 multiple choice answers to the question as a list of key-value pairs "choices"
            3. Provide the correct answer for the question from the list of answers as key "answer"
            4. Provide an explanation as to why the answer is correct as key "explanation"

            You must respond as a JSON object with the following structure:
            {{
                "question": "<question>",
                "choices": [
                    {{"key": "A", "value": "<choice>"}},
                    {{"key": "B", "value": "<choice>"}},
                    {{"key": "C", “value": "<choice>"}},
                    {{"key": "D", "value": "<choice>"}}
                ],
                "answer": "<answer key from choices list>",
                "explanation": "<explanation as to why the answer is correct>"
            }}

            Context: {self.document}
            """
    
    def summarize(self):
        with st.status("Summarizing...") as status:
            response = model.generate_content(["Give me a summary of this pdf file and mention the key points.", self.document])
            status.update(
                label="Summarization complete!", state="complete", expanded=False
            )

        with st.chat_message("model"):
            st.markdown(f"Document: {self.document.display_name}")
            st.markdown(response.text)
        st.session_state.chat_history.extend([{
            "role": "model",
            "content": f"Document: {self.document.display_name}"
        }, {
            "role": "model",
            "content": response.text
        }])
    
    def quizzify(self):
        self.answer_page = []
        with st.status("Generating quiz...") as status:
            response = model.generate_content(f"{self.template}")
            status.update(
                label="Generation complete!", state="complete", expanded=False
            )
        
        output = response.text.replace("```json\n", "").replace("\n```", "")
        # print(output)
        output = json.loads(output)

        display = ""
        for item in output:
            question = item["question"]
            choices = [choice["value"] for choice in item["choices"]]
            answer = item["answer"]
            explanation = item["explanation"]

            display += f"{question}\n"
            for index, choice in enumerate(choices):
                display += f"{chr(ord('A') + index)}. {choice}\n"
            
            self.answer_page.append({
                "question": question,
                "answer": answer,
                "explanation": explanation
            })
            display += "\n"

            # for choice in question.choices:
            #     display += f"{choice.key}. {choice.value}\n"
        
        # print(display)
        with st.chat_message("model"):
            st.markdown(display)
        st.session_state.chat_history.append([{
            "role": "model",
            "content": display
        }])


def generate_response(prompt):
    response = model.generate_content(prompt)
    with st.chat_message("model"):
        st.markdown(response.text)

    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })
    st.session_state.chat_history.append({
        "role": "model",
        "content": response.text
    })


if __name__ == "__main__":
    st.title("QuizzifyAI")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for index, message in enumerate(st.session_state.chat_history):
        if index != 0:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    user_input = st.chat_input("Type your message here...")
    with st.chat_message("model"):
        st.markdown("Upload a file to summarize or quizzify.")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        generate_response(user_input)

    processor = QuizProcessor()
    processor.ingest_documents()

    # with st.sidebar:
    #     form_submited = False
    #     with st.form("quiz_generator"):
    #         processor.topic = st.text_input("Quiz Topic") or processor.topic
    #         processor.amount = st.slider("Number of Questions", 1, 20)
    #         generator_submitted = st.form_submit_button("Generate")
            
    #         if generator_submitted:
    #             form_submited = True

    # if form_submited:
    #     processor.quizzify()
