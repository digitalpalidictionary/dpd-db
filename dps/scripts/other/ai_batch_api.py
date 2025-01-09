#!/usr/bin/env python3

import openai

import os
import json

from dps.tools.ai_related import get_openai_client

from db.db_helpers import get_db_session
from db.models import Russian
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths  

dpspth = DPSPaths()
pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def upload_and_create_batch(file_name):
    """Uploads a file and creates a batch for processing."""
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot proceed with batch creation.")
        return
    
    # Define file parameters
    file_path = os.path.join(dpspth.ai_for_batch_api_dir, f"{file_name}.jsonl")

    try:
        # Upload file and create batch
        with open(file_path, "rb") as file:
            batch_input_file = client.files.create(
                file=file,
                purpose="batch"
            )
            # Print the response from the API
            print("File upload response:", batch_input_file)

            # Count the number of lines in the file
            num_lines = sum(1 for line in open(file_path, 'r'))


            # Optionally, proceed to create a batch using the file ID
            # Customize the endpoint and other parameters as needed
            batch_response = client.batches.create(
                input_file_id=batch_input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": f"batch of {num_lines} words"}
            )
            print("Batch creation response:", batch_response)

    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError:
        print("A 429 status code was received; we should back off a bit.")
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)


def check_batch_list():
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot retrieve batch list.")
        return
    try:
        # Retrieve the list of all batches
        batches = client.batches.list()
        # Print each batch's ID and status
        for batch in batches:
            print(f"Batch ID: {batch.id}, Status: {batch.status}")
    except Exception as e:
        print("An error occurred while retrieving batch list:", str(e))


def check_batch_status(batch_id):
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot retrieve batch status.")
        return
    try:
        # Retrieve detailed information about a specific batch
        batch_info = client.batches.retrieve(batch_id=batch_id)
        print(f"Batch ID: {batch_info.id}, Status: {batch_info.status}")
        return batch_info
    except Exception as e:
        print(f"An error occurred while retrieving batch {batch_id} status:", str(e))
        return None


def serialize_request_counts(request_counts):
    # Convert the request_counts object to a dictionary if necessary
    if request_counts is None:
        return {}
    # assuming request_counts is an object with attributes
    return {
        "total": request_counts.total,
        "completed": request_counts.completed,
        "failed": request_counts.failed
    }


def print_batch_info(batch_id):
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot retrieve batch info.")
        return
    try:
        # Retrieve batch information
        batch_info = client.batches.retrieve(batch_id=batch_id)
        
        # Create a dictionary to represent the batch info
        batch_details = {
            "id": batch_info.id,
            "object": batch_info.object,
            "endpoint": batch_info.endpoint,
            "errors": batch_info.errors,
            "input_file_id": batch_info.input_file_id,
            "completion_window": batch_info.completion_window,
            "status": batch_info.status,
            "output_file_id": batch_info.output_file_id,
            "error_file_id": batch_info.error_file_id,
            "created_at": batch_info.created_at,
            "in_progress_at": batch_info.in_progress_at,
            "expires_at": batch_info.expires_at,
            "finalizing_at": batch_info.finalizing_at,
            "completed_at": batch_info.completed_at,
            "failed_at": batch_info.failed_at,
            "expired_at": batch_info.expired_at,
            "cancelling_at": batch_info.cancelling_at,
            "cancelled_at": batch_info.cancelled_at,
            "request_counts": serialize_request_counts(batch_info.request_counts),
            "metadata": batch_info.metadata,
        }
        
        # Print the batch details in a formatted JSON structure
        print(json.dumps(batch_details, indent=2))

    except Exception as e:
        print(f"An error occurred while retrieving batch {batch_id} information:", str(e))


def cancel_batch(batch_id):
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot cancel batch.")
        return
    try:
        # Retrieve batch information to check if the batch exists
        batch_info = client.batches.retrieve(batch_id=batch_id)

        if batch_info:
            # cancel the batch
            client.batches.cancel(batch_id=batch_id)
            print(f"Batch '{batch_id}' has been canceld successfully.")
        else:
            print(f"Batch '{batch_id}' does not exist.")

    except openai.APIError as e:
        print(f"Error canceling batch '{batch_id}': {e}")



def save_batch_results(batch_id, file_name):
    client = get_openai_client()
    if client is None:
        print("OpenAI client is not initialized. Cannot retrieve batch data.")
        return
    try:
        # Retrieve batch information to get the output file ID
        batch_info = client.batches.retrieve(batch_id=batch_id)

        # Check if output file ID is present in the batch details
        if batch_info.output_file_id:
            output_file_id = batch_info.output_file_id

            # Retrieve file content
            file_response = client.files.content(file_id=output_file_id)

            # Debugging print
            # print(f"file_response.text: {file_response.text}")

            # Split the response text into individual lines
            response_lines = file_response.text.splitlines()

            # Initialize a dictionary to store id and translated_text
            ids_and_contents = {}

            # Define output file path
            file_path = os.path.join(dpspth.ai_from_batch_api_dir, f"{file_name}.jsonl")

            # Process each line
            with open(file_path, 'a', encoding='utf-8') as f:
                for line in response_lines:
                    try:
                        # Decode each JSON object
                        decoded_response = json.loads(line)

                        # Extract custom_id and translated_text
                        custom_id = decoded_response.get('custom_id', '')
                        id = custom_id.split('-')[1] if '-' in custom_id else custom_id  # Extract the ID
                        translated_text = (
                            decoded_response.get('response', {})
                            .get('body', {})
                            .get('choices', [{}])[0]
                            .get('message', {})
                            .get('content', None)
                        )

                        if translated_text and id:
                            # Add to dictionary
                            ids_and_contents[id] = translated_text

                            # Save to JSONL format
                            json.dump({"id": id, "translated_text": translated_text}, f, ensure_ascii=False)
                            f.write('\n')  # Newline for JSONL format
                        else:
                            print(f"Missing content or id in line: {line}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding line: {e}, Line: {line}")

            print(f"Translated texts saved to {file_path}")
            return ids_and_contents

        else:
            print("No output file is available for this batch.")
            return {}

    except Exception as e:
        print(f"An error occurred while downloading batch {batch_id} output file: {e}")
        return {}


def update_ru_meaning_raw(ids_and_contents):
    print("Updating ru_meaning in db")
    updated_count = 0
    added_count = 0
    for id, content in ids_and_contents.items():
        existing_russian = db_session.query(Russian).filter(Russian.id == id).first()
        if existing_russian:
            existing_russian.ru_meaning_raw = content
            updated_count += 1
            # print(f"Updated {Russian.id} from '{existing_russian}' for '{content}'")
            db_session.commit()
        else:
            new_russian = Russian(id=id, ru_meaning_raw=content)
            added_count += 1
            # print(f"Added {Russian.id} for {content}")
            db_session.add(new_russian)

    print(f"Total updated records: {updated_count}")
    print(f"Total added records: {added_count}")


if __name__ == "__main__":

    #! Sent request from json to batch API
    file_name_in = ""

    # upload_and_create_batch(file_name_in)

    # check_batch_list()

    specific_batch_id = ""

    # print_batch_info(specific_batch_id)

    # ids_and_contents = save_batch_results(specific_batch_id, file_name_in)
    # update_ru_meaning_raw(ids_and_contents)

    # cancel_batch(specific_batch_id)

    # check_batch_status(specific_batch_id)



