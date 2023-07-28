import sqlite3
import pandas as pd
import os
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from langchain.chat_models import ChatOpenAI


def file_checker(name_of_file):
    while not os.path.exists(name_of_file):
        print("File not found.")
        name_of_file = input("Please input a valid file name: ")
    return name_of_file


def read_file(file):
    housing_list = []
    f = open(file, "r")
    for line in f:
        line = line.split("\t")
        housing_list.append(line)
    f.close()
    return housing_list


def sql_query(question):
    # Check if the file exists
    file_name = file_checker("redfinData.csv")

    # data cleaning since they csv didn't want to csv
    f = file_checker("redfinData.csv")
    file = read_file(f)

    # check to see if it is fixed

    # Read the CSV data into a DataFrame
    data = pd.DataFrame(file[1:], columns=['Region', 'Month of Period End', 'Measure Names', 'Measure Values'])
    print(data.head())

    # Specify your OpenAI API key
    api_key = "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"

    # Create an instance of the OpenAI language model
    llm = OpenAI(openai_api_key=api_key, temperature=0, max_tokens=300, model_name="gpt-3.5-turbo")

    # Create a SQLite database from the DataFrame
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    data.to_sql("redfin", engine, if_exists="replace")

    # Create an SQLDatabase object using the SQLite database
    database = SQLDatabase(engine)
    #
    # Create an SQLDatabaseChain object with the language model and database
    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=database, verbose=True)

    db_chain.run(question)


def read_file(file):
    housing_list = []
    f = open(file, "r")
    for line in f:
        line = line.split(",")
        housing_list.append(line)
    f.close()
    return housing_list


def mortgage_calculator(principle, rate, term):
    rate = rate / 100
    monthly_rate = rate / 12
    nterm = term * 12
    numerator = monthly_rate * ((1 + monthly_rate) ** nterm)
    denomerator = (1 + monthly_rate) ** nterm - 1
    payment = principle * numerator / denomerator
    return payment


def find_min(housing_data):
    lowest = 1000000000.00
    for home in housing_data:
        if float(home[1]) < lowest:
            lowest = float(home[1])

    return str(lowest)


def find_max(housing_data):
    largest = 0.0
    for home in housing_data:
        if float(home[7]) > largest:
            largest = float(home[7])

    return float(largest)


def toString(home_list):
    for i in home_list:
        print(" ")
        print("Address: " + str(i[3]) + "\n"
              + "Price: $" + str(i[7]) + "\n"
              + "Beds: " + str(i[8]) + "\n"
              + "Baths: " + str(i[9]) + "\n"
              + "Sqft: " + str(i[11]) + "\n"
              + "URL: " + str(i[20]) + "\n"
              + "Estimates monthly payments: $" + str(i[-1]))
        print(" ")


def find_avg_payments(housing_data, n):
    total = 0

    for home in housing_data:
        total += float(home[-1])

    avg = total / n

    return str(avg)


# buy side for home buyers
# Affordability based off gross income and using the 28% rule to determine affordability of a home
# find average HOA fees

Buy_data = read_file("Temp.csv")

# check to make sure it looks good
print(Buy_data[0])
print(Buy_data[0][7])

property_tax = .026

client_restraint = int(input("Are we provided with a clients budget(1) or income(2)?: "))
freq = 0

match = []
defined_matches = []
if client_restraint == 1:
    X = float(input("What is the clients budget?: "))
    temp = X
    income = float(input("What is the clients income?: "))

    percent_down = float(input("How much money down %: "))
    twenty_eight_rule = (income / 12) * .29
    thirty_six_rule = (income / 12) * .35
    print(str(twenty_eight_rule) + " what you can afford ea month with 28% of your monthly income")
    print(str(thirty_six_rule) + " what you can afford ea month with 36% of your monthly income")

    for home in Buy_data[1:]:
        monthly_expenses = 0.0
        if home[7].isdigit():
            price = float(home[7])

            if X >= price:
                principal = price - (price * percent_down)
                monthly_expenses = mortgage_calculator(principle=principal, rate=7.15, term=30)
                monthly_expenses += (price * property_tax) / 12
                monthly_expenses += 250

                if (twenty_eight_rule >= monthly_expenses) & (monthly_expenses <= thirty_six_rule):
                    home.append(monthly_expenses)
                    match.append(home)
                    freq += 1

    max_home = find_max(match)
    print(str(max_home) + "is the most expensive home")
    base_limit = max_home - (max_home * 0.20)

    # reduce the matches even more by returning only the homes in that top range
    for home in match:
        if float(home[7]) >= base_limit:
            defined_matches.append(home)

    # use a sql query to ask questions on findings:
    df = pd.DataFrame(defined_matches, columns=Buy_data[0].append("mo expenses"))
    # Specify your OpenAI API key
    api_key = "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"
    # Create an instance of the OpenAI language model
    llm = OpenAI(openai_api_key=api_key, temperature=0, max_tokens=300)

    # Create a SQLite database from the DataFrame
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    df.to_sql("redfin", engine, if_exists="replace")

    # Create an SQLDatabase object using the SQLite database
    database = SQLDatabase(engine)
    # Create an SQLDatabaseChain object with the language model and database
    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=database, verbose=True)

    PropType = df[2].tolist()
    print(set(PropType))  # unique values only
    client_type = input("What type of home are the looking for? : ")

    print("We found " + str(len(defined_matches)) + " matches\n")
    for home in defined_matches:
        if home[2] != client_type:
            defined_matches.remove(home)

    cities = df[4].tolist()
    unique_values = set(cities)
    total = len(defined_matches)
    for towns in unique_values:
        occurrences = 0
        for i in defined_matches:
            if i[4] == towns:
                occurrences += 1

        print(towns + " has " + str(occurrences) + " occurrences")

    print(str(total) + " Total homes")
    toString(defined_matches)

