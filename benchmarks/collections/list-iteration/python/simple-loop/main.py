import sys

def main():
    size = int(sys.argv[1])
    
    data = list(range(size))
    
    total = 0
    for element in data:
        total += element

if __name__ == "__main__":
    main()
