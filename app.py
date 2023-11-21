

from fastapi import FastAPI, HTTPException, Depends
from transformers import AutoModelForMaskedLM, AutoTokenizer
import torch
from pydantic import BaseModel
import psycopg2
import os
import json

app = FastAPI()


# Connect to the PostgreSQL database using environment variables.
def connect_to_database():
    try:
        connection = psycopg2.connect(
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT")
        )
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return connection

def insert_to_database(connection, user_text, suggested_word):
    try:
        cursor = connection.cursor()
        # Insert user_text and suggested_word into the storing table.
        query = "INSERT INTO storing (user_text, suggested_words) VALUES (%s, %s)"
        # Convert the Python dictionary to a JSON-formatted string.
        suggested_word_json = json.dumps(suggested_word)
        cursor.execute(query, (user_text, suggested_word_json))
        connection.commit()
        cursor.close()
    except psycopg2.Error as e:
        print(f"Error inserting data into the database: {e}")

class SequenceInput(BaseModel):
    sequence: str

class ModelWrapper:
    def __init__(self):
        # Load the pre-trained tokenizer and model.
        self.tokenizer = AutoTokenizer.from_pretrained('roberta-base')
        self.model = AutoModelForMaskedLM.from_pretrained('roberta-base')

model_wrapper = ModelWrapper()

# Dependency to get the model instance.
def get_model():
    return model_wrapper

@app.post("/suggest_word")
async def suggest_word(input_data: SequenceInput, model: ModelWrapper = Depends(get_model)):
    try:
        # Validate the input sequence.
        if not input_data.sequence.strip():
            raise HTTPException(status_code=422, detail="Input sequence is empty")

        # Tokenize the input sequence.
        input_seq = model.tokenizer.encode(input_data.sequence, return_tensors='pt')

        # Check for masked tokens in the input sequence.
        mask_token_index = torch.where(input_seq == model.tokenizer.mask_token_id)[1]

        # Validate that at least one masked token is present.
        if not mask_token_index.numel():
            raise HTTPException(status_code=422, detail="No masked token found in the input sequence")

        # Get token logits from the model.
        token_logits = model.model(input_seq).logits
        masked_token_logits = token_logits[0, mask_token_index, :]

        # Validate that logits are present for the masked token.
        if not masked_token_logits.numel():
            raise HTTPException(status_code=422, detail="No logits for the masked token")

        # Get the top-k suggested words.
        top_k_tokens = torch.topk(masked_token_logits, 5, dim=1).indices[0].tolist()
        suggested_words = [model.tokenizer.convert_ids_to_tokens(token) for token in top_k_tokens]

        # G means space. It had to be removed for human readable output.
        cleaned_words = [word.replace("Ġ", "") for word in suggested_words] 
        # Create a dictionary of suggested words.
        word_dict = {i: word for i, word in enumerate(cleaned_words, 1)}

        # Connect to the database and insert data.
        connection = connect_to_database()
        insert_to_database(connection, input_data.sequence, word_dict)

        return {"suggested_words": word_dict}
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()

@app.post("/select_word")
async def select_word(selected_word_id: int):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Retrieve suggested_words from the storing table.
        query = "SELECT suggested_words FROM storing"
        cursor.execute(query)
        result = cursor.fetchone()

        # convert back to dictionary.
        suggested_words = json.loads(result[0])

        # Convert selected_word_id to string (In the dict, keys are string).
        selected_word_id = str(selected_word_id)

        # Retrieve user_text from the storing table.
        text_query = "SELECT user_text FROM storing"
        cursor.execute(text_query)
        user_text_tuple = cursor.fetchone()

        # Extract user_text from the tuple.
        user_text = user_text_tuple[0]

        # Check if the result is empty.
        if not result:
            raise HTTPException(status_code=404, detail="User text not found in the database")

        # Validate selected_word_id.
        if selected_word_id not in suggested_words.keys():
            raise HTTPException(status_code=422, detail="Invalid selected_word_id")

        # Get the selected word based on the user's choice.
        selected_word = suggested_words[selected_word_id]

        # Replace <mask> in the user_text with the selected word.
        completed_sentence = user_text.replace("<mask>", selected_word)

        #{ Truncate the storing table to delete all rows.
        # We don't need to hold the texts. }
        delete_query = "TRUNCATE TABLE storing"
        cursor.execute(delete_query)
        connection.commit()

        return {"completed_sentence": completed_sentence}
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()