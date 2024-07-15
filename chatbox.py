import tkinter as tk
from tkinter import scrolledtext, simpledialog,Spinbox,Label
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
import sqlite3
import calendar
from datetime import datetime

model = load_model('chatbotmodel.h5')
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))

try:
    with open('data.json', 'r') as file:
        intents = json.load(file)
except FileNotFoundError:
    print("Error: data.json file not found.")
    intents = None
except json.JSONDecodeError as e:
    print(f"Error decoding data.json: {e}")
    intents = None

lemmatizer = WordNetLemmatizer()
def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words




def create_table():
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       item TEXT, 
                       quantity INTEGER, 
                       customer_name TEXT, 
                       status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reservations 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       customer_name TEXT, 
                       date TEXT, 
                       time TEXT, 
                       party_size INTEGER, 
                       status TEXT)''')
    connection.commit()
    connection.close()


create_table()


def save_order(item, quantity, customer_name):
    try:
        connection = sqlite3.connect('restaurant.db')
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO orders (item, quantity, customer_name, status) VALUES (?, ?, ?, 'Pending')",
            (item, quantity, customer_name)
        )
        connection.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()


def get_reservation(customer_name):
    try:
        connection = sqlite3.connect('restaurant.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM reservations WHERE customer_name = ?", (customer_name,))
        reservations = cursor.fetchall()
        if not reservations:
            print("No reservations found for this customer.")
            return None
        print("Here are the reservations for this customer:")
        for reservation in reservations:
            print(f"ID: {reservation[0]}, Date: {reservation[2]}, Time: {reservation[3]}, Party Size: {reservation[4]}")
        return reservations
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        if connection:
            connection.close()


def update_reservation(reservation_id, new_date=None, new_time=None, new_party_size=None):
    try:
        connection = sqlite3.connect('restaurant.db')
        cursor = connection.cursor()

        # Build the SQL query based on provided parameters
        update_query = "UPDATE reservations SET"
        update_fields = []
        if new_date:
            update_fields.append(f"date = '{new_date}'")
        if new_time:
            update_fields.append(f"time = '{new_time}'")
        if new_party_size:
            update_fields.append(f"party_size = {new_party_size}")

        # Join all update fields into the query
        update_query += ", ".join(update_fields)

        # Add WHERE clause to specify which reservation to update
        update_query += f" WHERE id = {reservation_id}"

        # Execute the update query
        cursor.execute(update_query)
        connection.commit()
        print(f"Reservation {reservation_id} updated successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if connection:
            connection.close()


def modify_reservation(customer_name):
    if not customer_name:
        print("Invalid customer name.")
        return
    reservations = get_reservation(customer_name)
    if not reservations:
        print("No reservations found for this customer.")
        return
    reservation_id = simpledialog.askinteger("Modify Reservation",
                                             "Enter the ID of the reservation you want to modify:")
    if not reservation_id:
        print("Invalid reservation ID.")
        return
    valid_reservation = False
    for reservation in reservations:
        if reservation[0] == reservation_id:
            valid_reservation = True
            break
    if not valid_reservation:
        print("Invalid reservation ID for this customer.")
        return
    new_date = simpledialog.askstring("Modify Reservation", "Enter the new date (YYYY-MM-DD):")
    new_time = simpledialog.askstring("Modify Reservation", "Enter the new time:")
    new_party_size = simpledialog.askinteger("Modify Reservation", "Enter the new party size:")
    update_reservation(reservation_id, new_date=new_date, new_time=new_time, new_party_size=new_party_size)


def get_orders(customer_name):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE customer_name = ? AND status IN ('Pending', 'Processing')
    """, (customer_name,))
    orders = cursor.fetchall()
    connection.close()
    return orders


def cancel_order(order_id):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ?", (order_id,))
    connection.commit()
    connection.close()


def save_reservation(customer_name, date, time, party_size):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO reservations (customer_name, date, time, party_size, status) VALUES (?, ?, ?, ?, 'Pending')",
        (customer_name, date, time, party_size))
    connection.commit()
    connection.close()


def get_reservations(customer_name):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM reservations WHERE customer_name = ? AND status = 'Pending'", (customer_name,))
    reservations = cursor.fetchall()
    connection.close()
    return reservations


def cancel_reservation(reservation_id):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE reservations SET status = 'Cancelled' WHERE id = ?", (reservation_id,))
    connection.commit()
    connection.close()


def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result




def Menu():
    menu = {
        "Yam Chips": [55.00, 70.00, 85.00],
        "Jelof Rice": [55.00, 70.00, 85.00],
        "Fried Rice": [55.00, 70.00, 85.00],
        "Plane Rice": [55.00, 70.00, 85.00],
        "Banku with Tilapia, Okro stew or pepper": [75.00, 100.00, 125.00]
    }
    sizes = ["Small size", "Medium size", "Large size"]
    menu_message = "Here is our menu:\n"
    for index, (item, prices) in enumerate(menu.items(), 1):
        menu_message += f"{index}. {item}\n"
        for size, price in zip(sizes, prices):
            menu_message += f"   - {size}: Ghc {price:.2f}\n"
    return menu_message


class TimePickerDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.selected_time = None
        super().__init__(parent, title=title)

    def body(self, master):
        Label(master, text="Hour:").grid(row=0, column=0)
        self.hour_spinbox = Spinbox(master, from_=1, to=12, width=5)
        self.hour_spinbox.grid(row=0, column=1)

        Label(master, text="Minute:").grid(row=1, column=0)
        self.minute_spinbox = Spinbox(master, from_=0, to=59, width=5, format="%02.0f")
        self.minute_spinbox.grid(row=1, column=1)

        Label(master, text="AM/PM:").grid(row=2, column=0)
        self.period_var = tk.StringVar(value="AM")
        self.period_spinbox = Spinbox(master, values=("AM", "PM"), textvariable=self.period_var, width=5)
        self.period_spinbox.grid(row=2, column=1)
        return self.hour_spinbox  # initial focus

    def apply(self):
        hour = self.hour_spinbox.get()
        minute = self.minute_spinbox.get()
        period = self.period_var.get()
        self.selected_time = f"{hour}:{minute} {period}"

    @staticmethod
    def ask_time(parent, title=None):
        dialog = TimePickerDialog(parent, title)
        return dialog.selected_time


class DatePickerDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.selected_date = None
        super().__init__(parent, title=title)

    def body(self, master):
        Label(master, text="Year:").grid(row=0, column=0)
        self.year_spinbox = Spinbox(master, from_=2020, to=2030, width=5)
        self.year_spinbox.grid(row=0, column=1)

        Label(master, text="Month:").grid(row=1, column=0)
        self.month_spinbox = Spinbox(master, from_=1, to=12, width=5)
        self.month_spinbox.grid(row=1, column=1)

        Label(master, text="Day:").grid(row=2, column=0)
        self.day_spinbox = Spinbox(master, from_=1, to=31, width=5)
        self.day_spinbox.grid(row=2, column=1)
        return self.year_spinbox

    def apply(self):
        year = int(self.year_spinbox.get())
        month = int(self.month_spinbox.get())
        day = int(self.day_spinbox.get())
        try:
            self.selected_date = f"{year:04d}-{month:02d}-{day:02d}"
            # Check if the date is valid
            datetime(year, month, day)
        except ValueError:
            self.selected_date = None

    @staticmethod
    def ask_date(parent, title=None):
        dialog = DatePickerDialog(parent, title)
        return dialog.selected_date



def MAINBOT(user_message):
    chatbot_response = ""
    if intents is None:
        return "ChatBot: Sorry, I'm currently unable to respond. Please try again later."
    ints = predict_class(user_message)

    if ints:
        intent = ints[0]['intent']
        if intent == 'order_food':
            item = simpledialog.askstring("Order Food", "Enter the food you'd like to order:")
            quantity = simpledialog.askinteger("Order Food", "Enter the quantity (number of packs):")
            customer_name = simpledialog.askstring("Order Food", "Enter your name:")
            save_order(item, quantity, customer_name)
            chatbot_response = f"ChatBot: Your order has been placed. We will process it shortly."
        # elif intent == 'get_orders':
        #     customer_name = simpledialog.askstring("Get Orders", "Enter your name:")
        #     orders = get_orders(customer_name)
        #     for order in orders:
        #         chatbot_response += f"ChatBot: Your pending orders.\n - {order[2]} packs of {order[1]}\n"
        #     else:
        #         chatbot_response = "You have no pending orders."
        elif intent == 'get_orders':
            customer_name = simpledialog.askstring("Get Orders", "Enter your name:")
            orders = get_orders(customer_name)
            if orders:  # Check if there are any orders
                chatbot_response = "ChatBot: Your orders:\n"
                for order in orders:
                    chatbot_response += f" - {order[2]} packs of {order[1]} (status: {order[4]})\n"
            else:
                chatbot_response = "You have no pending orders."

            #print(f"Debug: Chatbot response: {chatbot_response}")  # Debug statement


        elif intent == 'cancel_orders':
            customer_name = simpledialog.askstring("Cancel Orders", "Enter your name:")
            orders = get_orders(customer_name)
            if orders:
                chatbot_response="ChatBot: Your active orders: "#print("Your active orders:")
                for order in orders:
                    chatbot_response += f"\nID: {order[0]}, Item: {order[2]} packs of {order[1]}\n "
                chat_window.config(state=tk.NORMAL)
                chat_window.insert(tk.END, f"{chatbot_response}\n\n")
                chat_window.config(state=tk.DISABLED)
                chat_window.see(tk.END)
                order_id = simpledialog.askstring(f"Cancel orders",
                                                  f"Enter your order ID to be cancelled.")
                cancel_order(order_id)
                chatbot_response = " Sorry for the inconvenience.\n Your order has been cancelled.\n Thank you."
            else:
                print("You have no active orders.")
        elif intent == 'reservations':
            customer_name = simpledialog.askstring("Reservations", "Enter your name:")
            if customer_name:
                date = DatePickerDialog.ask_date(root,"Select Date")
                #date = simpledialog.askstring("Reservations", "Enter the date for the reservation (YYYY-MM-DD):")
                if date:
                    time = TimePickerDialog.ask_time(root, "Select Time")
                    if time:
                        party_size = simpledialog.askinteger("Reservations", "Enter the party size:")
                        if party_size:
                            save_reservation(customer_name, date, time, party_size)
                            chatbot_response = "ChatBot: Your reservation has been confirmed. We look forward to serving you."
                        else:
                            chatbot_response = "ChatBot: Invalid party size. Please try again."
                    else:
                        chatbot_response = "ChatBot: Invalid time. Please try again."
                else:
                    chatbot_response = "ChatBot: Invalid date. Please try again."
            else:
                chatbot_response = "ChatBot: Invalid name. Please try again."

        elif intent == 'get_reservations':
            customer_name = simpledialog.askstring("Get Reservations", "Enter your name:")
            reservations = get_reservations(customer_name)
            if reservations:
                #print("Your confirmed reservations:")
                for reservation in reservations:
                    chatbot_response += f" \n- {reservation[2]} at {reservation[3]} for {reservation[4]} people\n"
            else:
                chatbot_response = "You have no confirmed reservations."

        elif intent == 'cancel_reservation':
            customer_name = simpledialog.askstring("Cancel Reservations", "Enter your name:")
            if customer_name:
                reservations = get_reservations(customer_name)
                if reservations:
                    chatbot_response = "Your active reservations:\n"
                    for reservation in reservations:
                        chatbot_response += f"ID: {reservation[0]}, Date: {reservation[2]}, Time: {reservation[3]}, Party Size: {reservation[4]}\n"
                    chat_window.config(state=tk.NORMAL)
                    chat_window.insert(tk.END, f"{chatbot_response}\n\n")
                    chat_window.config(state=tk.DISABLED)
                    chat_window.see(tk.END)
                    reservation_id = simpledialog.askinteger(f"Cancel Reservations",
                                                             "Enter the reservation ID to be canceled:")
                    if reservation_id:
                        cancel_reservation(reservation_id)
                        chatbot_response = "ChatBot: Your reservation has been canceled."
                    else:
                        chatbot_response = "ChatBot: Invalid reservation ID. Please try again."
                else:
                    chatbot_response = "ChatBot: You have no active reservations."
            else:
                chatbot_response = "ChatBot: Invalid name. Please try again."
            chat_window.config(state=tk.NORMAL)
            chat_window.insert(tk.END, f"{chatbot_response}\n\n")
            chat_window.config(state=tk.DISABLED)
            chat_window.see(tk.END)


        elif intent == 'modify_reservation':
            customer_name = simpledialog.askstring("Modify Reservation", "Enter your name:")
            reservations = get_reservations(customer_name)
            if reservations:
                chatbot_response = "Your reservations:\n"
                for reservation in reservations:
                    chatbot_response += f" - ID: {reservation[0]}, Date: {reservation[2]} at {reservation[3]} for {reservation[4]} people\n"
                    chat_window.insert(tk.END, chatbot_response + "\n")
                    chat_window.see(tk.END)
                modify_reservation(customer_name)
            else:
                chatbot_response = "You have no reservations."


        elif intent == 'menu_enquiry':
            Menu()
            chatbot_response += "ChatBot: " + Menu()
        else:
            res = get_response(ints, intents)
            chatbot_response = "ChatBot: " + res

        return chatbot_response


def send():
    user_message = text_entry.get("1.0", tk.END, ).strip()
    if user_message:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"You: {user_message}\n\n")
        chat_window.config(state=tk.DISABLED)
        chat_window.see(tk.END)

        chatbot_response = MAINBOT(user_message)

        if chatbot_response:
            chat_window.config(state=tk.NORMAL)
            chat_window.insert(tk.END, f"ChatBot: {chatbot_response}\n\n")
            chat_window.config(state=tk.DISABLED)
            chat_window.see(tk.END)

        text_entry.delete("1.0", tk.END)


root = tk.Tk()
root.title("Restaurant Chatbot")
frame = tk.Frame(root)
frame.pack(expand=True, fill=tk.BOTH)
scrollbar = tk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_window = scrolledtext.ScrolledText(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, background="SkyBlue",
                                        font=("Times New Roman", 15), state=tk.DISABLED)
chat_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=chat_window.yview)
text_entry = tk.Text(root, height=4, width=80, font=("Times New Roman", 12))
text_entry.pack(pady=10, padx=10)
send_button = tk.Button(root, text="Send", command=send, width=10, height=2)
send_button.pack(side=tk.RIGHT, padx=10, pady=10)
root.mainloop()
