import mysql.connector
import hashlib

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="travel"
)
cursor = conn.cursor()

# Function to create a new user
def create_user(username, password):
    # Check if user with the same username already exists
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        print("User with the same username already exists.")
        return

    # Insert user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()

# Function to authenticate a user
def authenticate_user(username, password):
    # Check if username and password match in the database
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()

    return user is not None

# Function to update user password
def update_password(username, new_password):
    # Update user password
    cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, username))
    conn.commit()

# Function to delete a user
def delete_user(username):
    # Delete user from the database
    cursor.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit()

# Function to search destinations based on filters
def search_destinations(location=None, budget=None, activities=None, weather=None):
    # Base query
    query = "SELECT DISTINCT * FROM destination WHERE 1"

    # Add filters to the query
    if location:
        query += " AND location LIKE '%" + location + "%'"
    if budget:
        query += " AND budget <= " + str(budget)
    if activities:
        query += " AND activities LIKE '%" + activities + "%'"
    if weather:
        query += " AND weather LIKE '%" + weather + "%'"

    print("Query:", query)

    # Execute the query
    cursor.execute(query)
    destinations = cursor.fetchall()

    return destinations

# Function to get user input for destination
def get_user_input():
    print("Choose filters you want to apply (Enter 'none' if you don't want to apply a filter):")
    location = input("Enter the location (or 'none'): ")
    budget = input("Enter your budget (or 'none'): ")
    activities = input("Enter preferred activities (or 'none'): ")
    weather = input("Enter preferred weather (or 'none'): ")
    return location if location.lower() != 'none' else None, \
           float(budget) if budget.lower() != 'none' else None, \
           activities if activities.lower() != 'none' else None, \
           weather if weather.lower() != 'none' else None

def destinations():
    cursor.execute(create_table_destinations)
    cursor.execute(create_table_attractions)
    cursor.execute(create_table_accommodations)
    cursor.execute(create_table_restaurants)
    cursor.execute(create_table_transportation_options)
    conn.commit()

    # Get user input for country
    country = input("Enter the country (or 'none'): ")

    # Modify the example_query based on the user input
    example_query = f"""
    SELECT DISTINCT 
        d.location,
        d.budget,
        d.activities,
        d.weather,
        a.name AS attraction_name,
        a.description AS attraction_description,
        acc.name AS accommodation_name,
        acc.description AS accommodation_description,
        r.name AS restaurant_name,
        r.cuisine,
        t.mode AS transportation_mode,
        t.description AS transportation_description
    FROM 
        destinations d
    LEFT JOIN 
        attractions a ON d.id = a.destination_id
    LEFT JOIN 
        accommodations acc ON d.id = acc.destination_id
    LEFT JOIN 
        restaurants r ON d.id = r.destination_id
    LEFT JOIN 
        transportation_options t ON d.id = t.destination_id
    """

    # Add the WHERE clause to the query if location is provided
    if country.lower() != 'none':
        example_query += f"WHERE d.location LIKE '%{country}%'"

    # Execute the example query
    cursor.execute(example_query)
    result = cursor.fetchall()
    # Keep track of seen destinations
    seen_destinations = set()

    # Display the result, only print each destination once
    for row in result:
        destination = row[1]  # Assuming the second column is the destination name
        if destination not in seen_destinations:
            seen_destinations.add(destination)
            print(row)

def delete_duplicates(table_name, columns):
    # Construct the SELECT query to identify duplicate entries
    select_query = f"""
        SELECT {', '.join(columns)}
        FROM {table_name}
        GROUP BY {', '.join(columns)}
        HAVING COUNT(*) > 1
    """

    # Construct the DELETE query to remove duplicate entries
    delete_query = f"""
        DELETE FROM {table_name}
        WHERE ({', '.join(columns)}) IN ({select_query})
        AND id NOT IN (
            SELECT MIN(id)
            FROM {table_name}
            GROUP BY {', '.join(columns)}
        )
    """

    # Execute the DELETE query
    cursor.execute(delete_query)
    conn.commit()

    print("Duplicate entries deleted successfully.")

# Function to delete all data from tables
def delete_all_data():
    tables = ["destinations", "attractions", "accommodations", "restaurants", "transportation_options"]

    for table in tables:
        delete_query = f"DELETE FROM {table}"
        cursor.execute(delete_query)

    conn.commit()
    print("All data deleted successfully.")

# Function to create a custom itinerary with budget tracking and save it to SQL
def create_itinerary_with_budget_and_save():
    print("Welcome to Itinerary Creation with Budget Tracking and SQL Saving!")

    # Get user input for itinerary details
    num_destinations = int(input("How many destinations do you want to include in your itinerary? "))

    total_budget = float(input("Enter your total budget for the trip: "))
    remaining_budget = total_budget

    itinerary = []

    for i in range(num_destinations):
        print(f"\nDestination {i + 1}:")
        destination = input("Enter destination: ")
        activities = input("Enter preferred activities separated by commas: ")
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD): ")
        transportation = input("Enter preferred transportation (e.g., flight, train): ")
        accommodation = input("Enter preferred accommodation (e.g., hotel, Airbnb): ")

        destination_budget = float(input(f"Enter budget for {destination}: "))
        remaining_budget -= destination_budget

        # Create a dictionary for each destination
        destination_info = {
            "Destination": destination,
            "Activities": activities,
            "Start Date": start_date,
            "End Date": end_date,
            "Transportation": transportation,
            "Accommodation": accommodation,
            "Budget": destination_budget
        }

        # Append the destination info to the itinerary list
        itinerary.append(destination_info)

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS itineraries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            destination VARCHAR(100) NOT NULL,
            activities TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            transportation VARCHAR(100),
            accommodation VARCHAR(100),
            budget FLOAT NOT NULL
            );
            '''
        )
        # Insert data into SQL table
        cursor.execute("""
            INSERT INTO itineraries (destination, activities, start_date, end_date, transportation, accommodation, budget) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (destination, activities, start_date, end_date, transportation, accommodation, destination_budget))
        conn.commit()

    # Print the generated itinerary
    print("\nYour Custom Itinerary with Budget Tracking and SQL Saving:")
    for idx, destination_info in enumerate(itinerary, start=1):
        print(f"\nDestination {idx}:")
        for key, value in destination_info.items():
            print(f"{key}: {value}")

    print(f"\nRemaining budget after all destinations: ${remaining_budget:.2f}")

def generate_report():
    print("Generating Report...\n")

    # Execute query to fetch destinations data
    cursor.execute("SELECT * FROM destinations")
    destinations_data = cursor.fetchall()

    # Print destinations data
    print("Destinations:")
    print("ID\tLocation\tBudget\tActivities\tWeather")
    for destination in destinations_data:
        print(f"{destination[0]}\t{destination[1]}\t{destination[2]}\t{destination[3]}\t{destination[4]}")

    print()

    # Execute query to fetch users data
    cursor.execute("SELECT * FROM users")
    users_data = cursor.fetchall()

    # Print users data
    print("Users:")
    print("ID\tUsername\tPassword")
    for user in users_data:
        print(f"{user[0]}\t{user[1]}\t{user[2]}")

# Main function
if __name__ == "__main__":
    # Create a new user
    create_user("user1", "password123")

    # Authenticate the user
    if authenticate_user("user1", "password123"):
        print("Welcome to the Travel Planner App!")
        print("1. Generate Report")
        print("2. Create Itinerary with Budget and Save")
        print("3. Input Destinations")
        print("4. Search Destinations")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            if authenticate_user("user1", "password123"):
                generate_report()
            else:
                print("Invalid username or password.")
        elif choice == "2":
            if authenticate_user("user1", "password123"):
                create_itinerary_with_budget_and_save()
            else:
                print("Invalid username or password.")
        elif choice=="3":
            destinations()
        elif choice=='4':
            location, budget, activities, weather = get_user_input()
            search_results = search_destinations(location, budget, activities, weather)
            print("Search Results:")
            for destination in search_results:
                print(destination)
        elif choice == "6":
            print("Exiting program...")
            conn.close()
            exit()
        else:
            print("Invalid choice. Please try again.")

        generate_report()
        create_itinerary_with_budget_and_save()
        # Example data to be inserted into the destination table
        destinations_data = [
            ("Paris", 1000, "Sightseeing", "Sunny"),
            ("London", 1200, "Museums", "Rainy"),
            ("Tokyo", 1500, "Shopping", "Sunny")
        ]
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INT AUTO_INCREMENT PRIMARY KEY,
                   username VARCHAR(50) UNIQUE,
                   password VARCHAR(256))''')

        # Create destination table if not exists and insert example data
         # Check if the destination data already exists before inserting
        existing_destinations = cursor.execute("SELECT * FROM destination")
        existing_destinations = cursor.fetchall()
        existing_destinations = set([dest[1] for dest in existing_destinations])

        for destination_data in destinations_data:
            if destination_data[0] not in existing_destinations:
                cursor.execute("INSERT INTO destination (location, budget, activities, weather) VALUES (%s, %s, %s, %s)", destination_data)
                existing_destinations.add(destination_data[0])

        conn.commit()
        # SQL statements to create tables
        create_table_destinations = """
        CREATE TABLE IF NOT EXISTS destinations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            description TEXT
        )
        """

        create_table_attractions = """
        CREATE TABLE IF NOT EXISTS attractions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            destination_id INT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        )
        """

        create_table_accommodations = """
        CREATE TABLE IF NOT EXISTS accommodations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            destination_id INT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        )
        """

        create_table_restaurants = """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            destination_id INT,
            name VARCHAR(100) NOT NULL,
            cuisine VARCHAR(100),
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        )
        """

        create_table_transportation_options = """
        CREATE TABLE IF NOT EXISTS transportation_options (
            id INT AUTO_INCREMENT PRIMARY KEY,
            destination_id INT,
            mode VARCHAR(100) NOT NULL,
            description TEXT,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        )
        """

        # Execute create table statements
        cursor.execute(create_table_destinations)
        cursor.execute(create_table_attractions)
        cursor.execute(create_table_accommodations)
        cursor.execute(create_table_restaurants)
        cursor.execute(create_table_transportation_options)

        # Commit changes and close connection
        conn.commit()
        # Insert data into attractions table
        attractions_data = [
            (1, "Eiffel Tower", "Iconic landmark"),
            (2, "Big Ben", "Clock tower"),
            (3, "Tokyo Tower", "Observation tower"),
        ]

        insert_attractions_query = """
        INSERT INTO attractions (destination_id, name, description) 
        VALUES (%s, %s, %s)
        """

        cursor.executemany(insert_attractions_query, attractions_data)
        conn.commit()

        # Insert data into accommodations table
        accommodations_data = [
            (1, "Hotel ABC", "Luxury hotel"),
            (2, "Hotel XYZ", "Budget hotel"),
            (3, "Ryokan", "Traditional Japanese inn"),
        ]

        insert_accommodations_query = """
        INSERT INTO accommodations (destination_id, name, description) 
        VALUES (%s, %s, %s)
        """

        cursor.executemany(insert_accommodations_query, accommodations_data)
        conn.commit()

        # Insert data into restaurants table
        restaurants_data = [
            (1, "Le Jules Verne", "French"),
            (2, "The Ivy", "British"),
            (3, "Sushi Dai", "Japanese"),
        ]

        insert_restaurants_query = """
        INSERT INTO restaurants (destination_id, name, cuisine) 
        VALUES (%s, %s, %s)
        """

        cursor.executemany(insert_restaurants_query, restaurants_data)
        conn.commit()

        # Insert data into transportation_options table
        transportation_options_data = [
            (1, "Metro", "Public transportation system"),
            (2, "Tube", "Underground railway system"),
            (3, "Shinkansen", "High-speed bullet train"),
        ]

        insert_transportation_options_query = """
        INSERT INTO transportation_options (destination_id, mode, description) 
        VALUES (%s, %s, %s)
        """

        cursor.executemany(insert_transportation_options_query, transportation_options_data)
        conn.commit()
        
    else:
        print("Invalid username or password.")

    # Update user password
    update_password("user1", "newpassword456")

    # Delete user
    delete_user("user1")

# Close the database connection
conn.close()