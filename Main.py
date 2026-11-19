import inspect
import pydoc
from pathlib import Path
import pythoncom

from dotenv import load_dotenv
import os
import gradio as gr
from docx import Document
import win32com.client
import pdfplumber

from langchain_core.messages import HumanMessage,AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


print("Gradio version:", gr.__version__)
print("Gradio location:", gr.__file__)
print(inspect.signature(gr.Chatbot))

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_miniloglevel"]="2"

load_dotenv()

Gemini_key = os.getenv("GEMINI_API_KEY")

system_prompt="""
you are a helper, here to help CV's sound more professional
you will ask the customer what their current job is and what it entails 
you will answer questions about the CV
you always remind the user to edit what you say so it is still their words, you are here just to add some professional flavour to their CV
you will use the uploaded CVs as reference when chatting
make the edits concise and keep the wording to a minimum where possible as default but the user may ask you to edit the style
the tone with the user should be conversational
"""

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = Gemini_key,
    temperature = 1
)

prompt = ChatPromptTemplate.from_messages([
    ("system",system_prompt),
    ("system","The uploaded CV contains:\n{cv_text}"),
    (MessagesPlaceholder(variable_name="history")),
    ("user","{input}")]
)

chain = prompt | llm | StrOutputParser()

print("Click below to get started fixing your CV")

def read_cv(file):
    file_path = file.name

    print("Loading: ",file_path)

    if file_path.lower().endswith(".docx"):

        pdf_path = docx_to_pdf(file_path)
        text = read_pdf(pdf_path)

    elif file_path.lower().endswith(".pdf"):
        text = read_pdf(file_path)

    else:
        text = ""


    print("CV Loaded!")
    print("length: ",len(text))
    print(text[:500])
    return text

def read_pdf(pdf_path):
    text=""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text

def docx_to_pdf(docx_path):

    pythoncom.CoInitialize()

    try:
        word=win32com.client.Dispatch("word.Application")
        word.Visible=False

        doc = word.Documents.Open(str(docx_path))

        pdf_path = str(Path(docx_path).with_suffix(".pdf"))

        doc.SaveAs(pdf_path, FileFormat=17) #PDF

        doc.Close()
        word.Quit()

        return pdf_path

    finally:
        pythoncom.CoUninitialize()

def process_file(file):
    if file.name.endswith(".docx"):
        pdf_path = docx_to_pdf(file.name)
        return read_pdf(pdf_path)

    elif file.name.endswith(".pdf"):
        return read_pdf(file.name)

def chat(user_in, hist, cv_text):
    print(user_in)
    print(hist)
    print("=" * 50)
    print("CV Text length:", len(cv_text))
    print("=" *50)

    langchain_history = []
    for item in hist:
        if item["role"] == "user":
            langchain_history.append(
                HumanMessage(content=item["content"]))
        elif item["role"]=="assistant":
            langchain_history.append(
                AIMessage(content=item["content"]))

    response=chain.invoke({
        "input": user_in,
        "history":langchain_history,
        "cv_text": cv_text
    })

    updated_history = hist +[
        {"role":"user", "content":user_in},
        {"role":"assistant","content":response}
    ]

    return "", updated_history

def clear_chat():
    return"",[]

page = gr.Blocks(
    title="CV Fixer",
    theme=gr.themes.Soft()
)

with page:
    gr.Markdown(
        """
        CV Fixer
        Let's get that CV Sorted!
        """
    )

    chatbot = gr.Chatbot(show_label=True)

    msg = gr.Textbox(show_label=True, placeholder="Chat here")


    cv_upload = gr.File(label="Upload CV",
                    file_types=[".docx",".pdf"],
                    file_count="single"

    )
    cv_text = gr.State("")

    cv_upload.upload(
        fn=read_cv,
        inputs=cv_upload,
        outputs=cv_text
    )


    msg.submit(
        chat,
        [msg, chatbot,cv_text],
        [msg,chatbot])

    clear = gr.Button("Clear chat")
    clear.click(clear_chat, outputs=[msg,chatbot])




page.launch(share=True)
