from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String, index=True)


class Theme(Base):
    __tablename__ = 'theme'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")

    @property
    def serialize(self):
        '''Return object data in easily serializeable format'''
        return {
            'name': self.name,
            'id': self.id,
        }


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    summary = Column(String)
    cover = Column(String(250))
    release_date = Column(String(80), nullable=False)
    release_date_number = Column(Integer, nullable=False)
    url = Column(String(250), nullable=False)
    theme_id = Column(Integer, ForeignKey("theme.id"))
    theme = relationship("Theme")
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'summary': self.summary,
            'cover': self.cover,
            'release_date': self.release_date,
            'url': self.url,
            'theme_id': self.theme_id
        }

engine = create_engine('sqlite:///gamedatabasewithusers.db')
Base.metadata.create_all(engine)
