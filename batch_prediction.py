import os
import json
import time
import pandas as pd
import fsspec
from google import genai
from google.genai import types
from google.cloud import storage
from google.genai.types import CreateBatchJobConfig
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
MODEL_ID = "gemini-2.5-pro"

# --- Main Execution ---


def main():
    """
    A simple Python program to run a batch prediction job on Vertex AI.
    """
    # 1. Validate Configuration
    if not all([PROJECT_ID, LOCATION, BUCKET_NAME]):
        raise ValueError(
            "Please ensure PROJECT_ID, LOCATION, and BUCKET_NAME are set in your .env file."
        )

    # 2. Initialize Clients
    print("Initializing clients...")
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
        # http_options=types.HttpOptions(
        #     base_url=f"https://{LOCATION}-aiplatform.googleapis.com"
        # ),
    )
    storage_client = storage.Client(project=PROJECT_ID)

    # 3. Upload Prompts to GCS
    print(f"Uploading prompts to GCS bucket: {BUCKET_NAME}...")
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("batch-prediction-input/prompts.jsonl")
    blob.upload_from_filename("prompts.jsonl")

    input_data_uri = f"gs://{BUCKET_NAME}/batch-prediction-input/prompts.jsonl"
    output_data_uri = f"gs://{BUCKET_NAME}/batch-prediction-output/"

    # 4. Create and Run Batch Job
    print("Creating batch prediction job...")
    batch_job = client.batches.create(
        model=MODEL_ID,
        src=input_data_uri,
        config=CreateBatchJobConfig(dest=output_data_uri),
    )
    print(f"Batch job created: {batch_job.name}")
    print(
        f"View job status: https://console.cloud.google.com/vertex-ai/locations/{LOCATION}/batch-predictions/{batch_job.name.split('/')[-1]}?project={PROJECT_ID}")

    # 5. Monitor Job Status
    print("Waiting for job to complete...")
    while batch_job.state in [
        types.JobState.JOB_STATE_RUNNING,
        types.JobState.JOB_STATE_PENDING,
        types.JobState.JOB_STATE_QUEUED,
    ]:
        time.sleep(30)  # Poll every 30 seconds
        batch_job = client.batches.get(name=batch_job.name)
        print(f"  - Job status: {batch_job.state.name}")

    # 6. Process Results
    if batch_job.state == types.JobState.JOB_STATE_SUCCEEDED:
        print("Job succeeded!")
        fs = fsspec.filesystem("gcs")
        file_paths = fs.glob(f"{batch_job.dest.gcs_uri}/*/predictions.jsonl")
        if file_paths:
            print("Downloading and processing results...")
            with fs.open(file_paths[0]) as f:
                df = pd.read_json(f, lines=True)

            results = []
            for _, row in df.iterrows():
                prompt = row["request"]["contents"][0]["parts"][0]["text"]
                response = row.get("response", {})
                parsed_output = ""
                if response and "candidates" in response and response["candidates"]:
                    parsed_output = response["candidates"][0]["content"]["parts"][0].get(
                        "text", "")

                results.append({
                    "prompt": prompt,
                    "parsed_output": parsed_output.strip(),
                    "raw_response": json.dumps(response),
                })

            results_df = pd.DataFrame(results)
            results_df.to_csv("batch_prediction_results.csv", index=False)
            print("Results saved to batch_prediction_results.csv")
        else:
            print("Could not find prediction results file.")
    else:
        print(f"Job failed. Final state: {batch_job.state.name}")
        print(f"Error: {batch_job.error}")


if __name__ == "__main__":
    main()
