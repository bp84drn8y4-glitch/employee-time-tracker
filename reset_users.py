import sqlite3

conn = sqlite3.connect("time_tracker.db")
c = conn.cursor()

# Reset users table
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, 
                username TEXT UNIQUE, 
                password TEXT, 
                role TEXT)''')

# Create Employer Account
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
          ("admin", "Sam18@admin", "employer"))

conn.commit()
conn.close()

print("✅ Database Reset + Admin Account Created Successfully!")
print("Username: admin")
print("Password: Sam18@admin")
