# Multiplication Table Generator


number = int(input("Enter a number: "))


print(f"\nMultiplication Table for {number}:")
print("-" * 30)

for i in range(1, 11):
    result = number * i
    print(f"{number} x {i} = {result}")
