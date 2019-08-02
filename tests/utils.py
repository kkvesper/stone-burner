SAMPLE_CONFIG = {
    'environments': [
        {
            'name': 'e1',
            'aws_profile': 'e1_profile',
            'aws_region': 'r1',
            'states_bucket': 'e1_bucket'
        },
        {
            'name': 'e2',
            'aws_profile': 'e2',
            'aws_region': 'r2',
            'default': True,
            'states_bucket': 'e2_bucket'
        }
    ],
    'projects': {
        'p1': [
            'c1',
            'c2',
            {
                'my-generic-component': [
                    'mg1',
                    'mg2',
                ]
            },
            {'other-generic-component': ['oc1', 'oc2']},
        ],
        'p2': [
            'c1',
            {
                'c2': {'validate': {}},
                'c3': {'validate': {}},
            },
        ]
    }
}
