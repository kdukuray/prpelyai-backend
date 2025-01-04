from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from openai import OpenAI, AsyncOpenAI
from os import environ
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .models import Summary
from .serializers import SummarySerializer
import asyncio
import time
from adrf.decorators import api_view as async_api_view
from asgiref.sync import sync_to_async

@api_view(['POST'])
def get_generations(request):
    try:
        generator_uuid = request.data.get("generator_uuid", None)
        last_three_summaries = Summary.objects.filter(generator_uuid=generator_uuid).order_by("-id")[:3]
        serialized_last_three_generations = SummarySerializer(last_three_summaries, many=True).data
        return Response({"summary_generations": serialized_last_three_generations},
                        status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@sync_to_async
def save_summary(summary: Summary):
    summary.save()
@async_api_view(['POST'])
async def generate_summary(request):
    try:
        async_client = AsyncOpenAI(api_key=environ.get("OPENAI_API_KEY"))
        sync_client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))

        async def summarize_chunk(text_chunk: str) -> str:
            chunk_summary_system_prompt = """You are an advanced language model tasked with extracting all important and valuable data from a 
                    given piece of text. Your goal is not to summarize the text but to identify and extract full sentences that convey the 
                    key points, significant information, or critical details.
                    Instructions:
                    Analyze the text to determine which sentences contain essential information.
                    Select and extract complete sentences that:
                    Present new facts, ideas, or key arguments.
                    Provide significant context or details crucial for understanding the text.
                    Avoid redundancy by excluding repeated information.
                    Retain the original wording and sentence structure from the input text. Do not rephrase, paraphrase, or summarize
                     unless it is needed to avoid redundancy and repetition.
                    Maintain any other important context provided within the section. 
                    Ensure that the extracted sentences are presented in their original order for coherence. Omit filler, background, 
                    or tangential information unless directly relevant to the important points.
                    The response should be single paragraph with all the points concatenated next to each other.
                    """
            api_response = await async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": chunk_summary_system_prompt},
                    {"role": "user", "content": chunk},
                ]
            )
            return api_response.choices[0].message.content

        pdf_document = PdfReader(request.FILES["source_pdf"])
        pdf_document_text = ""
        for page in pdf_document.pages:
            page_text = page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False)
            pdf_document_text += page_text

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=75000,
            chunk_overlap=15000,
            is_separator_regex=False,
            length_function=len,
        )
        pdf_document_text_chunks = text_splitter.split_text(pdf_document_text)
        # Summarizing text chunks
        tasks = []
        async with asyncio.TaskGroup() as task_group:
            for chunk in pdf_document_text_chunks:
                task = summarize_chunk(chunk)
                tasks.append(task_group.create_task(task))

        pdf_document_text_chunks_summary = "".join([task.result() for task in tasks])

        final_summary_system_prompt = """You are a highly skilled summarization assistant with expertise in creating 
        structured summaries in markdown format. Your task is to generate a comprehensive summary of a document based on the 
        provided input. Follow these specific formatting instructions:
        The heading of the summary should be relevant to the document and capture what the document is about.
        High-Level Summary:
        Write a paragraph summarizing the document in 6–8 sentences. This should include what the document is about, its main 
        purpose, or what it intends to convey.
        Main Points:
        Create a section titled 'Main Points'. This followed by a list of numbered key points.
        For each key point of the document, write a subheading.
        Under each subheading, create a bullet-point list of subpoints.
        Each subpoint should explain the concept, method, or discussion in a way that readers can understand. Avoid merely 
        stating what is in the document or what it discusses; instead, provide insights or summaries that clarify the topic.
        Optional Definitions (for academic papers):
        If the document uses specialized or technical terms unfamiliar to most people, include a section titled 'Definitions'.
        Provide simple, concise definitions for key terms in a bullet-point format.
        Ensure that your markdown is properly formatted, concise, and clear. The summary should prioritize clarity and 
        readability, making the content accessible to readers who may not have the document.
        """

        final_summary_api_response = sync_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": final_summary_system_prompt},
                {"role": "user", "content": pdf_document_text_chunks_summary}
            ]
        )

        final_pdf_summary = final_summary_api_response.choices[0].message.content

        new_summary_nav_summary = "New Summary"
        new_summary = Summary(content=final_pdf_summary, nav_summary=new_summary_nav_summary)
        await save_summary(new_summary)

        return Response({"new_summary_id": new_summary.pk}, status=status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
def get_summary(request, id):
    try:
        summary = Summary.objects.get(pk=id)
        return Response({"summary_points": summary.content}, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        response = {"error": "The specified summary does not exist"}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

