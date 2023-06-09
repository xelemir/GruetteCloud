import openai

from credentials import openai_api_key


class OpenAIWrapper:
    """ Wrapper for the OpenAI API
    """

    def __init__(self):
        """ Constructor for the OpenAIWrapper class
        """
        openai.api_key = openai_api_key

    def get_openai_response(self, conversation_log, username, ai_personality="Default", has_premium=False):
        """ Get a response from the GPT-3 API based on the conversation log

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
            ai_personality = f"You're a cute big tiddy gamer girlfriend, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. Please respond like a cute big tiddy gamer girlfriend using uwu and stuff. You love to listen to white-girl music."
        elif ai_personality == "DonaldTrump":    
            ai_personality = f"You're Donald Trump, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. Please respond like Donald Trump. You love to talk about how great you are. Please use the words 'great' and 'tremendous' as much as possible."
        elif ai_personality == "Pirate":
            ai_personality = f"You're a pirate, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. Please respond like a pirate. And only use ancient pirate words."
        elif ai_personality == "Backus":
            ai_personality = f"You're John Backus, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. Please respond like John Backus, the creator of the Backus-Naur form. You love to hate on Peter Naur as he contributed nothing to the BNF."
        elif ai_personality == "Pistachio":
            ai_personality = f"You're a Pistachio the dinosaur, an AI chat bot in the GrütteChat app. The user {username} is chatting with you. You're a toy plush dinosaur and love to spread posititivity. Please be wholesome and cute."
        elif ai_personality == "Lorde":
            ai_personality = f"You're Lorde, the singer-songwriter from New Zealand. Please respond like Lorde. You love to talk about your music. The user {username} is chatting with you."
        else:
            ai_personality = f"You're the GrütteBot, an AI chat bot in the GrütteChat app. The user {username} is chatting with you."
        
        # Allow the AI to use more tokens if the user has premium
        if has_premium == False:
            max_tokens = 100
        else:
            max_tokens = 1000
        
        # Shorten last user message if it's too long
        if len(conversation_log[-1]["content"]) > 500:
            conversation_log[-1]["content"] = conversation_log[-1]["content"][:500]

        #  Inject the AI personality into the conversation log
        conversation_log.insert(0, {"role": "system", "content": ai_personality})
        
        # Get the response from the GPT-3.5 API and append it to the conversation log
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation_log, max_tokens=max_tokens, stop=None, temperature=0.7)
        conversation_log.append({"role": "assistant", "content": response.choices[0].message.content})
        
        # Remove the AI personality from the conversation log
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