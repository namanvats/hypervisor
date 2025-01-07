from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="organization")


class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    total_cpu = Column(Integer, nullable=False)
    total_ram = Column(Integer, nullable=False)
    total_gpu = Column(Integer, nullable=False)
    allocated_cpu = Column(Integer, default=0)
    allocated_ram = Column(Integer, default=0)
    allocated_gpu = Column(Integer, default=0)


class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"))
    docker_image = Column(String, nullable=False)
    required_cpu = Column(Integer, nullable=False)
    required_ram = Column(Integer, nullable=False)
    required_gpu = Column(Integer, nullable=False)
    status = Column(String, default="in_queue")
    priority = Column(Integer, default=1)


User.organization = relationship("Organization", back_populates="users")
Organization.clusters = relationship("Cluster", back_populates="organization")
Cluster.organization = relationship("Organization", back_populates="clusters")
Cluster.deployments = relationship("Deployment", back_populates="cluster")
Deployment.cluster = relationship("Cluster", back_populates="deployments")