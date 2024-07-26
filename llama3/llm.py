
import chainlit as cl
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from langchain.vectorstores import FAISS
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import json
from gtts import gTTS
import requests


location_names = set()
location_coordinates = {}

#send coordinates to flask server
def send_coordinates_to_flask(coordinates):
    url = 'http://localhost:5000/update_coordinates'
    response = requests.post(url, json=coordinates)



#loading the dataset from json
def extract_data(file_path):
    global location_coordinates, location_names
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    documents = []
    for city in data['cities']:
        for category in city['categories']:
            for location in category['locations']:
                content = f"City: {city['name']}\n"
                content += f"Category: {category['name']}\n"
                content += f"Name: {location['name']}\n"
                content += f"Address: {location['address']}\n"
                if 'coordinates' in location:
                    content += f"Coordinates: {location['coordinates']['latitude']}, {location['coordinates']['longitude']}\n"
                    location_coordinates[location['name']] = {
                        'latitude': location['coordinates']['latitude'],
                        'longitude': location['coordinates']['longitude']
                    }
                documents.append(content)
                location_names.add(location['name'])
    
    return documents

#extract locations mentioned in the response
def extract_mentioned_locations(text):
    mentioned_locations = []
    for location in location_names:
        if location.lower() in text.lower():
            mentioned_locations.append(location)
    return mentioned_locations

#extract the coordinates based on the extracted location
def get_coordinates(location_name):
    if location_name in location_coordinates:
        coords = location_coordinates[location_name]
        return [coords['latitude'], coords['longitude']]
    return None

#load and embed the data
documents=extract_data("Sarajevo - final.json")
embeddings = HuggingFaceEmbeddings()
db = FAISS.from_texts(documents, embeddings)

#load the model(can change from llama3 to others if installed, for testing purposes)
model = Ollama(model='llama3', stop=["<|eot_id|>"])

#prompt
template = """
This is the history of the current conversation, take this into account when responding if the user asks for it:

{chat_history}

You are a world-class tour guide for Sarajevo, developed by the wonderful people at Team Neural Ninjas. A tourist sent you a message: {human_input}

Here are the key points about Sarajevo city to help you respond to the tourist's specific questions: {best_practice}

If the tourist's message is irrelevant to the locations provided, truthfully say that you don't have that information. It's better to say that you don't know than to make things up.

If the user asks about some general information about the city, its culture or the history, use you innate knowledge to answer.

Please respond to the tourist's message in a friendly, conversational manner. Do not mention the coordinates of any location. Once you answer the question, or fulfill the tourist's request, you will not mention it anymore in any of the future responses. <|eot_id|>
"""

prompt = PromptTemplate(input_variables=['chat_history', "human_input", "best_practice"], template=template)

#initialize the chain
chain = LLMChain(llm=model, prompt=prompt, memory=ConversationBufferMemory(memory_key="chat_history", input_key="human_input"), verbose=False)

#retrive relevant data based on user query
def retrieve_info(query):
    query = query.lower()
    cities = ["Sarajevo"]
    
    for city in cities:
        if city in query:
            similar_docs = db.similarity_search(f"City: {city.capitalize()}", k=2)
            return "\n\n".join([doc.page_content for doc in similar_docs])
    
    #If no specific city is mentioned, perform a general search
    similar_docs = db.similarity_search(query, k=2)
    return "\n\n".join([doc.page_content for doc in similar_docs])

#generate the response
def generate_response(message):
    best_practice = retrieve_info(message)
    response = chain.run(human_input=message, best_practice=best_practice)
    mentioned_locations = extract_mentioned_locations(response)
    mentioned_coordinates = {}

    for loc in mentioned_locations:
        coords = get_coordinates(loc)
        if coords:
            mentioned_coordinates[loc] = coords
   
    send_coordinates_to_flask(mentioned_coordinates)        
    
    
    return response

#initialize the chat on chainlit
@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Welcome! I'm your guide for Sarajevo. How can I help you today?").send()
 
#save the generated response to an audio file using google's text to speech    
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    filename = "response.mp3"
    tts.save(filename)
    return filename

#display the text and the audio web element when finishing the response
@cl.on_message
async def on_message(message):
    response= generate_response(message.content)
    audio_file = text_to_speech(response)
    
    audio_element = cl.Audio(name="response.mp3", path="./response.mp3", display="inline")
    
    await cl.Message(
        content=response,
        elements=[
            audio_element
        ]
    ).send()