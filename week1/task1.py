# Student Grade Calculator


marks = float(input("Enter student's marks: "))


if marks >= 90:
    grade = "A"
elif marks >= 80:
    grade = "B"
elif marks >= 70:
    grade = "C"
elif marks >= 60:
    grade = "D"
else:
    grade = "Fail"


print(f"Marks: {marks}")
print(f"Grade: {grade}")
