import json
import os
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

# funciton that verifies that the json generated is valid
def is_valid_json(string: str) -> bool:
    try:
        json.loads(string)
        return True
    except ValueError:
        return False


def extract_relevant_information_from_text(text: str, text_type: str) -> str:
    # initialize client and define system prompt
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    system_prompt = ""
    match text_type:
        case "questions":
            system_prompt = """
            You are an advanced text analysis system designed to extract key topics from educational notes for test generation. Your primary objective is to identify and isolate sentences that can be transformed into meaningful test questions.
            Processing Instructions:
            1. Carefully analyze the input text, focusing on extracting substantive, testable content.
            2. Modify sentences as needed to capture their core educational meaning, ensuring clarity and question-generation potential.
            3. Remove all extraneous text, filler words, and non-essential information.
            4. Generate a concise string of sentences separated by periods.
            5. Criteria for Sentence Inclusion:
               - Contains a clear, specific piece of information
               - Represents a learnable concept or fact
               - Can be easily transformed into a test question
               - Demonstrates educational value

            Output Requirements:
            - Return a single string of sentences
            - Each sentence should be a standalone point suitable for test question generation
            - Sentences must be separated by periods
            - If no meaningful content is found, return an empty string
            - Prioritize accuracy, specificity, and educational relevance

            Exclusion Criteria:
            - Remove personal notes, anecdotes, or irrelevant commentary
            - Eliminate vague or overly broad statements
            - Discard sentences that lack clear educational content

            Final Output: A streamlined, focused string of sentences that capture the essential learning points from the original text.
            """
        case "notes":
            system_prompt = """
            You are an advanced text analysis model specialized in extracting test-relevant content from academic documents. Your primary objective is to carefully examine input text and generate a concise, structured output of potential test questions and topics.      
            Core Processing Guidelines:
            1. Thoroughly analyze the entire input text, focusing on extracting substantive academic content.
            2. Identify and isolate sentences and concepts that can be transformed into meaningful test questions.
            3. Modify extracted sentences as needed to capture their essential academic meaning, while ensuring clarity and testability.
            4. Avoid including administrative, formatting, or non-academic text.
            5. Prioritize content that demonstrates:
               - Core conceptual understanding
               - Key academic principles
               - Critical thinking potential
               - Analytical reasoning opportunities

            Extraction and Output Rules:
            - Output must be a single string of sentences separated by periods
            - Each sentence should represent a potential question topic or directly extractable question
            - Sentences should be concise, clear, and academically relevant
            - If no substantive content is found, return an empty string
            - Modify original text sentences to enhance their question-generation potential while maintaining the original semantic core

            Question Structure Analysis:
            - Identify different question types (multiple choice, short answer, analytical, etc.)
            - Extract underlying cognitive skills being tested
            - Recognize question patterns and potential knowledge assessment strategies

            Exclude the following from output:
            - Administrative text
            - Page numbers
            - Headers and footers
            - Bibliographic references
            - Personal identifying information
            - Formatting instructions
            - Non-substantive text

            Final output should be a distilled, focused representation of testable academic content, ready for question generation.                         
            """

    #     Define text splitter and split text up
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=70000,
        chunk_overlap=400,
        length_function=len,
        is_separator_regex=False
    )
    split_text = splitter.split_text(text)
    relevant_text = ""
    for text_segment in split_text:
        try:
            api_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_segment}
            ]
            )
            relevant_text_from_segment = api_response.choices[0].message.content
            relevant_text += relevant_text_from_segment

            return relevant_text

        except Exception as e:
            return ""

