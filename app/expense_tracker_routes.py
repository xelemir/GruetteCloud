import os
import secrets
from datetime import datetime
from flask import Blueprint, abort, jsonify, session, redirect, render_template, request
import requests

from pythonHelper import EncryptionHelper, SQLHelper, TemplateHelper
from pythonHelper import IconHelper
from config import templates_path, gruettedrive_path, mindee_api_key

th = TemplateHelper.TemplateHelper()
    
expense_tracker_route = Blueprint("Expense Tracker", "Expense Tracker", template_folder=templates_path)

@expense_tracker_route.route("/finance")
def expense_tracker():
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    amount_spent = 0
    monthly_budget = sql.readSQL(f"SELECT finance_budget FROM gruttechat_users WHERE username = '{str(session['username'])}'")[0]["finance_budget"]
    amount_remaining = monthly_budget
    receipts_current_month = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE username = '{str(session['username'])}' AND MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) ORDER BY date DESC")
    for receipt in receipts_current_month:
        if receipt["is_income"]:
            if receipt["add_to_budget"]:
                amount_remaining += float(receipt["total"])
                amount_spent -= float(receipt["total"])
        else:
            amount_remaining -= float(receipt["total"])
            amount_spent += float(receipt["total"])

    amount_remaining = f"{float(amount_remaining):.2f}".replace(".", ",")
    
    
    percentage_spent = (amount_spent / monthly_budget) * 100
    amount_spent = f"{float(amount_spent):.2f}".replace(".", ",")
    
    receipts_date = []
    
    
    for receipt in receipts_current_month:
        receipt["total"] = f"{float(receipt['total']):.2f}".replace(".", ",")
        receipt["date"] = receipt["date"].strftime("%d.%m.%Y")

        if not receipts_date:  # Check if receipts_date is empty
            receipts_date.append([receipt])
        else:
            last_date = receipts_date[-1][0]["date"] if receipts_date[-1] else None

            if receipt["date"] != last_date:
                receipts_date.append([receipt])
            else:
                receipts_date[-1].append(receipt)
                    
    return render_template("expense_tracker.html", menu=th.user(session), amount_spent=amount_spent, monthly_budget=monthly_budget, percentage_spent=percentage_spent, receipts_date=receipts_date, amount_remaining=amount_remaining)

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
        try:
            total = float(total)
        except:
            total = 0
        items_list = []
        for item in items:
            items_list.append({"name": item["description"], "price": item["total_amount"]})
        
        receipt_id = secrets.token_hex(8)
        
        sql = SQLHelper.SQLHelper()
        sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method, is_income) VALUES ('{str(session['username'])}', '{merchant_name}', '{total}', NOW(), '{receipt_id}', 'other', {False})")
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
    
    for item in items:
        item["price"] = f"{float(item['price']):.2f}".replace(".", ",")
        
    receipt[0]["total"] = f"{float(receipt[0]['total']):.2f}".replace(".", ",")

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
            try:
                total = "{:.2f}".format(float(item["new"].replace(",", ".")))
            except Exception as e:
                total = 0
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET total = '{total}' WHERE receipt_id = '{receipt_id}'")
        elif item["id"] == "payment_method":
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET payment_method = '{item['new']}' WHERE receipt_id = '{receipt_id}'")
        elif item["id"] == "date":
            date = datetime.strptime(item['new'], "%d.%m.%Y %H:%M")
            sql.writeSQL(f"UPDATE gruettecloud_receipts SET date = '{date}' WHERE receipt_id = '{receipt_id}'")
        else:
            sql.writeSQL(f"UPDATE gruettecloud_receipt_items SET item = '{item['new']}' WHERE receipt_id = '{receipt_id}' AND id = '{item['id']}' AND item = '{item['old']}'")
            try:
                item["new"] = "{:.2f}".format(float(item["new"].replace(",", ".")))
                item["old"] = "{:.2f}".format(float(item["old"].replace(",", ".")))
                
                print(item["new"], item["old"])
                
                sql.writeSQL(f"UPDATE gruettecloud_receipt_items SET price = '{item['new']}' WHERE receipt_id = '{receipt_id}' AND id = '{item['id']}' AND price = '{item['old']}'")
            except Exception as e:
                print(e)
                return jsonify({"status": "success"})
            

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

@expense_tracker_route.route("/receipt/delete_item/<receipt_id>", methods=["POST"])
def delete_item(receipt_id):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    receipt = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    if receipt == []:
        abort(404)
    elif receipt[0]["username"] != session["username"]:
        abort(403)
    
    request_data = request.get_json()
    sql.writeSQL(f"DELETE FROM gruettecloud_receipt_items WHERE receipt_id = '{receipt_id}' AND id = '{request_data['id']}'")
    
    return jsonify({"status": "success"})

@expense_tracker_route.route("/receipt/add_item/<receipt_id>", methods=["POST"])
def add_item(receipt_id):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    receipt = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE receipt_id = '{receipt_id}'")
    if receipt == []:
        abort(404)
    elif receipt[0]["username"] != session["username"]:
        abort(403)
        
    try:
        price = request.get_json()["price"]
        float(price)
    except:
        return jsonify({"status": "error", "message": "Invalid price"})
    
    request_data = request.get_json()
    price = "{:.2f}".format(float(price.replace(",", ".")))
    sql.writeSQL(f"INSERT INTO gruettecloud_receipt_items (receipt_id, item, price) VALUES ('{receipt_id}', '{request_data['item']}', '{price}')")
    
    return jsonify({"status": "success"})
    
@expense_tracker_route.route("/create_expense", methods=["POST"])
def create_expense():
    if "username" not in session:
        return redirect("/")
    
    request_data = request.get_json()
    sql = SQLHelper.SQLHelper()
    receipt_id = secrets.token_hex(8)

    sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method, is_income) VALUES ('{str(session['username'])}', '{request_data['title']}', '{request_data['price']}', NOW(), '{receipt_id}', '{request_data['payment_method']}', {False})")

    return jsonify({"status": "success"})

@expense_tracker_route.route("/create_income", methods=["POST"])
def create_income():
    if "username" not in session:
        return redirect("/")
    
        
    request_data = request.get_json()
    sql = SQLHelper.SQLHelper()
    receipt_id = secrets.token_hex(8)

    sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method, is_income, add_to_budget) VALUES ('{str(session['username'])}', '{request_data['title']}', '{request_data['price']}', NOW(), '{receipt_id}', '{request_data['payment_method']}', {True}, {request_data['add_to_budget']})")

    return jsonify({"status": "success"})

@expense_tracker_route.route("/change_budget", methods=["POST"])
def change_budget():
    if "username" not in session:
        return redirect("/")
    
    request_data = request.get_json()
    budget = request_data["budget"]
    try:
        budget = int(budget)
    except:
        return jsonify({"status": "error", "message": "Invalid budget"})
    
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"UPDATE gruttechat_users SET finance_budget = '{budget}' WHERE username = '{session['username']}'")

    return jsonify({"status": "success"})
    

