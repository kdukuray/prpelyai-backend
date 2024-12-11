from django.shortcuts import render
from openai import OpenAI
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from os import environ
from .models import Thread, Message
from .serializers import MessageSerializer

# function to get thread
@api_view(['POST'])
def get_thread(request):
    thread_id = int(request.data['thread_id'])
    thread = Thread.objects.get(pk=thread_id)
    # all_messages = Message.objects.filter(associated_thread=thread)
    all_messages = thread.message_set.all()
    all_messages_serialized  = MessageSerializer(all_messages, many=True).data
    return Response({'messages':all_messages_serialized})


@api_view(['POST'])
def chat(request):
    data = request.data
    client = OpenAI(api_key=environ.get('OPENAI_API_KEY'))
    system_prompt = "You are a helpful AI assistant"

    all_messages = [{"role": "system", "content": system_prompt}]

    all_messages.append({"role": "assistant", "content": data["message"]})

    if data["new_chat"] == "True":


        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=all_messages,
        )
        actual_response = resp.choices[0].message.content
        return Response({"actual_response": actual_response},status=status.HTTP_200_OK)

    else:
        thread_id = 1
        thread = Thread.objects.get(pk=thread_id)
        all_messages = [{"role": m.role, "content": m.message} for m in thread.message_set.all()]
        all_messages.append({"role": "user", "content": data["message"]})
        print(all_messages)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=all_messages,
        )
        new_user_message = Message(associated_thread=thread, role="user", message=data["message"])
        new_user_message.save()

        new_assistant_message = Message(associated_thread=thread, role="assistant", message=resp.choices[0].message.content)
        new_assistant_message.save()
        return Response({"d": "d"}, status=status.HTTP_200_OK)


    # When we get the response, we should check if it's new or not
    # if it is not new, it should be sent with a thread ID
    # based on the thread ID, retriveve all the messages in the thread,
    # Create a list of these messages
    # append the last message to it and send it via the api
    # print(data.get("message"))
    #
    #
    # return Response({"d": "d"}, status=status.HTTP_200_OK)

