"""Every 5 minutes during betting hours: scrape the books in parallel,
compare every pair, alert on Telegram, clean up."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from surebets import pipeline

LEAGUE = "nba"
WEBSITES = ["pinnacle", "teapuesto"]
INTERVAL_MINUTES = 5
SCRAPE_TIMEOUT_SECONDS = 120
# hours in UTC-5 (Lima) when bets could be placed by hand
HOURS = "0,1,2,14,15,16,17,18,19,20,21,22,23"

with DAG(
    f"{LEAGUE}_surebets",
    start_date=datetime(2022, 10, 1),
    schedule=f"*/{INTERVAL_MINUTES} {HOURS} * * *",
    dagrun_timeout=timedelta(minutes=INTERVAL_MINUTES),
    catchup=False,
    max_active_runs=1,
    tags=[LEAGUE, "scrape", "surebets", "telegram", "selenium"],
) as dag:
    trigger = PythonOperator(
        task_id="trigger",
        python_callable=pipeline.trigger,
        op_kwargs={"league": LEAGUE, "websites": WEBSITES},
    )
    calculate = PythonOperator(
        task_id="calculate",
        python_callable=pipeline.calculate,
        trigger_rule="all_done",  # compare whatever books did come back
        op_kwargs={"league": LEAGUE, "websites": WEBSITES},
    )
    clean = PythonOperator(
        task_id="clean",
        python_callable=pipeline.clean,
        trigger_rule="all_done",
        op_kwargs={"league": LEAGUE},
    )
    for website in WEBSITES:
        scrape = PythonOperator(
            task_id=f"scrape_{website}",
            python_callable=pipeline.scrape,
            op_kwargs={"league": LEAGUE, "website": website, "timeout": SCRAPE_TIMEOUT_SECONDS},
        )
        trigger >> scrape >> calculate
    calculate >> clean
