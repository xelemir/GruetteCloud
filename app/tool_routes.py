import os
from flask import jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
from PIL import Image, ImageDraw, ImageOps


from pythonHelper import SQLHelper, EncryptionHelper, MailHelper, TemplateHelper
from config import templates_path, render_path, gruetteStorage_path

    
tool_route = Blueprint("Tools", "Tools", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()


@tool_route.route("/create_render", methods=["GET", "POST"])
def createRender():
    if "username" not in session:
        return redirect("/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")[0]
    
    renders_in_use_light = os.listdir(os.path.join(render_path, "light"))
    renders_in_use_dark = os.listdir(os.path.join(render_path, "dark"))
    
    if not bool(user["is_admin"]):
        return redirect("/")
    
    elif request.method == "GET":
        return render_template("createRender.html", menu=th.user(session), render_created=False, renders_in_use_light=renders_in_use_light, renders_in_use_dark=renders_in_use_dark)
    
    else:
        device_selection = request.form['device']
        screenshot_image = request.files["file"]
        darkMode = request.form['theme']
        
        screenshot_image.save(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))
        
        # Load the screenshot image
        screenshot_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))

        # Load the device frame
        device = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", f"{device_selection}.png"))

        # Load the navbar image
        if darkMode == "true":
            navbar_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "ChromeDark.png"))
        else:
            navbar_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "ChromeLight.png"))
        
        
        # Check the dimensions of the images
        width1, height1 = device.size
        width2, height2 = screenshot_image.size

        # Calculate the maximum dimensions
        max_width = max(width1, width2)
        max_height = max(height1, height2)
        
        rad = 100
        # Create a circle mask for rounded corners
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
        alpha = Image.new('L', screenshot_image.size, 255)

        # Apply rounded corners to the screenshot image
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, height2 - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (width2 - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (width2 - rad, height2 - rad))
        screenshot_image.putalpha(alpha)

        # Create a new image with a transparent background
        result_image = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

        # Calculate the position to center the screenshot
        x_offset2 = (max_width - width2) // 2
        y_offset2 = (max_height - height2) // 2

        # Paste the screenshot onto the new image
        result_image.paste(screenshot_image, (x_offset2, y_offset2))

        # Check if the device is an iPhone (to add rounded corners)
        if "iPhone" in device_selection:
            
            # Paste the navbar image on top of the screenshot (adjust position as needed)
            result_image.paste(navbar_image, (x_offset2, y_offset2), navbar_image)

        # Paste the device frame onto the new image
        result_image.paste(device, (0, 0), device)

        # Save the final result
        result_image.save(os.path.join(render_path, "render.png"))

        
        return render_template("createRender.html", menu=th.user(session), render_created=True, renders_in_use_light=renders_in_use_light, renders_in_use_dark=renders_in_use_dark)