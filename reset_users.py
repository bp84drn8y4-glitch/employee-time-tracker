import sqlite3

conn = sqlite3.connect("time_tracker.db")
c = conn.cursor()

# Drop old users table and create fresh one
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE users (
                id INTEGER PRIMARY KEY, 
                username TEXT UNIQUE, 
                password TEXT, 
                role TEXT)''')

# Create Employer Account
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
          ("admin", "Sam18@admin", "employer"))

conn.commit()
conn.close()

print("✅ SUCCESS! Database Reset Complete")
print("Employer Account Created:")
print("Username: admin")
print("Password: Sam18@admin")
print("\nNow go to your app and login with these credentials.")
