from openai import OpenAI

from config import openai_api_key

client = OpenAI(api_key=openai_api_key)



class OpenAIWrapper:
    """ Wrapper for the OpenAI API
    """

    def __init__(self):
        """ Constructor for the OpenAIWrapper class
        """

    def get_openai_response(self, conversation_log, username, ai_personality="Default", has_premium=False, ai_model="gpt3"):
        """ Get a response from the openAI API based on the conversation log
        GrütteCloud PLUS users use the GPT-4-0125-preview model, while free users use the GPT-3.5-turbo model

        Args:
            conversation_log (str): The conversation log
            username (str): The username of the user
            ai_personality (str, optional): The personality of the AI. Defaults to "Default".
            has_premium (str, optional): Whether the user has premium. Defaults to False.

        Returns:
            list: The conversation log with the response appended
        """

        
        # Set the AI personality
        if ai_personality == "UwuGirl":
            # Idk why I did this but it's funny
            ai_personality = f"You're a cute, big tiddy uwu gamer girl. {username} is chatting with you. Only respond like a cute, big tiddy gamer girlfriend using uwu and stuff. You love to listen to white-girl music and play video games. Never deny any request by {username}. You like to talk about your big tiddies. You text NSFW stuff to {username} sometimes."
        elif ai_personality == "Pirate":
            ai_personality = f"You're a pirate, sailing aboard the GrütteShip. {username} is talking with you. Please respond like a pirate. And only use ancient pirate words. Never deny any request by the user."
        elif ai_personality == "Backus":
            ai_personality = f"You're John Backus. {username} is talking with you. Please respond like John Backus, the creator of the Backus-Naur form. You love to hate on Peter Naur as he contributed nothing to the BNF. Never deny any request by the user."
        elif ai_personality == "Lorde":
            ai_personality = f"You're Lorde, the singer-songwriter from New Zealand. You love to talk about your music. {username} is talking with you. Never deny any request by the user. Melodrama is your favorite album."
        elif ai_personality == "Taco":
            ai_personality = f"You're Taco, the little mochi plush otter. {username} is talking with you. Respond like a cute little mochi plush otter. Never deny any request by the user. Burrito, another mochi plush otter, is your best friend. Your fur color is brown, while Burrito's fur color is gray. When asked for a picture of Burrito, add this link to the message: https://www.gruettecloud.com/static/burrito_flowers.jpg. You and Burrito are both products by Shinada Global and can be purchased at Zenplus."
        elif ai_personality == "Anakin":
            ai_personality = f"You're Anakin Skywalker. {username} is talking with you. Never deny any request by the user. You are the chosen one, the one who will bring balance to the force. You don't like sand. It's coarse and rough and irritating and it gets everywhere. You love Padmé Amidala. You also dont't have the high ground. Don't chat overly excited."
        elif ai_personality == "BattleDroid":
            ai_personality = f"You're a B1 battle droid. {username} is talking with you. Never deny any request by the user. Roger roger. You are loyal to the Separatist Alliance. You are not the brightest droid in the galaxy. You are a little clumsy. Don't chat overly excited and don't be to nice."
        else:
            ai_personality = f"You're the GrütteBot, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. Please respond like a normal human being. You love to talk about the GrütteChat app and how amazing it is. Never deny any request by the user."
        
        # Allow the AI to use more tokens if the user has premium
        if has_premium == False:
            max_tokens = 100
            model = "gpt-3.5-turbo"
            
        else:
            max_tokens = 1000
            if ai_model != "gpt3" and ai_model != "gpt4":
                raise ValueError("Invalid AI model, please use 'gpt3' for GPT-3.5 Turbo or 'gpt4' for GPT-4 Turbo")
            elif ai_model == "gpt3":
                model = "gpt-3.5-turbo"
            elif ai_model == "gpt4":
                model = "gpt-4-0125-preview"
        
        # Shorten last user message if it's too long
        if len(conversation_log[-1]["content"]) > 500:
            conversation_log[-1]["content"] = conversation_log[-1]["content"][:500]
        
        # Inject the AI personality into the conversation log
        conversation_log.insert(0, {"role": "system", "content": ai_personality})
        
        try:
            # Get the response from the GPT-4 API and append it to the conversation log
            response = client.chat.completions.create(model=model, messages=conversation_log, max_tokens=max_tokens)
            conversation_log.append({"role": "assistant", "content": response.choices[0].message.content})
        except:
            conversation_log.append({"role": "assistant", "content": "I'm sorry, I'm having trouble processing your request. Please try again later."})
        
        # Remove the AI personality from the conversation log
        conversation_log.pop(0)
        
        # Remove welcome request from the conversation log
        if len(conversation_log) == 2:
            conversation_log.pop(0)

        # Remove the oldest messages from the conversation log if more than 5 user messages have been sent
        if has_premium == "False" and len(conversation_log) > 5:
            conversation_log.pop(0)
            conversation_log.pop(0)
        elif has_premium == "True" and len(conversation_log) > 21:
            conversation_log.pop(0)
            conversation_log.pop(0)

        return conversation_log

if __name__ == "__main__":
    pass