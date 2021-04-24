import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


from sqlalchemy import Column, Integer, String, LargeBinary, BigInteger, Text


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    
    email = Column(String(128))
    
    codename = Column(String(64))
    name = Column(String(64))

    login_link = Column(String(32))

    sessions = relationship('RecordingSession')
    
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        assert self.id is not None
        return str(self.id)


class RecordingSession(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)

    participant_id = Column(Integer, ForeignKey(User.id))
    participant = relationship(User, back_populates="sessions")

    sample_rate = Column(Integer)
    channels = Column(Integer)
    stage_name = Column(String(32))
    start_timestamp = Column(BigInteger)

    labels = relationship('AudioLabel')
    chunks = relationship('AudioChunk')

    @property
    def start_date(self):
        import datetime
        ts = datetime.datetime.utcfromtimestamp(self.start_timestamp)
        return ts.strftime('%Y.%m.%d %H:%M (UTC)')


class AudioLabel(Base):
    __tablename__ = 'labels'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey(RecordingSession.id))
    session = relationship(RecordingSession, back_populates="labels")

    label = Column(String(64))
    offset = Column(Integer)
    # end_sample = Column(Integer)
    extra = Column(Text)


class AudioChunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey(RecordingSession.id))
    session = relationship(RecordingSession, back_populates="chunks")
    
    offset = Column(Integer)
    sample_count = Column(Integer)
    pcm = Column(LargeBinary)
    
    
# class PendingSession(Base):
#     __tablename__ = 'pending_sessions'
#
#     id = Column(Integer, primary_key=True)
#     session_id = Column(Integer, ForeignKey(RecordingSession.id))
#     session = relationship(RecordingSession, back_populates="chunks")
#
#     start_ts_sec = Column(BigInteger)
    



