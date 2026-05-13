import requests
import json
from backend.config import Config


def query_llm(prompt, system_prompt=None):
    config = Config()

    if not config.LLM_API_KEY:
        return "LLM service is not configured. Please set LLM_API_KEY, LLM_API_BASE_URL, and LLM_MODEL_NAME in your .env file."

    if not system_prompt:
        system_prompt = "You are a professional data science and business analytics assistant. Provide clear, concise, and professional explanations."

    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            f"{config.LLM_API_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            error_msg = f"LLM API error (Status {response.status_code}): {response.text[:200]}"
            return f"I'm unable to generate an explanation at this time. {error_msg}"

    except requests.exceptions.Timeout:
        return "The LLM request timed out. Please try again later."
    except requests.exceptions.ConnectionError:
        return "Could not connect to the LLM API. Please check your LLM_API_BASE_URL in .env."
    except Exception as e:
        return f"An unexpected error occurred while contacting the LLM service: {str(e)}"


def ask_dataset_question(question, dataset_summary):
    prompt = f"""
You are a data analyst assistant. A user has asked a question about their dataset.

DATASET SUMMARY:
{json.dumps(dataset_summary, indent=2)}

USER QUESTION:
{question}

Please provide a clear, professional answer based on the dataset information above. Be specific, use numbers where relevant, and provide actionable insights. If the question cannot be answered with the available data, explain what data would be needed.

IMPORTANT STYLE RULES:
- Use plain text only. No markdown formatting (no asterisks, no hashes, no bullet markers like 1. or -).
- Use short paragraphs separated by blank lines.
- Keep it concise and business-focused.
"""

    return query_llm(prompt)


def explain_ml_results(ml_results, dataset_summary):
    prompt = f"""
You are a machine learning expert. Analyze these model training results and provide a clear business-focused explanation.

DATASET SUMMARY:
{json.dumps(dataset_summary, indent=2)}

ML RESULTS:
{json.dumps(ml_results, indent=2)}

Please explain:
- Which model performed best and why.
- What the key metrics mean in simple terms.
- Whether the result is good or poor and why.
- Which features likely influenced the result.
- Business interpretation of the ML result.
- Recommendations for improvement.

IMPORTANT STYLE RULES:
- Use plain text only. No markdown formatting (no asterisks, no hashes, no numbered lists).
- Write in clean paragraphs separated by blank lines.
- Keep it concise and business-focused.
"""

    return query_llm(prompt)


def generate_business_recommendations(dataset_summary, eda_insights, ml_results=None):
    prompt = f"""
You are a senior business consultant. Based on the data analysis results below, provide strategic business recommendations.

DATASET SUMMARY:
{json.dumps(dataset_summary, indent=2)}

EDA INSIGHTS:
{json.dumps(eda_insights, indent=2)}

ML RESULTS:
{json.dumps(ml_results, indent=2) if ml_results else 'No ML results available.'}

Provide:
- Key findings from the data.
- Actionable business recommendations.
- Potential risks or limitations.
- Next steps for deeper analysis.

IMPORTANT STYLE RULES:
- Use plain text only. No markdown formatting (no asterisks, no hashes, no numbered lists).
- Write in clean paragraphs separated by blank lines.
- Keep it concise and business-focused.
"""

    return query_llm(prompt)
