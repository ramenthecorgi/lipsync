from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, func

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
