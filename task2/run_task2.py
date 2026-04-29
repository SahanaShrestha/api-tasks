from insert_users import insert_users
from queries import query_all_users, query_same_city

insert_users()

print("\nAll Users Sorted:\n")
query_all_users()

print("\nUsers From Same City:\n")
query_same_city()