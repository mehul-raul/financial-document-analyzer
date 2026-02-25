## Importing libraries and files
import os
from config import settings
from langchain_community.document_loaders import PyPDFLoader 
from crewai.tools import tool

from crewai_tools import SerperDevTool

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
@tool("Financial Document Reader")
def read_data_tool(path: str) -> str:
    """Reads and extracts text content from a financial PDF document.
    Use this tool to load and parse financial reports, statements, or any PDF file.
    Args: path: File path to the PDF document.
    """
    loader = PyPDFLoader(file_path=path)
    docs = loader.load()

    full_report = ""
    for data in docs:
        content = data.page_content
        while "\n\n" in content:
            content = content.replace("\n\n", "\n")
        full_report += content + "\n"

    return full_report

