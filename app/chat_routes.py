from flask import render_template, request, redirect, session, Blueprint
import logging

from pythonHelper import EncryptionHelper, OpenAIWrapper, SQLHelper
from config import url_prefix, templates_path


eh = EncryptionHelper.EncryptionHelper()


chat_route = Blueprint("Chat", "Chat", template_folder=templates_path)


@chat_route.route("/ai/<method>", methods=["POST", "GET"])
def send(method):
    """ AI Chat route

    Args:
        method (str): The method to be executed

    Returns:
        str: The rendered template or a redirect
    """
    
    if "username" not in session:
        return redirect(f"{url_prefix}/")

    ai = OpenAIWrapper.OpenAIWrapper()
    sql = SQLHelper.SQLHelper()
    
    # Get chat history from session
    chat_history = session.get("chat_history", [])

    # Check if the method is back, clear chat history and redirect to home
    if method == "back":
        session.pop("chat_history", None)
        return redirect(f"{url_prefix}/")
    
    # Check if the method is restart, clear chat history and redirect to AI chat
    elif method == "restart":
        session.pop("chat_history", None)
        return redirect(f"{url_prefix}/ai/chat")

    # Check if new message is sent, then append it to chat history, get AI response, and refresh page
    elif "send" in request.form and request.form["message"] != "":
        chat_history.append({"role": "user", "content": request.form["message"]})
        
        # Get user selected AI personality from database
        user = sql.readSQL(f"SELECT ai_personality, has_premium FROM gruttechat_users WHERE username = '{session['username']}'")
        if user == []:
            selected_ai_personality = "Default"
            has_premium = False
        else:
            selected_ai_personality = user[0]["ai_personality"]
            has_premium = bool(user[0]["has_premium"])

        # Get AI response (response is appended to chat history internally)
        try:
            chat_history = ai.get_openai_response(chat_history, username=session["username"], ai_personality=selected_ai_personality, has_premium=has_premium)

        # If there is an error, append error message to chat history
        except Exception as e:
            logging.error(e)
            chat_history.append({"role": "assistant", "content": "I am having trouble connecting... Please try again later."})
            
        # Save chat history to session and refresh page
        session["chat_history"] = chat_history
        return redirect(f"{url_prefix}/ai/chat")
    
    # Reverse chat history to show most recent messages first and render template
    chat_history.reverse()
    return render_template("aichat.html", chat_history=chat_history, url_prefix = url_prefix)