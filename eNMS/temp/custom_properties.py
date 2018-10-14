CustomDevice = type(
    'CustomDevice',
    (Object,),
    {
        '__tablename__': 'CustomDevice',
        'id': Column(Integer, ForeignKey('Object.id'), primary_key=True),
        'test': Column(Integer, default='a')
    }
)
