import threading
import time
from services import schedule_deployments

scheduler_locks = {}

def periodic_scheduler(cluster_name, db, interval=30):
    if cluster_name not in scheduler_locks:
        scheduler_locks[cluster_name] = threading.Lock()
    
    def schedule_task():
        while True:
            try:
                with scheduler_locks[cluster_name]:
                    print(f"Periodic scheduler running for cluster {cluster_name}...")
                    schedule_deployments(cluster_name, db)
            except Exception as e:
                print(f"Error in scheduler for cluster {cluster_name}: {e}")
            finally:
                time.sleep(interval)

    threading.Thread(target=schedule_task, daemon=True).start()
    print(f"[Scheduler] Started periodic scheduler for cluster: {cluster_name}")