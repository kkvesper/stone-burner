SAMPLE_CONFIG = {
    'environments': [
        {
            'name': 'e1',
            'aws_profile': 'e1_profile',
            'states_bucket': 'e1_bucket'
        },
        {
            'name': 'e2',
            'aws_profile': 'e2',
            'default': True,
            'states_bucket': 'e2_bucket'
        }
    ],
    'projects': {
        'p1': [
            'c1',
            'c2',
            {'c3': {'validate': {'check-variables': False}}},
            {
                'my-generic-component': [
                    'mg1',
                    'mg2',
                    {'mg3': {'validate': {'check-variables': False}}},
                ]
            },
            {'other-generic-component': ['oc1', 'oc2']},
        ],
        'p2': [
            'c1',
            {
                'c2': {'validate': {'check-variables': False}},
                'c3': {'validate': {'check-variables': False}},
            },
        ]
    }
}
