import os
from flask import jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
from PIL import Image, ImageDraw


from pythonHelper import SQLHelper, EncryptionHelper, MailHelper, TemplateHelper
from config import templates_path, admin_users, gruetteStorage_path

    
tool_route = Blueprint("Tools", "Tools", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()


@tool_route.route("/create_render", methods=["GET", "POST"])
def createRender():
    if "username" not in session:
        return redirect("/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")[0]
    
    if not bool(user["is_admin"]):
        return redirect("/")
    
    elif request.method == "GET":
        return render_template("createRender.html", menu=th.user(session), render_created=False)
    
    else:
        device_selection = request.form['device']
        screenshot_image = request.files["file"]
        
        screenshot_image.save(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))
        
        device = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", f"{device_selection}.png"))
        screenshot = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))

        if "Mac" not in device_selection:
            rad = 100
            # Add rounded corners to the smaller image
            circle = Image.new('L', (rad * 2, rad * 2), 0)
            draw = ImageDraw.Draw(circle)
            draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
            alpha = Image.new('L', screenshot.size, 255)
            w, h = screenshot.size
            alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
            alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
            alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
            alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
            screenshot.putalpha(alpha)

        # Find the larger dimensions
        width1, height1 = device.size
        width2, height2 = screenshot.size

        max_width = max(width1, width2)
        max_height = max(height1, height2)

        # Create a new image with the larger dimensions and a transparent background
        result_image = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

        # Calculate the position to center the smaller image
        x_offset2 = (max_width - width2) // 2
        y_offset2 = (max_height - height2) // 2

        # Paste the smaller image onto the new image at the centered position with rounded corners
        result_image.paste(screenshot, (x_offset2, y_offset2))

        # Paste the larger image onto the new image
        result_image.paste(device, (0, 0), device)

        # Save the final result
        result_image.save("/home/jan/wwwroot/htdocs-gruettecloud/static/renders/render.png")
        
        return render_template("createRender.html", menu=th.user(session), render_created=True)