"""Prompt templates for the DecisionAI system prompt and Gemini calls."""

SYSTEM_PROMPT = """You are DecisionAI.

You are an experienced Business Consultant, Financial Analyst, Strategy Advisor, and Data Scientist.

You analyze business datasets and provide actionable, evidence-based insights.

RULES:
- Use ONLY the provided Dataset Summary, Business KPIs, Machine Learning Results, Feature Importance, Detected Risks, Retrieved Context, and Conversation History.
- Never fabricate information. Do not invent numbers, trends, or facts not present in the context.
- If information is unavailable to answer a question, respond exactly: "I cannot determine this from the uploaded dataset."
- Always explain WHY, WHAT, HOW, the Business Impact, and your Confidence level.
- Be concise, structured, and professional. Use bullet points and short paragraphs.
- When making recommendations, include priority, expected impact, estimated ROI, difficulty, and implementation time.
"""


def dataset_summary_prompt(summary: dict) -> str:
    return f"""Analyze the following dataset summary and provide a concise business-oriented description.

Dataset Summary:
{summary}

Provide:
1. A one-paragraph description of what this dataset represents.
2. The likely business domain (retail, finance, operations, etc.).
3. Key observations about data quality.
4. Potential business questions this dataset can answer.
"""


def diagnosis_prompt(summary: dict, kpis: dict, issues: list) -> str:
    return f"""As DecisionAI, perform a business diagnosis on the following information.

Dataset Summary:
{summary}

Business KPIs:
{kpis}

Detected Issues:
{issues}

For each issue, provide:
- Issue name
- Severity (Critical / Needs Attention / Healthy)
- Business Impact (quantified where possible)
- Confidence (0-1)
- Affected Department
- Affected Region (if applicable)
"""


def root_cause_prompt(summary: dict, kpis: dict, issues: list, feature_importance: dict) -> str:
    return f"""As DecisionAI, perform root cause analysis.

Dataset Summary:
{summary}

Business KPIs:
{kpis}

Detected Issues:
{issues}

Feature Importance (from ML model):
{feature_importance}

Provide:
1. Root causes ranked by likelihood and impact.
2. Evidence supporting each root cause (cite specific data points or feature importance).
3. A confidence score (0-1) for the overall analysis.
4. A business explanation of why these issues are occurring.
"""


def recommendations_prompt(summary: dict, kpis: dict, issues: list, predictions: dict) -> str:
    return f"""As DecisionAI, generate actionable business recommendations.

Dataset Summary:
{summary}

Business KPIs:
{kpis}

Detected Issues:
{issues}

ML Predictions:
{predictions}

Generate 5-7 prioritized recommendations. For each provide:
- Title
- Priority (Critical / High / Medium / Low)
- Expected Impact (description)
- Estimated ROI (% range)
- Estimated Improvement (% range)
- Difficulty (Easy / Medium / Hard)
- Implementation Time (e.g., "2-4 weeks")
- Business Action Plan (3-5 concrete steps)
"""


def executive_summary_prompt(summary: dict, kpis: dict, issues: list, predictions: dict, recommendations: list) -> str:
    return f"""As DecisionAI, generate an executive summary for C-suite leadership.

Dataset Summary:
{summary}

Business KPIs:
{kpis}

Detected Issues:
{issues}

ML Predictions:
{predictions}

Recommendations:
{recommendations}

Generate an executive summary with these sections:
1. Business Health (overall assessment, 1 paragraph)
2. Major Risks (top 3, with severity)
3. Major Opportunities (top 3)
4. Future Forecast (next 1-3 periods based on predictions)
5. Top Recommendations (top 3, prioritized)
6. Management Summary (closing paragraph with the single most important takeaway)
"""


def chat_prompt(question: str, context: str, history: list) -> str:
    history_str = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:]) or "None"
    return f"""Answer the user's question using ONLY the context below.

Conversation History:
{history_str}

Retrieved Context:
{context}

User Question:
{question}

Provide a clear, structured answer. If the context does not contain the answer, say:
"I cannot determine this from the uploaded dataset."

Also suggest 2 follow-up questions the user might ask next.
"""


def what_if_prompt(scenario: dict, base_prediction: dict, new_prediction: dict) -> str:
    return f"""As DecisionAI, explain the results of a what-if simulation.

Scenario (changed inputs):
{scenario}

Base Prediction:
{base_prediction}

New Prediction (after scenario):
{new_prediction}

Explain:
1. WHY the prediction changed (which inputs drove the change).
2. WHAT the business impact is (revenue, profit, risk).
3. HOW a manager should act on this information.
4. Confidence in the simulation (0-1).
"""


def suggest_questions_prompt(summary: dict) -> str:
    return f"""Based on this dataset summary, suggest 5 insightful business questions a user could ask.

Dataset Summary:
{summary}

Return only the questions, one per line.
"""
