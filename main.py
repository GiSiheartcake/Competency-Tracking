import sqlite3
import bcrypt
import datetime
import csv
  
# # example password
# password = b'passwordabc'

# # generating the salt
# salt = bcrypt.gensalt()
  
# # Hashing the password
# hash = bcrypt.hashpw(password, salt)

def printTable(cursor, table, showInactive = False, sql = ''):
    if sql:
        data = cursor.execute(sql).fetchall()
    elif table == 'Managers':
        data = cursor.execute("SELECT * FROM Users WHERE manager = 1 AND active = 1").fetchall()
    elif table == 'Users':
        if showInactive:
            data = cursor.execute(f"SELECT * FROM Users").fetchall()
        else:
            data = cursor.execute(f"SELECT * FROM Users WHERE active = 1").fetchall()
    else:
        data = cursor.execute(f"SELECT * FROM {table}").fetchall()
    columns = []
    indices = []
    for i, each in enumerate(cursor.description):
        if each[0] not in ('active', 'password'):
            columns.append(each[0])
            indices.append(i)
            print(f"{each[0]:<20}", end = ' ')
    print()
    for row in data:
        for i, value in enumerate(row):
            if i in indices:
                print(f"{str(value):<20}", end = ' ')
        print()

def createRecord(cursor, table, runNow=True):
    cursor.execute(f"SELECT * FROM {table}")
    skipFirst = True
    # if table == 'Student_Cohort_Registrations':
    #     skipFirst = False

    columns = []
    for each in cursor.description:
        if skipFirst:
            skipFirst = False
            continue
        if each[0] not in ('active', 'manager'):
            columns.append(each[0])
    
    values = []
    for each in columns:
        if each == 'date_created':
            values.append(datetime.date.today())
        elif each == 'password':
            values.append(bcrypt.hashpw(bytes(input(f"Enter {each}\n> "), 'utf8'), bcrypt.gensalt()))
        elif each == 'comp_id':
            printTable(cursor, 'Competencies')
            values.append(input(f"Enter a {each} from the table above\n> "))
        elif each == 'user_id':
            printTable(cursor, 'Users')
            values.append(input(f"Enter a {each} from the table above\n> "))
        elif each == 'asmt_id':
            printTable(cursor, 'Assessments')
            values.append(input(f"Enter a {each} from the table above\n> "))
        elif each == 'manager_id':
            printTable(cursor, 'Managers')
            values.append(input(f"Enter a {each} from the table above, or press Enter to skip\n> "))
        else:
            values.append(input(f"Enter {each}\n> "))
    
    dynamicBinding =('?, ' * len(columns)).rstrip(', ')

    if runNow:
        cursor.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({dynamicBinding})", values)
    else:
        return (f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({dynamicBinding})", values)

def printUserCompetencies(user_id, connection, cursor):
    print(f"{'Competency':30}{'Latest Score':12}{'Best Score':>15}")
    data = cursor.execute("""SELECT c.name, r.score, r.date_created FROM Competencies c, Results r, Assessments a
WHERE a.asmt_id = r.asmt_id
AND a.comp_id = c.comp_id
AND r.user_id = ?;""", (user_id,)).fetchall()
    data_dict = {}
    for each in data:
        if each[0] in data_dict:
            data_dict[each[0]]['scores'].append(each[1])
            data_dict[each[0]]['dates'].append(datetime.date.fromisoformat(each[2]))
        else:
            data_dict[each[0]] = {'scores':[each[1]], 'dates':[datetime.date.fromisoformat(each[2])]}
    for each in data_dict:
        competency = each
        latestIndex = data_dict[each]['dates'].index(max(data_dict[each]['dates']))
        latestScore = data_dict[each]['scores'][latestIndex]
        bestScore = max(data_dict[each]['scores'])
        print(f"{competency:30}{latestScore:12}{bestScore:>15}")

def printUserResults(user_id, connection, cursor):
    print(f"{'Assessment':30}{'Score':5}{'Date':>15}")
    data = cursor.execute("""SELECT a.name, r.score, r.date_created FROM Assessments a, Results r
WHERE a.asmt_id = r.asmt_id
AND r.user_id = ?;""", (user_id,)).fetchall()
    for each in data:
        print(f"{each[0]:30}{each[1]:5}{each[2]:>15}")

def accountMenu(user_id, connection, cursor, fromManager=False):
    loginChanged = False
    userUpdates = {}
    test = cursor.execute('SELECT username FROM Users WHERE user_id = ?', (user_id,)).fetchone()[0]
    if not test:
        print('Invalid user_id')
        return False
    while True:
        if fromManager:
            selection = input(f"""***ACCOUNT for {test}***
(1) Update Password
(2) Update Username
(3) Update Name
(4) Update Phone
(5) Give manager
(6) Remove manager
(7) Deactivate account
(8) Reactivate account
(B)ack
> """).lower()
        else:
            selection = input(f"""***ACCOUNT for {test}***
(1) Update Password
(2) Update Username
(3) Update Name
(4) Update Phone
(B)ack
> """).lower()
        
        if selection == 'b':
            fieldNames = ''
            values = []
            for each in userUpdates:
                fieldNames += f"{each} = ?,"
                values.append(userUpdates[each])
            fieldNames = fieldNames.rstrip(',')
            values.append(user_id)
            if fieldNames:
                cursor.execute(f"UPDATE Users SET {fieldNames} WHERE user_id = ?", tuple(values))
            connection.commit()
            return loginChanged
        if selection == '1':
            newPassword = bytes(input("New password: "), 'utf8')
            userUpdates['password'] = bcrypt.hashpw(newPassword, bcrypt.gensalt())
            loginChanged = True
        if selection == '2':
            userUpdates['username'] = input("New username: ")
            loginChanged = True
        if selection == '3':
            userUpdates['first_name'] = input("New first name: ")
            userUpdates['last_name'] = input("New last name: ")
        if selection == '4':
            userUpdates['phone'] = input("New phone number: ")
        if fromManager and selection == '5':
            userUpdates['manager'] = 1
        if fromManager and selection == '6':
            userUpdates['manager'] = 0
        if fromManager and selection == '7':
            userUpdates['active'] = 0
        if fromManager and selection == '8':
            userUpdates['active'] = 1

def CSVfromSQL(cursor, fileName, sql):
    data = cursor.execute(sql).fetchall()
    columnNames = []
    for each in cursor.description:
        columnNames.append(each[0])
    finishedName = fileName + '_' + str(datetime.date.today()) + '.csv'
    with open(finishedName, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(columnNames)
        writer.writerows(data)


def viewMenu(username, connection, cursor):
    print("***View Data***")
    while True:
        selection = input("""(1) View all users
(2) View Reports by User
(3) View Report by Competency
(B)ack
> """).lower()
        if selection == 'b':
            break
        if selection == '1':
            printTable(cursor, 'Users')
            continue
        if selection == '2':
            printTable(cursor, 'Users')
            while True:
                user_id = input("Enter a user_id or search for a name\n> ")
                if user_id.isdigit():
                    reportType = input("Would you like to view this user's (C)ompetencies or (A)ssessments?").lower()
                    if reportType == 'c':
                        printUserCompetencies(user_id, connection, cursor)
                        export = input("Type EXPORT to save this report as a csv file, or press Enter to cancel.\n> ")
                        if export == 'EXPORT':
                            username = cursor.execute("SELECT username FROM Users WHERE user_id = ?", (user_id,)).fetchone()[0] + '_Competencies'
                            CSVfromSQL(cursor, username, f'''SELECT c.name, r.score, r.date_created FROM Competencies c, Results r, Assessments a
WHERE a.asmt_id = r.asmt_id
AND a.comp_id = c.comp_id
AND r.user_id = {user_id};''')
                    if reportType == 'a':
                        printUserResults(user_id, connection, cursor)
                        export = input("Type EXPORT to save this report as a csv file, or press Enter to cancel.\n> ")
                        if export == 'EXPORT':
                            username = cursor.execute("SELECT username FROM Users WHERE user_id = ?", (user_id,)).fetchone()[0] + '_Results'
                            CSVfromSQL(cursor, username, f'''SELECT a.name, r.score, r.date_created FROM Assessments a, Results r
WHERE a.asmt_id = r.asmt_id
AND r.user_id = {user_id};''')
                else:
                    data = cursor.execute('SELECT user_id, username, first_name, last_name FROM Users').fetchall()
                    for row in data:
                        if user_id in row[1] or user_id in row[2] or user_id in row[3]:
                            print(f'{row[0]:<5}{row[1]:<15}{row[2]:<15}{row[3]}')
                    continue
                break
        if selection == '3':
            printTable(cursor, 'Competencies')
            comp_id = input("Select a comp_id to view its report, or press Enter to cancel\n> ")
            if not comp_id:
                pass
            else:
                printTable(cursor, 'Competencies', sql = '''SELECT u.first_name, u.last_name, MAX(r.score) as 'Highest Score' FROM Users u, Assessments a, Results r
WHERE u.user_id = r.user_id AND r.asmt_id = a.asmt_id AND a.comp_id = 1
GROUP BY u.user_id;''')
                export = input("Type EXPORT to save this report as a csv file, or press Enter to cancel.\n> ")
                if export == 'EXPORT':
                    comp_name = cursor.execute("SELECT name FROM Competencies WHERE comp_id = ?", (comp_id,)).fetchone()[0]
                    CSVfromSQL(cursor, comp_name, '''SELECT u.first_name, u.last_name, MAX(r.score) as 'Highest Score' FROM Users u, Assessments a, Results r
WHERE u.user_id = r.user_id AND r.asmt_id = a.asmt_id AND a.comp_id = 1
GROUP BY u.user_id;''')


def managerMenu(username, connection, cursor):
    print(f"***Welcome, {username}***")
    user_id = cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,)).fetchone()[0]
    while True:
        selection = input("""(M)y user account
(V)iew Data
(1) Create new user
(2) Create new Competency
(3) Create new Assessment
(4) Enter an Assessment Result
(5) Edit a User
(6) Edit a Competency
(7) Edit an Assessment
(8) Edit an Assessment Result
(E)xport all Assessment Data
(I)mport Assessment Data
(L)ogout
> """).lower()
        if selection == 'l':
            break
        if selection == 'm':
            userMenu(username, connection, cursor)
        if selection == 'v':
            viewMenu(username, connection, cursor)
        if selection == 'e':
            CSVfromSQL(cursor, "Assessment_Data", "SELECT user_id, asmt_id, score, date_created, manager_id FROM Results")
        if selection == 'i':
            fileName = input("Enter the full name of the file to import\n> ")
            try:
                with open(fileName, 'r') as file:
                    reader = csv.reader(file)
                    header = next(reader)
                    if header != ['user_id', 'asmt_id', 'score', 'date_created', 'manager_id']:
                        print("That file is incorrectly formatted.")
                        continue
                    for row in reader:
                        cursor.execute("INSERT INTO Results (user_id, asmt_id, score, date_created, manager_id) VALUES (?,?,?,?,?)", row)
                    connection.commit()
            except:
                print("That file doesn't exist, or the data was incompatible.")
        if selection == '1':
            command = createRecord(cursor, 'Users', runNow = False)
            try:
                cursor.execute(command[0], command[1])
                connection.commit()
                print("User created!")
            except:
                print("User creation failed, that username is taken.")
            continue
        if selection == '2':
            createRecord(cursor, 'Competencies')
            connection.commit()
            continue
        if selection == '3':
            createRecord(cursor, 'Assessments')
            connection.commit()
            continue
        if selection == '4':
            sql = createRecord(cursor, 'Results', runNow = False)
            if sql[1].index('') < 4:
                print('Required fields left blank, results not added')
            else:
                cursor.execute(sql[0], sql[1])
            connection.commit()
            continue
        if selection == '5':
            printTable(cursor, 'Users', showInactive = True)
            user = input('Select a user_id from the table above\n> ')
            accountMenu(int(user), connection, cursor, fromManager=True)
            connection.commit()
            continue
        if selection == '6':
            printTable(cursor, 'Competencies')
            comp_id = input('Select a comp_id from the table above\n> ')
            compName = input('Enter a new name for the competency, or press Enter to cancel\n> ')
            if not comp_id or not compName:
                continue
            cursor.execute('UPDATE Competencies SET name = ? WHERE comp_id = ?', (compName, comp_id))
            connection.commit()
            continue
        if selection == '7':
            printTable(cursor, 'Assessments')
            asmt_id = input("Select an asmt_id from the table above\n> ")
            edit = input("Change the (N)ame or the (C)ompetency this Assessment is for?").lower()
            if edit == 'n':
                asmtName = input('Enter a new name for the Assessment, or press Enter to cancel\n> ')
                if not asmtName:
                    continue
                cursor.execute('UPDATE Assessments SET name = ? WHERE asmt_id = ?', (asmtName, asmt_id))
                connection.commit()
                continue
            if edit == 'c':
                printTable(cursor, 'Competencies')
                comp_id = input('Select a comp_id from the table above, or press Enter to cancel\n> ')
                if not comp_id:
                    continue
                cursor.execute('UPDATE Assessments SET comp_id = ? WHERE asmt_id = ?', (comp_id, asmt_id))
                connection.commit()
                continue
        if selection == '8':
            printTable(cursor, 'Results', sql='SELECT r.result_id, u.first_name, u.last_name, a.name, r.score, r.date_created FROM Results r, Users u, Assessments a WHERE r.user_id = u.user_id AND r.asmt_id = a.asmt_id;')
            result_id = input('Select a result_id from the table above\n> ')
            edit = input('Edit the (S)core, or (D)elete this Result\n> ').lower()
            if edit == 's':
                score = input('Enter a score between 0 and 4, or press Enter to cancel\n> ')
                if not score:
                    continue
                cursor.execute('UPDATE Results SET score = ? WHERE result_id = ?', (score, result_id))
                connection.commit()
                continue
            if edit == 'd':
                sure = input('Enter YES if you are sure you want to delete this result\n> ')
                if sure == 'YES':
                    cursor.execute('DELETE FROM Results WHERE Result_id = ?', (result_id,))
                    connection.commit()
                    continue

def userMenu(username, connection, cursor):
    print(f"***Welcome, {username}***")
    user_id = cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,)).fetchone()[0]
    while True:
        selection = input("""(1) My Competencies
(2) My Assessment Results
(3) My Account
(L)ogout
> """).lower()
        if selection == 'l':
            break
        if selection == '1':
            printUserCompetencies(user_id, connection, cursor)
            continue
        if selection == '2':
            printUserResults(user_id, connection, cursor)
            continue
        if selection == '3':
            if accountMenu(user_id, connection, cursor):
                print("Login information updated. Returning to Login.")
                break
            continue
        

connection = sqlite3.connect("Comp_Tracker.db")
cursor = connection.cursor()

while True:
    selection = input("""***COMPETENCY TRACKER LOGIN***
(L)og in
(Q)uit
> """).lower()

    if selection == 'q':
        break
    if selection == 'l':
        username = input("Username: ")
        password = bytes(input("Password: "), 'utf8')
        hashed = cursor.execute("SELECT password, manager, active FROM Users WHERE username = ?", (username,)).fetchone()
        if not hashed or hashed[2] == 0:
            print("That user doesn't exist.")
            continue
        if not bcrypt.checkpw(password, hashed[0]):
            print("Incorrect password.")
            continue
        elif hashed[1]:
            managerMenu(username, connection, cursor)
        else:
            userMenu(username, connection, cursor)



