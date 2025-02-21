import os
from openai import OpenAI

# 환경변수에서 직접 API 키 읽기
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def get_chat_completion(
    user_prompt, 
    system_message="You are a helpful assistant.",
    model_name="gpt-4o-mini",
    ):
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
        )

        response = completion.choices[0].message.content
        print(response)
        return response
        
    except Exception as e:
        return f"Error occurred: {str(e)}"  