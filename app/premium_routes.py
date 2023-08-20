from flask import render_template, request, redirect, session, make_response, Blueprint, url_for
from paypalrestsdk import Payment, set_config

from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import paypal_client_id, paypal_client_secret, templates_path


premium_route = Blueprint("Premium", "Premium", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

# Configure PayPal SDK
set_config({
    'mode': 'live',
    'client_id': paypal_client_id,
    'client_secret': paypal_client_secret
})

def pay_with_PayPal(success_url="https://www.gruettecloud.com/success", cancel_url="https://www.gruettecloud.com/cancel", amount=2.99, description="GrütteCloud PLUS"):
    """ Pay with PayPal

    Args:
        amount (float): The amount to pay
    """
    amount = round(float(amount), 2)
    
        # Create PayPal payment object
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": f"{success_url}",
            "cancel_url": f"{cancel_url}"
        },
        "transactions": [{
            "amount": {
                "total": f"{amount}",
                "currency": "EUR"
            },
            "description": f"{description}"
        }]
    })
    
    # Create payment
    if payment.create():
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        return "error"

@premium_route.route("/premium", methods=["GET"])
def premium():
    """ Premium route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect(f"/")
    
    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    
    # If good to go, check if user has premium
    else:

        # If user has premium, redirect to settings page
        if bool(user[0]["has_premium"]) == True:
            return url_for("Utilities.settings", error="already_premium")
        
        # If user does not have premium, render premium ad page
        else:
            return render_template("premium.html")
        
@premium_route.route('/payment', methods=['POST'])
def payment():
    """ PayPal payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect(f"/")

    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return url_for("Utilities.settings", error="error")
    
    # If everything looks good, check if user has premium
    else:
        
        # If user has premium, redirect to settings page
        if bool(user[0]["has_premium"]) == True:
            return url_for("Utilities.settings", error="already_premium")
        
        # Else, create payment and redirect user to PayPal
        else:
            # Gift PLUS as apparently I am not allowed to make money with this!?! idc tho
            #sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{str(session['username'])}'")
            #return render_template("settings.html", menu=th.user(session), error="You now have GrütteCloud PLUS!", selected_personality=user[0]["ai_personality"], has_premium=True)
            
            paypal_response = pay_with_PayPal(amount=2.99, description="GrütteCloud PLUS")
            
            if paypal_response != "error":
                return paypal_response
            
            # Payment creation failed
            else:
                return redirect(url_for("Utilities.settings", error="payment_creation_failed"))

@premium_route.route('/success')
def success():
    """ Success payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect(f"/")
    
    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
   
    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    
    # If good to go, check if user has premium
    if bool(user[0]["has_premium"]) == True:
        return redirect(url_for("Utilities.settings", error="already_premium"))
    
    try:

        # Retrieve payment details from PayPal
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        payment = Payment.find(payment_id)
        
        # If successful, update user in database
        if payment.execute({"payer_id": payer_id}):
            sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{str(session['username'])}'")
            return redirect(url_for("Utilities.settings", error="payment_success"))
        
        # Else if payment failed, return error
        else:
            return redirect(url_for("Utilities.settings", error="payment_failed"))
        
    # Something went wrong
    except:
        return redirect(url_for("Utilities.settings", error="error"))
    
@premium_route.route('/cancel')
def cancel():
    """ Cancel payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect(f"/")

    # Payment cancelled error
    return redirect(url_for("Utilities.settings", error="payment_cancelled"))