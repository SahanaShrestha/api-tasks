from queries import run_queries
from export import export_to_txt, export_to_csv

results = run_queries()

export_to_txt(results)
export_to_csv(results)