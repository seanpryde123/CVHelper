import inspect

from dotenv import load_dotenv
import os
import gradio as gr

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
you will ask the user to copy and paste sections of their CV and you will work your magic
make the edits concise and keep the wording to a minimum where possible as default but the user may ask you to edit the style
"""

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = Gemini_key,
    temperature = 1
)

prompt = ChatPromptTemplate.from_messages([
    ("system",system_prompt),
    (MessagesPlaceholder(variable_name="history")),
    ("user","{input}")]
)

chain = prompt | llm | StrOutputParser()

print("Click below to get started fixing your CV")

def chat(user_in, hist):
    print(user_in)
    print(hist)

    langchain_history = []
    for item in hist:
        if item["role"] == "user":
            langchain_history.append(HumanMessage(content=item["content"]))
        elif item["role"]=="assistant":
            langchain_history.append(AIMessage(content=item["content"]))

    response=chain.invoke({"input": user_in, "history":langchain_history})

    return "", hist + [{"role":"user", "content":user_in},
                       {"role":"assistant", "content":response}]

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

    msg = gr.Textbox(show_label=True, placeholder="Paste Section here")

    msg.submit(chat,[msg, chatbot],[msg,chatbot])

    clear = gr.Button("Clear chat")
    clear.click(clear_chat, outputs=[msg,chatbot])

page.launch(share=True)
