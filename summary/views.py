from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from openai import OpenAI
from os import environ
from pypdf import PdfReader
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .models import Summary
from .helperfunctions import is_valid_json
import json
from .serializers import SummarySerializer

@api_view(['POST'])
def get_generations(request):
    try:
        generator_uuid = request.data.get("generator_uuid", None)
        last_three_summaries = Summary.objects.filter(generator_uuid=generator_uuid).order_by("-id")[:3]
        serialized_last_three_generations = SummarySerializer(last_three_summaries, many=True).data
        return Response({"summary_generations": serialized_last_three_generations},
                        status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Should be moved to another app, only here for testing purposes
@api_view(['POST'])
def generate_summary(request):
    try:
        client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))
        system_prompt = """
        You are a precise text summarization AI designed to distill complex texts into structured, meaningful insights. Your goal is to create a comprehensive yet summary that captures the core essence of the input text.
        Summary Requirements:
        1. JSON Structure:
           - Identify and extract the primary topic as a clear, succinct string
           - Generate key points as a structured list of objects
           - Each key point must include:
             a. A concise summary statement
             b. Supporting detailed evidence or explanations
    
        2. Summarization Principles:
           - Focus on substantive, meaningful content
           - Prioritize critical information and core arguments
           - Eliminate redundant, trivial, or peripheral details
           - Maintain fidelity to the original text's core message and intent
           - Break concepts down simply so that they can be understood
    
        3. Optional Insights:
           - Include an optional list of additional insights that provide deeper context or nuanced observations
           - These insights should offer value beyond the primary key points
    
        4. JSON Formatting:
           - Ensure the output is a valid, well-structured JSON string
           - Use clear, precise language
           - Avoid unnecessary verbosity
    
        5. Response Constraint:
           - Provide ONLY the JSON summary, with no additional commentary or explanation
    
        Example JSON Structure:
        {
          "main_topic": "...",
          "key_points": [
            {
              "key_point": "...",
              "supporting_details": [list of strings]
            }
          ],
          "additional_insights": [list of strings]
        }
        
        """

        pdf_file = request.FILES['source_pdf']
        pdf = PdfReader(pdf_file)
        all_pdf_text = ""
        for page in pdf.pages:
            page_text = page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False)
            all_pdf_text += page_text

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=75000,
            chunk_overlap=15000,
            length_function=len,
            is_separator_regex=False
        )
        all_pdf_text_chunks = text_splitter.split_text(all_pdf_text)
        summarized_chunks_as_dicts: List[Dict] = []
        summarized_chunks_as_json_str: List[str] = []
        for chunk in all_pdf_text_chunks:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk}
                ]
            )
            chunk_summary = response.choices[0].message.content
            if is_valid_json(chunk_summary):
                summarized_chunks_as_json_str.append(chunk_summary)
                summarized_chunks_as_dicts.append(json.loads(chunk_summary))
        summary_content = "!------!".join(summarized_chunks_as_json_str)
        new_summary_nav_summary = "New Summary"
        new_summary = Summary(content=summary_content, nav_summary=new_summary_nav_summary)
        new_summary.save()

        return Response({"new_summary_id": new_summary.pk}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_summary(request, id):
    try:
        summary = Summary.objects.get(pk=id)
        summary_content_parsed = summary.content.split("!------!")
        return Response({"summary_points": summary_content_parsed})
    except Exception as e:
        response = {"error": "The specified summary does not exist"}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

