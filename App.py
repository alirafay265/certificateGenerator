from flask import Flask, request
import requests
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlparse
import os
import base64
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

def get_ordinal_suffix(day):
    if 10 <= day % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

# superscripts = {
#     "st": "ˢᵗ",
#     "nd": "ⁿᵈ",
#     "rd": "ʳᵈ",
#     "th": "ᵗʰ"
# }

now = datetime.now()
day = now.day
suffix = get_ordinal_suffix(day)
# superscript_suffix = superscripts[suffix]
month = now.strftime("%B")
year = now.year

date_of_completion = f"{day}{suffix} {month} {year}"

SMTP_SERVER = "smtp.gmail.com" #If you are using a gmail provided email service
SMTP_PORT = 587
# SENDER_EMAIL = "alirafay121457@gmail.com" # your email
# SENDER_NAME = "Kamyabi Network" # your name
# SENDER_PASSWORD = "mrki nykv zjwu oeqr"  # Use App Password (generated through email account), not your Gmail password

CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Ensure all required environment variables are set
if not CIRCLE_API_KEY or not SENDER_EMAIL or not SENDER_PASSWORD:
    raise EnvironmentError("Missing required environment variables: CIRCLE_API_KEY, SENDER_EMAIL, or SENDER_PASSWORD.")


app = Flask(__name__)

# CIRCLE_API_KEY = "bvhns1fyFLHxqiczrsxbWyKanUfmuPDA"
TEMPLATE_PATH = "template/template1.png"
CERTIFICATE_DIR = "certificate/"
NAME_FONT_PATH = "fonts/WhisperingSignature.ttf"
COURSE_AND_DATE_FONT_PATH = "fonts/Poppins.ttf"
NAME_FONT_SIZE = 150  # Customize
COURSE_AND_DATE_FONT_SIZE = 60  # Customize
# NAME_TEXT_POSITION = (500, 410.508)  # Customize (x, y)
# COURSE_TEXT_POSITION = (500, 535.248)  # Customize (x, y)
# DATE_TEXT_POSITION = (500, 579.852)


os.makedirs(CERTIFICATE_DIR, exist_ok=True)

def get_member_name(member_id):
    url = f"https://app.circle.so/api/v1/community_members/{member_id}"
    headers = {
        "Authorization": f"Bearer {CIRCLE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("name") or f"Member-{member_id}"
    return f"Member-{member_id}"

def get_member_email(member_id):
    url = f"https://app.circle.so/api/v1/community_members/{member_id}"
    headers = {
        "Authorization": f"Bearer {CIRCLE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("email") or "Email not available"
    return f"Member-{member_id}"

    
def extract_course_name(webhook_url):
    parsed = urlparse(webhook_url)
    path = parsed.path.strip("/")
    return path.replace("-", " ").title()

def generate_certificate(name, course):
    img = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)
    name_font = ImageFont.truetype(NAME_FONT_PATH, NAME_FONT_SIZE)
    course_and_date_font = ImageFont.truetype(COURSE_AND_DATE_FONT_PATH, COURSE_AND_DATE_FONT_SIZE)
    # date_font = ImageFont.truetype(COURSE_AND_DATE_FONT_PATH, COURSE_AND_DATE_FONT_SIZE)
    

    name_text = f"{name}"
    course_text = f"for completing the {course} Course"
    date_text = f"on {date_of_completion}"
    
    
    # Get text width
    bbox1 = draw.textbbox((0, 0), course_text, font=course_and_date_font)
    bbox2 = draw.textbbox((0, 0), date_text, font=course_and_date_font)
    bbox3 = draw.textbbox((0, 0), name_text, font=name_font)
    
    
    text_width1 = bbox1[2] - bbox1[0]
    text_width2 = bbox2[2] - bbox2[0]
    text_width3 = bbox3[2] - bbox3[0]
    
    # Calculate centered X position
    center_x1 = (img.width - text_width1) // 2
    center_x2 = (img.width - text_width2) // 2
    center_x3 = (img.width - text_width3) // 2
    
    
    # y1 = COURSE_TEXT_POSITION[1]
    # y2 = DATE_TEXT_POSITION[1]

    draw.text((center_x3, 710), name_text, font=name_font, fill="white")
    draw.text((center_x1, 960), course_text, font=course_and_date_font, fill="white")
    draw.text((center_x2, 1030), date_text, font=course_and_date_font, fill="white")
    
    # draw.text(COURSE_AND_DATE_TEXT_POSITION, course_and_date_text, font=course_font, fill="black")
    
    
    # draw.text(DATE_TEXT_POSITION, date_of_completion, font=date_font, fill="black")
    
    filename_base = f"{name.replace(' ', '_')}_{course.replace(' ', '_')}"
    cert_path = os.path.join(CERTIFICATE_DIR, f"{filename_base}.png")
    img.save(cert_path)
    print(f"Certificate saved to {cert_path}")
    
    pdf_path = os.path.join(CERTIFICATE_DIR, f"{filename_base}.pdf")
    img.save(pdf_path, "PDF", resolution=100.0)
    
    return cert_path, pdf_path

def send_certificate_email(user_email, user_name, file_path, pdf_file_path, course_name):
    subject = "🎓 Your Course Completion Certificate"
    body = f"""
Hi {user_name},

🎉 Congratulations on completing your {course_name} Course!

We've attached your certificate as a PNG image & PDF.

Here's the link to verify your certificate: link
and here's the credential ID: id

Keep learning and growing 🚀

— Kamyabi Network Team
"""

    msg = EmailMessage()
    msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach certificate image
    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)

    maintype, subtype = "image", "png"
    msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
    
    # Attach PDF certificate
    with open(pdf_file_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_file_path)

    maintype, subtype = "application", "pdf"
    msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")



@app.route("/<course_url>/", methods=["POST"])
def handle_webhook(course_url):
    data = request.json
    if data.get("type") == "courses_completed":
        member_id = data["data"]["community_member_id"]
        name = get_member_name(member_id)
        course = extract_course_name(request.url)
        cert_path, pdf_path = generate_certificate(name, course)
        try:
            member_email = get_member_email(member_id)
        except Exception as e:
            print(f"Error fetching email: {e}")
            return {"error": "Failed to get user email"}, 500

        send_certificate_email(member_email, name, cert_path, pdf_path, course)
        return {"message": "Certificate generated"}, 200
    return {"error": "Invalid request"}, 400

if __name__ == "__main__":
    app.run(port=5000)