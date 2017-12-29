from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from main import db

engine = create_engine(
    'sqlite:///database.db', 
    connect_args = {'check_same_thread': False},
    convert_unicode = True, 
    echo = True
    )

db.session = scoped_session(
    sessionmaker(
        autocommit = False,
        autoflush = False,
        bind = engine
        )
    )

Base = declarative_base()
Base.query = db.session.query_property()

def init_db():

    napalm_dispatcher = {
                        # Ax: ASR1000, IOS XE
                        'Bnet-A1': ('192.168.243.78', 'ios'),
                        'Bnet-A2': ('192.168.243.79', 'ios'),
                        'Bnet-A3': ('192.168.243.69', 'ios'),
                        'Bnet-A4': ('192.168.243.135', 'ios'),
                        # C10K, IOS
                        'Bnet-E1': ('192.168.243.101', 'ios'),
                        'Bnet-E2': ('192.168.243.102', 'ios'),
                        'Bnet-E3': ('192.168.243.103', 'ios'),
                        'Bnet-E4': ('192.168.243.104', 'ios'),
                        'Bnet-E5': ('192.168.243.105', 'ios'),
                        'Bnet-E6': ('192.168.243.106', 'ios'),
                        'Bnet-E7': ('192.168.243.107', 'ios'),
                        # C7600, IOS
                        'Bnet-I1': ('192.168.243.108', 'ios'),
                        'Bnet-I2': ('192.168.243.110', 'ios'),
                        'Bnet-I3': ('192.168.243.115', 'ios'),
                        'Bnet-I4': ('192.168.243.116', 'ios'),
                        'Bnet-I5': ('192.168.243.119', 'ios'),
                        # Gx: GSR12K, IOS XR
                        'Bnet-G1': ('192.168.243.21', 'ios-xr'),
                        'Bnet-G2': ('192.168.243.22', 'ios-xr'),
                        # ASR9K, IOS XR 
                        'Bnet-P1': ('192.168.243.23', 'ios-xr'),
                        # Juniper devices, Junos
                        'Bnet-J1': ('192.168.243.77', 'junos'),
                        'Bnet-J2': ('192.168.243.82', 'junos'),
                        'Bnet-J3': ('192.168.243.83', 'junos'),
                        'Bnet-J4': ('192.168.243.117', 'junos'),
                        'Bnet-J5': ('192.168.243.118', 'junos'),
                        'Bnet-J6': ('192.168.243.133', 'junos'),
                        # Cisco RR, ASK1K, IOS-XE
                        'Bnet-R7': ('192.168.243.80', 'ios'),
                        # Cisco nexus
                        'Bnet-N1': ('192.168.243.134', 'nx-os'),
                        }

    # import all modules here that might define models so that
    # they will be registered properly on the metadata.
    # import models
    Base.metadata.create_all(bind=engine)
    
    from objects.models import Router
    # for hostname, (ip_address, operating_system) in napalm_dispatcher.items():
    #     values = {'name': hostname, 'ip_address': ip_address, 'operating_system': operating_system}
    #     device = Router(**values)
    #     db.session.add(device)
    # db.session.commit()
