
def add(a, b):
    return a + b

def divide(a, b):
    return a / b  # This has a potential division by zero issue

def main():
    print(add(1, 2))
    print(divide(10, 0))  # This will cause an error

if __name__ == "__main__":
    main()
