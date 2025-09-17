import os

dir = "./datasets/"
#read all the files in the directory
file = os.listdir(dir)
#.DS_Store and MAG file , we need to remove it
file.remove('.DS_Store')
file.remove('example')
file.remove('dblp')
file.remove('synthetic')
dir = "./datasets/synthetic/"
dir_path = "synthetic"
synthetic_file = os.listdir(dir)
synthetic_file = [os.path.join(dir_path, f) for f in synthetic_file]
file.extend(synthetic_file)

# file = ["walmart"]
# for f in file:
#     for k in range(5,25,5):
#         for g in range(5,25,5):
#             print(f"python main.py --network {file} --k {k} --g {g} &&")


#write the output to a file
with open("run.sh", "w") as f:
    for file in file:
        for k in range(5,25,5):
            for g in range(5,25,5):
                f.write(f"python main.py --network {file} --k {k} --g {g} &&\n")