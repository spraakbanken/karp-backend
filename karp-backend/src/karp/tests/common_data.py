CONFIG_PLACES = {
    "resource_id": "places",
    "resource_name": "Platser i Sverige",
    "fields": {
        "name": {"type": "string", "required": True},
        "municipality": {"collection": True, "type": "number", "required": True},
        "population": {"type": "number"},
        "area": {"type": "number"},
        "density": {"type": "number"},
        "code": {"type": "number", "required": True},
    },
    "sort": "name",
    "id": "code",
    "referenceable": ["name", "municipality", "code"],
}


PLACES = [
    {
        "code": 1,
        "name": "Grund test",
        "population": 3122,
        "area": 6312,
        "density": 6312,
        "municipality": [1],
        "larger_place": 7  # Alhamn
        # "smaller_places": 9 "Bjurvik2"
    },
    {
        "code": 2,
        "name": "Grunds",
        "population": 6312,
        "area": 20000,
        "density": 6,
        "municipality": [1],
    },
    {
        "code": 3,
        "name": "Botten test",
        "population": 4133,
        "area": 50000,
        "density": 7,
        "municipality": [2, 3],
        "larger_place": 8  # "Bjurvik"
        # "smaller_places": 4 "Hambo"
    },
    {
        "code": 4,
        "name": "Hambo",
        "population": 4132,
        "area": 50000,
        "municipality": [2, 3],
        "larger_place": 3  # Botten test
        # "smaller_places": 7 "Alhamn"
    },
    {"code": 5, "name": "Rutvik", "area": 50000, "municipality": [2, 3]},
    {
        "code": 6,
        "name": "Alvik",
        "area": 6312,
        "population": 6312,
        "density": 12,
        "municipality": [3]
        # "smaller_places": 7  "Bjurvik"
    },
    {
        "code": 7,
        "name": "Alhamn",
        "area": 6312,
        "population": 3812,
        "density": 12,
        "municipality": [2, 3],
        "larger_place": 4  # Hambo
        # "smaller_places": 1  "Grund test"
    },
    {
        "code": 8,
        "name": "Bjurvik",
        "area": 6312,
        "population": 6212,
        "density": 12,
        "municipality": [2, 3],
        "larger_place": 6  # Alvik
        # "smaller_places": 1  "Botten test"
    },
    {
        "code": 9,
        "name": "Bjurvik2",
        "area": 7312,
        "population": 641,
        "density": 12,
        "municipality": [2],
        "larger_place": 1,  # Grund test
    },
]


MUNICIPALITIES = [
    {
        "code": 1,
        "name": "Luleå kommun",
        "state": "Norrbottens län",
        "region": "Norrbotten",
        "capital": "Luleå",
        "area": {"land": 2094.08, "water": 148.39},
        "population": {"value": {"total": 77860}, "density": {"total": 37.18}},
    },
    {
        "code": 2,
        "name": "Norsjö kommun",
        "state": "Västerbottens län",
        "region": "Västerbotten",
        "capital": "Norsjö",
        "area": {"land": 1739.15, "water": 184.43},
        "population": {"value": {"total": 4101}, "density": {"total": 2.36}},
    },
    {
        "code": 3,
        "name": "Piteå kommun",
        "state": "Norrbottens län",
        "region": "Norrbotten",
        "capital": "Piteå",
        "area": {"land": 3086.04, "water": 149.04},
        "population": {"value": {"total": 42108}, "density": {"total": 13.64}},
    },
]
