import os

# 获取当前工作目录
current_directory = os.getcwd()

# 获取当前工作目录下的所有文件名
file_names = os.listdir(current_directory)

# 打印所有文件的完整目录位置
for file_name in file_names:
    file_path = os.path.join(current_directory, file_name)
    print(f"{file_name} 的目录位置：{file_path}")

