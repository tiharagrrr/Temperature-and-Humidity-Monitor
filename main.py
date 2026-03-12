import subprocess


def main():
    choice = 0
    print("Select an option:")
    print("1. Run basic sensor readings")
    print("2. Start web server")
    print("3. Deploy to Google Sheets App Script")
    print("4. Exit")

    while choice != 4:
        choice = input("> ")

        if choice == "1":
            subprocess.call(["python", "a1_basic_sensor.py"])
        elif choice == "2":
            subprocess.call(["python", "a2_web_server.py"])
        elif choice == "3":
            # Update the code in a3_part_1.py to deploy to Google Sheets App Script
            pass
        elif choice == "4":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
