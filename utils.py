from passlib.context import CryptContext
from models import Deployment, Cluster
from uuid import uuid4
import time
import threading
import redis
from sqlalchemy.orm import sessionmaker
from database import engine

SessionLocal = sessionmaker(bind=engine)

# Initialize Redis client
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_invite_code():
    return str(uuid4())

def generate_unique_cluster_name():
    return f"cluster-{uuid4()}"

def simulate_deployment_execution(deployment_data, lock, schedule_callback):
    """Simulates a deployment taking 3 minutes."""
    session = SessionLocal()
    try:
        time.sleep(15)
        with lock:
            deployment = session.query(Deployment).filter(Deployment.id == deployment_data['deployment'].id).first()
            if not deployment:
                print(f"Deployment {deployment_data['deployment'].id} not found.")
                return

            cluster = session.query(Cluster).filter(Cluster.name == deployment_data['cluster_name']).first()
            if not cluster:
                print(f"Cluster {deployment_data['cluster_name']} not found.")
                return

            # Mark deployment as completed
            deployment.status = "completed"

            # Release resources
            cluster.allocated_cpu -= deployment.required_cpu
            cluster.allocated_ram -= deployment.required_ram
            cluster.allocated_gpu -= deployment.required_gpu

            # Ensure no negative resources
            cluster.allocated_cpu = max(0, cluster.allocated_cpu)
            cluster.allocated_ram = max(0, cluster.allocated_ram)
            cluster.allocated_gpu = max(0, cluster.allocated_gpu)

            session.commit()

            print(f"Deployment {deployment.id} completed. Resources released.")
            print(f"Cluster {cluster.name} resources: CPU={cluster.allocated_cpu}, RAM={cluster.allocated_ram}, GPU={cluster.allocated_gpu}")

            schedule_callback(deployment_data['cluster_name'], session)
    except Exception as e:
        print(f"Error in simulate_deployment_execution: {e}")
    finally:
        session.close()


def enqueue_deployment(cluster_name, deployment_id, priority):
    """Enqueue a deployment into Redis."""
    redis_client.zadd(cluster_name, {deployment_id: priority})
    print(f"Enqueued deployment {deployment_id} with priority {priority}. Current queue: {list_queue(cluster_name)}")


def dequeue_deployment(cluster_name):
    """Dequeue the highest-priority deployment from Redis."""
    result = redis_client.zpopmax(cluster_name)
    print(f"Dequeued deployment: {result}. Current queue: {list_queue(cluster_name)}")
    return int(result[0][0]) if result else None


def list_queue(cluster_name):
    """List all deployments in the Redis queue for a cluster."""
    print(f"Listing queue for cluster {cluster_name}...")
    return redis_client.zrange(cluster_name, 0, -1, withscores=True)


def delete_deployment_from_queue(cluster_name, deployment_id, db, schedule_callback):
    """Remove a deployment from the Redis queue and release resources if running."""
    redis_client.zrem(cluster_name, deployment_id)

    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if deployment:
        if deployment.status == "running":
            # Release resources back to the cluster
            cluster = deployment.cluster
            cluster.allocated_cpu -= deployment.required_cpu
            cluster.allocated_ram -= deployment.required_ram
            cluster.allocated_gpu -= deployment.required_gpu

            # Ensure resources do not go negative
            cluster.allocated_cpu = max(0, cluster.allocated_cpu)
            cluster.allocated_ram = max(0, cluster.allocated_ram)
            cluster.allocated_gpu = max(0, cluster.allocated_gpu)

            db.commit()
            
            schedule_callback(cluster_name, db)
        
        db.delete(deployment)
        db.commit()
