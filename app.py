from shiny.express import input, render, ui, session
from shiny import reactive, req
from shinymedia import input_video_clip, audio_spinner
from model import chat
from faicons import icon_svg
from htmltools import css

messages = []

input_video_clip(
    "clip",
    reset_on_record=True,
    class_="mt-5 mx-auto",
    style=css(width="600px", max_width="100%"),
    video_bits_per_second=256000,
    audio_bits_per_second=64000,
)

@reactive.extended_task
async def chat_task(video_clip, messages, session):
    with ui.Progress(session=session) as p:
        chat_output = await chat(video_clip, messages, p)
        return chat_output, messages

@reactive.effect
@reactive.event(input.clip, ignore_none=False)
def start_chat():
    chat_task.cancel()
    req(input.clip())
    chat_task(input.clip(), messages[:], session)
    
@render.express
def response():
    
    if chat_task.status() == "initial":
        with ui.card(class_="mt-3 mx-auto", style=css(width="600px", max_width="100%")):
            ui.markdown(
                """
                **Instructions:** Ask ChatGPT-4o any question you want to by recording your clips and once its 
                done answering you can ask more question again and again until you want to. 
                
                Reload the browser to start a new conversation.

                Some ideas to get you started:

                * “What do you think of the outfit I'm wearing?”
                * “Where does it look like I am right now?”
                * “Tell me an interesting fact about an object you see in this video.”
                """
            )
        return
    
    if input.clip() is None or chat_task.status() == "running":
        return
    
    chat_result_audio, chat_result_messages = chat_task.result()

    global messages
    messages = chat_result_messages[:]
    
    audio_spinner(src=chat_result_audio)

with ui.panel_fixed(bottom=0, left=0, right=0, height="auto", id="footer"):
    with ui.div(class_="mx-auto", style=css(width="600px", max_width="100%")):
        with ui.div(class_="float-left"):
            "Built in Python with "
            ui.a("Shiny", href="https://shiny.posit.co/py/")
        with ui.div(class_="float-right"):
            with ui.a(href="https://github.com/AdityaPurswani/CuriosCompanion"):
                icon_svg("github", margin_right="0.5em")
                "View source code"

with ui.panel_fixed(top=0, left=0, right=0, height="auto", id="header"):
    with ui.div(class_="mx-auto", style=css(width="600px", max_width="100%")):
        with ui.div(class_="items-center"):
            "CURIOUS COMPANION"
      
ui.head_content(
    ui.tags.style(
        """
        #header {
            padding: 0.5em 0.7em;
            background-color: #6fc276;
            color: black;
            text-align: center;
            font-weight: bold;
        }
        """
    )
)
          
ui.head_content(
    ui.tags.style(
        """
        #footer {
            padding: 0.5em 0.7em;
            background-color: #6fc276;
            color: black;
        }
        #footer a {
            color: black;
        }
        """
    )
)
