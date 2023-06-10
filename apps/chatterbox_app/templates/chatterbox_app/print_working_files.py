import os

print_files = ["base.html", "home.html", "my_account.html"]

for file_name in print_files:
    try:
        with open(os.path.join(os.getcwd(), file_name), "r") as file:
            print(f"Here is my {file_name}:")
            print(f"```{file_name}")
            print(file.read())
            print("```")
    except FileNotFoundError:
        print(f"{file_name} not found in the root directory.")