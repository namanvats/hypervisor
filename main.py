from fastapi import FastAPI
from database import SessionLocal
from models import Cluster
from scheduler import periodic_scheduler
from routes import user_routes, organization_routes, cluster_routes, deployment_routes

app = FastAPI()

@app.on_event("startup")
def start_schedulers():
    db = SessionLocal()
    clusters = db.query(Cluster).all()
    for cluster in clusters:
        periodic_scheduler(cluster.name, db, interval=30)
    print("Schedulers started for all clusters.")

# Include routes
app.include_router(user_routes.router, prefix="/user")
app.include_router(organization_routes.router, prefix="/organization")
app.include_router(cluster_routes.router, prefix="/cluster")
app.include_router(deployment_routes.router, prefix="/deployment")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
