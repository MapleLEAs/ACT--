AIRPORT_REGIONS = {
    'tower': {
        'name': '塔台区域',
        'center': (0, 0),
        'radius': 50,
        'devices': ['VHF-001', 'VHF-002', 'VHF-003'],
        'env_zone': 'controlled'
    },
    'runway_A': {
        'name': '跑道18L区域',
        'center': (100, 50),
        'radius': 300,
        'devices': ['ILS-001', 'DME-001', 'VOR-001'],
        'env_zone': 'outdoor'
    },
    'runway_B': {
        'name': '跑道36R区域',
        'center': (-100, -50),
        'radius': 300,
        'devices': ['ILS-002', 'DME-002', 'VOR-002'],
        'env_zone': 'outdoor'
    },
    'navigation_station': {
        'name': '导航站',
        'center': (200, 100),
        'radius': 100,
        'devices': ['HF-001', 'HF-002', 'HF-003'],
        'env_zone': 'semi_outdoor'
    }
}