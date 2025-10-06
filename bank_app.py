from flask import Flask,render_template,request,redirect,url_for,session
import sqlite3
from algorithm import face_recognition_algorithm
import os
from werkzeug.utils import secure_filename
from banknote_detection_model import detect_banknote
from datetime import datetime

bank_app = Flask(__name__)
#We need a secret_key for session management
bank_app.secret_key = 'bank_app'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bank.db")
#To sign up, user should upload 3 images and UPLOAD_FOLDER is the destination folder which stores these images.
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
bank_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Defines the route for home page
@bank_app.route("/",methods = ['GET','POST'])
#This is called view function, it is executed when user visits the "/" route
def home():
    return render_template("home.html")

@bank_app.route('/signup')
def signup():
    return render_template("signup.html")

@bank_app.route('/delete')
def delete():
    return render_template("delete_user.html")

@bank_app.route('/deposit_money')
def deposit_money():
    return render_template("deposit.html")

@bank_app.route('/withdraw_money')
def withdraw_money():
    return render_template("withdraw.html")

@bank_app.route('/transfer_money')
def transfer_money():
    return render_template("transfer.html")

@bank_app.route('/admin_login')
def admin_login():
    return render_template("admin_home.html")

@bank_app.route('/user_login')
def user_login():
    return render_template("login.html")



@bank_app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        #Get user_id from user
        user_id = request.form.get('user_id')
        if user_id:
            #Check user_id
            if check_id_in_db(user_id):
                #Open a new session and save the user_id for possible other uses.
                session['user_id'] = user_id
                #If id is found in the database, redirect user for face verification
                return redirect(url_for('face_verification',user_id = user_id))
            else: 
                return render_template("invalid_tc.html")
    #If the request method is get, redirect the user to the login page.
    return render_template("login.html")

#This function checks if user_id exists in the database
def check_id_in_db(user_id):
    #Connect to the database
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM account WHERE tc_id = ?",(user_id,))
        count = cursor.fetchone()[0]
        return count > 0

@bank_app.route('/logout')
def logout():
    session.pop('user_id', None)
    message= "Successfully logged out!"
    return render_template("home.html",msg = message)

@bank_app.route("/add_user", methods = ['POST','GET'])
def add_user():
    if request.method == 'POST':
        try:
            name = request.form['name']
            user_id = request.form['user_id']
            money = request.form['money']
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO account (tc_id,name,amount_of_money) VALUES (?,?,?)",(user_id,name,money))
                connection.commit()
                message = "Successfully signed up!"
            images = request.files.getlist('images')
            user_folder = os.path.join(bank_app.config['UPLOAD_FOLDER'], secure_filename(user_id))
            os.makedirs(user_folder, exist_ok=True)
            image_names = ['image1.jpg', 'image2.jpg', 'image3.jpg']
            for i, image in enumerate(images):
                image.save(os.path.join(user_folder, image_names[i]))
        except:
            connection.rollback()
            message = "This user is already signed up!"
        finally:
            connection.close()
            return render_template('home.html',msg = message)

@bank_app.route("/delete_user", methods=['POST'])
def delete_user():
    if request.method == 'POST':
        try:
            user_id = request.form['user_id']
            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM account WHERE tc_id = ?", (user_id,))
                count = cursor.fetchone()[0]
                if count == 0:
                    message = "Not a valid ID. No such user exists."
                else:
                    cursor.execute("DELETE FROM account WHERE tc_id = ?", (user_id,))
                    connection.commit()
                    message= "Deletion is successful. See you again!"
        except: 
            connection.rollback()
            message = "Error in the deletion"
        finally:
            connection.close()
            return render_template('home.html',msg = message)

@bank_app.route("/face_verification/<user_id>")
def face_verification(user_id):
    if face_recognition_algorithm(user_id):
        return redirect(url_for('account',user_id = user_id))
    return render_template('not_verified.html')

@bank_app.route("/banknote_detect")
def banknote_detect():
    amount_detect = detect_banknote()
    if(amount_detect == "0_liras"):
        amount = 0
    if(amount_detect == "5_liras"):
        amount = 5
    if(amount_detect == "10_liras"):
        amount = 10
    if(amount_detect == "20_liras"):
        amount = 20  
    if(amount_detect == "50_liras"):
        amount = 50
    if(amount_detect == "100_liras"):
        amount = 100    
    if(amount_detect == "200_liras"):
        amount = 200
    return amount


def image_path(user_id):
    
    user_folder = os.path.join(BASE_DIR, 'static', 'images', str(user_id))
    
    if os.path.exists(user_folder):
        images = sorted([img for img in os.listdir(user_folder) if img.lower().endswith(('.jpg'))])
        if images:
            return '/'.join(['images', str(user_id), images[0]])
    return None



@bank_app.route("/account/<user_id>")
def account(user_id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT amount_of_money FROM account WHERE tc_id = ?",(user_id,))
        result_tuple = cursor.fetchone()
        money = result_tuple[0]
        session['amount_of_money'] = money
        cursor.execute("SELECT name FROM account WHERE tc_id = ?",(user_id,))
        result_tuple = cursor.fetchone()
        name = result_tuple[0]
        session['name'] = name
        image = image_path(user_id)
        session['image'] = image
        return render_template("account.html",money = money,name = name,image_path = image)

@bank_app.route("/deposit/",methods=['POST'])
def deposit():
    user_id = session.get('user_id')
    money_amount = session.get('amount_of_money')
    name = session.get('name')
    image = session.get('image')
    new_amount = money_amount
    connect = 0
    if request.method == "POST":
        try:
            amount_requested = float(request.form['deposit'])
            amount_detect = banknote_detect()
            if(amount_detect == amount_requested): 
                amount = amount_detect
            else:
                message = f"Detected amount ({amount_detect}) is not equal to requested amount ({amount_requested}). Try again!"
            new_amount = money_amount + amount
            with sqlite3.connect(DB_PATH) as connection:
                connect = 1
                cursor = connection.cursor()
                cursor.execute("UPDATE account SET amount_of_money = ? WHERE tc_id = ?",(new_amount,user_id))
                connection.commit()
                session['amount_of_money'] = new_amount
                add_transaction(user_id, ("+" + str(float(amount)) + " TL"),"Depositing Money")
                message = "Your money has been successfully deposited into your account!"
        except:
            connection.rollback()
            message = "Error in depositing money!"
        finally:
            if connect:
                connection.close()
            return render_template('continue_deposit.html',msg = message,money = new_amount,name = name,image_path = image)

@bank_app.route("/continue_deposit/",methods=['POST'])
def continue_deposit():
    money_amount = session.get('amount_of_money')
    name = session.get('name')
    image = session.get('image')
    if request.method == "POST":
        response = request.form.get('response')
        if (response == "yes"):
            return render_template("deposit.html")
        if (response == "no"):
            return render_template("account.html",money = money_amount, name = name, image_path = image)

@bank_app.route("/withdraw/",methods=['POST'])
def withdraw():
    user_id = session.get('user_id')
    money_amount = session.get('amount_of_money')
    name = session.get('name')
    image = session.get('image')
    new_amount = money_amount
    connect = 0
    if request.method == "POST":
        try:
            amount = float(request.form['withdraw'])
            if amount > money_amount:
                message = "Insufficient balance,transaction failed!"
            else: 
                new_amount = money_amount - amount
                with sqlite3.connect(DB_PATH) as connection:
                    connect = 1
                    cursor = connection.cursor()
                    cursor.execute("UPDATE account SET amount_of_money = ? WHERE tc_id = ?",(new_amount,user_id))
                    connection.commit()
                    session['amount_of_money'] = new_amount
                    add_transaction(user_id, ("-" + str(amount) + " TL"),"Withdrawing Money")
                    message = "Your money has been successfully withdrawed from your account!"
        except:
            connection.rollback()
            message = "Error in withdrawing money!"
        finally:
            if connect:
                connection.close()
            return render_template('account.html',msg = message, money =new_amount,name = name,image_path = image)


def calculate_transaction_amount():
    transaction_amount = 0.00
    now = datetime.now()
    current_time = now.time()
    time_range1_start = datetime.strptime('12:30', '%H:%M').time()
    time_range1_end = datetime.strptime('13:30', '%H:%M').time()
    time_range2_start = datetime.strptime('17:00', '%H:%M').time()
    time_range2_end = datetime.strptime('23:59', '%H:%M').time()
    time_range3_start = datetime.strptime('00:00', '%H:%M').time()
    time_range3_end = datetime.strptime('08:00', '%H:%M').time()
    if(time_range1_start < current_time < time_range1_end):
        transaction_amount = 4.76
    elif(time_range2_start < current_time < time_range2_end):
        transaction_amount = 4.76
    elif(time_range3_start < current_time < time_range3_end):
        transaction_amount = 4.76
    return transaction_amount


@bank_app.route("/transfer/",methods=['POST'])
def transfer():
    user_id = session.get('user_id')
    money_amount = session.get('amount_of_money')
    name = session.get('name')
    image = session.get('image')
    new_amount = money_amount
    connect = 0
    if request.method == "POST":
        try:
            transfer_amount = float(request.form['transfer'])
            transferred_to_id = request.form['transfer_id']
            if transfer_amount > money_amount:
                message = "Insufficient balance, transaction failed!"
                return render_template('account.html', msg=message, money=new_amount, name=name, image_path=image)
            else: 
                with sqlite3.connect(DB_PATH) as connection:
                    connect = 1
                    cursor = connection.cursor()
                    cursor.execute("SELECT name, amount_of_money FROM account WHERE tc_id = ?",(transferred_to_id,))
                    result_tuple = cursor.fetchone()
                    if not result_tuple:
                        message = "User not found!"
                        return render_template('account.html', msg=message, money=new_amount, name=name, image_path=image)
                    
                    recipient_name = result_tuple[0]
                    old_amount_transferred = result_tuple[1]
                    session['recipient_name'] = recipient_name
                    session['transferred_to_id'] = transferred_to_id
                    session['old_amount_transferred'] = old_amount_transferred
                    session['transfer_amount'] = transfer_amount
                    session['transaction_amount'] = calculate_transaction_amount()
                    return render_template('receipt.html', transfer_amount=transfer_amount, 
                                        transferred_to_id=transferred_to_id, 
                                        recipient_name=recipient_name,transaction_amount = calculate_transaction_amount())
        except:
            connection.rollback()
            message = "Error in transferring money!"
            return render_template('account.html',msg = message,money = new_amount,name = name,image_path = image)
        finally:
            if connect:
                connection.close()

def add_transaction(account_id,amount,transaction_name):
    connect = 0
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    formatted_time = now.strftime('%H:%M:%S')
    date = formatted_date + " " + formatted_time
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connect = 1
            cursor = connection.cursor()
            cursor.execute("INSERT INTO transactions (account_id, transaction_amount,date,transaction_name) VALUES (?,?,?,?)",(account_id, amount,date,transaction_name))
            connection.commit()
    except:
        connection.rollback()
    finally:
        if connect:
            connection.close()

@bank_app.route("/receipt/",methods=['POST'])
def receipt():
    user_id = session.get('user_id')
    money_amount = session.get('amount_of_money')
    name = session.get('name')
    image = session.get('image')
    transaction_amount = session.get('transaction_amount')
    transferred_to_id = session.get('transferred_to_id')
    old_amount_transferred = session.get('old_amount_transferred')
    transfer_amount = session.get('transfer_amount')
    new_amount = money_amount
    connect = 0

    if request.method == "POST":
        response = request.form.get('response')
        if (response == "yes"):
            try:
                with sqlite3.connect(DB_PATH) as connection:
                    connect = 1
                    cursor = connection.cursor()
                    new_amount = money_amount - transfer_amount
                    new_amount -= transaction_amount
                    new_amount_transferred = old_amount_transferred + transfer_amount
                    cursor.execute("UPDATE account SET amount_of_money = ? WHERE tc_id = ?", (new_amount, user_id))
                    cursor.execute("UPDATE account SET amount_of_money = ? WHERE tc_id = ?",(new_amount_transferred,   transferred_to_id))
                    connection.commit()
                    session['amount_of_money'] = new_amount
                    add_transaction(user_id, "-" + str(float(transfer_amount +transaction_amount)) + " TL", "EFT")
                    add_transaction(transferred_to_id, "+" + str(float(transfer_amount)) + " TL", "EFT")
                    message = "Money has been successfully transferred!"  
            except:
                connection.rollback()
                message = "Error in completing the transfer!"
            finally:
                if connect:
                    connection.close()
                return render_template('account.html',msg = message,money = new_amount,name = name,image_path = image)
        else:
            return render_template("account.html",money = money_amount, name = name, image_path = image)
@bank_app.route("/last_transactions/",methods = ['GET'])
def last_transactions():   
    account_id = session.get('user_id')
    connect  = 0
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connect = 1
            cursor = connection.cursor()
            cursor.execute("SELECT transaction_amount, date, transaction_name FROM transactions WHERE account_id = ? ORDER BY date DESC", (account_id,))
            transactions = cursor.fetchall()
    except:
        connection.rollback()
    finally:
        if connect:

            connection.close()
        return render_template('last_transactions.html',transactions = transactions)

if __name__ == "__main__":
    bank_app.run(debug=True)


