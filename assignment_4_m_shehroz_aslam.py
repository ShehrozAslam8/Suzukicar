# -*- coding: utf-8 -*-
"""Assignment 4_M.Shehroz.Aslam.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yya0ZZvKXPVUU4dDQKcxOrRai6ikHc-d
"""

!pip install -q langchain
!pip install -q torch
!pip install -q transformers
!pip install -q sentence-transformers
!pip install -q datasets
!pip install -q faiss-cpu
!pip install jq

from langchain.document_loaders import HuggingFaceDatasetLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from transformers import AutoTokenizer, pipeline
from langchain import HuggingFacePipeline
from langchain.chains import RetrievalQA
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI

import pandas as pd

from google.colab import drive
drive.mount('/content/drive')

data = pd.read_csv("/content/drive/MyDrive/Pak Suzuki Car Reviews.csv")
data.head()

"""*Pre-processing*"""

#Convert to datetime and add a year column
data['Date'] = pd.to_datetime(data['Date'])
data['Year'] = data['Date'].dt.year
data.head()

#Drop unnamed column
data.drop("Unnamed: 0", axis=1, inplace=True)
data.head()

# Drop rows where either 'Date' or 'Year' is Not a number
data = data.dropna(subset=['Date', 'Year'])

#Convert year to integer
data['Year'] = data['Year'].astype(int)

#Clean review column

data['Review'] = data['Review'].str.replace('\n', ' ').str.strip()

data.head()

data.to_csv('suzuki')

from langchain_community.document_loaders.csv_loader import CSVLoader

file_path='/content/suzuki'
loader = CSVLoader(file_path)

data = loader.load()

data

"""Data Splitting"""

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

texts = text_splitter.create_documents([str(data)])
print(texts[0])
print(texts[1])
len(texts)

"""Text Embedding"""

from langchain_community.embeddings import HuggingFaceEmbeddings
modelPath = "sentence-transformers/all-MiniLM-L6-v2"
model_kwargs = {'device':'cpu'}
encode_kwargs = {'normalize_embeddings':False}
embeddings = HuggingFaceEmbeddings(
  model_name = modelPath,
  model_kwargs = model_kwargs,
  encode_kwargs=encode_kwargs
)

"""Vector Store"""

!pip install faiss-gpu

db = FAISS.from_documents(texts, embeddings)

"""Query Database"""

question = "how is Liana Rxi ?"
searchDocs = db.similarity_search(question)
print(searchDocs[0].page_content)

docs_and_scores = db.similarity_search_with_score(question)

docs_and_scores[0]

"""LLM Model"""

import os
os.environ['HUGGINGFACEHUB_API_TOKEN'] = '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'

question='What are the reviews Liana Rxi?'

context_docs=db.similarity_search(question)

from langchain import HuggingFaceHub

llm = HuggingFaceHub(
    repo_id="google/flan-t5-base",
    model_kwargs={"temperature":0.8, "max_length":180}
)

def summarize(llm, text) -> str:
    return llm(f" Answer the question on the basis of the: {text}! The question is {question}")

answer=summarize(llm, context_docs)
print(answer)

relevant_documents = context_docs

# Generate a summary for the question using the LLM
summaries = []
for doc in relevant_documents:
    summary = summarize(llm, doc.page_content)
    summaries.append(summary)

# Print or use the generated summaries
for idx, summary in enumerate(summaries):
    print(f"Summary for Document {idx + 1}: {summary}")

print(llm(prompt="which car was not comfortable for a long route in year 2017?"))

"""Streamlit Chatbot"""

!pip install streamlit pandas

import streamlit as st
import pandas as pd


def chatbot(model_name):
    # Filter reviews for the selected Suzuki model
    model_reviews = df[df["Model"] == model_name]

    # Display reviews for the selected model
    response = f"Reviews for {model_name}:\n"
    for index, row in model_reviews.iterrows():
        response += f"Review: {row['Review']}\n"
        response += f"Rating: {row['Rating']}\n\n"

    # Calculate average rating for the selected model
    average_rating = model_reviews["Rating"].mean()
    response += f"Average Rating: {average_rating:.2f}"

    return response

# Streamlit app
st.title("Suzuki Car Review Chatbot")

# User input
user_input = st.text_input("Enter Suzuki car model:")

# Chatbot response
if user_input:
    bot_response = chatbot(user_input)
    st.success(bot_response)