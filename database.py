from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('mysql+mysqldb://root@localhost/lebonscrap?use_unicode=1', convert_unicode=True, echo=True)
session = scoped_session(sessionmaker(autocommit=False,
    autoflush=False,
    bind=engine))

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import sys
    sys.path.append('../lebonscrap/')
    from Entities import Appartement, Photo
    #Base.metadata.create_all(bind=engine)
