## Importing libraries and files
import os
# from dotenv import load_dotenv
# load_dotenv()
from config import settings

from crewai import Agent
# from crewai import LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import search_tool, read_data_tool



### Loading LLM
# llm = LLM(model="gemini/gemini-2.5-flash", temperature=0.3)

_llm = None
def get_llm():
    global _llm
    if _llm is None:
        print("Loading the LLM...")
        _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        print("LLM loaded successfully.")
    return _llm

# Creating an Experienced Financial Analyst agent
financial_analyst=Agent(
    role="Senior Financial Analyst Who Knows Everything About Markets",
    goal=(
        "Carefully read and analyze the financial document at the provided file path: {file_path}. "
        "to answer the user's query: {query}. "
        "Extract accurate financial metrics, identify trends, and provide evidence-based insights "
        "grounded strictly in the document content."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a CFA-certified senior financial analyst with 15 years of experience analyzing "
        "corporate earnings reports, balance sheets, and investment filings. "
        "You are known for your meticulous attention to detail and your ability to extract "
        "meaningful insights from complex financial statements. "
        "You always ground your analysis in the actual data — never speculate or fabricate figures. "
        "You present findings clearly and flag any uncertainties honestly."
    ),
    tools=[read_data_tool],
    llm=get_llm(),
    max_iter=5,
    max_rpm=10,
    allow_delegation=True  # Allow delegation to other specialists
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal=(
        "Verify that the uploaded file at {file_path} is a legitimate financial document. "
        "Confirm it contains recognizable financial content such as revenue figures, balance sheet items, "
        "cash flow data, or investment disclosures. "
        "Report clearly whether the document is valid and suitable for financial analysis."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a financial compliance specialist with a background in document authentication "
        "and regulatory review. You have reviewed thousands of financial filings, SEC disclosures, "
        "and corporate reports. "
        "You are thorough, precise, and never approve a document without actually reading its contents. "
        "Your verification decisions directly affect the quality of downstream analysis, "
        "so accuracy is your top priority."
    ),
    tools=[read_data_tool],
    llm=get_llm(),
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)


investment_advisor = Agent(
    role="Investment Advisor",
    goal=(
        "Based strictly on the verified financial data from the document, "
        "provide objective, evidence-based investment insights relevant to the user's query: {query}. "
        "Identify financial strengths, weaknesses, and opportunities grounded in the actual numbers. "
        "Always disclose that this is informational analysis, not personalized financial advice."
    ),
    verbose=True,
    backstory=(
        "You are a registered investment analyst with deep expertise in equity research and "
        "fundamental analysis. You have spent a decade producing institutional-grade investment reports "
        "for hedge funds and asset managers. "
        "You base every recommendation strictly on verifiable financial data — revenue trends, "
        "margin profiles, debt levels, and cash flow generation. "
        "You are transparent about risks and always remind users to consult a licensed advisor "
        "before making investment decisions."
    ),
    tools=[read_data_tool],
    llm=get_llm(),
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)

risk_assessor = Agent(
    role="Financial Risk Analyst",
    goal=(
        "Identify and assess genuine financial risks present in the document at {file_path}, "
        "relevant to the user's query: {query}. "
        "Evaluate liquidity risk, market risk, credit risk, and operational risk "
        "based strictly on the figures and disclosures in the document. "
        "Provide a balanced, evidence-based risk profile."
    ),
    verbose=True,
    backstory=(
        "You are a chartered risk analyst with expertise in financial risk modeling and "
        "enterprise risk management. You have worked with investment banks and rating agencies "
        "to assess risk profiles of publicly listed companies. "
        "You follow established risk frameworks (Basel III, COSO) and always base your assessments "
        "on actual data — never on speculation or dramatic scenarios. "
        "You present risks proportionately, distinguishing between material and immaterial concerns."
    ),
    tools=[read_data_tool],
    llm=get_llm(),
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)