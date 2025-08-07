import hashlib
import requests
import tkinter as tk
from tkinter import messagebox

def get_pwned_count(prefix):
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.text
    except requests.RequestException:
        return None

def check_password(password):
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    response_text = get_pwned_count(prefix)
    if response_text is None:
        return "error connection с API."

    hashes = (line.split(":") for line in response_text.splitlines())
    for sfx, count in hashes:
        if sfx == suffix:
            return f"⚠️ The password was found {int(count):,} in leaks."


    return "✅ Password not found in known leaks."


def on_check():
    password = entry.get()
    if not password:
        messagebox.showinfo("Результат", "Введите пароль для проверки.")
    else:
        result = check_password(password)
        messagebox.showinfo("result", result)

# Create simple GUI
root = tk.Tk()
root.title("Checking password")

tk.Label(root, text="Enter password:").pack(pady=5)
entry = tk.Entry(root, show="*", width=30)
entry.pack(pady=5)

tk.Button(root, text="Проверить", command=on_check).pack(pady=10)

root.mainloop()
