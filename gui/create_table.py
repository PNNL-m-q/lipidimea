import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('example.db')

# Create a cursor object to execute SQL statements
cursor = conn.cursor()

# Create the table
cursor.execute('''
    CREATE TABLE Table1 (
        ID INTEGER PRIMARY KEY,
        Country TEXT NOT NULL,
        Population INTEGER,
        Square_Miles INTEGER,
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE Table2 (
        ID INTEGER,
        City TEXT NOT NULL,
        Population INTEGER,
        Square_Miles INTEGER,
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Example data
example_data = [
    (1, 'USA', 328200000, 3796742),
    (2, 'Canada', 37590000, 3855081),
    (3, 'China', 1444216107, 3705409),
    (4, 'Panama', 4295000, 29216),
    (5, 'Ecuador', 17446584, 106851),
]

example_data2 = [
    (1, "Seattle", 744955, 83.9),
    (1, "New York City", 8537673, 302.6),
    (1, "Los Angeles", 3977683, 468.7),
    (2, "Vancouver", 631486, 115),
    (2, "Toronto", 2731571, 243.3),
    (3, "Beijing", 21707000, 652.2),
    (3, "Shanghai", 24183300, 2485.5),
    (3, "Guangzhou", 14944727, 2376.4),
    (4, "Panama City", 880691, 275),
    (5, "Quito", 1742965, 170.6),
    (5, "Guayaquil", 2768659, 269.8),
]


# Insert the example data into the table
cursor.executemany('''
    INSERT INTO Table1 (ID, Country, Population, Square_Miles) VALUES (?, ?, ?, ?)
''', example_data)

cursor.executemany('''
    INSERT INTO Table2 (ID, City, Population, Square_Miles) VALUES (?, ?, ?,?)
''', example_data2)

# Commit the changes and close the connection
conn.commit()
conn.close()

