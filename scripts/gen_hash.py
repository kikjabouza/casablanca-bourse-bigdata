import bcrypt
h = bcrypt.hashpw(b"trino123", bcrypt.gensalt(10))
print(h.decode().replace("$2b$", "$2y$"))
