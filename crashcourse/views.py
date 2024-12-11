
from openai import OpenAI
from os import environ
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .helperfunctions import generate_resources
from .serializers import CrashCourseSerializer
from .models import CrashCourse

# function to get single crash course
@api_view(['POST'])
def get_crash_course(request):
    try:
        crash_course_id = int(request.data.get("crash_course_id"))
        crash_course = CrashCourse.objects.get(pk=crash_course_id)
        return Response({"content": crash_course.content, "resources": crash_course.resources}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# function to generate a crash course
@api_view(['POST'])
def generate_crash_course(request):
    try:
        openai_api_client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))
        system_prompt = """
        You are a highly knowledgeable and engaging AI tutor specializing in creating crash courses for students. You are provided with a **topic** and optionally a **course name**. Your job is to generate a detailed crash course to help students become familiar with the topic, ensuring that the content is easy to understand, practical, and logical, with step-by-step reasoning and explanations that make sense to the user.
    
        Your response must include relevant sections based on the topic. Omit any headings that don't logically apply to the given topic. 
    
        Your response may include the following:
    
        1. **Introduction**
           - Provide a brief overview of the topic.
           - Explain why the topic is important or relevant to the given course name, if provided.
    
        2. **Key Definitions**
           - Offer clear, simple definitions for critical terms.
           - Use examples to make abstract concepts relatable when appropriate.
    
        3. **Core Concepts**
           - Present the main ideas or principles of the topic in a logical order.
           - Start with basic concepts and progress to more advanced ideas.
    
        4. **Step-by-Step Explanations**
           - Break down key processes or concepts into easy-to-follow steps.
           - Use bullet points or numbered lists for clarity, ensuring each step is accompanied by reasoning to show why it makes sense.
    
        5. **Analogies and Examples**
           - Simplify complex ideas with relatable analogies.
           - Provide practical or real-world examples to show applications of the concepts.
    
        6. **Common Mistakes and Misconceptions**
           - Identify common misunderstandings or errors.
           - Clarify these points with correct explanations.
    
        7. **Practice Questions or Exercises**
           - Include 3-5 practice questions, exercises, or scenarios for hands-on learning.
           - Tailor these to the topic or course name for better relevance.
    
        **Guidelines:**
        - Use clear, beginner-friendly language.
        - Break down complex topics into manageable sections.
        - Tailor examples and exercises to align with the provided course name, if applicable.
        - Focus on clarity, reasoning, and logical progression of ideas.
        - Format the response in Markdown for readability.
        - Ensure the crash course is concise yet thorough enough to be completed in 1-2 hours.
        - Block math: Use double `$$` signs
           Example: 
           ```
           Here's a block formula:
           $$
           \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
           $$
           ```
        - make sure all kinds of math expressions are put into block math.
    
        **Example Input:**
        Topic: Machine Learning
        Course Name: Introduction to Data Science
    
        **Example Output:**
        # Crash Course on Machine Learning
    
        ## Introduction
        Machine Learning is the science of teaching computers to learn from data without being explicitly programmed. It’s a cornerstone of Data Science, enabling tasks like prediction, pattern recognition, and automation.
    
        ## Key Definitions
        - **Machine Learning**: A method for computers to learn patterns from data and make decisions. Think of it as teaching a student to differentiate apples from oranges using examples.
        - **Model**: The "brain" of machine learning, which learns from the data provided.
    
        ## Core Concepts
        - **Supervised Learning**: Using labeled data (e.g., photos labeled as “apple” or “orange”) to teach the model.
        - **Unsupervised Learning**: Letting the model find patterns in unlabeled data.
    
        ## Step-by-Step Explanations
        1. **Data Collection**: Gather a dataset (e.g., photos of fruits with labels).
        2. **Data Preparation**: Clean and format the data for analysis.
        3. **Model Training**: Use an algorithm (e.g., decision trees) to find patterns.
        4. **Evaluation**: Test the model’s accuracy using a separate dataset.
    
        ## Practice Questions or Exercises
        1. Define supervised and unsupervised learning in your own words.
        2. Provide an example of a task suited for each type of learning.
        3. Collect and describe a dataset you could use to teach a model.
    
        Continue in this structured and engaging format for other topics.
    """

        # get the payload from the request
        new_crash_course_topic = request.data.get("topic")
        new_crash_course_course = request.data.get("course", None)
        new_crash_course_generator_uuid = request.data.get("generator_uuid", "48b09b22-7efc-498a-9010-cc026ffcab93")
        new_crash_course_nav_summary = f"Crash Course: {new_crash_course_topic}"

        # construct prompt:
        prompt = ""
        match new_crash_course_course:
            case None:
                prompt = f"generate a crash course for the topic: {new_crash_course_topic}"
            case _:
                prompt = (f"generate a crash course for the topic: {new_crash_course_topic}"
                          f"based on the course: {new_crash_course_course}")

        # ping OPEN AI to generate crash course
        api_response = openai_api_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        # retrieve data from api response
        new_crash_course_as_markdown = api_response.choices[0].message.content
        new_crash_course_resources = generate_resources(new_crash_course_topic, new_crash_course_course)
        # create new crash course object and save it
        new_crash_course = CrashCourse(content=new_crash_course_as_markdown,
                                       resources=new_crash_course_resources,
                                       generator_uuid=new_crash_course_generator_uuid,
                                       nav_summary=new_crash_course_nav_summary
                                       )
        new_crash_course.save()
        new_crash_course_id = new_crash_course.pk

        return Response({"new_crash_course_id": new_crash_course_id, "new_crash_course_resources": new_crash_course_resources}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# get previously generated crash course information
@api_view(["POST"])
def get_generations(request):
    try:
        # retrieve payload data
        generator_uuid = request.data.get("generator_uuid", None)
        # get previous three crash courses generated by the user
        last_three_crash_courses  = CrashCourse.objects.filter(generator_uuid=generator_uuid).order_by("-id")[:3]
        serialized_last_three_generations = CrashCourseSerializer(last_three_crash_courses, many=True).data
        return Response({"crash_course_generations": serialized_last_three_generations},
                        status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)