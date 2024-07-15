import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3


def create_database():
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       item TEXT, 
                       quantity INTEGER, 
                       customer_name TEXT, 
                       status TEXT DEFAULT 'pending')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reservations 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       customer_name TEXT, 
                       date TEXT, 
                       time TEXT, 
                       party_size INTEGER, 
                       status TEXT DEFAULT 'pending')''')
    connection.commit()
    connection.close()


create_database()


def get_orders(customer_name=None, status=None):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()

    if customer_name and status:
        cursor.execute("SELECT * FROM orders WHERE customer_name LIKE ? AND status = ?",
                       ('%' + customer_name + '%', status))
    elif customer_name:
        cursor.execute("SELECT * FROM orders WHERE customer_name LIKE ?", ('%' + customer_name + '%',))
    elif status:
        cursor.execute("SELECT * FROM orders WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM orders")

    orders = cursor.fetchall()
    connection.close()
    return orders


def get_reservations(customer_name=None, status=None):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()

    if customer_name and status:
        cursor.execute("SELECT * FROM reservations WHERE customer_name LIKE ? AND status = ?",
                       ('%' + customer_name + '%', status))
    elif customer_name:
        cursor.execute("SELECT * FROM reservations WHERE customer_name LIKE ?", ('%' + customer_name + '%',))
    elif status:
        cursor.execute("SELECT * FROM reservations WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM reservations")

    reservations = cursor.fetchall()
    connection.close()
    return reservations


def update_order_status(order_id, status):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    connection.commit()
    connection.close()
    display_orders()


def update_reservation_status(reservation_id, status):
    connection = sqlite3.connect('restaurant.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE reservations SET status = ? WHERE id = ?", (status, reservation_id))
    connection.commit()
    connection.close()
    display_reservations()


def display_orders():
    customer_name = search_entry.get()
    status = status_combobox.get()
    orders = get_orders(customer_name, status)
    orders_list.delete(*orders_list.get_children())
    if orders:
        for order in orders:
            orders_list.insert("", "end", values=order)
    else:
        messagebox.showinfo("No Orders", "No orders found for this customer and status.")


def display_reservations():
    customer_name = search_entry.get()
    status = status_combobox.get()
    reservations = get_reservations(customer_name, status)
    reservations_list.delete(*reservations_list.get_children())
    if reservations:
        for reservation in reservations:
            reservations_list.insert("", "end", values=reservation)
    else:
        messagebox.showinfo("No Reservations", "No reservations found for this customer and status.")


def delete_selected_order():
    selected_item = orders_list.selection()
    if selected_item:
        order_id = orders_list.item(selected_item)["values"][0]
        confirm = messagebox.askyesno("Delete Order", "Are you sure you want to delete this order?")
        if confirm:
            update_order_status(order_id, "Cancelled")


def delete_selected_reservation():
    selected_item = reservations_list.selection()
    if selected_item:
        reservation_id = reservations_list.item(selected_item)["values"][0]
        confirm = messagebox.askyesno("Delete Reservation", "Are you sure you want to delete this reservation?")
        if confirm:
            update_reservation_status(reservation_id, "Cancelled")


def confirm_pending_reservation():
    selected_item = reservations_list.selection()
    if selected_item:
        reservation_id = reservations_list.item(selected_item)["values"][0]
        update_reservation_status(reservation_id, "Confirmed")


def process_order():
    selected_item = orders_list.selection()
    if selected_item:
        order_id = orders_list.item(selected_item)["values"][0]
        update_order_status(order_id, "Processing")


def deliver_order():
    selected_item = orders_list.selection()
    if selected_item:
        order_id = orders_list.item(selected_item)["values"][0]
        update_order_status(order_id, "Delivered")


root = tk.Tk()
root.title("Restaurant Query System")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

search_label = tk.Label(frame, text="Customer Name:")
search_label.grid(row=0, column=0, padx=5, pady=5)

search_entry = tk.Entry(frame)
search_entry.grid(row=0, column=1, padx=5, pady=5)

status_label = tk.Label(frame, text="Status:")
status_label.grid(row=0, column=2, padx=5, pady=5)

status_var = tk.StringVar()
status_combobox = ttk.Combobox(frame, textvariable=status_var, values=["Pending", "Confirmed", "Cancelled"])
status_combobox.grid(row=0, column=3, padx=5, pady=5)

query_orders_button = tk.Button(frame, text="Query Orders", command=display_orders)
query_orders_button.grid(row=0, column=4, padx=5, pady=5)

query_reservations_button = tk.Button(frame, text="Query Reservations", command=display_reservations)
query_reservations_button.grid(row=0, column=5, padx=5, pady=5)

process_checkbox = tk.Checkbutton(frame, text="Processing", variable=tk.BooleanVar(), command=process_order)
process_checkbox.grid(row=1, column=2, padx=5, pady=5)

deliver_checkbox = tk.Checkbutton(frame, text="Delivered", variable=tk.BooleanVar(), command=deliver_order)
deliver_checkbox.grid(row=1, column=3, padx=5, pady=5)

confirm_checkbox = tk.Checkbutton(frame, text="Confirm Pending Reservations", variable=tk.BooleanVar(),
                                  command=confirm_pending_reservation)
confirm_checkbox.grid(row=1, column=4, padx=5, pady=5)

orders_frame = tk.LabelFrame(root, text="Orders")
orders_frame.pack(padx=10, pady=10, fill="both", expand=True)

orders_columns = ("id", "item", "quantity", "customer_name", "status")
orders_list = ttk.Treeview(orders_frame, columns=orders_columns, show="headings")
for col in orders_columns:
    orders_list.heading(col, text=col.capitalize())

orders_scrollbar = ttk.Scrollbar(orders_frame, orient="vertical", command=orders_list.yview)
orders_list.configure(yscroll=orders_scrollbar.set)
orders_list.pack(side="left", fill="both", expand=True)
orders_scrollbar.pack(side="right", fill="y")

delete_order_button = tk.Button(orders_frame, text="Delete Order", command=delete_selected_order)
delete_order_button.pack(pady=5)

reservations_frame = tk.LabelFrame(root, text="Reservations")
reservations_frame.pack(padx=10, pady=10, fill="both", expand=True)

reservations_columns = ("id", "customer_name", "date", "time", "party_size", "status")
reservations_list = ttk.Treeview(reservations_frame, columns=reservations_columns, show="headings")
for col in reservations_columns:
    reservations_list.heading(col, text=col.capitalize())

reservations_scrollbar = ttk.Scrollbar(reservations_frame, orient="vertical", command=reservations_list.yview)
reservations_list.configure(yscroll=reservations_scrollbar.set)
reservations_list.pack(side="left", fill="both", expand=True)
reservations_scrollbar.pack(side="right", fill="y")

delete_reservation_button = tk.Button(reservations_frame, text="Delete Reservation",
                                      command=delete_selected_reservation)
delete_reservation_button.pack(pady=5)

root.mainloop()
