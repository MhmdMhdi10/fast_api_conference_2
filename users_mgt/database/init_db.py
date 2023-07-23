from database import engine, Base
# from auth import User

Base.metadata.create_all(bind=engine)
