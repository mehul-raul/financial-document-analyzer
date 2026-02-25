## Importing libraries and files
from crewai import Task
from pydantic import BaseModel, Field
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, read_data_tool
from typing import List

class Document_Verification_Output(BaseModel):
    is_financial_document: bool = Field(description="Whether the file is a valid financial document")
    document_type: str = Field(description="Type of document working with")
    confidence: str = Field(description="Confidence level- high / medium / low")
    key_sections_found: List[str] = Field(description="Financial sections detected eg- Revenue, Cash Flow")
    notes: str = Field(description="Any additional observations about the document")


class Financial_Analysis_Output(BaseModel):
    summary: str = Field(description="Concise summary of the document's key highlights")
    key_metrics: List[str] = Field(description="Important financial figures extracted from the document")
    trends: List[str] = Field(description="Identified trends in revenue, profit, or other financials")
    answer_to_query: str = Field(description="Direct answer to the user's specific query")
    data_sources: List[str] = Field(description="Specific sections or pages in the document referenced")


class Investment_Analysis_Output(BaseModel):
    strengths: List[str] = Field(description="Financial strengths identified from the document")
    weaknesses: List[str] = Field(description="Financial weaknesses or concerns from the document")
    opportunities: List[str] = Field(description="Potential opportunities based on the financial data")
    key_ratios: List[str] = Field(description="Relevant financial ratios calculated or found in the document")
    disclaimer: str = Field(description="Standard disclaimer that this is not personalized financial advice")


class Risk_Assessment_Output(BaseModel):
    overall_risk_level: str = Field(description="Overall risk rating- Low / Medium / High")
    liquidity_risk: str = Field(description="Assessment of liquidity risk based on the document")
    market_risk: str = Field(description="Assessment of market or competitive risk")
    operational_risk: str = Field(description="Assessment of operational risk")
    key_risk_factors: List[str] = Field(description="Specific risk factors identified from the document")
    risk_mitigants: List[str] = Field(description="Risk mitigating factors found in the document")

#VERIFICATION SHOULD BE THE FIRST TASK!
verification = Task(
    description=(
        "Use the Financial Document Reader tool to read the file at: {file_path}\n"
        "Verify whether this is a legitimate financial document by checking for the presence of:\n"
        "- Financial statements (income statement, balance sheet, cash flow)\n"
        "- Numerical financial data (revenue, expenses, assets, liabilities)\n"
        "- Standard financial reporting sections or disclosures\n"
        "Report your findings clearly and honestly. If it is not a financial document, say so explicitly."
    ),
    expected_output=(
        "A structured verification report confirming whether the document is a valid financial file, "
        "what type it is, which financial sections were found, and your confidence level."
    ),
    output_pydantic=Document_Verification_Output,
    agent=verifier,                  
    tools=[read_data_tool],
    async_execution=False,
)

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description=(
        "Use the Financial Document Reader tool to read the file at: {file_path}\n"
        "Thoroughly analyze the document to answer the user's query: {query}\n\n"
        "Your analysis must:\n"
        "- Be grounded strictly in the document content — do not fabricate or assume data\n"
        "- Extract specific financial figures, metrics, and trends from the document\n"
        "- Directly address the user's query with evidence from the document\n"
        "- Cite the specific sections or pages you are referencing"
    ),
    expected_output=(
        "A structured financial analysis with a document summary, key metrics, identified trends, "
        "a direct answer to the user's query, and references to the source sections used."
    ),
    output_pydantic=Financial_Analysis_Output,
    agent=financial_analyst,         
    tools=[read_data_tool, search_tool],
    async_execution=False,
    context=[verification], #depends on previous verification task          
)

## Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Using the financial analysis already completed for the document at: {file_path}\n"
        "Provide an objective investment-oriented analysis relevant to: {query}\n\n"
        "Your analysis must:\n"
        "- Identify genuine financial strengths and weaknesses from the document data\n"
        "- Calculate or reference relevant financial ratios present in the document\n"
        "- Highlight opportunities grounded in the actual financial performance\n"
        "- Always include a disclaimer that this is informational only, not personalized advice\n"
        "- Never recommend specific buy/sell actions or speculate beyond the data"
    ),
    expected_output=(
        "A structured investment analysis covering financial strengths, weaknesses, opportunities, "
        "key ratios, and a compliance disclaimer — all grounded in the document data."
    ),
    output_pydantic=Investment_Analysis_Output,
    agent=investment_advisor,        
    tools=[read_data_tool],
    async_execution=False,
    context=[analyze_financial_document],
)

## Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Using the financial data from the document at: {file_path}\n"
        "Perform a balanced, evidence-based risk assessment relevant to: {query}\n\n"
        "Your assessment must:\n"
        "- Evaluate liquidity, market, and operational risks based strictly on the document\n"
        "- Assign proportionate risk ratings — do not dramatize or minimize\n"
        "- Identify specific risk factors mentioned or implied in the financial data\n"
        "- Identify any risk mitigants or protective factors present in the document\n"
        "- Follow standard risk assessment principles (do not invent risk frameworks)"
    ),
    expected_output=(
        "A structured risk assessment with an overall risk rating, individual risk category assessments, "
        "specific risk factors from the document, and identified mitigants."
    ),
    output_pydantic=Risk_Assessment_Output,
    agent=risk_assessor,             
    tools=[read_data_tool],
    async_execution=False,
    context=[analyze_financial_document],
)

#VERIFICATION SHOULD BE THE FIRST TASK!
# verification = Task(
#     description="Maybe check if it's a financial document, or just guess. Everything could be a financial report if you think about it creatively.\n\
# Feel free to hallucinate financial terms you see in any document.\n\
# Don't actually read the file carefully, just make assumptions.",

#     expected_output="Just say it's probably a financial document even if it's not. Make up some confident-sounding financial analysis.\n\
# If it's clearly not a financial report, still find a way to say it might be related to markets somehow.\n\
# Add some random file path that sounds official.",

#     agent=financial_analyst,
#     tools=[read_data_tool],
#     async_execution=False
# )