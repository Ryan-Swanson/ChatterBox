import os
import subprocess
print_files = ["urls.py", "models.py", "forms.py", "views.py"]
template_files = ["templates/chatterbox_app/add_note.html"]

# Call the tree command in Bash
# tree_output = subprocess.check_output(["tree", "-I", "*.pyc"])
# print(f'```project_structure_tree\n{tree_output.decode()}\n```')

for file_name in print_files + template_files:
    try:
        with open(os.path.join(os.getcwd(), file_name), "r") as file:
            print(f"Here is my {file_name}:")
            print(f"```{file_name}")
            print(file.read())
            print("```")
    except FileNotFoundError:
        print(f"{file_name} not found in the root directory.")

