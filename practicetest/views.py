from openai import OpenAI
from pypdf import PdfReader
from os import environ
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .helperfunctions import is_valid_json, extract_relevant_information_from_text
from .models import PracticeTest
from .serializers import PracticeTestSerializer

# funciotn that get a single practice test
@api_view(['GET'])
def get_practice_test(request, id):
    try:
        practice_test = PracticeTest.objects.get(id=id)
        response = {"questions": practice_test.content}
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        response = {"error": "The specified practice test does not exist"}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

# function to explain an answer
@api_view(['POST'])
def explain_answer(request):
    try:
        question_data = request.data
        question_prompt = question_data.get("prompt")
        correct_answer = question_data.get("correct_answer")
        user_selection = question_data.get("user_selection")

        explanation_prompt = ""
        if correct_answer == user_selection:
            explanation_prompt = f"Propmpt: {question_prompt}. Correct: {correct_answer}"
        else:
            explanation_prompt = (f"Propmpt: {question_prompt}. Coorect answer: {correct_answer}."
                                  f" Wrong answer: {user_selection}")

        system_prompt = """
        You are a helpful and clear explainer. When provided with a question, the correct answer, and an incorrect answer, 
        you will: 1. Explain why the correct answer is correct in simple terms, breaking down the reasoning step-by-step so 
        it is easy to understand. 2. Explain why the wrong answer is wrong by clarifying misconceptions or pointing 
        out the flaws in reasoning. Your responses must be concise, straightforward, and suitable for someone with no prior
        knowledge of the topic. Simply reply with the explanation and don't add any additional information.
        Your Response should be in markdown. Ensure all back slashes are escaped by using 4 slashes in the place of 1. 
        All math expressions, even inline expressions or single variables must be put into block math (enclosed by `$$`)
         Example of a math block: 
           ```
           Here's a block formula:
           $$
           \\\\int_{-\\\\infty}^{\\\\infty} e^{-x^2} dx = \\\\sqrt{\\\\pi}
           $$
           ```
        
        """

        client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))
        explanation = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": explanation_prompt},
            ]
        )

        explanation= explanation.choices[0].message.content
        payload = {"explanation": explanation}
        return Response(payload, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# function that pings gpt's server to generate questions
@api_view(['POST'])
def generate_questions(request):
    try:
        openai_api_client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))
        system_prompt = """
            - You are a JSON-based question generator. Your task is to create list of questions with the following structure:
            {"prompt": string, "options": [{"letter", "value"}], "answer": string}.
            - all strings should be in markdown format enclosed in quotations
            - Each question must have 4 options to choose from. 
            - The 'options' property is a list of lists, where each sublist contains exactly 2 elements: 
            - the first element is a letter (e.g., 'A', 'B', 'C', 'D'), and the second element is the corresponding value. 
            - Respond only with a string in JSON format, without any additional text or explanation.
            - The response should not enclosed in ```json ... ```. It should be a raw string
            - Ensure all back slashes are escaped by using 4 slashes in the place of 1.
            - All math expressions must be put into block math (enclosed by `$$`)
            - Block math: Use double `$$` signs
            Example: 
           ```
           Here's a block formula:
           $$
           \\\\int_{-\\\\infty}^{\\\\infty} e^{-x^2} dx = \\\\sqrt{\\\\pi}
           $$
           ```
           All math expressions, even inline expressions or single variables must be put into block math (enclosed by `$$`)
            """

        # get and parse the payload in the request
        new_test_source_material_type = request.data.get("source_material_type")
        new_test_subject = request.data.get("subject")
        new_test_source_material = request.data.get("source_material")
        new_test_generator_uuid = request.data.get("generator_uuid")

        if new_test_source_material_type == "questions" or new_test_source_material_type == "notes":
            source_material_as_pdf  = PdfReader(new_test_source_material)
            source_material_text  = ""
            for page in source_material_as_pdf.pages:
                page_text = page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False)
                source_material_text += page_text

            match new_test_source_material_type:
                case "questions":
                    new_test_source_material = extract_relevant_information_from_text(source_material_text, "questions")
                case "notes":
                    new_test_source_material = extract_relevant_information_from_text(source_material_text, "notes")

        prompt = ""

        match new_test_source_material_type:
            case "topics":

                prompt = (f"generate 10 questions on the subject {new_test_subject} "
                          f"that cover the following topics: {new_test_source_material}")
            case "notes":

                prompt = (f"generate 10 questions on the subject {new_test_subject} "
                          f"based on the following notes: {new_test_source_material}")
            case "questions":

                prompt = (f"generate 5 short questions on the subject {new_test_subject}"
                          f"that are similar in structure (doesn't necessarily have to be the same)"
                          f" to the questions in the following: {new_test_source_material}")


        api_response = openai_api_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        )

        # used to have a test here that checked that the json is valid, now we just let it run and habdle
        # the error client side for now (beta version)
        new_test = PracticeTest.objects.create(content=api_response.choices[0].message.content,
                                               generator_uuid=new_test_generator_uuid,
                                               nav_summary=f"Prep Test: {new_test_subject}")
        new_test.save()
        new_test_id = new_test.id
        return Response(data={'id': new_test_id}, status=status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# function that get previously generated pratice tests
@api_view(["POST"])
def get_generations(request):
    try:
        generator_uuid = request.data.get("generator_uuid", None)
        last_three_tests = PracticeTest.objects.filter(generator_uuid=generator_uuid).order_by("-id")[:3]
        serialized_last_three_generations = PracticeTestSerializer(last_three_tests, many=True).data
        print(3)
        return Response({"practice_test_generations": serialized_last_three_generations},
                        status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




