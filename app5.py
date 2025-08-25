import ssl
import os
import random
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session, flash

import mysql.connector

# MySQL connection
db = mysql.connector.connect(
    host="localhost",          # Or your RDS endpoint
    user="flaskuser",               # Your MySQL username
    password="StrongPassword123!",   # Your MySQL password
    database="laundrybaba"
)
cursor = db.cursor()


app = Flask(__name__)

# Load secret key from environment variable (fallback if not set)
app.secret_key = os.urandom(24) 

otp_storage = {}

## TLS Function

@app.route("/mtls-test")
def mtls_test():
    return "✅ Hello, mutual TLS with ECC works!"

if __name__ == "__main__":
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="/root/crtlb/server-crt/server.crt", keyfile="/root/crtlb/server-crt/server.key")
    context.load_verify_locations("/root/crtlab/ca.crt")
    context.verify_mode = ssl.CERT_REQUIRED  # Require client cert

# Function to send OTP via email
def send_otp_email(receiver_email, otp):
    SENDER_EMAIL = "lovearora337@gmail.com"
    SENDER_PASSWORD = "sedkldpekqdkoomu"

    try:
        message = f"Subject: Your OTP Code\n\nYour LaundryBaba.com OTP is: {otp}"
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message)
        print(f"✅ OTP sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# Index Function
@app.route("/")
def home():
    return render_template("index.html")

# register function

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        otp = str(random.randint(100000, 999999))  # Generate 6-digit OTP
        otp_storage[email] = otp
        send_otp_email(email, otp)
        session["email"] = email
        return redirect(url_for("verify_otp"))
    return render_template("register.html")

# Verify function 

@app.route("/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form.get("otp")
        email = session.get("email")
        first_name = session.get("first_name")
        last_name = session.get("last_name")

        if otp_storage.get(email) == user_otp:
            # ✅ Insert user into MySQL (no phone)
            try:
                sql = """
                    INSERT INTO users (first_name, last_name, email)
                    VALUES (%s, %s, %s)
                """
                values = (first_name, last_name, email)
                cursor.execute(sql, values)
                db.commit()
                flash("✅ OTP verified & user registered successfully!", "success")
            except mysql.connector.Error as err:
                flash(f"⚠️ Database error: {err}", "danger")
                return redirect(url_for("verify_otp"))

            return redirect(url_for("success"))
        else:
            flash("❌ Invalid OTP, please try again.", "danger")
            return redirect(url_for("verify_otp"))

    return render_template("verify.html")


@app.route("/success")
def success():
    if not session.get("email"):
        # No session? go back to register
        return redirect(url_for("register"))

    return render_template(
        "success.html",
        first_name=session.get("first_name"),
        last_name=session.get("last_name"),
        email=session.get("email")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=context)

