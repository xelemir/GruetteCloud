import os
import secrets
from flask import Blueprint, abort, jsonify, session, redirect, render_template, request
import requests

from pythonHelper import EncryptionHelper, SQLHelper, TemplateHelper
from pythonHelper import IconHelper
from config import templates_path, gruettedrive_path, mindee_api_key

th = TemplateHelper.TemplateHelper()
    
expense_tracker_route = Blueprint("Expense Tracker", "Expense Tracker", template_folder=templates_path)

@expense_tracker_route.route("/spending")
def expense_tracker():
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    amount_spent = 0
    monthly_budget = 350
    receipts_current_month = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE username = '{str(session['username'])}' AND MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW())")
    for receipt in receipts_current_month:
        amount_spent += float(receipt["total"])
    
    percentage_spent = (amount_spent / monthly_budget) * 100
    amount_spent = f"{float(amount_spent):.2f}".replace(".", ",")
    
    for receipt in receipts_current_month:
        receipt["total"] = f"{float(receipt['total']):.2f}".replace(".", ",")
    
    return render_template("expense_tracker.html", menu=th.user(session), amount_spent=amount_spent, monthly_budget=monthly_budget, percentage_spent=percentage_spent, receipts_current_month=receipts_current_month)

@expense_tracker_route.route("/upload-receipt", methods=["GET", "POST"])
def upload_receipt():
    if "username" not in session:
        return redirect("/")
    
    if request.method == 'POST':
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")

        if user == []:
            # Security check
            return redirect(f"/logout")

        file = request.files['receipt']
        
        # API endpoint
        url = 'https://api.mindee.net/v1/products/mindee/expense_receipts/v5/predict'

        # Multipart/form-data payload
        files = {'document': file}

        # Headers
        headers = {
            'Authorization': f'Token {mindee_api_key}',
        }

        # Make the API request
        response = requests.post(url, files=files, headers=headers)

        # Print the response
        r = response.json()
        items = r["document"]["inference"]["pages"][0]["prediction"]["line_items"]
        merchant_name = r["document"]["inference"]["pages"][0]["prediction"]["supplier_name"]["raw_value"]
        total = r["document"]["inference"]["pages"][0]["prediction"]["total_amount"]["value"]
        items_list = []
        for item in items:
            items_list.append({"name": item["description"], "price": item["total_amount"]})
        
        receipt_id = secrets.token_hex(8)
        
        sql = SQLHelper.SQLHelper()
        sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method) VALUES ('{str(session['username'])}', '{merchant_name}', '{total}', NOW(), '{receipt_id}', 'other')")
        for item in items_list:
            sql.writeSQL(f"INSERT INTO gruettecloud_receipt_items (receipt_id, item, price) VALUES ('{receipt_id}', '{item['name']}', '{item['price']}')")
        
        return jsonify({"status": "success", "receipt_id": receipt_id})

@expense_tracker_route.route("/receipt/<receipt_id>")
def receipt(receipt_id):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    receipt = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    if receipt == []:
        abort(404)
    elif receipt[0]["username"] != session["username"]:
        abort(403)
    
    items = sql.readSQL(f"SELECT * FROM gruettecloud_receipt_items WHERE receipt_id = '{receipt_id}'")
    receipt[0]["date"] = receipt[0]["date"].strftime("%d.%m.%Y %H:%M")

    return render_template("receipt.html", menu=th.user(session), receipt_id=receipt_id, receipt=receipt[0], items=items)

@expense_tracker_route.route("/receipt/edit/<receipt_id>", methods=["POST"])
def edit_receipt(receipt_id):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    receipt = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    if receipt == []:
        abort(404)
    elif receipt[0]["username"] != session["username"]:
        abort(403)
        
    request_data = request.get_json()
    for item in request_data:
        if item["id"] == "merchant_name":
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET merchant_name = '{item['new']}' WHERE receipt_id = '{receipt_id}' AND merchant_name = '{item['old']}'")
        elif item["id"] == "total":
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET total = '{float(item['new'])}' WHERE receipt_id = '{receipt_id}'")
        elif item["id"] == "payment_method":
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET payment_method = '{item['new']}' WHERE receipt_id = '{receipt_id}'")
        else:
            sql.writeSQL(f"UPDATE gruettecloud_receipt_items SET item = '{item['new']}' WHERE receipt_id = '{receipt_id}' AND id = '{item['id']}' AND item = '{item['old']}'")
            sql.writeSQL(f"UPDATE gruettecloud_receipt_items SET price = '{item['new']}' WHERE receipt_id = '{receipt_id}' AND id = '{item['id']}' AND price = '{item['old']}'")

    return jsonify({"status": "success"})

@expense_tracker_route.route("/receipt/delete/<receipt_id>", methods=["POST"])
def delete_receipt(receipt_id):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    receipt = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    if receipt == []:
        abort(404)
    elif receipt[0]["username"] != session["username"]:
        abort(403)
    
    sql.writeSQL(f"DELETE FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    sql.writeSQL(f"DELETE FROM gruettecloud_receipt_items WHERE receipt_id = '{receipt_id}'")
    
    return jsonify({"status": "success"})
    
@expense_tracker_route.route("/create_expense", methods=["POST"])
def create_expense():
    if "username" not in session:
        return redirect("/")
    
        
    request_data = request.get_json()
    sql = SQLHelper.SQLHelper()
    receipt_id = secrets.token_hex(8)

    sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method) VALUES ('{str(session['username'])}', '{request_data['title']}', '{request_data['price']}', NOW(), '{receipt_id}', '{request_data['payment_method']}')")

    return jsonify({"status": "success"})
    
