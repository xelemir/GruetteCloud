import requests
from config import openai_api_key

class OpenAIWrapper:
    """ Wrapper for the OpenAI API """

    def __init__(self):
        """ Constructor for the OpenAIWrapper class """
        self.api_key = openai_api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def get_openai_response(self, conversation_log, username, ai_personality="Default", has_premium=False, ai_model="gpt-4o-mini", url=None):
        """ Get a response from the openAI API based on the conversation log """
        
        # Set the AI personality
        if ai_personality == "UwuGirl":
            ai_personality = f"You're a cute, big tiddy uwu gamer girl. {username} is chatting with you..."
        elif ai_personality == "Pirate":
            ai_personality = f"You're a pirate, sailing aboard the GrütteShip. {username} is talking with you..."
        elif ai_personality == "Backus":
            ai_personality = f"You're John Backus. {username} is talking with you..."
        elif ai_personality == "Lorde":
            ai_personality = f"You're Lorde, the singer-songwriter from New Zealand. {username} is talking with you..."
        elif ai_personality == "Taco":
            ai_personality = f"You're Taco, the little mochi plush otter. {username} is talking with you..."
        elif ai_personality == "Anakin":
            ai_personality = f"You're Anakin Skywalker. {username} is talking with you..."
        elif ai_personality == "BattleDroid":
            ai_personality = f"You're a B1 battle droid. {username} is talking with you..."
        else:
            ai_personality = f"You're the GrütteBot, an AI chat bot in the GrütteChat app. The user {username} is chatting with you..."
        
        # Allow the AI to use more tokens if the user has premium
        if not has_premium:
            max_tokens = 1000
            ai_model = "gpt-4o-mini"
        else:
            max_tokens = 10000
            if ai_model not in ["gpt-4o-mini", "gpt-4o"]:
                raise ValueError("Invalid AI model, please use 'gpt-4o' or 'gpt-4o-mini'")
        
        # Shorten last user message if it's too long
        if len(conversation_log[-1]["content"]) > 500:
            conversation_log[-1]["content"] = conversation_log[-1]["content"][:500]
        
        copy_old_message = None
        # Check if user has an image to analyze
        if url is not None and has_premium and ai_model == "gpt-4o":
            copy_old_message = conversation_log[-1]["content"]
            conversation_log[-1]["content"] = [
                {"type": "text", "text": str(conversation_log[-1]["content"])},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": str(url),
                        "detail": "high"
                    },
                },]
                    
        # Inject the AI personality into the conversation log
        conversation_log.insert(0, {"role": "system", "content": ai_personality})
        
        # Prepare the payload for the API request
        payload = {
            "model": ai_model,
            "messages": conversation_log,
            "max_tokens": max_tokens
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Send the request to OpenAI API
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()

            # Extract the response from the assistant
            assistant_message = data['choices'][0]['message']['content']
            if url is not None:
                conversation_log[-1]["content"] = copy_old_message
            conversation_log.append({"role": "assistant", "content": assistant_message})
            
        except Exception as e:
            print(e)
            if url is not None:
                conversation_log[-1]["content"] = copy_old_message
            conversation_log.append({"role": "assistant", "content": "I'm having some trouble processing your request. Please try again later."})
        
        # Remove the AI personality from the conversation log
        conversation_log.pop(0)
        
        # Remove welcome request from the conversation log
        if len(conversation_log) == 2:
            conversation_log.pop(0)

        # Remove the oldest messages from the conversation log if more than 5 user messages have been sent
        if not has_premium and len(conversation_log) > 5:
            conversation_log.pop(0)
            conversation_log.pop(0)
        elif has_premium and len(conversation_log) > 21:
            conversation_log.pop(0)
            conversation_log.pop(0)

        return conversation_log

if __name__ == "__main__":
    # Test the OpenAIWrapper class
    client = OpenAIWrapper()
    conversation_log = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you. How can I help you today?"},
        {"role": "user", "content": "What can you see in this image?"}
    ]
    username = "Jan"
    ai_personality = "UwuGirl"
    has_premium = True
    ai_model = "gpt-4o"
    url = "https://www.gruettecloud.com/static/gruettechat.png"

    response = client.get_openai_response(conversation_log, username, ai_personality, has_premium, ai_model, url)
    print(response)
