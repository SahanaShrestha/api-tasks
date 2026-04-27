# Find Largest Number in a List without max()

def find_largest(numbers):
    if not numbers:
        return None
    
    largest = numbers[0]
    
    for num in numbers[1:]:
        if num > largest:
            largest = num
    
    return largest

if __name__ == "__main__":
    test_list1 = [5, 2, 9, 1, 7, 3]
    print(f"List: {test_list1}")
    print(f"Largest number: {find_largest(test_list1)}\n")
    
    test_list2 = [15, 8, 42, 23, 99, 10]
    print(f"List: {test_list2}")
    print(f"Largest number: {find_largest(test_list2)}\n")
    
    test_list3 = [-5, -10, -1, -20]
    print(f"List: {test_list3}")
    print(f"Largest number: {find_largest(test_list3)}\n")
    
    user_input = input("Enter numbers separated by spaces: ")
    numbers = [float(x) for x in user_input.split()]
    print(f"Largest number: {find_largest(numbers)}")
