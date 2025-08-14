# Comprehensive Guide to Gemini Batch Prediction with Google Search

This guide provides a technical walkthrough for setting up and running a batch prediction job on Google Cloud Vertex AI using the Gemini family of models. It specifically focuses on how to enable and configure the `google_search` tool to get real-time, up-to-date information in your batch requests.

## 1. Prerequisites

Before you begin, ensure you have the following:

*   A Google Cloud Project with the Vertex AI API enabled.
*   A Google Cloud Storage (GCS) bucket in the same location as your Vertex AI jobs (e.g., `us-central1`).
*   The `gcloud` CLI and the `google-genai` Python library installed and authenticated.
*   A service account with the `Storage Admin` and `Vertex AI User` roles.

## 2. The Batch Prediction Prompt (`prompts.jsonl`)

The core of a batch prediction job is the input file, which is a [JSON Lines](https://jsonlines.org/) (`.jsonl`) file. Each line in this file is a complete, self-contained JSON object representing a single request to the model.

### 2.1. Basic Structure

Each line in your `prompts.jsonl` file must be a JSON object with a single top-level key: `"request"`. The value of this key is another object containing the details of the prompt.

```json
{
  "request": {
    "contents": [ ... ],
    "tools": [ ... ],
    "generationConfig": { ... }
  }
}
```

### 2.2. Enabling the `google_search` Tool

To enable the `google_search` tool, you must add a `"tools"` array to your request object. Inside this array, add a JSON object with a `"google_search"` key.

```json
{
  "request": {
    "contents": [ ... ],
    "tools": [
      {
        "google_search": {
          "timeRangeFilter": null
        }
      }
    ],
    "generationConfig": { ... }
  }
}
```

### 2.3. Configuring `timeRangeFilter`

The `timeRangeFilter` allows you to restrict the search results to a specific time period. For real-time data, you will often want the most recent information.

*   **To get the latest information without a specific time-bound filter**, set the value of `timeRangeFilter` to `null`. This tells the model to use its default behavior, which is to prioritize the most recent and relevant results.

*   **To filter to a specific time range**, you can use predefined string values like `"LAST_HOUR"`, `"LAST_DAY"`, etc., for online predictions. However, for batch predictions, it is more reliable to use `null` or a full `Interval` object.

**Code Snippet: Prompt with `google_search` and `timeRangeFilter`**

This is the correct and validated format for a single prompt in your `prompts.jsonl` file.

```json
{
  "request": {
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "What is the current weather in London, UK?"
          }
        ]
      }
    ],
    "tools": [
      {
        "google_search": {
          "timeRangeFilter": null
        }
      }
    ],
    "generationConfig": {
      "temperature": 1.0
    }
  }
}
```

## 3. Sample Prompt and Result

Here is a real example taken from a successful batch prediction job using the `gemini-2.5-flash` model.

### Sample Prompt

This prompt asks for the current weather in New York City.

```json
{
  "request": {
    "contents": [
      {
        "parts": [
          {
            "text": "What is the temperature, humidity, and wind speed in New York City right now?"
          }
        ],
        "role": "user"
      }
    ],
    "generationConfig": {
      "temperature": 1
    },
    "tools": [
      {
        "google_search": {
          "timeRangeFilter": null
        }
      }
    ]
  }
}
```

### Sample Result

The following is the corresponding result from the `batch_2.5_flash_predictions.jsonl` file.

```json
{
  "status": "",
  "processed_time": "2025-08-14T16:27:27.775+00:00",
  "request": {
    "contents": [
      {
        "parts": [
          {
            "text": "What is the temperature, humidity, and wind speed in New York City right now?"
          }
        ],
        "role": "user"
      }
    ],
    "generationConfig": {
      "temperature": 1
    },
    "tools": [
      {
        "google_search": {
          "timeRangeFilter": null
        }
      }
    ]
  },
  "response": {
    "candidates": [
      {
        "content": {
          "parts": [
            {
              "text": "The current temperature in New York City is 85°F (29°C), and it feels like 90°F (32°C). The humidity is around 62%. Winds are light and variable."
            }
          ],
          "role": "model"
        },
        "finishReason": "STOP",
        "groundingMetadata": {
          "groundingChunks": [
            {
              "web": {
                "domain": "google.com",
                "title": "Weather information for New York, NY, US",
                "uri": "https://www.google.com/search?q=weather+in+New York, NY,+US"
              }
            },
            {
              "web": {
                "domain": "wunderground.com",
                "title": "wunderground.com",
                "uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGoAnHCgy4y62gthEo5DWCFifb0-kQvejaAsr70_D51CWlaHVdEpWPCYi-h1Kc68Z7dUf7fEEL-dV7Dvshot18kRdhOHK1O94eztawRxzSosTL_beOQRi3jGteFzv5WtZ5kWqt3RIr4dvraKo5JMCMs6g=="
              }
            },
            {
              "web": {
                "domain": "wunderground.com",
                "title": "wunderground.com",
                "uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG3rY7m_4kyLjnEjKIEEstLv3MBn8YlrnQo-ke_WikRd_iUX3_eDpuhyazP8loUieWxaxhg_Na2qAHfCjzD_dW46tXu2zboqg3JFZvz6BuVHK7_8peHytKYUaE-u_bMMtoeCAn5YywK7G1IhERhl-U-kZo="
              }
            }
          ],
          "groundingSupports": [
            {
              "groundingChunkIndices": [
                0,
                1,
                2
              ],
              "segment": {
                "endIndex": 149,
                "startIndex": 120,
                "text": "Winds are light and variable."
              }
            }
          ],
          "retrievalMetadata": {},
          "searchEntryPoint": { ... }
        }
      }
    ]
  }
}
```

As you can see, the model successfully used the `google_search` tool to retrieve real-time weather data and provide an accurate, up-to-date answer.